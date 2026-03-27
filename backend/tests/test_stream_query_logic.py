import sys
import os
import asyncio

sys.path.insert(0, 'backend')

from app.core.chroma import get_documents_collection
from app.core.embeddings import get_embeddings

async def test_stream_query_logic():
    print("=" * 60)
    print("测试流式接口的查询逻辑")
    print("=" * 60)
    
    print("\n1. 检查知识库状态")
    collection = get_documents_collection()
    count = collection.count()
    print(f"   文档总数: {count}")
    
    if count == 0:
        print("\n✗ 知识库为空！")
        return
    
    print("\n2. 测试查询逻辑（模拟流式接口）")
    
    embeddings = get_embeddings()
    query = "公司有哪些福利？"
    
    print(f"   查询: {query}")
    print("   生成查询向量...")
    
    query_embedding = await embeddings.aembed_query(query)
    print(f"   ✓ 向量维度: {len(query_embedding)}")
    
    print("\n   执行查询...")
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )
    
    print(f"   查询结果:")
    print(f"     返回文档数: {len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0}")
    
    context_parts = []
    sources = []
    
    if results["documents"] and results["documents"][0]:
        print(f"\n   处理查询结果:")
        for i, doc in enumerate(results["documents"][0]):
            print(f"     文档 {i+1}:")
            print(f"       长度: {len(doc)}")
            print(f"       内容: {doc[:100]}...")
            
            context_parts.append(f"[{i+1}] {doc}")
            
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            print(f"       Metadata: {metadata}")
            
            sources.append({
                "id": str(i+1),
                "filename": metadata.get("document_name", "未知"),
                "content": doc[:200] + "..."
            })
    else:
        print(f"\n   ✗ 没有查询到文档！")
    
    context = "\n\n".join(context_parts) if context_parts else "暂无相关知识库内容"
    
    print(f"\n3. 构建的上下文:")
    print(f"   长度: {len(context)}")
    print(f"   内容: {context[:300]}...")
    
    print(f"\n4. 构建的来源:")
    print(f"   数量: {len(sources)}")
    for i, source in enumerate(sources):
        print(f"   {i+1}. {source['filename']}")
        print(f"      内容: {source['content'][:80]}...")

if __name__ == "__main__":
    asyncio.run(test_stream_query_logic())
