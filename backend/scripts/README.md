# File Watcher Service

自动监控文件夹变化并处理文档的服务。

## 功能特性

- **实时监控**: 使用 watchdog 库监控文件系统事件
- **增量处理**: 新文件自动处理，不重复
- **修改检测**: 通过 MD5 哈希检测文件是否真正变化
- **删除同步**: 文件删除后自动从向量库移除
- **断点续传**: 记录处理状态，中断后可继续
- **多线程处理**: 支持并行处理多个文件
- **防抖处理**: 避免频繁修改触发多次处理

## 安装依赖

```bash
pip install watchdog
```

## 配置

编辑 `scripts/config/watch.json`:

```json
{
  "watch_dirs": [
    {
      "path": "D:/knowledge_base/policies",
      "enabled": true,
      "recursive": true,
      "extensions": [".pdf", ".docx", ".txt", ".md", ".doc"]
    }
  ],
  "processing": {
    "workers": 4,
    "batch_size": 10,
    "retry_times": 3,
    "retry_delay": 5,
    "debounce_seconds": 2
  },
  "storage": {
    "state_db": "data/watch_state.db",
    "log_dir": "data/watch_logs"
  }
}
```

### 配置说明

| 字段 | 说明 |
|------|------|
| `watch_dirs` | 监控目录列表 |
| `path` | 目录路径 |
| `enabled` | 是否启用 |
| `recursive` | 是否递归监控子目录 |
| `extensions` | 监控的文件扩展名 |
| `workers` | 处理线程数 |
| `debounce_seconds` | 防抖时间（秒） |

## 使用方法

### 启动监控服务

```bash
# 从 backend 目录运行
cd backend
python scripts/file_watcher.py

# 指定配置文件
python scripts/file_watcher.py --config scripts/config/watch.json

# 跳过初始扫描
python scripts/file_watcher.py --no-initial-scan

# 后台运行
python scripts/file_watcher.py --daemon
```

### 批量处理命令

```bash
# 处理单个文件
python scripts/batch_processor.py --file /path/to/document.pdf

# 处理整个目录
python scripts/batch_processor.py --dir /path/to/documents

# 处理待处理文件
python scripts/batch_processor.py --pending

# 重试失败文件
python scripts/batch_processor.py --retry

# 查看统计信息
python scripts/batch_processor.py --stats
```

## 工作流程

```
文件事件触发
    │
    ├── 创建事件 ──▶ 检查是否已存在 ──▶ 不存在 ──▶ 加入处理队列
    │
    ├── 修改事件 ──▶ 计算文件哈希 ──▶ 与记录不同 ──▶ 删除旧向量 ──▶ 加入处理队列
    │
    └── 删除事件 ──▶ 查询数据库记录 ──▶ 存在记录 ──▶ 删除向量 ──▶ 删除记录
```

## 文件状态

| 状态 | 说明 |
|------|------|
| `pending` | 等待处理 |
| `processing` | 正在处理 |
| `done` | 处理完成 |
| `failed` | 处理失败 |

## 数据库结构

文件状态存储在 SQLite 数据库中：

| 字段 | 类型 | 说明 |
|------|------|------|
| file_path | TEXT | 文件完整路径 |
| file_hash | TEXT | 文件MD5哈希 |
| status | TEXT | 状态 |
| last_modified | REAL | 最后修改时间 |
| processed_at | REAL | 处理时间 |
| chunk_count | INTEGER | 分块数量 |
| document_id | TEXT | 文档ID |
| error_message | TEXT | 错误信息 |

## 日志

日志文件位于 `data/watch_logs/` 目录，按日期命名：
- `watcher_20240115.log`

## 注意事项

1. **首次运行**: 会扫描所有配置目录，处理所有未处理的文件
2. **文件修改**: 只有文件内容真正变化（哈希不同）才会重新处理
3. **文件删除**: 删除文件会自动从向量库中移除对应向量
4. **错误处理**: 失败的文件会记录错误信息，可使用 `--retry` 重试
5. **性能**: 建议根据机器性能调整 `workers` 数量

## 与现有系统集成

文件监控服务与现有的文档上传功能共享同一个向量数据库（ChromaDB），处理后的文档可以在聊天界面中被检索到。

### 区别

| 功能 | Web上传 | 文件监控 |
|------|---------|----------|
| 适用场景 | 少量文件 | 大量文件 |
| 操作方式 | 手动上传 | 自动监控 |
| 进度查看 | Web界面 | 日志/命令行 |
| 文件删除 | 手动删除 | 自动同步 |
