import sys
import os

sys.path.insert(0, 'backend')

from app.config import settings
from app.core.chroma import get_documents_collection, get_chroma_client

print("=" * 60)
print("文档上传入库流程详解")
print("=" * 60)

print("\n1. 文档上传流程:")
print("   前端上传 → /api/documents/upload")
print("   文件保存 → data/uploads/{doc_id}_{filename}")
print("   后台任务 → process_document_task")
print("   Agent处理 → document_agent")
print("   Skill执行 → document_upload")

print("\n2. 文档处理流程 (document_upload skill):")
print("   步骤1: DocumentParser - 解析文档内容")
print("   步骤2: TextSplitter - 切分文本")
print("          参数: chunk_size=500, chunk_overlap=50")
print("   步骤3: EmbeddingProcessor - 生成向量")
print("   步骤4: VectorStore - 存储到 ChromaDB")

print("\n3. 存储位置:")
print(f"   ChromaDB 持久化目录: {settings.chroma_persist_dir}")
print(f"   绝对路径: {os.path.abspath(settings.chroma_persist_dir)}")

print("\n4. 检查存储目录:")
chroma_dir = os.path.abspath(settings.chroma_persist_dir)
if os.path.exists(chroma_dir):
    print(f"   ✓ 目录存在: {chroma_dir}")
    print(f"\n   目录内容:")
    for item in os.listdir(chroma_dir):
        item_path = os.path.join(chroma_dir, item)
        if os.path.isdir(item_path):
            print(f"     📁 {item}/")
        else:
            print(f"     📄 {item}")
else:
    print(f"   ✗ 目录不存在: {chroma_dir}")

print("\n5. 检查 ChromaDB 数据:")
try:
    client = get_chroma_client()
    print(f"   ✓ ChromaDB 客户端已初始化")
    
    collection = get_documents_collection()
    count = collection.count()
    print(f"   ✓ documents collection 存在")
    print(f"   文档总数: {count}")
    
    if count > 0:
        print(f"\n   示例文档 (前3个):")
        results = collection.peek(limit=3)
        for i in range(len(results['ids'])):
            print(f"\n   文档 {i+1}:")
            print(f"     ID: {results['ids'][i]}")
            metadata = results['metadatas'][i] if results['metadatas'] else {}
            print(f"     文件名: {metadata.get('document_name', '未知')}")
            print(f"     文档ID: {metadata.get('document_id', '未知')}")
            print(f"     内容长度: {len(results['documents'][i])}")
            print(f"     内容预览: {results['documents'][i][:80]}...")
    
except Exception as e:
    print(f"   ✗ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n6. 检查上传目录:")
upload_dir = "data/uploads"
if os.path.exists(upload_dir):
    print(f"   ✓ 上传目录存在: {os.path.abspath(upload_dir)}")
    files = os.listdir(upload_dir)
    print(f"   已上传文件数: {len(files)}")
    if files:
        print(f"   文件列表:")
        for f in files[:5]:
            file_path = os.path.join(upload_dir, f)
            size = os.path.getsize(file_path)
            print(f"     📄 {f} ({size} bytes)")
else:
    print(f"   ✗ 上传目录不存在")

print("\n" + "=" * 60)
