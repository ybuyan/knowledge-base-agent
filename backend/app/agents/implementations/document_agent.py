import uuid
import os
from typing import Dict, Any
from app.agents.base import BaseAgent, agent_engine
from app.skills.engine import SkillEngine
from app.core.config_loader import config_loader


class DocumentAgent(BaseAgent):
    
    @property
    def agent_id(self) -> str:
        return "document_agent"
    
    @property
    def name(self) -> str:
        return "文档处理Agent"
    
    def __init__(self):
        self.skill_engine = SkillEngine()
    
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        file_path = input_data.get("file_path")
        original_filename = input_data.get("original_filename")
        
        if not file_path:
            raise ValueError("file_path is required")
        
        document_id = str(uuid.uuid4())
        # Use original_filename if provided, otherwise fall back to basename
        filename = original_filename if original_filename else os.path.basename(file_path)
        
        context = {
            "file_path": file_path,
            "document_id": document_id,
            "document_name": filename
        }
        
        result = await self.skill_engine.execute("document_upload", context)
        
        return {
            "document_id": document_id,
            "filename": filename,
            "chunk_count": result.get("chunk_count", 0),
            "status": "success"
        }


agent_engine.register(DocumentAgent())
