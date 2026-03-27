"""
Tool Executor - Tool执行器
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json

from app.services.tool_types import ToolCall, ToolResult
from app.tools.base import ToolRegistry

logger = logging.getLogger(__name__)


class ToolCache:
    """Tool结果缓存"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()
    
    def _is_expired(self, cached_item: Dict) -> bool:
        """检查缓存是否过期"""
        return time.time() - cached_item["timestamp"] > self._ttl
    
    async def get(self, cache_key: str) -> Optional[ToolResult]:
        """获取缓存结果"""
        async with self._lock:
            if cache_key not in self._cache:
                return None
            
            cached = self._cache[cache_key]
            if self._is_expired(cached):
                del self._cache[cache_key]
                return None
            
            # 标记为缓存命中
            result = cached["result"]
            result.cached = True
            return result
    
    async def set(self, cache_key: str, result: ToolResult) -> None:
        """设置缓存"""
        async with self._lock:
            # LRU淘汰
            if len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            self._cache[cache_key] = {
                "result": result,
                "timestamp": time.time()
            }


class ToolMiddleware:
    """Tool中间件基类"""
    
    async def before_execute(self, tool_call: ToolCall) -> ToolCall:
        """执行前钩子"""
        return tool_call
    
    async def after_execute(self, result: ToolResult) -> ToolResult:
        """执行后钩子"""
        return result
    
    async def on_error(self, tool_call: ToolCall, error: Exception) -> ToolResult:
        """错误处理钩子"""
        return ToolResult(
            success=False,
            data={},
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            error=str(error)
        )


class LoggingMiddleware(ToolMiddleware):
    """日志中间件"""
    
    async def before_execute(self, tool_call: ToolCall) -> ToolCall:
        logger.info(f"Tool executing: {tool_call.name}, args: {tool_call.arguments}")
        return tool_call
    
    async def after_execute(self, result: ToolResult) -> ToolResult:
        logger.info(f"Tool executed: {result.tool_name}, success: {result.success}, cached: {result.cached}")
        return result
    
    async def on_error(self, tool_call: ToolCall, error: Exception) -> ToolResult:
        logger.error(f"Tool error: {tool_call.name}, error: {error}")
        return await super().on_error(tool_call, error)


class RetryMiddleware(ToolMiddleware):
    """重试中间件"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self._max_retries = max_retries
        self._retry_delay = retry_delay
    
    async def before_execute(self, tool_call: ToolCall) -> ToolCall:
        return tool_call
    
    async def after_execute(self, result: ToolResult) -> ToolResult:
        return result
    
    async def on_error(self, tool_call: ToolCall, error: Exception) -> ToolResult:
        # 重试逻辑由Executor处理
        return await super().on_error(tool_call, error)


class ToolExecutor:
    """Tool执行器 - 统一管理Tool执行"""
    
    def __init__(
        self,
        cache_enabled: bool = True,
        middlewares: List[ToolMiddleware] = None
    ):
        self._cache = ToolCache() if cache_enabled else None
        self._middlewares = middlewares or [LoggingMiddleware()]
    
    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行单个Tool调用"""
        start_time = time.time()
        
        # 1. 检查缓存
        if self._cache:
            cache_key = tool_call.get_cache_key()
            cached_result = await self._cache.get(cache_key)
            if cached_result:
                return cached_result
        
        # 2. 执行前置中间件
        for middleware in self._middlewares:
            tool_call = await middleware.before_execute(tool_call)
        
        # 3. 执行Tool
        try:
            tool = ToolRegistry.get(tool_call.name)
            result_data = await tool.execute(**tool_call.arguments)
            
            result = ToolResult(
                success=True,
                data=result_data,
                tool_name=tool_call.name,
                tool_call_id=tool_call.id,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            # 错误处理
            result = await self._handle_error(tool_call, e)
        
        # 4. 执行后置中间件
        for middleware in self._middlewares:
            result = await middleware.after_execute(result)
        
        # 5. 缓存结果
        if self._cache and result.success:
            await self._cache.set(cache_key, result)
        
        return result
    
    async def execute_batch(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """批量执行Tool调用（并行）"""
        tasks = [self.execute(tc) for tc in tool_calls]
        return await asyncio.gather(*tasks)
    
    async def _handle_error(self, tool_call: ToolCall, error: Exception) -> ToolResult:
        """处理执行错误"""
        for middleware in self._middlewares:
            if hasattr(middleware, "on_error"):
                return await middleware.on_error(tool_call, error)
        
        return ToolResult(
            success=False,
            data={},
            tool_name=tool_call.name,
            tool_call_id=tool_call.id,
            error=str(error)
        )
    
    def add_middleware(self, middleware: ToolMiddleware) -> None:
        """添加中间件"""
        self._middlewares.append(middleware)
    
    def clear_cache(self) -> None:
        """清空缓存"""
        if self._cache:
            self._cache._cache.clear()


# 全局实例
_tool_executor: Optional[ToolExecutor] = None


def get_tool_executor() -> ToolExecutor:
    """获取Tool执行器实例"""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutor()
    return _tool_executor
