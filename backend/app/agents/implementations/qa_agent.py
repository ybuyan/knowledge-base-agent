import uuid
from typing import Dict, Any, AsyncGenerator
from app.agents.base import BaseAgent, agent_engine
from app.skills.engine import SkillEngine
from app.core.config_loader import config_loader


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
        question = input_data.get("question")
        session_id = input_data.get("session_id", str(uuid.uuid4()))
        
        if not question:
            raise ValueError("question is required")
        
        context = {
            "query": question,
            "question": question,
            "session_id": session_id
        }
        
        result = await self.skill_engine.execute("qa_rag", context)
        
        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "session_id": session_id
        }
    
    async def run_stream(self, input_data: Dict[str, Any]) -> AsyncGenerator[str, None]:
        from app.core.llm import get_llm
        from app.prompts.manager import prompt_manager
        
        question = input_data.get("question")
        session_id = input_data.get("session_id", str(uuid.uuid4()))
        
        context = {
            "query": question,
            "question": question,
            "session_id": session_id
        }
        
        result = await self.skill_engine.execute("qa_rag", context)
        
        llm = get_llm()
        prompts = prompt_manager.render("qa_rag", {
            "context": context.get("context", ""),
            "question": question
        })
        
        messages = [
            ("system", prompts["system"]),
            ("human", prompts["user"])
        ]
        
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content


agent_engine.register(QAAgent())
