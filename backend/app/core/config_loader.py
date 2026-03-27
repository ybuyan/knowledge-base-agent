import json
import os
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    _instance = None
    _configs: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
    
    def _get_config_path(self, config_name: str) -> Path:
        config_paths = {
            "skills": self.base_dir / "skills" / "config.json",
            "prompts": self.base_dir / "prompts" / "config.json",
            "tools": self.base_dir / "tools" / "config.json",
            "agents": self.base_dir / "agents" / "config.json",
            "settings": self.base_dir / "core" / "config.json"
        }
        return config_paths.get(config_name)
    
    def load(self, config_name: str) -> Dict[str, Any]:
        if config_name not in self._configs:
            config_path = self._get_config_path(config_name)
            if config_path and config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._configs[config_name] = json.load(f)
            else:
                self._configs[config_name] = {}
        return self._configs[config_name]
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        skills_config = self.load("skills")
        for skill in skills_config.get("skills", []):
            if skill["id"] == skill_id:
                return skill
        return None
    
    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        prompts_config = self.load("prompts")
        for prompt in prompts_config.get("prompts", []):
            if prompt["id"] == prompt_id:
                return prompt
        return None
    
    def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        tools_config = self.load("tools")
        for tool in tools_config.get("tools", []):
            if tool["id"] == tool_id:
                return tool
        return None
    
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        agents_config = self.load("agents")
        for agent in agents_config.get("agents", []):
            if agent["id"] == agent_id:
                return agent
        return None
    
    def get_setting(self, path: str, default: Any = None) -> Any:
        settings = self.load("settings")
        keys = path.split(".")
        value = settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def reload(self, config_name: Optional[str] = None):
        if config_name:
            self._configs.pop(config_name, None)
        else:
            self._configs.clear()


config_loader = ConfigLoader()
