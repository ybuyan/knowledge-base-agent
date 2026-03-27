from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.core.mongodb import mongodb
import logging

logger = logging.getLogger(__name__)


class DocumentStatusModel(BaseModel):
    id: str
    filename: str
    status: str = "QUEUED"
    size: int = 0
    uploadTime: str
    file_path: Optional[str] = None
    chunk_count: Optional[int] = None
    error: Optional[str] = None
    error_detail: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentDB:
    
    @staticmethod
    async def save(doc: DocumentStatusModel) -> bool:
        if mongodb.database is None:
            logger.warning("MongoDB未连接，无法保存文档状态")
            return False
        
        try:
            doc.updated_at = datetime.utcnow()
            await mongodb.database.document_status.update_one(
                {"id": doc.id},
                {"$set": doc.model_dump()},
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"保存文档状态失败: {e}")
            return False
    
    @staticmethod
    def save_sync(doc: DocumentStatusModel) -> bool:
        """Synchronous version for batch processing"""
        try:
            from pymongo import MongoClient
            client = MongoClient("mongodb://localhost:27017")
            db = client["agent"]
            
            doc.updated_at = datetime.utcnow()
            db.document_status.update_one(
                {"id": doc.id},
                {"$set": doc.model_dump()},
                upsert=True
            )
            client.close()
            return True
        except Exception as e:
            logger.error(f"同步保存文档状态失败: {e}")
            return False
    
    @staticmethod
    async def get(doc_id: str) -> Optional[DocumentStatusModel]:
        if mongodb.database is None:
            return None
        
        try:
            doc = await mongodb.database.document_status.find_one({"id": doc_id})
            if doc:
                doc.pop("_id", None)
                return DocumentStatusModel(**doc)
            return None
        except Exception as e:
            logger.error(f"获取文档状态失败: {e}")
            return None
    
    @staticmethod
    async def list(page: int = 1, page_size: int = 10) -> tuple[List[DocumentStatusModel], int]:
        if mongodb.database is None:
            return [], 0
        
        try:
            total = await mongodb.database.document_status.count_documents({})
            skip = (page - 1) * page_size
            cursor = mongodb.database.document_status.find().sort("created_at", -1).skip(skip).limit(page_size)
            docs = []
            async for doc in cursor:
                doc.pop("_id", None)
                docs.append(DocumentStatusModel(**doc))
            return docs, total
        except Exception as e:
            logger.error(f"获取文档列表失败: {e}")
            return [], 0
    
    @staticmethod
    async def delete(doc_id: str) -> bool:
        if mongodb.database is None:
            return False
        
        try:
            result = await mongodb.database.document_status.delete_one({"id": doc_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"删除文档状态失败: {e}")
            return False
    
    @staticmethod
    async def update_status(doc_id: str, status: str, **kwargs) -> bool:
        if mongodb.database is None:
            return False
        
        try:
            update_data = {"status": status, "updated_at": datetime.utcnow()}
            update_data.update(kwargs)
            result = await mongodb.database.document_status.update_one(
                {"id": doc_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"更新文档状态失败: {e}")
            return False
