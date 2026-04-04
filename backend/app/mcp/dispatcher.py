"""
MCP 请求分发器
将 JSON-RPC 2.0 方法路由到对应的 MCPServer 处理逻辑
"""
from typing import Optional, Dict, Any
import logging
import time

from app.mcp.base import MCPServerRegistry, MCPCapabilities
from app.mcp.protocol import (
    JSONRPCRequest, JSONRPCResponse, JSONRPCError, MCPErrorCode,
    InitializeResult, ServerInfo, ContentItem, CallToolResult,
    ReadResourceResult, ResourceContent
)
from app.mcp.auth_middleware import AuthContext
from app.mcp.access_control import ResourceAccessControl
from app.mcp.audit_logger import AuditLogger
from app.mcp.rate_limiter import RateLimiter, RateLimitExceeded

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
    
    增强功能：
      - 速率限制检查
      - 访问权限检查（针对 resources/* 方法）
      - 审计日志记录
      - 性能监控
    """

    def __init__(
        self,
        registry: MCPServerRegistry = None,
        access_control: Optional[ResourceAccessControl] = None,
        audit_logger: Optional[AuditLogger] = None,
        rate_limiter: Optional[RateLimiter] = None
    ):
        self.registry = registry or MCPServerRegistry
        self.access_control = access_control
        self.audit_logger = audit_logger
        self.rate_limiter = rate_limiter

    def _make_error(self, req_id, code: int, message: str) -> JSONRPCResponse:
        return JSONRPCResponse(
            id=req_id,
            error=JSONRPCError(code=code, message=message)
        )

    def _make_result(self, req_id, result: Any) -> JSONRPCResponse:
        return JSONRPCResponse(id=req_id, result=result)

    async def dispatch(self, request: JSONRPCRequest, auth_context: Optional[AuthContext] = None) -> Optional[JSONRPCResponse]:
        """
        主入口：根据 method 路由到对应处理方法。
        notification（id=None）处理后返回 None。
        
        增强功能：
        1. 速率限制检查
        2. 访问权限检查（针对 resources/* 方法）
        3. 审计日志记录
        4. 性能监控
        
        Args:
            request: JSON-RPC 请求
            auth_context: 认证上下文（可选）
        
        Returns:
            JSONRPCResponse: 响应对象，notification 返回 None
        """
        start_time = time.time()
        is_notification = request.id is None
        method = request.method
        params = request.params or {}
        
        # 速率限制检查（如果启用）
        if self.rate_limiter and auth_context:
            try:
                await self.rate_limiter.check_rate_limit(
                    user_id=auth_context.user_id,
                    rate_limit=auth_context.rate_limit,
                    window_seconds=60
                )
            except RateLimitExceeded as e:
                if is_notification:
                    return None
                return self._make_error(
                    request.id,
                    429,  # Too Many Requests
                    f"Rate limit exceeded. Retry after {e.retry_after} seconds."
                )

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
                result = await self._handle_resources_list(params, auth_context)
            elif method == "resources/read":
                result = await self._handle_resources_read(params, auth_context)
            elif method == "prompts/list":
                result = await self._handle_prompts_list(params)
            elif method == "prompts/get":
                result = await self._handle_prompts_get(params)
            else:
                if is_notification:
                    return None
                response = self._make_error(request.id, MCPErrorCode.METHOD_NOT_FOUND, f"Method not found: {method}")
                await self._log_access(auth_context, method, None, None, False, MCPErrorCode.METHOD_NOT_FOUND, f"Method not found: {method}", start_time)
                return response
        except ToolNotFoundError as e:
            if is_notification:
                return None
            response = self._make_error(request.id, MCPErrorCode.TOOL_NOT_FOUND, str(e))
            await self._log_access(auth_context, method, None, params.get("name"), False, MCPErrorCode.TOOL_NOT_FOUND, str(e), start_time)
            return response
        except ResourceNotFoundError as e:
            if is_notification:
                return None
            response = self._make_error(request.id, MCPErrorCode.RESOURCE_NOT_FOUND, str(e))
            await self._log_access(auth_context, method, params.get("uri"), None, False, MCPErrorCode.RESOURCE_NOT_FOUND, str(e), start_time)
            return response
        except PromptNotFoundError as e:
            if is_notification:
                return None
            response = self._make_error(request.id, MCPErrorCode.PROMPT_NOT_FOUND, str(e))
            await self._log_access(auth_context, method, None, None, False, MCPErrorCode.PROMPT_NOT_FOUND, str(e), start_time)
            return response
        except PermissionError as e:
            if is_notification:
                return None
            response = self._make_error(request.id, 403, str(e))
            await self._log_access(auth_context, method, params.get("uri"), None, False, 403, str(e), start_time)
            return response
        except Exception as e:
            logger.exception(f"Error handling method {method}")
            if is_notification:
                return None
            response = self._make_error(request.id, MCPErrorCode.INTERNAL_ERROR, str(e))
            await self._log_access(auth_context, method, params.get("uri"), params.get("name"), False, MCPErrorCode.INTERNAL_ERROR, str(e), start_time)
            return response

        # 记录成功的访问
        await self._log_access(auth_context, method, params.get("uri"), params.get("name"), True, None, None, start_time)
        
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

    async def _handle_resources_list(self, params: Dict, auth_context: Optional[AuthContext] = None) -> Dict:
        """
        合并所有 Server 的 resource 列表
        
        增强功能：根据用户权限过滤资源列表
        - 未认证用户: 只返回 PUBLIC 资源
        - 员工用户: 返回 PUBLIC + INTERNAL 资源
        - 管理员: 返回所有资源
        
        Args:
            params: 请求参数
            auth_context: 认证上下文
        
        Returns:
            Dict: 资源列表
        """
        resources = []
        for server in self.registry.list_servers():
            for resource in server.list_resources():
                resources.append(resource)
        
        # 如果启用访问控制且有认证上下文，过滤资源
        if self.access_control and auth_context:
            resources = self.access_control.filter_resources(resources, auth_context)
        
        # 转换为字典
        return {"resources": [r.model_dump() for r in resources]}

    async def _handle_resources_read(self, params: Dict, auth_context: Optional[AuthContext] = None) -> Dict:
        """
        按 URI 找到对应 Server，调用 read_resource；URI 不存在返回 RESOURCE_NOT_FOUND
        
        增强功能：在读取前检查访问权限
        - 无权限: 抛出 PermissionError
        - 有权限: 正常返回资源内容
        
        Args:
            params: 请求参数
            auth_context: 认证上下文
        
        Returns:
            Dict: 资源内容
        
        Raises:
            PermissionError: 如果用户无权访问该资源
            ResourceNotFoundError: 如果资源不存在
        """
        uri = params.get("uri", "")

        # 检查访问权限
        if self.access_control and auth_context:
            if not self.access_control.check_access(uri, auth_context):
                raise PermissionError(f"Access denied to resource: {uri}")

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
    
    async def _log_access(
        self,
        auth_context: Optional[AuthContext],
        method: str,
        resource_uri: Optional[str],
        tool_name: Optional[str],
        success: bool,
        error_code: Optional[int],
        error_message: Optional[str],
        start_time: float
    ) -> None:
        """
        记录访问日志
        
        Args:
            auth_context: 认证上下文
            method: JSON-RPC 方法名
            resource_uri: 访问的资源 URI
            tool_name: 调用的工具名
            success: 是否成功
            error_code: 错误码
            error_message: 错误信息
            start_time: 请求开始时间
        """
        if not self.audit_logger or not auth_context:
            return
        
        # 计算响应时间
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # 创建一个模拟的 Request 对象（因为这里没有真实的 Request）
        # 在实际使用中，应该从 router 层传递真实的 Request 对象
        class MockRequest:
            def __init__(self):
                self.headers = {}
                self.client = None
        
        mock_request = MockRequest()
        
        try:
            await self.audit_logger.log_access(
                auth_context=auth_context,
                method=method,
                resource_uri=resource_uri,
                tool_name=tool_name,
                success=success,
                error_code=error_code,
                error_message=error_message,
                request=mock_request,
                response_time_ms=response_time_ms
            )
        except Exception as e:
            # 审计日志失败不应该影响主流程
            logger.error(f"Failed to log access: {e}")

