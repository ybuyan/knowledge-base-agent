import uuid
from typing import Any, Dict

from app.agents.base import BaseAgent, agent_engine
from app.core.config_loader import config_loader
from app.skills.engine import SkillEngine


class QAAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "qa_agent"

    @property
    def name(self) -> str:
        return "问答Agent"

    def __init__(self):
        self.skill_engine = SkillEngine()

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        question = input_data.get("question") or input_data.get("query")
        session_id = input_data.get("session_id", str(uuid.uuid4()))

        if not question:
            raise ValueError("question is required")

        context = {"query": question, "question": question, "session_id": session_id}

        result = await self.skill_engine.execute("qa_rag", context)

        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "session_id": session_id,
        }


agent_engine.register(QAAgent())
