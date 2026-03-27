"""
清理孤立的文档数据

此脚本用于清理历史遗留的"幽灵数据"：
- 在 keyword_index 中存在但在 document_status 中不存在的记录
- 在 ChromaDB 中存在但在 document_status 中不存在的向量
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.mongodb import get_mongo_db
from app.core.chroma import get_documents_collection
from app.models.document import DocumentDB


async def cleanup_orphaned_keyword_index():
    """清理孤立的关键词索引"""
    print("\n清理孤立的关键词索引")
    print("=" * 60)
    
    # 获取所有有效的文档ID
    docs, total = await DocumentDB.list(page=1, page_size=10000)
    valid_doc_ids = {doc.id for doc in docs}
    print(f"有效文档数: {len(valid_doc_ids)}")
    
    # 检查 keyword_index
    db = get_mongo_db()
    if not db:
        print("❌ MongoDB 未连接")
        return
    
    # 获取所有唯一的 doc_id
    pipeline = [
        {"$group": {"_id": "$doc_id"}},
        {"$project": {"doc_id": "$_id", "_id": 0}}
    ]
    
    indexed_doc_ids = set()
    async for doc in db.keyword_index.aggregate(pipeline):
        indexed_doc_ids.add(doc['doc_id'])
    
    print(f"索引中的文档数: {len(indexed_doc_ids)}")
    
    # 找出孤立的文档ID
    orphaned_ids = indexed_doc_ids - valid_doc_ids
    
    if not orphaned_ids:
        print("✅ 没有发现孤立的关键词索引")
        return
    
    print(f"\n发现 {len(orphaned_ids)} 个孤立的文档索引:")
    for doc_id in orphaned_ids:
        count = await db.keyword_index.count_documents({"doc_id": doc_id})
        print(f"  - {doc_id}: {count} 条记录")
    
    # 询问是否删除
    if input("\n是否删除这些孤立的索引? (yes/no): ").lower() == 'yes':
        total_deleted = 0
        for doc_id in orphaned_ids:
            result = await db.keyword_index.delete_many({"doc_id": doc_id})
            deleted = result.deleted_count
            total_deleted += deleted
            print(f"  ✓ 删除 {doc_id}: {deleted} 条记录")
        
        print(f"\n✅ 总共删除 {total_deleted} 条孤立索引")
    else:
        print("取消删除")


async def cleanup_orphaned_vectors():
    """清理孤立的向量数据"""
    print("\n清理孤立的向量数据")
    print("=" * 60)
    
    # 获取所有有效的文档ID
    docs, total = await DocumentDB.list(page=1, page_size=10000)
    valid_doc_ids = {doc.id for doc in docs}
    print(f"有效文档数: {len(valid_doc_ids)}")
    
    try:
        collection = get_documents_collection()
        
        # 获取所有向量
        results = collection.get()
        
        if not results or 'ids' not in results or not results['ids']:
            print("✅ ChromaDB 中没有向量数据")
            return
        
        total_vectors = len(results['ids'])
        print(f"ChromaDB 中的向量数: {total_vectors}")
        
        # 检查每个向量的 document_id
        orphaned_vector_ids = []
        orphaned_doc_ids = set()
        
        for i, vector_id in enumerate(results['ids']):
            metadata = results['metadatas'][i] if results['metadatas'] else {}
            doc_id = metadata.get('document_id')
            
            if doc_id and doc_id not in valid_doc_ids:
                orphaned_vector_ids.append(vector_id)
                orphaned_doc_ids.add(doc_id)
        
        if not orphaned_vector_ids:
            print("✅ 没有发现孤立的向量数据")
            return
        
        print(f"\n发现 {len(orphaned_vector_ids)} 个孤立的向量，来自 {len(orphaned_doc_ids)} 个文档:")
        for doc_id in orphaned_doc_ids:
            count = sum(1 for vid, meta in zip(results['ids'], results['metadatas']) 
                       if meta.get('document_id') == doc_id)
            print(f"  - {doc_id}: {count} 个向量")
        
        # 询问是否删除
        if input("\n是否删除这些孤立的向量? (yes/no): ").lower() == 'yes':
            # 按文档ID批量删除
            for doc_id in orphaned_doc_ids:
                collection.delete(where={"document_id": doc_id})
                print(f"  ✓ 删除文档 {doc_id} 的向量")
            
            print(f"\n✅ 总共删除 {len(orphaned_vector_ids)} 个孤立向量")
        else:
            print("取消删除")
            
    except Exception as e:
        print(f"❌ 清理向量数据失败: {e}")


async def show_statistics():
    """显示数据统计"""
    print("\n数据统计")
    print("=" * 60)
    
    # 文档状态
    docs, total = await DocumentDB.list(page=1, page_size=10000)
    print(f"文档记录数 (document_status): {total}")
    
    # 关键词索引
    db = get_mongo_db()
    if db:
        keyword_count = await db.keyword_index.count_documents({})
        print(f"关键词索引记录数 (keyword_index): {keyword_count}")
        
        # 统计每个文档的索引数
        pipeline = [
            {"$group": {"_id": "$doc_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        print("\n索引最多的文档 (Top 5):")
        async for doc in db.keyword_index.aggregate(pipeline):
            print(f"  - {doc['_id']}: {doc['count']} 条")
    
    # ChromaDB 向量
    try:
        collection = get_documents_collection()
        vector_count = collection.count()
        print(f"\n向量数据数 (ChromaDB): {vector_count}")
    except Exception as e:
        print(f"\n向量数据数 (ChromaDB): 检查失败 - {e}")
    
    print("=" * 60)


async def main():
    """主函数"""
    print("\n孤立数据清理工具")
    print("=" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 显示数据统计")
        print("2. 清理孤立的关键词索引")
        print("3. 清理孤立的向量数据")
        print("4. 清理所有孤立数据")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-4): ").strip()
        
        if choice == '0':
            print("退出")
            break
        elif choice == '1':
            await show_statistics()
        elif choice == '2':
            await cleanup_orphaned_keyword_index()
        elif choice == '3':
            await cleanup_orphaned_vectors()
        elif choice == '4':
            await cleanup_orphaned_keyword_index()
            await cleanup_orphaned_vectors()
            await show_statistics()
        else:
            print("无效选项")


if __name__ == "__main__":
    asyncio.run(main())
