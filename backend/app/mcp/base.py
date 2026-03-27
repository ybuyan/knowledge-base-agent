"""
MCP 基类定义
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class MCPTool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPResource(BaseModel):
    uri: str
    name: str
    description: str
    mimeType: str = "text/plain"


class MCPPromptArgument(BaseModel):
    name: str
    description: str
    required: bool = False


class MCPPrompt(BaseModel):
    name: str
    description: str
    arguments: List[MCPPromptArgument]


class MCPCapabilities(BaseModel):
    tools: Optional[Dict] = None
    resources: Optional[Dict] = None
    prompts: Optional[Dict] = None


class MCPServer:
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}

    def register_tool(self, tool: MCPTool) -> None:
        self.tools[tool.name] = tool

    def register_resource(self, resource: MCPResource) -> None:
        self.resources[resource.uri] = resource

    def register_prompt(self, prompt: MCPPrompt) -> None:
        self.prompts[prompt.name] = prompt

    def list_tools(self) -> List[MCPTool]:
        return list(self.tools.values())

    def list_resources(self) -> List[MCPResource]:
        return list(self.resources.values())

    def list_prompts(self) -> List[MCPPrompt]:
        return list(self.prompts.values())

    def get_capabilities(self) -> MCPCapabilities:
        return MCPCapabilities(
            tools={"listChanged": False} if self.tools else None,
            resources={"subscribe": False, "listChanged": False} if self.resources else None,
            prompts={"listChanged": False} if self.prompts else None,
        )

    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.tools.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
        return await self._execute_tool_impl(name, arguments)

    async def _execute_tool_impl(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError("Subclasses must implement _execute_tool_impl")

    async def read_resource(self, uri: str) -> str:
        resource = self.resources.get(uri)
        if not resource:
            raise ValueError(f"Resource not found: {uri}")
        return await self._read_resource_impl(uri)

    async def _read_resource_impl(self, uri: str) -> str:
        raise NotImplementedError("Subclasses must implement _read_resource_impl")

    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict:
        raise NotImplementedError("Subclasses must implement get_prompt")


class MCPServerRegistry:
    _servers: Dict[str, MCPServer] = {}

    @classmethod
    def register(cls, server: MCPServer) -> None:
        cls._servers[server.name] = server

    @classmethod
    def get(cls, name: str) -> Optional[MCPServer]:
        return cls._servers.get(name)

    @classmethod
    def list_all(cls) -> List[str]:
        return list(cls._servers.keys())

    @classmethod
    def list_servers(cls) -> List[MCPServer]:
        return list(cls._servers.values())
