import asyncio
import httpx
import sys
sys.path.insert(0, 'backend')

async def test_embedding():
    from app.core.embeddings import get_embeddings
    
    print("测试 Embedding...")
    try:
        embeddings = get_embeddings()
        result = await embeddings.aembed_query("测试文本")
        print(f"✓ Embedding 成功，维度: {len(result)}")
        return True
    except Exception as e:
        print(f"✗ Embedding 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_llm():
    from app.core.llm import call_llm
    
    print("\n测试 LLM...")
    try:
        result = await call_llm("你好，请回复'连接成功'")
        print(f"✓ LLM 成功: {result[:100]}")
        return True
    except Exception as e:
        print(f"✗ LLM 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_chroma():
    from app.core.chroma import get_documents_collection
    
    print("\n测试 ChromaDB...")
    try:
        collection = get_documents_collection()
        count = collection.count()
        print(f"✓ ChromaDB 成功，文档数: {count}")
        return True
    except Exception as e:
        print(f"✗ ChromaDB 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_full_flow():
    print("\n测试完整流程...")
    try:
        from app.core.embeddings import get_embeddings
        from app.core.chroma import get_documents_collection
        
        embeddings = get_embeddings()
        query_embedding = await embeddings.aembed_query("测试问题")
        
        collection = get_documents_collection()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        print(f"✓ 完整流程成功，检索到 {len(results['documents'][0])} 个文档")
        return True
    except Exception as e:
        print(f"✗ 完整流程失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 60)
    print("开始诊断测试...")
    print("=" * 60)
    
    results = []
    results.append(await test_embedding())
    results.append(await test_llm())
    results.append(await test_chroma())
    results.append(await test_full_flow())
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print(f"  Embedding: {'✓' if results[0] else '✗'}")
    print(f"  LLM: {'✓' if results[1] else '✗'}")
    print(f"  ChromaDB: {'✓' if results[2] else '✗'}")
    print(f"  完整流程: {'✓' if results[3] else '✗'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
