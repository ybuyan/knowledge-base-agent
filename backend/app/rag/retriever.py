"""
RAG 检索器
支持向量检索 + 重排序
"""

import logging
from typing import Any, Dict, List, Optional

from app.core.chroma import get_documents_collection
from app.core.config_loader import config_loader
from app.core.embeddings import get_embeddings
from app.rag.reranker import get_reranker

logger = logging.getLogger(__name__)


class RAGRetriever:
    def __init__(
        self,
        documents_top_k: int = 5,
        conversations_top_k: int = 3,
        score_threshold: float = 0.7,
        use_rerank: bool = True,
        rerank_top_k: int = 3,
    ):
        self.documents_top_k = documents_top_k
        self.conversations_top_k = conversations_top_k
        self.score_threshold = score_threshold
        self.use_rerank = use_rerank
        self.rerank_top_k = rerank_top_k
        self.embeddings = get_embeddings()

    async def retrieve_documents(
        self, query: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        query_embedding = await self.embeddings.aembed_query(query)
        collection = get_documents_collection()

        where_filter = self._build_where_filter(filters)

        initial_top_k = (
            self.documents_top_k * 3 if self.use_rerank else self.documents_top_k
        )

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=initial_top_k,
            where=where_filter,
        )

        documents = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0

                documents.append(
                    {
                        "id": results["ids"][0][i] if results["ids"] else f"doc_{i}",
                        "content": doc,
                        "metadata": metadata,
                        "score": distance,
                    }
                )

        if self.use_rerank and documents:
            documents = await self._rerank_documents(query, documents)

        return documents[: self.documents_top_k]

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
        self, query: str, documents: List[Dict[str, Any]]
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
