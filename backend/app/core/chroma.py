from app.config import settings
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Optional
import os


_client: Optional[chromadb.Client] = None


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
