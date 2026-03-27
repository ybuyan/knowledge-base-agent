"""
Unit tests for LLMClient
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.llm_client import LLMClient, LLMConfig, get_llm_client
from app.services.tool_types import ToolDecision, ToolCall


class TestLLMConfig:
    """LLMConfig测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = LLMConfig()
        
        # 模型应该从 settings 读取
        from app.config import settings
        assert config.model == settings.llm_model
        assert config.temperature == 0.3
        assert config.max_tokens == 2000
        assert config.tool_decision_temperature == 0.1
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = LLMConfig(
            model="qwen-turbo",
            temperature=0.5,
            max_tokens=1000
        )
        
        assert config.model == "qwen-turbo"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000


class TestLLMClient:
    """LLMClient测试"""
    
    @pytest.mark.asyncio
    async def test_chat(self):
        """测试普通聊天"""
        config = LLMConfig()
        client = LLMClient(config)
        
        # Mock the LLM client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_get_client', return_value=mock_client):
            result = await client.chat([{"role": "user", "content": "Hi"}])
            
            assert result == "Hello!"
    
    @pytest.mark.asyncio
    async def test_chat_with_tools_no_tool_call(self):
        """测试带Tool的聊天（无Tool调用）"""
        client = LLMClient()
        
        # Mock response without tool calls
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Direct answer"
        mock_response.choices[0].message.tool_calls = None
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_get_client', return_value=mock_client):
            decision = await client.chat_with_tools(
                [{"role": "user", "content": "Hi"}],
                [{"type": "function", "function": {"name": "test", "description": "test", "parameters": {}}}]
            )
            
            assert decision.should_use_tool is False
            assert len(decision.tool_calls) == 0
    
    @pytest.mark.asyncio
    async def test_chat_with_tools_with_tool_call(self):
        """测试带Tool的聊天（有Tool调用）"""
        client = LLMClient()
        
        # Mock response with tool calls
        mock_tool_call = MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "list_documents"
        mock_tool_call.function.arguments = "{}"
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.choices[0].message.tool_calls = [mock_tool_call]
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch.object(client, '_get_client', return_value=mock_client):
            decision = await client.chat_with_tools(
                [{"role": "user", "content": "List documents"}],
                [{"type": "function", "function": {"name": "list_documents", "description": "List", "parameters": {}}}]
            )
            
            assert decision.should_use_tool is True
            assert len(decision.tool_calls) == 1
            assert decision.tool_calls[0].name == "list_documents"


class TestGetLLMClient:
    """get_llm_client测试"""
    
    def test_singleton(self):
        """测试单例模式"""
        client1 = get_llm_client()
        client2 = get_llm_client()
        
        assert client1 is client2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
