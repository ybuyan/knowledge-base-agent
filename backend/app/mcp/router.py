"""
MCP FastAPI 路由
挂载 /mcp 端点
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.mcp.transport import handle_jsonrpc_request, sse_generator
from app.mcp.base import MCPServerRegistry

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.post("")
async def mcp_endpoint(request: Request) -> JSONResponse:
    """HTTP POST 端点，处理单次 JSON-RPC 请求"""
    result = await handle_jsonrpc_request(request)
    if result is None:
        # Notification: no response body
        return JSONResponse(content=None, status_code=204)
    return JSONResponse(content=result.model_dump(exclude_none=False), status_code=200)


@router.get("/sse")
async def mcp_sse_endpoint(request: Request) -> StreamingResponse:
    """SSE 端点，建立持久连接并推送消息"""
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
