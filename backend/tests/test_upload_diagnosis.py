import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_upload_flow():
    from app.config import settings
    from app.core.embeddings import get_embeddings
    from app.skills.processors.document import DocumentParser, TextSplitter
    from app.skills.processors.embedding import EmbeddingProcessor
    from app.skills.processors.store import VectorStore
    
    print("=" * 50)
    print("诊断文档上传流程")
    print("=" * 50)
    
    print("\n1. 检查配置...")
    print(f"   - dashscope_api_key: {settings.dashscope_api_key[:20] if settings.dashscope_api_key else 'None'}...")
    print(f"   - embedding_model: {settings.embedding_model}")
    print(f"   - llm_base_url: {settings.llm_base_url}")
    
    test_file = "data/uploads/29e8f92c-4955-435b-9c38-e6d0964baf47_员工手册.pdf"
    if not os.path.exists(test_file):
        print(f"\n错误: 测试文件不存在: {test_file}")
        return
    
    print(f"\n2. 测试文件: {test_file}")
    print(f"   - 文件大小: {os.path.getsize(test_file)} bytes")
    
    print("\n3. 解析文档...")
    parser = DocumentParser()
    context = {"file_path": test_file}
    result = await parser.process(context, {"supported_formats": ["pdf", "docx", "txt"]})
    print(f"   - 文档格式: {result.get('document_format')}")
    print(f"   - 文本长度: {len(result.get('document_text', ''))} 字符")
    context.update(result)
    
    print("\n4. 切分文本...")
    splitter = TextSplitter()
    result = await splitter.process(context, {"chunk_size": 500, "chunk_overlap": 50})
    chunks = result.get("chunks", [])
    print(f"   - 切分数量: {len(chunks)} 个片段")
    if chunks:
        print(f"   - 第一个片段预览: {chunks[0][:100]}...")
    context.update(result)
    
    print("\n5. 向量化...")
    try:
        embedder = EmbeddingProcessor()
        result = await embedder.process(context, {})
        embeddings = result.get("chunk_embeddings", [])
        print(f"   - 向量数量: {len(embeddings)}")
        if embeddings:
            print(f"   - 向量维度: {len(embeddings[0])}")
        context.update(result)
    except Exception as e:
        print(f"   - 错误: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n6. 存储向量...")
    try:
        store = VectorStore()
        result = await store.process(context, {"collection": "documents"})
        print(f"   - 存储数量: {result.get('stored_count', 0)}")
    except Exception as e:
        print(f"   - 错误: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 50)
    print("诊断完成！所有步骤成功。")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_upload_flow())
