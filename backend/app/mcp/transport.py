"""
MCP 传输层
HTTP POST 处理 + SSE 生成器
"""
import asyncio
import json
import logging
from typing import Optional, AsyncGenerator

from fastapi import Request

from app.mcp.dispatcher import MCPDispatcher
from app.mcp.protocol import (
    JSONRPCRequest, JSONRPCResponse, JSONRPCError, MCPErrorCode
)

logger = logging.getLogger(__name__)

# Singleton dispatcher
_dispatcher = MCPDispatcher()


def _error_response(req_id, code: int, message: str) -> JSONRPCResponse:
    return JSONRPCResponse(
        id=req_id,
        error=JSONRPCError(code=code, message=message)
    )


async def handle_jsonrpc_request(request: Request) -> Optional[JSONRPCResponse]:
    """
    处理 HTTP POST JSON-RPC 请求。
    返回 None 表示 notification（调用方应返回 204）。
    """
    # Parse JSON
    try:
        body = await request.body()
        data = json.loads(body)
    except (json.JSONDecodeError, Exception):
        return _error_response(None, MCPErrorCode.PARSE_ERROR, "Parse error: invalid JSON")

    # Validate JSONRPCRequest
    try:
        rpc_request = JSONRPCRequest.model_validate(data)
    except Exception:
        req_id = data.get("id") if isinstance(data, dict) else None
        return _error_response(req_id, MCPErrorCode.INVALID_REQUEST, "Invalid Request")

    # Dispatch
    return await _dispatcher.dispatch(rpc_request)


async def sse_generator(request: Request) -> AsyncGenerator[str, None]:
    """
    SSE 生成器：建立连接时推送 endpoint 事件，然后保持连接。
    """
    queue: asyncio.Queue = asyncio.Queue()

    # Push initial endpoint event
    yield f"event: endpoint\ndata: {json.dumps({'uri': '/mcp'})}\n\n"

    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break
            # Wait for messages with timeout to periodically check disconnect
            try:
                message = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield f"event: message\ndata: {json.dumps(message)}\n\n"
            except asyncio.TimeoutError:
                # Send keepalive comment
                yield ": keepalive\n\n"
    except Exception:
        pass  # Silently clean up on disconnect
    finally:
        # Drain queue silently
        while not queue.empty():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                break
