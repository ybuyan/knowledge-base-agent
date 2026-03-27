"""
测试文档删除是否正确清理向量数据
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.chroma import get_documents_collection, delete_document_vectors
from app.rag.keyword_index import delete_keyword_index
from app.models.document import DocumentDB
import asyncio


async def check_document_vectors(doc_id: str):
    """检查文档的向量数据是否存在"""
    collection = get_documents_collection()
    
    # 方法1: 通过 metadata 查询
    try:
        results = collection.get(
            where={"document_id": doc_id}
        )
        print(f"\n=== 通过 metadata 查询 document_id={doc_id} ===")
        print(f"找到 {len(results['ids'])} 条向量记录")
        if results['ids']:
            print(f"向量 IDs: {results['ids'][:5]}...")  # 只显示前5个
            if results['metadatas']:
                print(f"元数据示例: {results['metadatas'][0]}")
    except Exception as e:
        print(f"查询失败: {e}")
    
    # 方法2: 通过 ID 前缀查询
    try:
        all_results = collection.get()
        matching_ids = [id for id in all_results['ids'] if id.startswith(doc_id)]
        print(f"\n=== 通过 ID 前缀查询 {doc_id}* ===")
        print(f"找到 {len(matching_ids)} 条匹配的向量记录")
        if matching_ids:
            print(f"匹配的 IDs: {matching_ids[:5]}...")
    except Exception as e:
        print(f"查询失败: {e}")


async def check_keyword_index(doc_id: str):
    """检查文档的关键词索引是否存在"""
    from app.core.mongodb import get_mongo_db
    
    db = get_mongo_db()
    if db is None:
        print("\n=== MongoDB 未连接 ===")
        return
    
    collection = db["keyword_index"]
    count = await collection.count_documents({"doc_id": doc_id})
    print(f"\n=== 关键词索引检查 ===")
    print(f"文档 {doc_id} 的关键词索引记录数: {count}")
    
    if count > 0:
        sample = await collection.find_one({"doc_id": doc_id})
        print(f"示例记录: {sample}")


async def check_database_record(doc_id: str):
    """检查数据库中的文档记录"""
    doc = await DocumentDB.get(doc_id)
    print(f"\n=== 数据库记录检查 ===")
    if doc:
        print(f"文档记录存在: {doc.filename}")
        print(f"状态: {doc.status}")
    else:
        print(f"文档记录不存在")


async def test_deletion(doc_id: str):
    """测试删除操作"""
    print(f"\n{'='*60}")
    print(f"测试文档删除: {doc_id}")
    print(f"{'='*60}")
    
    print("\n--- 删除前检查 ---")
    await check_database_record(doc_id)
    await check_document_vectors(doc_id)
    await check_keyword_index(doc_id)
    
    print("\n--- 执行删除操作 ---")
    
    # 删除向量
    print("删除向量数据...")
    delete_document_vectors(doc_id)
    
    # 删除关键词索引
    print("删除关键词索引...")
    deleted_count = await delete_keyword_index(doc_id)
    print(f"删除了 {deleted_count} 条关键词索引")
    
    # 删除数据库记录
    print("删除数据库记录...")
    await DocumentDB.delete(doc_id)
    
    print("\n--- 删除后检查 ---")
    await check_database_record(doc_id)
    await check_document_vectors(doc_id)
    await check_keyword_index(doc_id)


async def list_all_documents():
    """列出所有文档"""
    print("\n=== 所有文档列表 ===")
    docs = await DocumentDB.list()
    for doc in docs:
        print(f"- {doc.id}: {doc.filename} ({doc.status})")
    return docs


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='测试文档删除')
    parser.add_argument('--doc-id', help='要测试的文档ID')
    parser.add_argument('--list', action='store_true', help='列出所有文档')
    parser.add_argument('--check', help='检查指定文档的数据')
    
    args = parser.parse_args()
    
    if args.list:
        await list_all_documents()
    elif args.check:
        await check_database_record(args.check)
        await check_document_vectors(args.check)
        await check_keyword_index(args.check)
    elif args.doc_id:
        await test_deletion(args.doc_id)
    else:
        print("请使用 --list 列出文档，或 --doc-id <ID> 测试删除，或 --check <ID> 检查文档")


if __name__ == "__main__":
    asyncio.run(main())
