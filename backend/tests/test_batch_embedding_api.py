import asyncio
import httpx
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.skills.processors.document import DocumentParser, TextSplitter

async def test_batch_embedding():
    print("测试批量嵌入...")
    
    test_file = "data/uploads/29e8f92c-4955-435b-9c38-e6d0964baf47_员工手册.pdf"
    
    # 解析和切分
    parser = DocumentParser()
    context = {"file_path": test_file}
    result = await parser.process(context, {"supported_formats": ["pdf", "docx", "txt"]})
    context.update(result)
    
    splitter = TextSplitter()
    result = await splitter.process(context, {"chunk_size": 500, "chunk_overlap": 50})
    chunks = result.get("chunks", [])
    
    print(f"切分数量: {len(chunks)}")
    
    # 测试不同批量大小
    url = f"{settings.llm_base_url}/embeddings"
    headers = {
        "Authorization": f"Bearer {settings.embedding_api_key}",
        "Content-Type": "application/json"
    }
    
    # 测试全部一次性
    print("\n1. 测试一次性发送全部 49 个片段...")
    async with httpx.AsyncClient(timeout=120.0, verify=False) as client:
        try:
            payload = {
                "model": settings.embedding_model,
                "input": chunks,
                "encoding_format": "float"
            }
            response = await client.post(url, json=payload, headers=headers)
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   成功! 返回 {len(data['data'])} 个向量")
            else:
                print(f"   错误: {response.text[:500]}")
        except Exception as e:
            print(f"   异常: {e}")
    
    # 测试分批处理
    print("\n2. 测试分批处理 (每批 10 个)...")
    batch_size = 10
    all_embeddings = []
    
    async with httpx.AsyncClient(timeout=60.0, verify=False) as client:
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            print(f"   处理批次 {i//batch_size + 1}: {len(batch)} 个片段...")
            
            try:
                payload = {
                    "model": settings.embedding_model,
                    "input": batch,
                    "encoding_format": "float"
                }
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    all_embeddings.extend([item["embedding"] for item in data["data"]])
                    print(f"      成功!")
                else:
                    print(f"      错误: {response.text[:200]}")
                    break
            except Exception as e:
                print(f"      异常: {e}")
                break
    
    print(f"\n总共获取 {len(all_embeddings)} 个向量")

if __name__ == "__main__":
    asyncio.run(test_batch_embedding())
