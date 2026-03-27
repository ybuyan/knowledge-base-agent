# 向量删除问题修复

## 问题描述

用户反馈：删除文档后，仍然能查询到被删除文档的内容。

## 根本原因

文档删除时，向量数据没有被正确清理。原因是 `delete_document_vectors` 函数使用的删除方法不可靠：

```python
# 原实现 - 不可靠
def delete_document_vectors(doc_id: str) -> bool:
    collection = get_documents_collection()
    collection.delete(where={"document_id": doc_id})  # 通过 metadata 过滤
```

问题：
1. ChromaDB 的 `where` 过滤在某些情况下可能不工作
2. 依赖 metadata 字段的正确性
3. 没有验证删除是否成功

## 解决方案

### 1. 修复删除函数

修改 `backend/app/core/chroma.py` 中的 `delete_document_vectors` 函数：

```python
def delete_document_vectors(doc_id: str) -> bool:
    """Delete all vectors associated with a document from ChromaDB"""
    try:
        collection = get_documents_collection()
        
        # 方法1: 尝试通过 metadata 删除
        try:
            collection.delete(where={"document_id": doc_id})
        except Exception as meta_error:
            print(f"Metadata deletion failed: {meta_error}")
        
        # 方法2: 通过 ID 前缀删除（更可靠）
        # 向量 ID 格式: {document_id}_chunk_{i}
        all_ids = collection.get()["ids"]
        ids_to_delete = [id for id in all_ids if id.startswith(doc_id)]
        
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)
            print(f"Deleted {len(ids_to_delete)} vector chunks for document {doc_id}")
        else:
            print(f"No vectors found for document {doc_id}")
        
        return True
    except Exception as e:
        print(f"Error deleting vectors for document {doc_id}: {e}")
        return False
```

改进：
- 使用双重删除策略：先尝试 metadata 过滤，再使用 ID 前缀匹配
- ID 前缀匹配更可靠，因为向量 ID 格式固定为 `{document_id}_chunk_{i}`
- 添加日志输出，便于调试
- 验证是否找到要删除的向量

### 2. 清理现有孤立数据

创建了清理脚本 `backend/scripts/cleanup_orphaned_vectors.py`：

```bash
# 检查孤立的向量数据（dry run）
python backend/scripts/cleanup_orphaned_vectors.py

# 实际执行清理
python backend/scripts/cleanup_orphaned_vectors.py --execute

# 验证清理结果
python backend/scripts/cleanup_orphaned_vectors.py --verify
```

### 3. 诊断工具

创建了诊断脚本 `backend/tests/diagnose_vector_deletion.py`：

```bash
# 诊断向量数据结构
python backend/tests/diagnose_vector_deletion.py
```

创建了测试脚本 `backend/tests/test_document_deletion.py`：

```bash
# 列出所有文档
python backend/tests/test_document_deletion.py --list

# 检查特定文档的数据
python backend/tests/test_document_deletion.py --check <doc_id>

# 测试删除操作
python backend/tests/test_document_deletion.py --doc-id <doc_id>
```

## 验证步骤

1. 运行诊断脚本，检查当前向量数据状态：
   ```bash
   python backend/tests/diagnose_vector_deletion.py
   ```

2. 检查是否有孤立的向量数据：
   ```bash
   python backend/scripts/cleanup_orphaned_vectors.py
   ```

3. 如果有孤立数据，执行清理：
   ```bash
   python backend/scripts/cleanup_orphaned_vectors.py --execute
   ```

4. 测试新的删除功能：
   - 上传一个测试文档
   - 记录文档 ID
   - 删除文档
   - 验证向量数据是否被清理：
     ```bash
     python backend/tests/test_document_deletion.py --check <doc_id>
     ```

## 相关文件

- `backend/app/core/chroma.py` - 修复的删除函数
- `backend/app/api/routes/documents.py` - 文档删除 API
- `backend/app/rag/indexer.py` - 索引器的删除方法（参考实现）
- `backend/scripts/cleanup_orphaned_vectors.py` - 清理孤立数据
- `backend/tests/diagnose_vector_deletion.py` - 诊断工具
- `backend/tests/test_document_deletion.py` - 测试工具

## 注意事项

1. 向量 ID 格式必须保持为 `{document_id}_chunk_{i}`，否则 ID 前缀匹配会失效
2. 清理孤立数据前建议先备份 ChromaDB 数据目录
3. 如果向量数据量很大，`collection.get()` 可能会比较慢，可以考虑优化

## 后续改进

1. 添加删除操作的事务性保证
2. 在删除后验证是否成功
3. 添加删除操作的审计日志
4. 考虑使用 ChromaDB 的批量删除 API 提高性能
