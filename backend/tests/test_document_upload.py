import sys
import os

sys.path.insert(0, 'backend')

print("=" * 60)
print("测试文档上传处理流程")
print("=" * 60)

import asyncio
from app.skills.engine import SkillEngine

async def test_document_processing():
    test_file = "backend/docs/员工手册.pdf"
    
    if not os.path.exists(test_file):
        print(f"\n✗ 测试文件不存在: {test_file}")
        return
    
    print(f"\n使用测试文件: {test_file}")
    
    skill_engine = SkillEngine()
    
    context = {
        "file_path": test_file,
        "document_id": "test_doc_001",
        "document_name": "员工手册.pdf"
    }
    
    print("\n开始处理文档...")
    
    try:
        result = await skill_engine.execute("document_upload", context)
        
        print("\n✓ 文档处理成功！")
        print(f"  文档ID: {result.get('document_id')}")
        print(f"  分块数量: {result.get('chunk_count')}")
        print(f"  状态: {result.get('status')}")
        
        from app.core.chroma import get_documents_collection
        collection = get_documents_collection()
        count = collection.count()
        print(f"\n知识库文档总数: {count}")
        
    except Exception as e:
        print(f"\n✗ 文档处理失败: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_document_processing())

print("\n" + "=" * 60)
