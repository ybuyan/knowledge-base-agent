"""
MCP FastAPI 路由
挂载 /mcp 端点，集成认证、授权、审计日志等功能
"""
from fastapi import APIRouter, Request, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient

from app.mcp.transport import handle_jsonrpc_request, sse_generator
from app.mcp.base import MCPServerRegistry
from app.mcp.auth_middleware import MCPAuthMiddleware, AuthContext
from app.mcp.api_key_manager import APIKeyManager
from app.mcp.access_control import ResourceAccessControl
from app.mcp.audit_logger import AuditLogger
from app.mcp.rate_limiter import RateLimiter
from app.mcp.dispatcher import MCPDispatcher
from app.config import settings

router = APIRouter(prefix="/mcp", tags=["mcp"])

# 初始化组件（单例）
_mongo_client = AsyncIOMotorClient(settings.mongo_url)
_api_key_manager = APIKeyManager(_mongo_client)
_auth_middleware = MCPAuthMiddleware(_api_key_manager)
_access_control = ResourceAccessControl()
_audit_logger = AuditLogger(_mongo_client)
_rate_limiter = RateLimiter(_mongo_client)
_dispatcher = MCPDispatcher(
    registry=MCPServerRegistry,
    access_control=_access_control,
    audit_logger=_audit_logger,
    rate_limiter=_rate_limiter
)

# 注意：审计日志批量写入在 main.py 的 startup 事件中启动


async def get_auth_context(request: Request) -> Optional[AuthContext]:
    """
    依赖注入：获取认证上下文
    
    对于公开端点，认证失败返回 guest 上下文
    对于管理端点，认证失败抛出 401 异常
    """
    try:
        return await _auth_middleware.authenticate_request(request)
    except HTTPException:
        # 对于公开端点，返回 guest 上下文
        return _auth_middleware.create_guest_context()


async def require_auth_context(request: Request) -> AuthContext:
    """
    依赖注入：要求认证上下文（用于管理端点）
    
    认证失败抛出 401 异常
    """
    return await _auth_middleware.authenticate_request(request)


@router.post("")
async def mcp_endpoint(
    request: Request,
    auth_context: Optional[AuthContext] = Depends(get_auth_context)
) -> JSONResponse:
    """
    HTTP POST 端点，处理单次 JSON-RPC 请求
    
    增强功能：
    - 集成认证中间件
    - 支持 API Key 认证
    - 未认证用户以 guest 身份访问
    """
    # 使用增强的 dispatcher（已集成认证、授权、审计）
    import json
    from app.mcp.protocol import JSONRPCRequest, JSONRPCError, MCPErrorCode
    
    # Parse JSON
    try:
        body = await request.body()
        data = json.loads(body)
    except (json.JSONDecodeError, Exception):
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": MCPErrorCode.PARSE_ERROR, "message": "Parse error: invalid JSON"}
            },
            status_code=200
        )
    
    # Validate JSONRPCRequest
    try:
        rpc_request = JSONRPCRequest.model_validate(data)
    except Exception:
        req_id = data.get("id") if isinstance(data, dict) else None
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": MCPErrorCode.INVALID_REQUEST, "message": "Invalid Request"}
            },
            status_code=200
        )
    
    # Dispatch with auth context
    result = await _dispatcher.dispatch(rpc_request, auth_context)
    
    if result is None:
        # Notification: no response body
        return JSONResponse(content=None, status_code=204)
    
    return JSONResponse(content=result.model_dump(exclude_none=False), status_code=200)


