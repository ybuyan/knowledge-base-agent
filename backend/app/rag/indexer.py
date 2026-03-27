"""
文档索引器
支持智能分块和丰富元数据
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import uuid
from app.core.embeddings import get_embeddings
from app.core.chroma import get_documents_collection
from app.skills.processors.document import DocumentParser, SmartTextSplitter
from app.core.constants import DocumentConstants
import logging

logger = logging.getLogger(__name__)


class DocumentIndexer:
    
    def __init__(
        self, 
        chunk_size: int = 500, 
        chunk_overlap: int = 50,
        doc_type: str = "general"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.doc_type = doc_type
        self.embeddings = get_embeddings()
        self.collection = get_documents_collection()
        self.parser = DocumentParser()
        self.splitter = SmartTextSplitter()
    
    async def index_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        document_id = str(uuid.uuid4())
        filename = os.path.basename(file_path)
        
        parse_result = await self.parser.process(
            {"file_path": file_path},
            {"supported_formats": DocumentConstants.SUPPORTED_FORMATS}
        )
        
        text = parse_result.get("document_text", "")
        
        detected_type = self.splitter.detect_doc_type(text, filename)
        doc_type = metadata.get("doc_type") if metadata else None or detected_type
        
        split_result = await self.splitter.process(
            {"document_text": text},
            {
                "doc_type": doc_type,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            }
        )
        
        chunks_data = split_result.get("chunks", [])
        
        if not chunks_data:
            return {
                "document_id": document_id,
                "chunk_count": 0,
                "status": "empty"
            }
        
        chunks = [c["content"] if isinstance(c, dict) else c for c in chunks_data]
        
        chunk_embeddings = await self.embeddings.aembed_documents(chunks)
        
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = self._build_metadata(
            document_id=document_id,
            filename=filename,
            chunks=chunks_data,
            doc_type=doc_type,
            extra_metadata=metadata
        )
        
        self.collection.add(
            ids=ids,
            embeddings=chunk_embeddings,
            documents=chunks,
            metadatas=metadatas
        )
        
        logger.info(f"文档索引完成: {filename}, 类型={doc_type}, 分块数={len(chunks)}")
        
        return {
            "document_id": document_id,
            "filename": filename,
            "chunk_count": len(chunks),
            "doc_type": doc_type,
            "status": "indexed"
        }
    
    def _build_metadata(
        self,
        document_id: str,
        filename: str,
        chunks: List[Any],
        doc_type: str,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        metadatas = []
        now = datetime.utcnow().isoformat()
        
        base_metadata = {
            "document_id": document_id,
            "document_name": filename,
            "doc_type": doc_type,
            "indexed_at": now,
            **self._extract_file_metadata(filename),
            **(extra_metadata or {})
        }
        
        for i, chunk in enumerate(chunks):
            if isinstance(chunk, dict):
                chunk_meta = chunk.get("metadata", {})
            else:
                chunk_meta = {}
            
            meta = {
                **base_metadata,
                "chunk_index": i,
                "char_count": len(chunk["content"] if isinstance(chunk, dict) else chunk),
                **chunk_meta
            }
            
            metadatas.append(meta)
        
        return metadatas
    
    def _extract_file_metadata(self, filename: str) -> Dict[str, Any]:
        ext = os.path.splitext(filename)[1].lower().replace(".", "")
        
        file_type_map = {
            "pdf": "policy",
            "docx": "document",
            "doc": "document",
            "txt": "text",
            "md": "technical"
        }
        
        return {
            "file_extension": ext,
            "file_type": file_type_map.get(ext, "unknown")
        }
    
    async def remove_document(self, document_id: str) -> bool:
        try:
            all_ids = self.collection.get()["ids"]
            ids_to_delete = [id for id in all_ids if id.startswith(document_id)]
            
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                logger.info(f"文档已删除: {document_id}, 删除分块数={len(ids_to_delete)}")
            
            return True
        except Exception as e:
            logger.error(f"删除文档失败: {e}")
            return False
    
    async def reindex_document(
        self,
        file_path: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        await self.remove_document(document_id)
        return await self.index_document(file_path, metadata)
    
    async def get_document_chunks(self, document_id: str) -> List[Dict[str, Any]]:
        try:
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            chunks = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"]):
                    chunks.append({
                        "id": results["ids"][i],
                        "content": doc,
                        "metadata": results["metadatas"][i] if results["metadatas"] else {}
                    })
            
            return sorted(chunks, key=lambda x: x["metadata"].get("chunk_index", 0))
        except Exception as e:
            logger.error(f"获取文档分块失败: {e}")
            return []
    
    async def update_chunk_metadata(
        self,
        chunk_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        try:
            self.collection.update(
                ids=[chunk_id],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"更新分块元数据失败: {e}")
            return False
