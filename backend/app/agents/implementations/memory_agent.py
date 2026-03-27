"""
MemoryAgent - 对话记忆检索 Agent

从 ChromaDB conversations 集合中检索历史对话，
支持按 session_id 过滤，为多轮对话提供语义记忆能力。
"""

import logging
from typing import Dict, Any, List, AsyncGenerator

from app.agents.base import BaseAgent
from app.core.chroma import get_conversations_collection
from app.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)

TOP_K_MEMORIES = 5


class MemoryAgent(BaseAgent):
    """
    记忆检索 Agent

    职责：根据当前查询，从历史对话向量库中检索语义相关的记忆片段。
    不负责生成回答，只返回结构化的记忆列表供上层（OrchestratorAgent）使用。

    input_data 字段:
        query (str): 当前用户查询
        session_id (str, optional): 会话 ID，用于过滤历史
    """

    @property
    def agent_id(self) -> str:
        return "memory_agent"

    @property
    def name(self) -> str:
        return "记忆检索Agent"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检索与 query 语义相关的历史对话记忆。

        返回:
            {"memories": [...], "query": query}
            每条 memory 包含 content、metadata、distance
        """
        query: str = input_data.get("query", "")
        session_id: str = input_data.get("session_id", "")

        if not query:
            return {"memories": [], "query": query}

        embeddings = get_embeddings()
        query_embedding = await embeddings.aembed_query(query)

        collection = get_conversations_collection()

        try:
            kwargs: Dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": TOP_K_MEMORIES,
            }
            if session_id:
                kwargs["where"] = {"session_id": session_id}

            results = collection.query(**kwargs)
        except Exception as e:
            logger.warning("MemoryAgent 检索失败: %s", e)
            return {"memories": [], "query": query}

        memories: List[Dict[str, Any]] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, distances):
            memories.append({
                "content": doc,
                "metadata": meta or {},
                "distance": dist,
            })

        logger.info("MemoryAgent 检索到 %d 条记忆", len(memories))
        return {"memories": memories, "query": query}
