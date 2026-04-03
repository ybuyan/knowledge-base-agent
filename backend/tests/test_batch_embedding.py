import asyncio
import httpx

async def test_batch_embedding():
    print("=" * 60)
    print("测试批量 Embedding API")
    print("=" * 60)
    
    api_key = "sk-a530317402894edb852ab83b68e05dab"
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    
    async with httpx.AsyncClient(verify=False) as client:
        url = f"{base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print("\n测试1: 单个文本")
        payload1 = {
            "model": "text-embedding-v3",
            "input": "测试文本"
        }
        
        response1 = await client.post(url, json=payload1, headers=headers)
        print(f"状态码: {response1.status_code}")
        if response1.status_code == 200:
            print("✓ 成功")
            data = response1.json()
            print(f"Embedding 维度: {len(data['data'][0]['embedding'])}")
        else:
            print(f"✗ 失败: {response1.text}")
        
        print("\n测试2: 多个文本（数组格式）")
        payload2 = {
            "model": "text-embedding-v3",
            "input": ["文本1", "文本2"]
        }
        
        response2 = await client.post(url, json=payload2, headers=headers)
        print(f"状态码: {response2.status_code}")
        if response2.status_code == 200:
            print("✓ 成功")
            data = response2.json()
            print(f"返回的 embedding 数量: {len(data['data'])}")
        else:
            print(f"✗ 失败: {response2.text}")
        
        print("\n测试3: 大批量文本")
        payload3 = {
            "model": "text-embedding-v3",
            "input": [f"文本{i}" for i in range(10)]
        }
        
        response3 = await client.post(url, json=payload3, headers=headers)
        print(f"状态码: {response3.status_code}")
        if response3.status_code == 200:
            print("✓ 成功")
            data = response3.json()
            print(f"返回的 embedding 数量: {len(data['data'])}")
        else:
            print(f"✗ 失败: {response3.text}")

if __name__ == "__main__":
    asyncio.run(test_batch_embedding())
