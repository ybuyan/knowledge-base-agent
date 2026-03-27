# 为什么清除后还有文档？

## 问题

执行 `clear_all_data.py` 后，前端仍然显示文档列表。

## 原因分析

文档数据有三个来源：

### 1. 数据库（DocumentDB）
- 存储文档元数据
- 清除脚本会删除 ✓

### 2. 向量数据库（ChromaDB）
- 存储文档的向量表示
- 清除脚本会删除 ✓

### 3. 上传目录（文件系统）
- 存储实际的文件
- 之前的脚本默认不删除 ✗

### 4. 内存缓存（_memory_fallback）
- API 路由中的全局字典
- 缓存文档状态
- 清除脚本无法直接访问 ✗

## 文档列表的加载逻辑

在 `backend/app/api/routes/documents.py` 中：

```python
async def list_documents():
    # 1. 从存储目录同步文件
    _sync_files_from_storage()
    
    # 2. 从数据库获取文档
    docs, total = await DocumentDB.list(page, pageSize)
    
    # 3. 从内存存储获取文档
    storage_docs = _list_doc_storage()
    
    # 4. 合并去重
    merged_docs = merge(docs, storage_docs)
    
    return merged_docs
```

关键问题：`_sync_files_from_storage()` 会自动将上传目录中的文件添加到文档列表！

## 解决方案

### 已实施的修复

1. **默认删除上传的文件**
   - 修改 `clear_all_data.py`，默认 `include_files=True`
   - 新增 `--keep-files` 参数（不推荐使用）

2. **提示重启服务**
   - 清除完成后提示用户重启后端服务
   - 重启会清空内存缓存（`_memory_fallback`）

### 正确的清除流程

```bash
# 1. 停止后端服务
# Ctrl+C 或 kill 进程

# 2. 执行清除脚本
cd backend
python scripts/clear_all_data.py --yes

# 3. 重启后端服务
python -m uvicorn app.main:app --reload
```

### 或者使用完全重置

```bash
# 一步到位（包括完全重置 ChromaDB）
python scripts/clear_all_data.py --yes --complete-reset
```

## 新的参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--yes` | 跳过确认 | False |
| `--include-conversations` | 包括对话历史 | False |
| `--keep-files` | 保留上传的文件 | False（即默认删除）|
| `--complete-reset` | 完全重置 ChromaDB | False |
| `--dry-run` | 预览模式 | False |

## 重要提示

### ⚠️ 必须重启服务

清除数据后，必须重启后端服务，原因：

1. **内存缓存**：`_memory_fallback` 是全局变量，只有重启才能清空
2. **文件监控**：后台任务可能仍在扫描文件
3. **连接池**：数据库连接可能缓存了旧数据

### ⚠️ 默认删除文件

新版本默认删除上传的文件，因为：

1. 保留文件会导致数据不一致
2. 文件会被自动同步回文档列表
3. 无法真正清空知识库

如果确实需要保留文件，使用 `--keep-files`：

```bash
python scripts/clear_all_data.py --yes --keep-files
```

但这不推荐，因为会导致：
- 文档列表仍然显示文件
- 向量数据缺失，查询失败
- 数据不一致

## 验证清除结果

### 1. 检查数据库

```bash
python scripts/quick_check_vectors.py
```

应该显示：
```
数据库文档数: 0
向量文档数: 0
孤立向量: 0
```

### 2. 检查上传目录

```bash
ls data/uploads/
```

应该为空或不存在。

### 3. 检查前端

刷新浏览器，文档列表应该为空。

如果仍有文档，说明：
1. 没有重启后端服务
2. 使用了 `--keep-files` 参数
3. 有其他进程在写入文件

## 完整清除步骤

```bash
# 1. 停止后端服务
# Ctrl+C

# 2. 清除所有数据
cd backend
python scripts/clear_all_data.py --yes --complete-reset

# 输出应该包含：
# ✓ 已删除 X 条文档记录
# ✓ 已删除 X 条文档向量
# ✓ 已删除 X 条关键词索引
# ✓ 已删除 X 个上传的文件
# ⚠️  重要：请重启后端服务以清除内存缓存

# 3. 重启后端服务
python -m uvicorn app.main:app --reload

# 4. 验证
python scripts/quick_check_vectors.py

# 5. 刷新前端浏览器
# 文档列表应该为空
```

## 总结

清除知识库数据需要：
1. ✓ 删除数据库记录
2. ✓ 删除向量数据
3. ✓ 删除关键词索引
4. ✓ 删除上传的文件（新增）
5. ✓ 重启后端服务（新增）

只有完成所有步骤，才能真正清空知识库。
