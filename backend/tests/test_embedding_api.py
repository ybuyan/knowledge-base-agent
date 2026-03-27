import asyncio
import httpx
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

async def test_embedding_api():
    print("测试 Embedding API...")
    print(f"API Key: {settings.embedding_api_key[:20]}...")
    print(f"Model: {settings.embedding_model}")
    print(f"Base URL: {settings.llm_base_url}")
    
    url = f"{settings.llm_base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.embedding_api_key}",
        "Content-Type": "application/json"
    }
    
    # 测试单个文本
    print("\n1. 测试单个文本嵌入...")
    payload1 = {
        "model": settings.embedding_model,
        "input": "这是一个测试文本",
        "encoding_format": "float"
    }
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        try:
            response = await client.post(url, json=payload1, headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   成功! 向量维度: {len(data['data'][0]['embedding'])}")
            else:
                print(f"   错误: {response.text}")
        except Exception as e:
            print(f"   异常: {e}")
    
    # 测试批量文本
    print("\n2. 测试批量文本嵌入...")
    payload2 = {
        "model": settings.embedding_model,
        "input": ["文本1", "文本2", "文本3"],
        "encoding_format": "float"
    }
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        try:
            response = await client.post(url, json=payload2, headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   成功! 返回 {len(data['data'])} 个向量")
            else:
                print(f"   错误: {response.text}")
        except Exception as e:
            print(f"   异常: {e}")
    
    # 测试不带 encoding_format
    print("\n3. 测试不带 encoding_format...")
    payload3 = {
        "model": settings.embedding_model,
        "input": "这是一个测试文本"
    }
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        try:
            response = await client.post(url, json=payload3, headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   成功! 向量维度: {len(data['data'][0]['embedding'])}")
            else:
                print(f"   错误: {response.text}")
        except Exception as e:
            print(f"   异常: {e}")

if __name__ == "__main__":
    asyncio.run(test_embedding_api())
