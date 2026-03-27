import sys
import os
import asyncio

sys.path.insert(0, 'backend')

from app.core.chroma import get_documents_collection
from app.skills.engine import SkillEngine

async def test_document_upload():
    print("=" * 60)
    print("测试文档上传入库流程")
    print("=" * 60)
    
    test_file = "backend/docs/员工手册.pdf"
    
    if not os.path.exists(test_file):
        print(f"\n✗ 测试文件不存在: {test_file}")
        return
    
    print(f"\n1. 检查上传前知识库状态")
    collection = get_documents_collection()
    count_before = collection.count()
    print(f"   文档数量: {count_before}")
    
    print(f"\n2. 开始处理文档: {test_file}")
    
    skill_engine = SkillEngine()
    
    context = {
        "file_path": test_file,
        "document_id": "test_doc_manual",
        "document_name": "员工手册.pdf"
    }
    
    try:
        print("   - 解析文档...")
        print("   - 分块文本...")
        print("   - 生成向量...")
        print("   - 存储到知识库...")
        
        result = await skill_engine.execute("document_upload", context)
        
        print("\n✓ 文档处理成功！")
        print(f"   文档ID: {result.get('document_id')}")
        print(f"   分块数量: {result.get('chunk_count')}")
        print(f"   存储数量: {result.get('stored_count')}")
        
        print(f"\n3. 检查上传后知识库状态")
        count_after = collection.count()
        print(f"   文档数量: {count_after}")
        print(f"   新增文档: {count_after - count_before}")
        
        print(f"\n4. 验证文档内容")
        results = collection.peek(limit=3)
        
        if results['ids']:
            print(f"   ✓ 找到 {len(results['ids'])} 个文档块")
            for i in range(min(2, len(results['ids']))):
                print(f"\n   文档块 {i+1}:")
                print(f"     ID: {results['ids'][i]}")
                metadata = results['metadatas'][i] if results['metadatas'] else {}
                print(f"     文件名: {metadata.get('document_name', '未知')}")
                print(f"     内容预览: {results['documents'][i][:100]}...")
        else:
            print("   ✗ 未找到文档")
            
        print(f"\n5. 测试查询功能")
        from app.core.embeddings import get_embeddings
        
        embeddings = get_embeddings()
        query = "公司有哪些福利？"
        print(f"   查询: {query}")
        
        query_embedding = await embeddings.aembed_query(query)
        
        search_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        if search_results['documents'] and search_results['documents'][0]:
            print(f"   ✓ 找到 {len(search_results['documents'][0])} 个相关文档")
            for i, doc in enumerate(search_results['documents'][0][:2]):
                print(f"\n   相关文档 {i+1}:")
                print(f"     内容: {doc[:150]}...")
        else:
            print("   ✗ 未找到相关文档")
        
    except Exception as e:
        print(f"\n✗ 文档处理失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_document_upload())
