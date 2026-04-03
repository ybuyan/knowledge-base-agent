import asyncio
import httpx

async def test_embedding_api():
    print("=" * 60)
    print("测试 Embedding API")
    print("=" * 60)
    
    api_key = "sk-a530317402894edb852ab83b68e05dab"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    async with httpx.AsyncClient(verify=False) as client:
        print("\n测试单个文本:")
        url = f"{base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "text-embedding-v3",
            "input": "测试文本"
        }
        
        response = await client.post(url, json=payload, headers=headers)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {data}")
        
        print("\n测试批量文本:")
        payload = {
            "model": "text-embedding-v3",
            "input": ["文本1", "文本2", "文本3"]
        }
        
        response = await client.post(url, json=payload, headers=headers)
        print(f"状态码: {response.status_code}")
        data = response.json()
        print(f"响应: {data}")

if __name__ == "__main__":
    asyncio.run(test_embedding_api())
