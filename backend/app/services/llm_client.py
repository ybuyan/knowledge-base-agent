"""
LLM Client - 统一LLM调用接口
"""

import json
from typing import Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass
import logging

from app.core.llm import get_llm_async
from app.services.tool_types import ToolDecision

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """LLM配置"""
    model: str = None
    temperature: float = 0.3
    max_tokens: int = 2000
    tool_decision_temperature: float = 0.1
    
    def __post_init__(self):
        """初始化后处理，设置默认模型"""
        if self.model is None:
            from app.config import settings
            self.model = settings.llm_model


class LLMClient:
    """统一LLM调用客户端"""
    
    def __init__(self, config: LLMConfig = None):
        self._config = config or LLMConfig()
        self._client = None
    
    async def _get_client(self):
        """获取LLM客户端"""
        if self._client is None:
            self._client = await get_llm_async()
        return self._client
    
    async def chat(
        self,
        messages: List[Dict],
        temperature: float = None,
        max_tokens: int = None,
        **kwargs
    ) -> str:
        """普通聊天补全"""
        client = await self._get_client()
        
        response = await client.chat.completions.create(
            model=self._config.model,
            messages=messages,
            temperature=temperature or self._config.temperature,
            max_tokens=max_tokens or self._config.max_tokens,
            **kwargs
        )
        
        return response.choices[0].message.content
    
    async def chat_with_tools(
        
        self,
        messages: List[Dict],
        tools: List[Dict],
        temperature: float = None
    ) -> ToolDecision:
        """带Tool的聊天，返回Tool决策"""
        client = await self._get_client()
        
        response = await client.chat.completions.create(
            model=self._config.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature or self._config.tool_decision_temperature
        )
        return ToolDecision.from_openai_response(response)

    async def stream_chat(
        self,
        messages: List[Dict],
        temperature: float = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式聊天
        
        支持处理包含工具调用结果的消息。当消息中包含tool_calls和tool结果时，
        会正确格式化为OpenAI API要求的格式。
        
        参数:
            messages (List[Dict]): 消息列表
            temperature (float, optional): 温度参数
            **kwargs: 其他参数
        
        返回:
            AsyncGenerator[str, None]: 流式文本生成器
        
        注意:
            - 消息中的content为None时会被正确处理
            - tool_calls和tool消息会被正确格式化
        """
        client = await self._get_client()
        
        # 格式化消息，确保符合OpenAI API要求
        formatted_messages = []
        for msg in messages:
            formatted_msg = {}
            
            # 处理role
            if "role" in msg:
                formatted_msg["role"] = msg["role"]
            
            # 处理content - 如果是None且不是tool消息，跳过
            if msg.get("role") != "tool":
                if msg.get("content") is not None:
                    formatted_msg["content"] = msg["content"]
            
            # 处理tool_calls
            if "tool_calls" in msg:
                formatted_msg["tool_calls"] = msg["tool_calls"]
            
            # 处理tool消息的特殊字段
            if msg.get("role") == "tool":
                if "tool_call_id" in msg:
                    formatted_msg["tool_call_id"] = msg["tool_call_id"]
                if "name" in msg:
                    formatted_msg["name"] = msg["name"]
                if "content" in msg:
                    # content需要是字符串
                    content = msg["content"]
                    if isinstance(content, dict):
                        formatted_msg["content"] = json.dumps(content, ensure_ascii=False)
                    else:
                        formatted_msg["content"] = str(content)
            
            formatted_messages.append(formatted_msg)
        
        stream = await client.chat.completions.create(
            model=self._config.model,
            messages=formatted_messages,
            temperature=temperature or self._config.temperature,
            stream=True,
            **kwargs
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 全局实例
_llm_client: Optional[LLMClient] = None


def get_llm_client(config: LLMConfig = None) -> LLMClient:
    """获取LLM客户端实例"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient(config)
    return _llm_client
