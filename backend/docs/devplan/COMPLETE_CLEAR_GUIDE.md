# 完全清除知识库 - 快速指南

## 问题：清除后仍有文档？

如果执行清除脚本后前端仍显示文档，原因是：

1. **没有删除上传的文件** - 文件会被自动同步回来
2. **没有重启后端服务** - 内存缓存未清空

## 正确的清除步骤

### 方法一：停止服务后清除（推荐）

```bash
# 1. 停止后端服务
# 按 Ctrl+C 或关闭终端

# 2. 执行清除
cd backend
python scripts/clear_all_data.py --yes

# 3. 重启服务
python -m uvicorn app.main:app --reload

# 4. 刷新浏览器
```

### 方法二：服务运行时清除

```bash
# 1. 执行清除
cd backend
python scripts/clear_all_data.py --yes

# 2. 重启后端服务
# 按 Ctrl+C 停止服务
# 然后重新启动：
python -m uvicorn app.main:app --reload

# 3. 刷新浏览器
```

## 重要说明

### ⚠️ 必须重启服务

清除后必须重启后端服务，否则：
- 内存缓存（`_memory_fallback`）不会清空
- 前端仍会显示旧文档

### ⚠️ 默认删除文件

新版本脚本默认删除上传的文件，因为：
- 保留文件会导致它们被自动同步回文档列表
- 无法真正清空知识库

如果需要保留文件（不推荐）：
```bash
python scripts/clear_all_data.py --yes --keep-files
```

## 验证清除结果

### 1. 检查数据

```bash
python scripts/quick_check_vectors.py
```

预期输出：
```
数据库文档数: 0
向量文档数: 0
孤立向量: 0
```

### 2. 检查文件

```bash
# Windows
dir data\uploads

# Linux/Mac
ls data/uploads/
```

应该为空或显示"找不到文件"。

### 3. 检查前端

刷新浏览器，文档列表应该为空。

## 完整清除（包括对话历史）

```bash
# 停止服务
# Ctrl+C

# 完全清除
python scripts/clear_all_data.py --yes --include-conversations --complete-reset

# 重启服务
python -m uvicorn app.main:app --reload
```

## 快速参考

| 命令 | 说明 |
|------|------|
| `--yes` | 跳过确认 |
| `--dry-run` | 预览模式 |
| `--include-conversations` | 包括对话历史 |
| `--keep-files` | 保留文件（不推荐）|
| `--complete-reset` | 完全重置 ChromaDB |

## 故障排除

### 问题：清除后仍有文档

**原因：** 没有重启服务

**解决：** 重启后端服务

### 问题：文件仍然存在

**原因：** 使用了 `--keep-files` 参数

**解决：** 重新运行不带 `--keep-files` 的命令

### 问题：向量数据未清除

**原因：** ChromaDB 连接问题

**解决：** 使用 `--complete-reset` 完全重置

## 总结

完全清除知识库的三个关键步骤：

1. ✓ 执行清除脚本（默认删除文件）
2. ✓ 重启后端服务
3. ✓ 刷新浏览器

只有完成所有步骤，才能真正清空知识库！
