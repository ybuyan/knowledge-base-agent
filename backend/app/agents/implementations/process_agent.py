"""
ProcessAgent — 流程指引 Agent

从 SkillEngine 中找到匹配的 process 类型 skill，
执行流程引擎，返回结构化响应（含 ui_components）。
"""
import logging
from typing import Any, Dict

from app.agents.base import BaseAgent, agent_engine
from app.skills.engine import SkillEngine

logger = logging.getLogger(__name__)


class ProcessAgent(BaseAgent):

    @property
    def agent_id(self) -> str:
        return "process_agent"

    @property
    def name(self) -> str:
        return "流程指引Agent"

    def __init__(self):
        self.skill_engine = SkillEngine()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query: str = input_data.get("query", "")
        session_id: str = input_data.get("session_id", "")
        process_action: str = input_data.get("process_action", "next")
        process_input: Dict = input_data.get("process_input", {})
        flow_id: str = input_data.get("flow_id", "")

        # 找到匹配的 process skill（支持 skill id 或 display_name）
        skill_id = self._resolve_skill_id(flow_id) if flow_id else self._match_skill(query)
        if not skill_id:
            return {
                "answer": "抱歉，暂未找到对应的流程，请尝试描述您需要办理的业务。",
                "ui_components": None,
            }

        context = {
            "query": query,
            "session_id": session_id,
            "process_action": process_action,
            "process_input": process_input,
            "username": input_data.get("username", ""),
        }

        try:
            result = await self.skill_engine.execute(skill_id, context)
            return result
        except Exception as e:
            logger.error("ProcessAgent execute error: %s", e)
            return {
                "answer": f"流程执行异常：{e}，请联系 HR。",
                "ui_components": None,
            }

    def _resolve_skill_id(self, flow_id: str) -> str:
        """将 flow_id（可能是 skill id 或 display_name）解析为真实 skill id"""
        skills = self.skill_engine.skill_loader._cache
        # 直接匹配 id
        if flow_id in skills:
            return flow_id
        # 按 display_name 匹配
        for sid, skill in skills.items():
            if skill.name == flow_id or skill.id == flow_id:
                return sid
        return ""

    def _match_skill(self, query: str) -> str:
        """根据 query 匹配 process 类型的 skill"""
        skills = self.skill_engine.skill_loader._cache
        for sid, skill in skills.items():
            if skill.frontmatter.get("skill_type") != "process":
                continue
            for trigger in skill.triggers:
                if trigger in query:
                    return sid
        return ""


agent_engine.register(ProcessAgent())
