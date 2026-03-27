import sys
import os
import asyncio

sys.path.insert(0, 'backend')

from app.skills.processors.document import DocumentParser, TextSplitter

async def test_document_parsing():
    print("=" * 60)
    print("测试文档解析和分块")
    print("=" * 60)
    
    test_file = "backend/docs/员工手册.pdf"
    
    if not os.path.exists(test_file):
        print(f"\n✗ 测试文件不存在: {test_file}")
        return
    
    print(f"\n1. 解析文档: {test_file}")
    
    parser = DocumentParser()
    context = {"file_path": test_file}
    params = {"supported_formats": ["pdf"]}
    
    result = await parser.process(context, params)
    
    print(f"✓ 文档解析成功")
    print(f"  文档格式: {result['document_format']}")
    print(f"  文档名称: {result['document_name']}")
    print(f"  文本长度: {len(result['document_text'])} 字符")
    print(f"  文本预览: {result['document_text'][:200]}...")
    
    print(f"\n2. 分块文本")
    splitter = TextSplitter()
    context = {"document_text": result['document_text']}
    params = {"chunk_size": 500, "chunk_overlap": 50}
    
    split_result = await splitter.process(context, params)
    
    print(f"✓ 文本分块成功")
    print(f"  分块数量: {split_result['chunk_count']}")
    
    if split_result['chunks']:
        print(f"\n3. 查看前3个分块:")
        for i, chunk in enumerate(split_result['chunks'][:3]):
            print(f"\n  分块 {i+1}:")
            print(f"    长度: {len(chunk)} 字符")
            print(f"    内容: {chunk[:100]}...")
    
    print(f"\n4. 测试 Embedding")
    from app.core.embeddings import get_embeddings
    
    embeddings = get_embeddings()
    
    # 测试单个分块
    test_chunk = split_result['chunks'][0] if split_result['chunks'] else "测试文本"
    print(f"  测试单个分块 (长度: {len(test_chunk)})")
    
    try:
        embedding = await embeddings.aembed_query(test_chunk)
        print(f"  ✓ 单个分块 embedding 成功，维度: {len(embedding)}")
    except Exception as e:
        print(f"  ✗ 单个分块 embedding 失败: {e}")
    
    # 测试批量分块
    print(f"\n  测试批量分块 (前5个)")
    test_chunks = split_result['chunks'][:5]
    
    try:
        embeddings_list = await embeddings.aembed_documents(test_chunks)
        print(f"  ✓ 批量 embedding 成功，数量: {len(embeddings_list)}")
    except Exception as e:
        print(f"  ✗ 批量 embedding 失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_document_parsing())
