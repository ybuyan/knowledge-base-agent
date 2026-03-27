import sys
sys.path.insert(0, 'backend')

from app.api.routes.documents import documents_db

print("=" * 60)
print("检查文档上传状态")
print("=" * 60)

print(f"\n文档数据库内容:")
for doc_id, doc_info in documents_db.items():
    print(f"\n文档ID: {doc_id}")
    print(f"  文件名: {doc_info.get('filename')}")
    print(f"  状态: {doc_info.get('status')}")
    print(f"  大小: {doc_info.get('size')}")
    print(f"  上传时间: {doc_info.get('uploadTime')}")
    
    if 'error' in doc_info:
        print(f"  ✗ 错误信息: {doc_info['error']}")
    
    if 'chunk_count' in doc_info:
        print(f"  ✓ 分块数量: {doc_info['chunk_count']}")

print("\n" + "=" * 60)