@router.get("/sse")
async def mcp_sse_endpoint(
    request: Request,
    auth_context: Optional[AuthContext] = Depends(get_auth_context)
) -> StreamingResponse:
    """
    SSE 端点，建立持久连接并推送消息
    
    增强功能：
    - 集成认证中间件
    - 支持 API Key 认证
    """
    return StreamingResponse(
        sse_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/capabilities")
async def mcp_capabilities() -> JSONResponse:
    """返回所有已注册 Server 的能力声明（调试用）"""
    capabilities = {}
    for server in MCPServerRegistry.list_servers():
        caps = server.get_capabilities()
        capabilities[server.name] = caps.model_dump(exclude_none=True)
    return JSONResponse(content=capabilities)


@router.get("/public/resources")
async def list_public_resources() -> JSONResponse:
    """
    公开资源目录（新增）
    
    无需认证，返回所有 PUBLIC 级别的资源列表
    供外部用户浏览可用资源
    """
    # 创建 guest 上下文
    guest_context = _auth_middleware.create_guest_context()
    
    # 获取所有资源
    all_resources = []
    for server in MCPServerRegistry.list_servers():
        for resource in server.list_resources():
            all_resources.append(resource)
    
    # 过滤出公开资源
    public_resources = _access_control.filter_resources(all_resources, guest_context)
    
    return JSONResponse(content={
        "resources": [r.model_dump() for r in public_resources]
    })


# ==================== 管理员端点 ====================

@router.post("/admin/api-keys")
async def create_api_key(
    request: Request,
    auth_context: AuthContext = Depends(require_auth_context)
) -> JSONResponse:
    """
    创建 API Key（管理员端点）
    
    需要 admin 角色
    """
    # 检查管理员权限
    if auth_context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    # 解析请求体
    body = await request.json()
    
    # 生成 API Key
    api_key = await _api_key_manager.generate_api_key(
        user_id=body.get("user_id"),
        username=body.get("username"),
        role=body.get("role"),
        permissions=body.get("permissions", []),
        rate_limit=body.get("rate_limit"),
        expires_days=body.get("expires_days"),
        description=body.get("description", "")
    )
    
    return JSONResponse(content=api_key.model_dump())


@router.delete("/admin/api-keys/{key}")
async def revoke_api_key(
    key: str,
    auth_context: AuthContext = Depends(require_auth_context)
) -> JSONResponse:
    """
    撤销 API Key（管理员端点）
    
    需要 admin 角色
    """
    # 检查管理员权限
    if auth_context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    # 撤销 API Key
    success = await _api_key_manager.revoke_api_key(key)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found"
        )
    
    return JSONResponse(content={"success": True, "message": "API Key revoked"})


@router.get("/admin/api-keys")
async def list_api_keys(
    user_id: Optional[str] = Query(None),
    auth_context: AuthContext = Depends(require_auth_context)
) -> JSONResponse:
    """
    列出 API Keys（管理员端点）
    
    需要 admin 角色
    """
    # 检查管理员权限
    if auth_context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    if user_id:
        # 列出特定用户的 API Keys
        api_keys = await _api_key_manager.list_user_api_keys(user_id)
    else:
        # 列出所有 API Keys（需要实现）
        # 暂时返回空列表
        api_keys = []
    
    return JSONResponse(content={
        "api_keys": [key.model_dump() for key in api_keys]
    })


@router.get("/admin/audit-logs")
async def get_audit_logs(
    user_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    auth_context: AuthContext = Depends(require_auth_context)
) -> JSONResponse:
    """
    查询审计日志（管理员端点）
    
    需要 admin 角色
    """
    # 检查管理员权限
    if auth_context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    if user_id:
        # 查询特定用户的访问历史
        logs = await _audit_logger.get_user_access_history(user_id, limit)
    else:
        # 查询所有日志（需要实现）
        # 暂时返回空列表
        logs = []
    
    return JSONResponse(content={
        "logs": [log.model_dump() for log in logs]
    })


@router.get("/admin/stats/resource")
async def get_resource_stats(
    resource_uri: str = Query(...),
    days: int = Query(7, ge=1, le=90),
    auth_context: AuthContext = Depends(require_auth_context)
) -> JSONResponse:
    """
    获取资源访问统计（管理员端点）
    
    需要 admin 角色
    """
    # 检查管理员权限
    if auth_context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    # 获取统计信息
    stats = await _audit_logger.get_resource_access_stats(resource_uri, days)
    
    return JSONResponse(content=stats)

