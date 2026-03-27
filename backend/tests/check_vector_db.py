#!/usr/bin/env python
"""
检查向量数据库中的文档 metadata
"""
import sys
sys.path.insert(0, 'c:\\D\\code\\learning\\Agent\\AI-assistent\\backend')

from app.core.chroma import get_documents_collection

def check_vector_db():
    collection = get_documents_collection()
    
    # 获取所有文档
    results = collection.get()
    
    print(f"总共有 {len(results['ids'])} 个文档片段\n")
    
    # 按 document_id 分组统计
    doc_stats = {}
    for i, doc_id in enumerate(results['ids']):
        metadata = results['metadatas'][i] if results['metadatas'] else {}
        doc_name = metadata.get('document_name', 'Unknown')
        
        if doc_name not in doc_stats:
            doc_stats[doc_name] = {
                'count': 0,
                'ids': []
            }
        doc_stats[doc_name]['count'] += 1
        doc_stats[doc_name]['ids'].append(doc_id)
    
    print("文档统计:")
    print("-" * 60)
    for doc_name, stats in sorted(doc_stats.items()):
        print(f"文档名: {doc_name}")
        print(f"  片段数: {stats['count']}")
        print(f"  示例ID: {stats['ids'][0] if stats['ids'] else 'N/A'}")
        print()
    
    # 检查 Unknown 的文档
    unknown_count = doc_stats.get('Unknown', {}).get('count', 0)
    unknown_count += doc_stats.get('unknown', {}).get('count', 0)
    
    if unknown_count > 0:
        print(f"⚠️  发现 {unknown_count} 个片段的 document_name 为 Unknown")
        print("建议：重新上传这些文档")
    else:
        print("✅ 所有文档都有正确的 document_name")

if __name__ == "__main__":
    check_vector_db()
