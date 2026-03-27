"""
检查ChromaDB中的metadata
"""

from app.core.chroma import get_documents_collection

collection = get_documents_collection()

# 获取所有数据
results = collection.get()

print(f"Total documents: {len(results['ids'])}")
print("\nSample metadata:")

for i in range(min(5, len(results['ids']))):
    print(f"\nDocument {i+1}:")
    print(f"  ID: {results['ids'][i]}")
    print(f"  Metadata: {results['metadatas'][i] if results['metadatas'] else 'None'}")
    print(f"  Content preview: {results['documents'][i][:100]}...")
