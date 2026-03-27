import sys
sys.path.insert(0, 'backend')

from app.core.chroma import get_documents_collection

print("=" * 60)
print("检查知识库数据和 metadata")
print("=" * 60)

collection = get_documents_collection()
count = collection.count()

print(f"\n知识库文档总数: {count}")

if count > 0:
    print("\n获取前3个文档的详细信息:")
    results = collection.peek(limit=3)
    
    for i in range(len(results['ids'])):
        print(f"\n文档 {i+1}:")
        print(f"  ID: {results['ids'][i]}")
        
        if results['metadatas']:
            metadata = results['metadatas'][i]
            print(f"  Metadata:")
            for key, value in metadata.items():
                print(f"    {key}: {value}")
        else:
            print(f"  ⚠️ 没有 metadata")
        
        if results['documents']:
            doc = results['documents'][i]
            print(f"  文档内容长度: {len(doc)}")
            print(f"  内容预览: {doc[:150]}...")
        else:
            print(f"  ⚠️ 没有文档内容")
    
    print("\n\n测试查询:")
    from app.core.embeddings import get_embeddings
    import asyncio
    
    async def test_query():
        embeddings = get_embeddings()
        query_embedding = await embeddings.aembed_query("公司福利")
        
        print(f"\n查询: '公司福利'")
        
        query_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"\n查询结果:")
        print(f"  返回文档数: {len(query_results['documents'][0]) if query_results['documents'] else 0}")
        
        if query_results['documents'] and query_results['documents'][0]:
            for i in range(len(query_results['documents'][0])):
                print(f"\n  结果 {i+1}:")
                print(f"    距离: {query_results['distances'][0][i]:.4f}")
                
                if query_results['metadatas']:
                    metadata = query_results['metadatas'][0][i]
                    print(f"    Metadata:")
                    for key, value in metadata.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"    ⚠️ 没有 metadata")
                
                doc = query_results['documents'][0][i]
                print(f"    内容预览: {doc[:100]}...")
    
    asyncio.run(test_query())

print("\n" + "=" * 60)
