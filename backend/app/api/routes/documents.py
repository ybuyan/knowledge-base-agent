from fastapi import APIRouter, UploadFile, File, HTTPException, Query, BackgroundTasks, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import os
import uuid
import logging
import asyncio

from app.models.document import DocumentDB, DocumentStatusModel
from app.core.chroma import delete_document_vectors
from app.core.constants import DocumentConstants
from app.rag.keyword_index import delete_keyword_index
from app.api.dependencies import require_hr

router = APIRouter()
logger = logging.getLogger(__name__)

# Background task for processing server-uploaded files
_scanning_task = None

async def scan_and_process_server_files():
    """Background task to scan and process files uploaded directly to server"""
    while True:
        try:
            logger.info("Scanning for new server-uploaded files...")
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    # Extract doc_id from filename
                    parts = filename.split('_', 1)
                    if len(parts) == 2:
                        doc_id, original_filename = parts
                    else:
                        doc_id = str(uuid.uuid4())
                        original_filename = filename
                        # Rename to standard format
                        new_file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{original_filename}")
                        os.rename(file_path, new_file_path)
                        file_path = new_file_path
                    
                    # Check if already in database
                    existing_doc = await DocumentDB.get(doc_id)
                    if not existing_doc:
                        # New file found, process it
                        logger.info(f"Found new server-uploaded file: {original_filename}")
                        await process_document_task(file_path, doc_id, original_filename)
            
            # Sleep for 30 seconds before next scan
            await asyncio.sleep(30)
        except Exception as e:
            logger.error(f"Error in scan_and_process_server_files: {e}")
            await asyncio.sleep(30)

def start_background_scanner():
    """Start the background file scanner"""
    global _scanning_task
    if _scanning_task is None:
        _scanning_task = asyncio.create_task(scan_and_process_server_files())
        logger.info("Started background file scanner")


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    size: int
    uploadTime: str
    error: Optional[str] = None
    chunk_count: Optional[int] = None


class DocumentsListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int


UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

_memory_fallback: dict = {}


def _get_doc_storage(doc_id: str) -> Optional[dict]:
    return _memory_fallback.get(doc_id)


def _set_doc_storage(doc_id: str, data: dict):
    _memory_fallback[doc_id] = data


def _del_doc_storage(doc_id: str):
    _memory_fallback.pop(doc_id, None)


def _list_doc_storage() -> list:
    return list(_memory_fallback.values())


async def process_document_task(file_path: str, doc_id: str, filename: str):
    try:
        # Check if document exists in database, if not create it
        existing_doc = await DocumentDB.get(doc_id)
        if not existing_doc:
            # Document not in database (file was uploaded directly to server)
            # Create a new document record
            stat = os.stat(file_path)
            upload_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            doc = DocumentStatusModel(
                id=doc_id,
                filename=filename,
                status="INDEXING",
                size=stat.st_size,
                uploadTime=upload_time,
                file_path=file_path
            )
            await DocumentDB.save(doc)
            logger.info(f"Created new document record for server-uploaded file: {filename}")
        else:
            await DocumentDB.update_status(doc_id, "INDEXING")
        
        _set_doc_storage(doc_id, {**(_get_doc_storage(doc_id) or {}), "status": "INDEXING"})
        logger.info(f"开始处理文档: {filename} (ID: {doc_id})")
        
        from app.agents import agent_engine
        
        result = await agent_engine.execute("document_agent", {
            "file_path": file_path,
            "original_filename": filename
        })
        
        chunk_count = result.get("chunk_count", 0)
        await DocumentDB.update_status(doc_id, "READY", chunk_count=chunk_count)
        _set_doc_storage(doc_id, {**(_get_doc_storage(doc_id) or {}), "status": "READY", "chunk_count": chunk_count})
        logger.info(f"文档处理成功: {filename}, chunk_count: {chunk_count}")

        # 异步触发流程提取，不阻塞上传响应
        try:
            from app.services.flow_extractor import get_flow_extractor
            from app.skills.processors.document import DocumentParser
            parser = DocumentParser()
            parse_result = await parser.process(
                {"file_path": file_path},
                {"supported_formats": ["pdf", "docx", "doc", "txt", "md"]}
            )
            document_text = parse_result.get("document_text", "")
            if document_text:
                flow_extractor = get_flow_extractor()
                asyncio.create_task(
                    flow_extractor.extract_and_save(document_text, doc_id, filename)
                )
                logger.info(f"[FlowExtractor] 已触发流程提取任务: {filename}")
        except Exception as fe:
            logger.warning(f"[FlowExtractor] 触发流程提取失败 (不影响上传): {fe}")

    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        await DocumentDB.update_status(doc_id, "ERROR", error=str(e), error_detail=error_detail)
        _set_doc_storage(doc_id, {**(_get_doc_storage(doc_id) or {}), "status": "ERROR", "error": str(e)})
        logger.error(f"文档处理失败: {filename}\n错误: {e}\n详情:\n{error_detail}")


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    allowed_types = DocumentConstants.SUPPORTED_EXTENSIONS
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}. 支持的类型: {', '.join(allowed_types)}"
        )
    
    doc_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{file.filename}")
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    upload_time = datetime.now().isoformat()
    
    doc = DocumentStatusModel(
        id=doc_id,
        filename=file.filename,
        status="QUEUED",
        size=len(content),
        uploadTime=upload_time,
        file_path=file_path
    )
    
    await DocumentDB.save(doc)
    _set_doc_storage(doc_id, doc.model_dump())
    
    background_tasks.add_task(process_document_task, file_path, doc_id, file.filename)
    
    return DocumentResponse(
        id=doc_id,
        filename=file.filename,
        status="QUEUED",
        size=len(content),
        uploadTime=upload_time
    )


