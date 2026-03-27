# 文档删除数据同步问题修复

## 问题描述

用户在前端页面删除文档后，再次查询时仍然能够检索到被删除文档中的内容。

## 根本原因

文档删除时只清理了部分数据，导致数据不一致：

### 删除前的清理操作（不完整）
1. ✅ 删除物理文件
2. ✅ 删除 MongoDB `document_status` 集合中的文档记录
3. ✅ 删除 ChromaDB 中的向量数据
4. ❌ **未删除** MongoDB `keyword_index` 集合中的关键词索引

### 数据存储架构

系统使用了三层存储结构：

```
文档数据存储
├── 物理文件 (uploads/)
├── MongoDB
│   ├── document_status (文档元数据)
│   └── keyword_index (关键词倒排索引) ⚠️ 删除时被遗漏
└── ChromaDB
    └── documents collection (向量数据)
```

## 问题影响

当用户删除文档后：
- 文档列表中不再显示该文档 ✅
- 但查询时，关键词检索仍能匹配到该文档的内容 ❌
- 导致返回"幽灵数据"，用户体验差

## 修复方案

### 1. 添加关键词索引删除函数

在 `backend/app/rag/keyword_index.py` 中添加：

```python
async def delete_keyword_index(doc_id: str) -> int:
    """
    删除文档的关键词索引。

    参数:
        doc_id: 文档 ID

    返回:
        删除的记录数量
    """
    from app.core.mongodb import get_mongo_db

    db = get_mongo_db()
    if db is None:
        logger.warning("KeywordIndex: MongoDB 未连接，跳过删除")
        return 0
    
    collection = db[COLLECTION_NAME]
    result = await collection.delete_many({"doc_id": doc_id})
    
    deleted_count = result.deleted_count
    logger.info("KeywordIndex: 文档 %s 删除 %d 条索引", doc_id, deleted_count)
    return deleted_count
```

### 2. 更新文档删除API

在 `backend/app/api/routes/documents.py` 中：

**添加导入：**
```python
from app.rag.keyword_index import delete_keyword_index
```

**更新删除函数：**
```python
async def delete_document(doc_id: str):
    doc = await DocumentDB.get(doc_id)
    
    if not doc:
        doc_data = _get_doc_storage(doc_id)
        if not doc_data:
            raise HTTPException(status_code=404, detail="Document not found")
        doc = DocumentStatusModel(**doc_data)
    
    file_path = doc.file_path
    
    # Delete the physical file
    if file_path and os.path.exists(file_path):
        os.remove(file_path)
    
    # Delete from database
    await DocumentDB.delete(doc_id)
    _del_doc_storage(doc_id)
    
    # Delete vectors from ChromaDB
    delete_document_vectors(doc_id)
    
    # Delete keyword index from MongoDB ⭐ 新增
    await delete_keyword_index(doc_id)
    
    return {"message": "Document deleted successfully", "id": doc_id}
```

## 验证方法

### 使用测试脚本

```bash
# 1. 列出所有文档及其数据分布
python backend/tests/test_document_deletion.py list

# 2. 检查特定文档的数据
python backend/tests/test_document_deletion.py check <doc_id>

# 3. 删除文档后再次检查
# 通过API删除文档
# 然后运行: python backend/tests/test_document_deletion.py check <doc_id>
```

### 手动验证步骤

1. 上传一个测试文档
2. 记录文档ID
3. 查询该文档内容，确认能检索到
4. 删除该文档
5. 再次查询相同内容，确认无法检索到
6. 使用测试脚本检查各存储中的数据是否完全清除

### 数据库检查

```python
# 检查 MongoDB keyword_index
db = get_mongo_db()
count = await db.keyword_index.count_documents({"doc_id": "<doc_id>"})
print(f"关键词索引记录数: {count}")  # 应该为 0

# 检查 ChromaDB
collection = get_documents_collection()
results = collection.get(where={"document_id": "<doc_id>"})
print(f"向量记录数: {len(results['ids'])}")  # 应该为 0

# 检查 document_status
doc = await DocumentDB.get("<doc_id>")
print(f"文档记录: {doc}")  # 应该为 None
```

## 相关文件

- `backend/app/api/routes/documents.py` - 文档删除API
- `backend/app/rag/keyword_index.py` - 关键词索引管理
- `backend/app/core/chroma.py` - 向量数据库操作
- `backend/app/models/document.py` - 文档数据模型
- `backend/tests/test_document_deletion.py` - 删除功能测试脚本

## 注意事项

1. 此修复确保了数据的完整性和一致性
2. 删除操作是不可逆的，建议在生产环境中添加软删除功能
3. 如果有历史遗留的"幽灵数据"，需要手动清理：

```python
# 清理孤立的关键词索引
from app.core.mongodb import get_mongo_db
from app.models.document import DocumentDB

db = get_mongo_db()
all_docs = await DocumentDB.list(page=1, page_size=1000)
valid_doc_ids = {doc.id for doc in all_docs[0]}

# 删除不存在的文档的索引
async for record in db.keyword_index.find():
    if record['doc_id'] not in valid_doc_ids:
        await db.keyword_index.delete_many({"doc_id": record['doc_id']})
        print(f"清理孤立索引: {record['doc_id']}")
```

## 修复状态

- ✅ 问题已识别
- ✅ 修复代码已实现
- ✅ 测试脚本已创建
- ⏳ 待部署验证
