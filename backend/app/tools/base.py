from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    id: str
    name: str
    description: str
    enabled: bool = True
    category: str = "general"
    parameters: Dict[str, Any]
    implementation: str


class BaseTool(ABC):
    """Tool 基类"""

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        pass


class ToolRegistry:
    """Tool 注册表"""

    _tools: Dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool_id: str):
        def decorator(tool_class):
            instance = tool_class()
            cls._tools[tool_id] = instance
            return tool_class

        return decorator

    @classmethod
    def get(cls, tool_id: str) -> BaseTool:
        tool = cls._tools.get(tool_id)
        if not tool:
            raise ValueError(f"Tool not found: {tool_id}")
        return tool

    @classmethod
    def list_all(cls) -> List[str]:
        return list(cls._tools.keys())

    @classmethod
    def get_tools_for_llm(cls) -> List[Dict[str, Any]]:
        """获取LLM可用的Tool定义列表"""
        tools = []
        for tool_id, tool in cls._tools.items():
            defn = tool.definition
            if defn.enabled:
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": defn.name,
                            "description": defn.description,
                            "parameters": defn.parameters,
                        },
                    }
                )
        return tools