def _sync_files_from_storage():
    """Sync files from upload directory to database"""
    try:
        files_synced = 0
        for filename in os.listdir(UPLOAD_DIR):
            file_path = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                # Check if file is already in database
                # Extract doc_id from filename (format: docid_filename.ext)
                parts = filename.split('_', 1)
                if len(parts) == 2:
                    doc_id, original_filename = parts
                else:
                    # Generate new ID for files without doc_id prefix
                    doc_id = str(uuid.uuid4())
                    original_filename = filename
                    # Rename file to include doc_id
                    new_file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{original_filename}")
                    os.rename(file_path, new_file_path)
                    file_path = new_file_path
                
                # Check if already in memory storage
                if not _get_doc_storage(doc_id):
                    stat = os.stat(file_path)
                    doc_data = {
                        "id": doc_id,
                        "filename": original_filename,
                        "status": "READY",  # Assume ready if file exists
                        "size": stat.st_size,
                        "uploadTime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "file_path": file_path,
                        "chunk_count": None,
                        "error": None
                    }
                    _set_doc_storage(doc_id, doc_data)
                    files_synced += 1
                    logger.info(f"Synced file from storage: {original_filename}")
        
        if files_synced > 0:
            logger.info(f"Total files synced from storage: {files_synced}")
    except Exception as e:
        logger.error(f"Error syncing files from storage: {e}")


@router.get("", response_model=DocumentsListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100)
):
    # First sync any files from storage directory
    _sync_files_from_storage()
    
    # Get docs from database
    docs, total = await DocumentDB.list(page, pageSize)
    
    # Also get docs from memory storage (includes synced files)
    storage_docs = _list_doc_storage()
    
    # Merge and deduplicate
    all_doc_ids = set()
    merged_docs = []
    
    # Add database docs first
    for doc in docs:
        if doc.id not in all_doc_ids:
            all_doc_ids.add(doc.id)
            merged_docs.append(doc.model_dump())
    
    # Add storage docs if not already in list
    for doc_data in storage_docs:
        if doc_data["id"] not in all_doc_ids:
            all_doc_ids.add(doc_data["id"])
            merged_docs.append(doc_data)
    
    # Sort by upload time (newest first)
    merged_docs.sort(key=lambda x: x.get("uploadTime", ""), reverse=True)
    
    total = len(merged_docs)
    start = (page - 1) * pageSize
    end = start + pageSize
    docs_data = merged_docs[start:end]
    
    return DocumentsListResponse(
        documents=[
            DocumentResponse(
                id=doc["id"],
                filename=doc["filename"],
                status=doc["status"],
                size=doc["size"],
                uploadTime=doc["uploadTime"],
                error=doc.get("error"),
                chunk_count=doc.get("chunk_count")
            )
            for doc in docs_data
        ],
        total=total
    )


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    doc = await DocumentDB.get(doc_id)
    
    if not doc:
        doc_data = _get_doc_storage(doc_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        doc = DocumentStatusModel(**doc_data)
    
    file_path = doc.file_path
    
    # Delete the physical file
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from database
    await DocumentDB.delete(doc_id)
    _del_doc_storage(doc_id)
    
    # Delete vectors from ChromaDB
    delete_document_vectors(doc_id)
    
    # Delete keyword index from MongoDB
    await delete_keyword_index(doc_id)
    
    return {"message": "Document deleted successfully", "id": doc_id}


@router.post("/{doc_id}/reindex")
async def reindex_document(doc_id: str, background_tasks: BackgroundTasks):
    doc = await DocumentDB.get(doc_id)
    
    if not doc:
        doc_data = _get_doc_storage(doc_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail="文档不存在")
        doc = DocumentStatusModel(**doc_data)
    
    file_path = doc.file_path
    
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    await DocumentDB.update_status(doc_id, "QUEUED")
    _set_doc_storage(doc_id, {**doc.model_dump(), "status": "QUEUED"})
    
    background_tasks.add_task(process_document_task, file_path, doc_id, doc.filename)
    
    return {"message": "重新索引已开始", "id": doc_id}
