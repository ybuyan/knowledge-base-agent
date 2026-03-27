import sys
import os

sys.path.insert(0, 'backend')

from app.core.chroma import get_documents_collection

print("=" * 60)
print("检查知识库状态")
print("=" * 60)

collection = get_documents_collection()
count = collection.count()

print(f"\n知识库中的文档总数: {count}")

if count > 0:
    print("\n获取前5个文档:")
    results = collection.peek(limit=5)
    
    for i in range(len(results['ids'])):
        print(f"\n文档 {i+1}:")
        print(f"  ID: {results['ids'][i]}")
        metadata = results['metadatas'][i] if results['metadatas'] else {}
        print(f"  文件名: {metadata.get('document_name', '未知')}")
        print(f"  内容预览: {results['documents'][i][:100]}...")
else:
    print("\n⚠️ 知识库为空！没有找到任何文档。")

print("\n" + "=" * 60)
