"""
清理孤立的向量数据

当文档从数据库中删除但向量数据未删除时，会产生孤立的向量数据。
这个脚本会找到并清理这些孤立数据。
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.chroma import get_documents_collection
from app.models.document import DocumentDB
import asyncio


async def find_orphaned_vectors():
    """找到孤立的向量数据"""
    collection = get_documents_collection()
    
    # 获取所有向量的 document_id
    all_data = collection.get()
    vector_doc_ids = set()
    
    print("=== 分析向量数据 ===")
    for id in all_data['ids']:
        # ID 格式: {document_id}_chunk_{i}
        if '_chunk_' in id:
            doc_id = id.split('_chunk_')[0]
            vector_doc_ids.add(doc_id)
    
    print(f"向量数据中的文档数: {len(vector_doc_ids)}")
    
    # 获取数据库中的所有文档
    db_docs = await DocumentDB.list()
    db_doc_ids = {doc.id for doc in db_docs}
    
    print(f"数据库中的文档数: {len(db_doc_ids)}")
    
    # 找到孤立的向量
    orphaned_doc_ids = vector_doc_ids - db_doc_ids
    
    print(f"\n=== 孤立的向量数据 ===")
    print(f"孤立文档数: {len(orphaned_doc_ids)}")
    
    if orphaned_doc_ids:
        print("\n孤立的文档 ID:")
        for doc_id in sorted(orphaned_doc_ids):
            # 统计该文档的向量数量
            count = sum(1 for id in all_data['ids'] if id.startswith(doc_id))
            print(f"  {doc_id}: {count} 个向量分块")
    
    return orphaned_doc_ids, all_data['ids']


async def cleanup_orphaned_vectors(orphaned_doc_ids, all_ids, dry_run=True):
    """清理孤立的向量数据"""
    if not orphaned_doc_ids:
        print("\n没有孤立的向量数据需要清理")
        return
    
    collection = get_documents_collection()
    
    # 收集要删除的向量 ID
    ids_to_delete = []
    for doc_id in orphaned_doc_ids:
        matching_ids = [id for id in all_ids if id.startswith(doc_id)]
        ids_to_delete.extend(matching_ids)
    
    print(f"\n=== 清理操作 ===")
    print(f"将删除 {len(ids_to_delete)} 个向量分块")
    
    if dry_run:
        print("\n[DRY RUN] 不会实际删除数据")
        print("要实际执行删除，请使用 --execute 参数")
        return
    
    # 执行删除
    print("\n开始删除...")
    try:
        collection.delete(ids=ids_to_delete)
        print(f"✓ 成功删除 {len(ids_to_delete)} 个向量分块")
    except Exception as e:
        print(f"✗ 删除失败: {e}")


async def verify_cleanup():
    """验证清理结果"""
    orphaned_doc_ids, _ = await find_orphaned_vectors()
    
    if not orphaned_doc_ids:
        print("\n✓ 所有孤立向量已清理完成")
    else:
        print(f"\n✗ 仍有 {len(orphaned_doc_ids)} 个孤立文档")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='清理孤立的向量数据')
    parser.add_argument('--execute', action='store_true', help='实际执行删除（默认为 dry run）')
    parser.add_argument('--verify', action='store_true', help='验证清理结果')
    
    args = parser.parse_args()
    
    if args.verify:
        await verify_cleanup()
    else:
        orphaned_doc_ids, all_ids = await find_orphaned_vectors()
        await cleanup_orphaned_vectors(orphaned_doc_ids, all_ids, dry_run=not args.execute)


if __name__ == "__main__":
    asyncio.run(main())
