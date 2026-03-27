"""
Unit tests for ToolExecutor
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.tool_executor import ToolExecutor, ToolCache, ToolMiddleware
from app.services.tool_types import ToolCall, ToolResult


class TestToolCache:
    """Tool缓存测试"""
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        cache = ToolCache(max_size=10, ttl_seconds=60)
        
        result = ToolResult(
            success=True,
            data={"test": "data"},
            tool_name="test_tool",
            tool_call_id="test_id"
        )
        
        await cache.set("test_key", result)
        cached = await cache.get("test_key")
        
        assert cached is not None
        assert cached.success is True
        assert cached.cached is True
        assert cached.data == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """测试缓存未命中"""
        cache = ToolCache()
        cached = await cache.get("nonexistent_key")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_cache_lru_eviction(self):
        """测试LRU淘汰"""
        cache = ToolCache(max_size=2, ttl_seconds=60)
        
        for i in range(3):
            result = ToolResult(
                success=True,
                data={"index": i},
                tool_name=f"tool_{i}",
                tool_call_id=f"id_{i}"
            )
            await cache.set(f"key_{i}", result)
        
        # 第一个应该被淘汰
        cached = await cache.get("key_0")
        assert cached is None
        
        # 后两个应该存在
        cached = await cache.get("key_1")
        assert cached is not None
        cached = await cache.get("key_2")
        assert cached is not None


class TestToolCall:
    """ToolCall测试"""
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        call1 = ToolCall(id="1", name="test_tool", arguments={"a": 1, "b": 2})
        call2 = ToolCall(id="2", name="test_tool", arguments={"b": 2, "a": 1})
        
        # 相同参数应该生成相同的缓存键
        assert call1.get_cache_key() == call2.get_cache_key()
    
    def test_different_args_different_key(self):
        """测试不同参数生成不同缓存键"""
        call1 = ToolCall(id="1", name="test_tool", arguments={"a": 1})
        call2 = ToolCall(id="2", name="test_tool", arguments={"a": 2})
        
        assert call1.get_cache_key() != call2.get_cache_key()


class TestToolResult:
    """ToolResult测试"""
    
    def test_to_openai_tool_message(self):
        """测试转换为OpenAI消息格式"""
        result = ToolResult(
            success=True,
            data={"documents": [{"id": "1", "filename": "test.pdf"}]},
            tool_name="list_documents",
            tool_call_id="call_123"
        )
        
        message = result.to_openai_tool_message()
        
        assert message["role"] == "tool"
        assert message["tool_call_id"] == "call_123"
        assert message["name"] == "list_documents"
        assert "documents" in message["content"]


class TestToolExecutor:
    """ToolExecutor测试"""
    
    @pytest.mark.asyncio
    async def test_execute_with_cache_hit(self):
        """测试缓存命中时的执行"""
        executor = ToolExecutor(cache_enabled=True)
        
        # 预先设置缓存
        call = ToolCall(id="1", name="test_tool", arguments={"query": "test"})
        result = ToolResult(
            success=True,
            data={"result": "cached"},
            tool_name="test_tool",
            tool_call_id="1"
        )
        await executor._cache.set(call.get_cache_key(), result)
        
        # 执行应该返回缓存结果
        executed = await executor.execute(call)
        assert executed.cached is True
        assert executed.data == {"result": "cached"}
    
    @pytest.mark.asyncio
    async def test_execute_batch(self):
        """测试批量执行"""
        executor = ToolExecutor(cache_enabled=False)
        
        calls = [
            ToolCall(id="1", name="list_documents", arguments={}),
            ToolCall(id="2", name="get_system_status", arguments={})
        ]
        
        with patch.object(executor, 'execute', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = ToolResult(
                success=True,
                data={},
                tool_name="test",
                tool_call_id="1"
            )
            
            results = await executor.execute_batch(calls)
            assert len(results) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
