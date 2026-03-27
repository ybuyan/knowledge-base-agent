import sys
import os
import asyncio

sys.path.insert(0, 'backend')

from app.skills.engine import SkillEngine
from app.core.chroma import get_documents_collection

async def test_upload_with_debug():
    print("=" * 60)
    print("测试文档上传（详细调试）")
    print("=" * 60)
    
    test_file = "backend/docs/员工手册.pdf"
    
    if not os.path.exists(test_file):
        print(f"\n✗ 测试文件不存在: {test_file}")
        return
    
    print(f"\n1. 解析文档...")
    from app.skills.processors.document import DocumentParser
    
    parser = DocumentParser()
    parse_result = await parser.process(
        {"file_path": test_file},
        {"supported_formats": ["pdf"]}
    )
    
    print(f"   ✓ 解析成功，文本长度: {len(parse_result['document_text'])}")
    
    print(f"\n2. 分块文本...")
    from app.skills.processors.document import TextSplitter
    
    splitter = TextSplitter()
    split_result = await splitter.process(
        {"document_text": parse_result['document_text']},
        {"chunk_size": 500, "chunk_overlap": 50}
    )
    
    chunks = split_result['chunks']
    print(f"   ✓ 分块成功，数量: {len(chunks)}")
    
    print(f"\n3. 生成向量（分批处理）...")
    from app.core.embeddings import get_embeddings
    
    embeddings = get_embeddings()
    
    # 分批处理，每批10个
    batch_size = 10
    all_embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        print(f"   处理批次 {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1} ({len(batch)} 个文本块)...")
        
        try:
            batch_embeddings = await embeddings.aembed_documents(batch)
            all_embeddings.extend(batch_embeddings)
            print(f"   ✓ 批次成功")
        except Exception as e:
            print(f"   ✗ 批次失败: {e}")
            
            # 打印失败的文本
            for j, chunk in enumerate(batch):
                print(f"\n   失败的文本块 {j}:")
                print(f"   长度: {len(chunk)}")
                print(f"   内容: {chunk[:200]}...")
            
            raise
    
    print(f"\n   ✓ 向量生成成功，总数: {len(all_embeddings)}")
    
    print(f"\n4. 存储到知识库...")
    from app.skills.processors.store import VectorStore
    
    store = VectorStore()
    store_result = await store.process(
        {
            "chunks": chunks,
            "chunk_embeddings": all_embeddings,
            "document_id": parse_result['document_id'],
            "document_name": parse_result['document_name']
        },
        {"collection": "documents"}
    )
    
    print(f"   ✓ 存储成功，数量: {store_result['stored_count']}")
    
    print(f"\n5. 验证知识库...")
    collection = get_documents_collection()
    count = collection.count()
    print(f"   知识库文档总数: {count}")
    
    if count > 0:
        print(f"\n✓ 文档上传入库成功！")
        
        # 测试查询
        print(f"\n6. 测试查询...")
        query = "公司有哪些福利？"
        query_embedding = await embeddings.aembed_query(query)
        
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        
        if results['documents'] and results['documents'][0]:
            print(f"   ✓ 查询成功，找到 {len(results['documents'][0])} 个相关文档")
            print(f"\n   最相关的文档:")
            print(f"   {results['documents'][0][0][:200]}...")

if __name__ == "__main__":
    asyncio.run(test_upload_with_debug())
