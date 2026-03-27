"""
诊断向量删除问题
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.chroma import get_documents_collection
import asyncio


async def diagnose():
    collection = get_documents_collection()
    
    print("=== ChromaDB 向量数据诊断 ===\n")
    
    # 获取所有数据
    all_data = collection.get()
    total_count = len(all_data['ids'])
    
    print(f"总向量数: {total_count}\n")
    
    if total_count == 0:
        print("没有向量数据")
        return
    
    # 分析 ID 格式
    print("=== ID 格式分析 ===")
    sample_ids = all_data['ids'][:10]
    for id in sample_ids:
        print(f"  {id}")
    
    # 提取 document_id
    doc_ids = set()
    for id in all_data['ids']:
        # ID 格式: {document_id}_chunk_{i}
        if '_chunk_' in id:
            doc_id = id.split('_chunk_')[0]
            doc_ids.add(doc_id)
    
    print(f"\n发现 {len(doc_ids)} 个不同的文档ID:")
    for doc_id in sorted(doc_ids)[:10]:
        count = sum(1 for id in all_data['ids'] if id.startswith(doc_id))
        print(f"  {doc_id}: {count} 个分块")
    
    # 检查 metadata
    print("\n=== Metadata 分析 ===")
    if all_data['metadatas']:
        sample_meta = all_data['metadatas'][0]
        print(f"Metadata 字段: {list(sample_meta.keys())}")
        print(f"示例 metadata:")
        for key, value in sample_meta.items():
            print(f"  {key}: {value}")
        
        # 检查 document_id 字段
        if 'document_id' in sample_meta:
            print(f"\n✓ metadata 中有 'document_id' 字段")
        else:
            print(f"\n✗ metadata 中没有 'document_id' 字段！")
    
    # 测试两种删除方法
    if doc_ids:
        test_doc_id = list(doc_ids)[0]
        print(f"\n=== 测试删除方法 (文档: {test_doc_id}) ===")
        
        # 方法1: 通过 metadata 查询
        print("\n方法1: 通过 metadata 查询")
        try:
            results = collection.get(where={"document_id": test_doc_id})
            print(f"  找到 {len(results['ids'])} 条记录")
            if results['ids']:
                print(f"  示例 ID: {results['ids'][0]}")
        except Exception as e:
            print(f"  ✗ 查询失败: {e}")
        
        # 方法2: 通过 ID 前缀匹配
        print("\n方法2: 通过 ID 前缀匹配")
        try:
            matching_ids = [id for id in all_data['ids'] if id.startswith(test_doc_id)]
            print(f"  找到 {len(matching_ids)} 条记录")
            if matching_ids:
                print(f"  示例 ID: {matching_ids[0]}")
        except Exception as e:
            print(f"  ✗ 匹配失败: {e}")
        
        # 测试删除（不实际执行）
        print(f"\n如果要删除文档 {test_doc_id}:")
        print(f"  方法1 命令: collection.delete(where={{'document_id': '{test_doc_id}'}})")
        print(f"  方法2 命令: collection.delete(ids={matching_ids[:3]}...)")


if __name__ == "__main__":
    asyncio.run(diagnose())
