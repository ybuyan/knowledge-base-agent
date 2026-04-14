from app.config import settings
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

_client: Optional[chromadb.Client] = None

EMBEDDING_DIMENSIONS = {
    "text-embedding-v1": 1536,
    "text-embedding-v2": 1536,
    "text-embedding-v3": 1024,
    "text-embedding-ada-002": 1536,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}


def get_expected_dimension() -> int:
    """获取当前 embedding 模型期望的维度"""
    model = settings.embedding_model
    return EMBEDDING_DIMENSIONS.get(model, 1536)


def get_collection_dimension(collection) -> Optional[int]:
    """获取集合当前的维度"""
    try:
        if collection.count() == 0:
            return None
        sample = collection.get(limit=1, include=["embeddings"])
        if sample["embeddings"] and len(sample["embeddings"]) > 0:
            return len(sample["embeddings"][0])
        return None
    except Exception:
        return None


def get_chroma_client() -> chromadb.Client:
    global _client
    if _client is None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
    return _client


def get_documents_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="documents",
        metadata={"description": "文档知识库"}
    )


def get_conversations_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="conversations",
        metadata={"description": "对话历史"}
    )


def reset_collections(force: bool = False):
    """
    检查并修复维度不匹配问题
    
    Args:
        force: 是否强制重建（忽略维度检查）
    """
    client = get_chroma_client()
    expected_dim = get_expected_dimension()
    
    need_reset = force
    
    if not force:
        try:
            docs_collection = client.get_collection("documents")
            current_dim = get_collection_dimension(docs_collection)
            
            if current_dim is not None and current_dim != expected_dim:
                logger.warning(f"维度不匹配: 集合维度={current_dim}, 期望维度={expected_dim}")
                need_reset = True
                logger.info("将重建集合以修复维度问题")
        except Exception:
            need_reset = True
    
    if need_reset:
        try:
            client.delete_collection("documents")
            logger.info("已删除 documents 集合")
        except Exception:
            pass
        try:
            client.delete_collection("conversations")
            logger.info("已删除 conversations 集合")
        except Exception:
            pass
        logger.info(f"集合已重建，embedding 维度: {expected_dim}")
    else:
        logger.info(f"集合维度检查通过: {expected_dim}")


def init_chroma():
    get_documents_collection()
    get_conversations_collection()
    return {
        "status": "success",
        "message": "ChromaDB 初始化成功",
        "collections": ["documents", "conversations"]
    }


def get_chroma_stats() -> dict:
    try:
        docs_collection = get_documents_collection()
        convs_collection = get_conversations_collection()
        
        return {
            "status": "success",
            "documents_count": docs_collection.count(),
            "conversations_count": convs_collection.count()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def delete_document_vectors(doc_id: str) -> bool:
    """Delete all vectors associated with a document from ChromaDB"""
    try:
        collection = get_documents_collection()
        
        # 方法1: 尝试通过 metadata 删除
        try:
            collection.delete(where={"document_id": doc_id})
        except Exception as meta_error:
            print(f"Metadata deletion failed: {meta_error}")
        
        # 方法2: 通过 ID 前缀删除（更可靠）
        # 向量 ID 格式: {document_id}_chunk_{i}
        all_ids = collection.get()["ids"]
        ids_to_delete = [id for id in all_ids if id.startswith(doc_id)]
        
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"Deleted {len(ids_to_delete)} vector chunks for document {doc_id}")
        else:
            print(f"No vectors found for document {doc_id}")
        
        return True
    except Exception as e:
        print(f"Error deleting vectors for document {doc_id}: {e}")
        return False
