import sys
import os
import asyncio

sys.path.insert(0, 'backend')

from app.core.chroma import get_documents_collection
from app.core.embeddings import get_embeddings

async def test_distance():
    print("=" * 60)
    print("测试 ChromaDB 距离值")
    print("=" * 60)
    
    embeddings = get_embeddings()
    query = "公司有哪些福利？"
    
    print(f"\n查询: {query}")
    print("生成查询向量...")
    query_embedding = await embeddings.aembed_query(query)
    
    print("\n查询知识库...")
    collection = get_documents_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )
    
    print(f"\n查询结果:")
    if results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            doc = results["documents"][0][i]
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            
            print(f"\n文档 {i+1}:")
            print(f"  距离: {distance:.4f}")
            print(f"  文件名: {metadata.get('document_name', '未知')}")
            print(f"  内容: {doc[:100]}...")
            
            # 检查距离阈值
            if distance >= 0.7:
                print(f"  ✓ 通过阈值检查 (distance >= 0.7)")
            else:
                print(f"  ✗ 未通过阈值检查 (distance < 0.7)")
    else:
        print("没有查询到文档")

print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_distance())
