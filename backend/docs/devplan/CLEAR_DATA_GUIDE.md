# 清除知识库数据指南

## 概述

`clear_all_data.py` 脚本用于清除所有知识库数据，包括文档记录、向量数据、关键词索引等。

## 使用方法

### 基本用法

```bash
cd backend

# 预览将要删除的内容（推荐先执行）
python scripts/clear_all_data.py --dry-run

# 交互式清除（会要求确认）
python scripts/clear_all_data.py

# 直接清除（跳过确认）
python scripts/clear_all_data.py --yes
```

### 高级选项

```bash
# 包括对话历史
python scripts/clear_all_data.py --include-conversations

# 删除上传的文件
python scripts/clear_all_data.py --include-files

# 完全重置（删除 ChromaDB 目录）
python scripts/clear_all_data.py --complete-reset

# 组合使用
python scripts/clear_all_data.py --yes --include-files --complete-reset
```

## 参数说明

| 参数 | 简写 | 说明 |
|------|------|------|
| `--yes` | `-y` | 跳过确认，直接执行 |
| `--include-conversations` | - | 包括对话历史 |
| `--include-files` | - | 删除上传的文件 |
| `--complete-reset` | - | 完全重置（删除 ChromaDB 目录）|
| `--dry-run` | - | 仅显示将要删除的内容 |

## 清除内容

### 默认清除

- ✓ 数据库中的所有文档记录
- ✓ ChromaDB 中的所有文档向量
- ✓ MongoDB 中的所有关键词索引

### 可选清除

- `--include-conversations`: 对话历史向量
- `--include-files`: 上传的文件
- `--complete-reset`: ChromaDB 完全重置

## 使用场景

### 1. 开发测试

清除测试数据，重新开始：

```bash
python scripts/clear_all_data.py --yes --include-files
```

### 2. 数据迁移

完全重置系统：

```bash
python scripts/clear_all_data.py --yes --complete-reset --include-files
```

### 3. 清理孤立数据

只清除知识库数据，保留对话历史：

```bash
python scripts/clear_all_data.py --yes
```

### 4. 预览模式

查看将要删除的内容：

```bash
python scripts/clear_all_data.py --dry-run
```

## 安全提示

### ⚠️ 重要警告

1. **此操作不可逆**：删除的数据无法恢复
2. **建议备份**：执行前备份重要数据
3. **先预览**：使用 `--dry-run` 查看将要删除的内容
4. **生产环境**：谨慎使用，建议先在测试环境验证

### 备份建议

执行清除前，建议备份以下内容：

```bash
# 备份 ChromaDB
cp -r data/chroma data/chroma_backup_$(date +%Y%m%d)

# 备份上传的文件
cp -r data/uploads data/uploads_backup_$(date +%Y%m%d)

# 导出数据库（如果使用 PostgreSQL）
pg_dump dbname > backup_$(date +%Y%m%d).sql
```

## 执行流程

### 1. 预览阶段

```bash
python scripts/clear_all_data.py --dry-run
```

输出示例：
```
============================================================
DRY RUN 模式 - 仅显示将要删除的内容
============================================================

数据库文档记录: 12 条
文档向量数据: 156 条
关键词索引: 156 条

要实际执行删除，请移除 --dry-run 参数
```

### 2. 确认阶段

```bash
python scripts/clear_all_data.py
```

输出示例：
```
============================================================
⚠️  警告：此操作将删除所有知识库数据！
============================================================

将要删除:
  - 所有文档记录（数据库）
  - 所有向量数据（ChromaDB）
  - 所有关键词索引（MongoDB）

此操作不可逆！

请输入 'yes' 确认删除，或输入其他内容取消:
> 
```

### 3. 执行阶段

输入 `yes` 后：

```
=== 清除数据库文档记录 ===
  ✓ 已删除 12 条文档记录

=== 清除向量数据 ===
  ✓ 已删除 156 条文档向量

=== 清除关键词索引 ===
  ✓ 已删除 156 条关键词索引

============================================================
清除完成
============================================================
总计删除: 324 条记录

知识库已清空，可以重新上传文档。
```

## 常见问题

### Q1: 清除后需要重启服务吗？

A: 不需要。清除操作不影响正在运行的服务。

### Q2: 清除后如何恢复数据？

A: 清除操作不可逆。如果需要恢复，只能从备份中恢复。

### Q3: 清除会影响用户账户吗？

A: 不会。此脚本只清除知识库数据，不影响用户账户。

### Q4: 清除会影响配置吗？

A: 不会。配置文件不受影响。

### Q5: 可以只清除特定文档吗？

A: 此脚本清除所有数据。如需删除特定文档，请使用文档删除 API。

## 相关脚本

- `cleanup_orphaned_vectors.py` - 清理孤立的向量数据
- `cleanup_orphaned_data.py` - 清理孤立的数据
- `quick_check_vectors.py` - 检查数据一致性

## 技术细节

### 清除顺序

1. 数据库文档记录
2. 向量数据（ChromaDB）
3. 关键词索引（MongoDB）
4. 上传的文件（可选）

### 实现方式

- **数据库**: 使用 `DocumentDB.delete()` 逐个删除
- **ChromaDB**: 删除集合并重新创建
- **MongoDB**: 使用 `delete_many({})` 批量删除
- **文件**: 使用 `Path.unlink()` 删除

### 性能考虑

- 大量数据时可能需要较长时间
- ChromaDB 完全重置比常规清除更快
- 建议在低峰期执行

## 示例场景

### 场景 1: 开发环境重置

```bash
# 1. 预览
python scripts/clear_all_data.py --dry-run

# 2. 清除所有数据和文件
python scripts/clear_all_data.py --yes --include-files --complete-reset

# 3. 重新上传文档
# 通过前端或 API 上传新文档
```

### 场景 2: 清理测试数据

```bash
# 只清除知识库，保留对话历史
python scripts/clear_all_data.py --yes
```

### 场景 3: 生产环境维护

```bash
# 1. 备份
cp -r data/chroma data/chroma_backup
cp -r data/uploads data/uploads_backup

# 2. 预览
python scripts/clear_all_data.py --dry-run

# 3. 确认后清除
python scripts/clear_all_data.py

# 4. 验证
python scripts/quick_check_vectors.py
```

## 总结

`clear_all_data.py` 是一个强大的数据清除工具，使用时请：

1. ✓ 先使用 `--dry-run` 预览
2. ✓ 备份重要数据
3. ✓ 在测试环境验证
4. ✓ 生产环境谨慎使用
5. ✓ 记录操作日志
