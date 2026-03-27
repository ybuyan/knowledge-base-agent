"""
MCP 请求分发器
将 JSON-RPC 2.0 方法路由到对应的 MCPServer 处理逻辑
"""
from typing import Optional, Dict, Any
import logging

from app.mcp.base import MCPServerRegistry, MCPCapabilities
from app.mcp.protocol import (
    JSONRPCRequest, JSONRPCResponse, JSONRPCError, MCPErrorCode,
    InitializeResult, ServerInfo, ContentItem, CallToolResult,
    ReadResourceResult, ResourceContent
)

logger = logging.getLogger(__name__)


class ToolNotFoundError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


class PromptNotFoundError(Exception):
    pass


class MCPDispatcher:
    """
    将 JSON-RPC 方法路由到对应的 MCPServer 处理逻辑。
    支持方法：
      initialize, ping,
      tools/list, tools/call,
      resources/list, resources/read,
      prompts/list, prompts/get,
      notifications/initialized (notification, 无响应)
    """

    def __init__(self, registry: MCPServerRegistry = None):
        self.registry = registry or MCPServerRegistry

    def _make_error(self, req_id, code: int, message: str) -> JSONRPCResponse:
        return JSONRPCResponse(
            id=req_id,
            error=JSONRPCError(code=code, message=message)
        )

    def _make_result(self, req_id, result: Any) -> JSONRPCResponse:
        return JSONRPCResponse(id=req_id, result=result)

    async def dispatch(self, request: JSONRPCRequest) -> Optional[JSONRPCResponse]:
        """主入口：根据 method 路由到对应处理方法。notification（id=None）处理后返回 None。"""
        is_notification = request.id is None
        method = request.method
        params = request.params or {}

        # notifications/initialized and other notifications: no response
        if method == "notifications/initialized":
            return None

        try:
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "ping":
                result = await self._handle_ping()
            elif method == "tools/list":
                result = await self._handle_tools_list(params)
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "resources/list":
                result = await self._handle_resources_list(params)
            elif method == "resources/read":
                result = await self._handle_resources_read(params)
            elif method == "prompts/list":
                result = await self._handle_prompts_list(params)
            elif method == "prompts/get":
                result = await self._handle_prompts_get(params)
            else:
                if is_notification:
                    return None
                return self._make_error(request.id, MCPErrorCode.METHOD_NOT_FOUND, f"Method not found: {method}")
        except ToolNotFoundError as e:
            if is_notification:
                return None
            return self._make_error(request.id, MCPErrorCode.TOOL_NOT_FOUND, str(e))
        except ResourceNotFoundError as e:
            if is_notification:
                return None
            return self._make_error(request.id, MCPErrorCode.RESOURCE_NOT_FOUND, str(e))
        except PromptNotFoundError as e:
            if is_notification:
                return None
            return self._make_error(request.id, MCPErrorCode.PROMPT_NOT_FOUND, str(e))
        except Exception as e:
            logger.exception(f"Error handling method {method}")
            if is_notification:
                return None
            return self._make_error(request.id, MCPErrorCode.INTERNAL_ERROR, str(e))

        if is_notification:
            return None
        return self._make_result(request.id, result)

    async def _handle_initialize(self, params: Dict) -> Dict:
        """聚合所有注册 Server 的 capabilities，返回 InitializeResult"""
        servers = self.registry.list_servers()

        merged_tools = None
        merged_resources = None
        merged_prompts = None

        for server in servers:
            caps = server.get_capabilities()
            if caps.tools is not None:
                merged_tools = caps.tools
            if caps.resources is not None:
                merged_resources = caps.resources
            if caps.prompts is not None:
                merged_prompts = caps.prompts

        capabilities = MCPCapabilities(
            tools=merged_tools,
            resources=merged_resources,
            prompts=merged_prompts,
        )

        result = InitializeResult(
            protocolVersion="2024-11-05",
            capabilities=capabilities.model_dump(exclude_none=True),
            serverInfo=ServerInfo(name="knowledge-qa-mcp", version="1.0.0")
        )
        return result.model_dump()

    async def _handle_ping(self) -> Dict:
        return {}

    async def _handle_tools_list(self, params: Dict) -> Dict:
        """遍历 registry 中所有 Server，合并 tool 列表"""
        tools = []
        for server in self.registry.list_servers():
            for tool in server.list_tools():
                tools.append(tool.model_dump())
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict) -> Dict:
        """找到对应 Server，调用 execute_tool；工具不存在返回 TOOL_NOT_FOUND；执行异常返回 isError: true"""
        name = params.get("name")
        arguments = params.get("arguments") or {}

        target_server = None
        for server in self.registry.list_servers():
            if name in server.tools:
                target_server = server
                break

        if target_server is None:
            raise ToolNotFoundError(f"Tool not found: {name}")

        try:
            raw_result = await target_server.execute_tool(name, arguments)
            # If result already has content key, return as-is
            if isinstance(raw_result, dict) and "content" in raw_result:
                return raw_result
            # Convert to text content
            import json
            text = json.dumps(raw_result, ensure_ascii=False) if not isinstance(raw_result, str) else raw_result
            result = CallToolResult(
                content=[ContentItem(type="text", text=text)],
                isError=False
            )
            return result.model_dump()
        except Exception as e:
            result = CallToolResult(
                content=[ContentItem(type="text", text=str(e))],
                isError=True
            )
            return result.model_dump()

    async def _handle_resources_list(self, params: Dict) -> Dict:
        """合并所有 Server 的 resource 列表"""
        resources = []
        for server in self.registry.list_servers():
            for resource in server.list_resources():
                resources.append(resource.model_dump())
        return {"resources": resources}

    async def _handle_resources_read(self, params: Dict) -> Dict:
        """按 URI 找到对应 Server，调用 read_resource；URI 不存在返回 RESOURCE_NOT_FOUND"""
        uri = params.get("uri", "")

        target_server = None
        for server in self.registry.list_servers():
            if uri in server.resources:
                target_server = server
                break

        if target_server is None:
            raise ResourceNotFoundError(f"Resource not found: {uri}")

        text = await target_server.read_resource(uri)
        resource = target_server.resources[uri]
        result = ReadResourceResult(
            contents=[ResourceContent(uri=uri, mimeType=resource.mimeType, text=text)]
        )
        return result.model_dump()

    async def _handle_prompts_list(self, params: Dict) -> Dict:
        """合并所有 Server 的 prompt 列表"""
        prompts = []
        for server in self.registry.list_servers():
            for prompt in server.list_prompts():
                prompts.append(prompt.model_dump())
        return {"prompts": prompts}

    async def _handle_prompts_get(self, params: Dict) -> Dict:
        """按名称找到对应 Server，调用 get_prompt；不存在返回 PROMPT_NOT_FOUND"""
        name = params.get("name", "")
        arguments = params.get("arguments") or {}

        target_server = None
        for server in self.registry.list_servers():
            if name in server.prompts:
                target_server = server
                break

        if target_server is None:
            raise PromptNotFoundError(f"Prompt not found: {name}")

        result = await target_server.get_prompt(name, arguments)
        return result
