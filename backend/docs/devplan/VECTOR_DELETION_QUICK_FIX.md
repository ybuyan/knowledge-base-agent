# 向量删除问题 - 快速修复指南

## 问题

删除文档后，仍然能查询到被删除文档的内容。

## 原因

向量数据没有被正确删除。`delete_document_vectors` 函数使用的 metadata 过滤方法不可靠。

## 快速修复步骤

### 1. 检查问题（1分钟）

```bash
cd backend
python scripts/quick_check_vectors.py
```

这会显示：
- 数据库中有多少文档
- 向量数据库中有多少文档
- 是否有孤立的向量数据（已删除但向量仍存在）
- 是否有缺失的向量数据（文档存在但向量不存在）

### 2. 清理孤立数据（2分钟）

如果发现孤立的向量数据：

```bash
# 先预览要删除的数据（dry run）
python scripts/cleanup_orphaned_vectors.py

# 确认无误后，实际执行删除
python scripts/cleanup_orphaned_vectors.py --execute

# 验证清理结果
python scripts/quick_check_vectors.py
```

### 3. 验证修复（1分钟）

测试删除功能是否正常：

1. 在前端上传一个测试文档
2. 记录文档 ID（从 URL 或文档列表中获取）
3. 删除该文档
4. 检查向量是否被删除：

```bash
python tests/test_document_deletion.py --check <文档ID>
```

应该显示：
- 数据库记录不存在 ✓
- 向量数据不存在 ✓
- 关键词索引不存在 ✓

## 技术细节

### 修复内容

修改了 `backend/app/core/chroma.py` 中的 `delete_document_vectors` 函数：

- 原方法：只使用 metadata 过滤删除（不可靠）
- 新方法：使用 ID 前缀匹配删除（可靠）

向量 ID 格式：`{document_id}_chunk_{i}`

新实现会：
1. 先尝试 metadata 过滤删除
2. 再通过 ID 前缀匹配删除（确保删除成功）
3. 输出删除日志

### 相关脚本

- `scripts/quick_check_vectors.py` - 快速检查数据一致性
- `scripts/cleanup_orphaned_vectors.py` - 清理孤立的向量数据
- `tests/diagnose_vector_deletion.py` - 详细诊断向量数据结构
- `tests/test_document_deletion.py` - 测试删除功能

## 预防措施

1. 定期运行 `quick_check_vectors.py` 检查数据一致性
2. 删除文档后，检查日志确认向量已删除
3. 如果发现问题，立即运行清理脚本

## 完整文档

详细技术文档：`backend/docs/devplan/VECTOR_DELETION_FIX.md`
