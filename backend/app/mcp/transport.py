"""
MCP 传输层
HTTP POST 处理 + SSE 生成器
"""

import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import Request

logger = logging.getLogger(__name__)


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
