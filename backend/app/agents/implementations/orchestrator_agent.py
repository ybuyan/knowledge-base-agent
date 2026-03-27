"""
OrchestratorAgent - 轻量意图路由 Agent

纯规则意图识别，无需 LLM，将请求路由到 QAAgent 或 MemoryAgent。
hybrid 意图时并行调用两者，合并结果。
"""

import asyncio
import logging
from typing import Dict, Any, List

from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

# 触发记忆检索的关键词
MEMORY_KEYWORDS: List[str] = ["上次", "之前", "刚才", "你说过", "我问过", "刚刚说", "前面提到"]

# 触发混合模式的关键词（同时查文档 + 记忆）
HYBRID_KEYWORDS: List[str] = ["对比", "不同", "区别", "和之前", "和上次", "比较"]


def _detect_intent(query: str) -> str:
    """
    纯规则意图识别，返回 'qa' | 'memory' | 'hybrid'
    """
    for kw in HYBRID_KEYWORDS:
        if kw in query:
            return "hybrid"
    for kw in MEMORY_KEYWORDS:
        if kw in query:
            return "memory"
    return "qa"


class OrchestratorAgent(BaseAgent):
    """
    编排 Agent

    职责：意图识别 + 路由，不做任何业务逻辑。
    - qa      → 直接委托 QAAgent（通过 agent_engine）
    - memory  → 委托 MemoryAgent
    - hybrid  → 并行调用 QAAgent + MemoryAgent，合并结果

    input_data 字段:
        query (str): 用户查询
        session_id (str, optional): 会话 ID
        history (list, optional): 对话历史
    """

    @property
    def agent_id(self) -> str:
        return "orchestrator_agent"

    @property
    def name(self) -> str:
        return "编排路由Agent"

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        from app.agents.base import agent_engine  # 延迟导入避免循环

        query: str = input_data.get("query", "")
        session_id: str = input_data.get("session_id", "")
        history: list = input_data.get("history", [])

        intent = _detect_intent(query)
        logger.info("OrchestratorAgent 意图识别: '%s' -> %s", query[:30], intent)

        if intent == "memory":
            return await agent_engine.execute(
                "memory_agent",
                {"query": query, "session_id": session_id}
            )

        if intent == "hybrid":
            qa_task = agent_engine.execute(
                "qa_agent",
                {"query": query, "history": history, "session_id": session_id}
            )
            memory_task = agent_engine.execute(
                "memory_agent",
                {"query": query, "session_id": session_id}
            )
            qa_result, memory_result = await asyncio.gather(qa_task, memory_task)
            return {
                "intent": "hybrid",
                "qa": qa_result,
                "memories": memory_result.get("memories", []),
            }

        # 默认 qa
        return await agent_engine.execute(
            "qa_agent",
            {"query": query, "history": history, "session_id": session_id}
        )
