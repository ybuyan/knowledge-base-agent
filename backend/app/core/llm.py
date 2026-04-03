"""
LLM 客户端模块
支持通义千问等 OpenAI 兼容 API
"""
from app.config import settings
from typing import Optional
import httpx
import ssl
import os
import warnings
import certifi

warnings.filterwarnings("ignore")

os.environ['SSL_CERT_FILE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''


def get_llm():
    from langchain_openai import ChatOpenAI
    from app.core.config_loader import config_loader
    
    api_key = settings.dashscope_api_key or settings.llm_api_key
    if not api_key:
        raise ValueError("请配置 DASHSCOPE_API_KEY 或 LLM_API_KEY")
    
    debug = config_loader.get_setting("llm.debug", False)
    
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=api_key,
        base_url=settings.llm_base_url,
        temperature=0.7,
        streaming=True,
        verbose=debug
    )


async def get_llm_async():
    from openai import AsyncOpenAI
    from app.core.config_loader import config_loader
    
    api_key = settings.dashscope_api_key or settings.llm_api_key
    if not api_key:
        raise ValueError("请配置 DASHSCOPE_API_KEY 或 LLM_API_KEY")
    
    http_client = httpx.AsyncClient(
        verify=False,
    )
    
    return AsyncOpenAI(
        api_key=api_key,
        base_url=settings.llm_base_url,
        http_client=http_client
    )


async def call_llm(prompt: str, system_prompt: str = "") -> str:
    client = await get_llm_async()
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    response = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.7
    )
    
    return response.choices[0].message.content


async def stream_llm(prompt: str, system_prompt: str = ""):
    client = await get_llm_async()
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    stream = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.7,
        stream=True
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def test_llm_connection() -> dict:
    try:
        answer = await call_llm("你好，请回复'连接成功'")
        return {
            "status": "success",
            "message": "LLM 连接成功",
            "response": answer,
            "model": settings.llm_model
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"LLM 连接失败: {str(e)}"
        }
