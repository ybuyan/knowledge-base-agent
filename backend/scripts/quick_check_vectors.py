"""
快速检查向量删除问题
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.chroma import get_documents_collection
from app.models.document import DocumentDB
import asyncio


async def quick_check():
    print("=" * 60)
    print("向量删除问题快速检查")
    print("=" * 60)
    
    # 1. 检查数据库中的文档
    print("\n1. 数据库中的文档:")
    db_docs = await DocumentDB.list()
    db_doc_ids = {doc.id: doc.filename for doc in db_docs}
    print(f"   共 {len(db_doc_ids)} 个文档")
    for doc_id, filename in list(db_doc_ids.items())[:5]:
        print(f"   - {doc_id[:8]}...: {filename}")
    if len(db_doc_ids) > 5:
        print(f"   ... 还有 {len(db_doc_ids) - 5} 个")
    
    # 2. 检查向量数据
    print("\n2. 向量数据库中的文档:")
    collection = get_documents_collection()
    all_data = collection.get()
    
    vector_doc_ids = {}
    for id in all_data['ids']:
        if '_chunk_' in id:
            doc_id = id.split('_chunk_')[0]
            vector_doc_ids[doc_id] = vector_doc_ids.get(doc_id, 0) + 1
    
    print(f"   共 {len(vector_doc_ids)} 个文档的向量数据")
    for doc_id, count in list(vector_doc_ids.items())[:5]:
        print(f"   - {doc_id[:8]}...: {count} 个分块")
    if len(vector_doc_ids) > 5:
        print(f"   ... 还有 {len(vector_doc_ids) - 5} 个")
    
    # 3. 找出孤立的向量
    print("\n3. 孤立的向量数据（已删除但向量仍存在）:")
    orphaned = set(vector_doc_ids.keys()) - set(db_doc_ids.keys())
    
    if orphaned:
        print(f"   ⚠️  发现 {len(orphaned)} 个孤立文档的向量数据！")
        total_orphaned_chunks = sum(vector_doc_ids[doc_id] for doc_id in orphaned)
        print(f"   共 {total_orphaned_chunks} 个孤立的向量分块")
        print("\n   孤立的文档 ID:")
        for doc_id in sorted(orphaned)[:10]:
            print(f"   - {doc_id}: {vector_doc_ids[doc_id]} 个分块")
        if len(orphaned) > 10:
            print(f"   ... 还有 {len(orphaned) - 10} 个")
        
        print("\n   💡 解决方案:")
        print("   运行清理脚本: python backend/scripts/cleanup_orphaned_vectors.py --execute")
    else:
        print("   ✓ 没有孤立的向量数据")
    
    # 4. 找出缺失的向量
    print("\n4. 缺失的向量数据（文档存在但向量不存在）:")
    missing = set(db_doc_ids.keys()) - set(vector_doc_ids.keys())
    
    if missing:
        print(f"   ⚠️  发现 {len(missing)} 个文档缺少向量数据！")
        print("\n   缺失向量的文档:")
        for doc_id in sorted(missing)[:10]:
            print(f"   - {doc_id}: {db_doc_ids[doc_id]}")
        if len(missing) > 10:
            print(f"   ... 还有 {len(missing) - 10} 个")
        
        print("\n   💡 解决方案:")
        print("   重新索引这些文档")
    else:
        print("   ✓ 所有文档都有向量数据")
    
    # 5. 总结
    print("\n" + "=" * 60)
    print("总结:")
    print(f"  数据库文档数: {len(db_doc_ids)}")
    print(f"  向量文档数: {len(vector_doc_ids)}")
    print(f"  孤立向量: {len(orphaned)}")
    print(f"  缺失向量: {len(missing)}")
    
    if orphaned or missing:
        print("\n  ⚠️  发现数据不一致问题！")
    else:
        print("\n  ✓ 数据一致性良好")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(quick_check())
