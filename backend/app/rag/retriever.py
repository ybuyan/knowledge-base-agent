"""
RAG 检索器
支持向量检索 + 重排序
"""
from typing import List, Dict, Any, Optional
from app.core.embeddings import get_embeddings
from app.core.chroma import get_documents_collection, get_conversations_collection
from app.core.config_loader import config_loader
from app.rag.reranker import get_reranker
import logging

logger = logging.getLogger(__name__)


class RAGRetriever:
    def __init__(
        self,
        documents_top_k: int = 5,
        conversations_top_k: int = 3,
        score_threshold: float = 0.7,
        use_rerank: bool = True,
        rerank_top_k: int = 3
    ):
        self.documents_top_k = documents_top_k
        self.conversations_top_k = conversations_top_k
        self.score_threshold = score_threshold
        self.use_rerank = use_rerank
        self.rerank_top_k = rerank_top_k
        self.embeddings = get_embeddings()
    
    async def retrieve_documents(
        self, 
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        query_embedding = await self.embeddings.aembed_query(query)
        collection = get_documents_collection()
        
        where_filter = self._build_where_filter(filters)
        
        initial_top_k = self.documents_top_k * 3 if self.use_rerank else self.documents_top_k
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=initial_top_k,
            where=where_filter
        )
        
        documents = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0
                
                documents.append({
                    "id": results["ids"][0][i] if results["ids"] else f"doc_{i}",
                    "content": doc,
                    "metadata": metadata,
                    "score": distance
                })
        
        if self.use_rerank and documents:
            documents = await self._rerank_documents(query, documents)
        
        return documents[:self.documents_top_k]
    
    def _build_where_filter(self, filters: Optional[Dict[str, Any]]) -> Optional[Dict]:
        if not filters:
            return None
        
        conditions = []
        for key, value in filters.items():
            if isinstance(value, list):
                conditions.append({key: {"$in": value}})
            else:
                conditions.append({key: value})
        
        if len(conditions) == 0:
            return None
        elif len(conditions) == 1:
            return conditions[0]
        else:
            return {"$and": conditions}
    
    async def _rerank_documents(
        self, 
        query: str, 
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        try:
            reranker = get_reranker()
            if reranker.is_available():
                logger.debug(f"对 {len(documents)} 个文档进行重排序")
                return reranker.rerank(query, documents, self.documents_top_k)
            else:
                logger.debug("重排序模型不可用，使用原始排序")
                return documents
        except Exception as e:
            logger.warning(f"重排序失败: {e}，使用原始排序")
            return documents
    
    async def retrieve_conversations(self, query: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query_embedding = await self.embeddings.aembed_query(query)
        collection = get_conversations_collection()
        
        where_filter = None
        if session_id:
            where_filter = {"session_id": session_id}
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=self.conversations_top_k,
            where=where_filter
        )
        
        conversations = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                conversations.append({
                    "content": doc,
                    "metadata": metadata
                })
        
        return conversations
    
    async def retrieve_all(
        self, 
        query: str, 
        session_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        documents = await self.retrieve_documents(query, filters)
        conversations = await self.retrieve_conversations(query, session_id)
        
        return {
            "documents": documents,
            "conversations": conversations
        }
    
    def build_context(self, documents: List[Dict[str, Any]], conversations: List[Dict[str, Any]]) -> str:
        context_parts = []
        
        if documents:
            context_parts.append("=== 相关文档 ===")
            for i, doc in enumerate(documents):
                score_info = f" (相关度: {doc.get('rerank_score', doc.get('score', 0)):.2f})" if doc.get('rerank_score') or doc.get('score') else ""
                context_parts.append(f"\n[{i+1}] {doc['content']}{score_info}")
        
        if conversations:
            context_parts.append("\n\n=== 相关对话历史 ===")
            for conv in conversations:
                context_parts.append(f"\n{conv['content']}")
        
        return "\n".join(context_parts)
