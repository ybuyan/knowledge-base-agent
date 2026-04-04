# 提示词配置管理 - 快速参考

## 📋 常用命令

### 配置管理

```bash
# 重置配置（删除+导入）
python scripts/reset_prompts.py

# 增量更新配置
python scripts/init_prompt_config.py

# 检查配置
python scripts/check_prompts.py

# 导出配置
python scripts/export_prompt_config.py

# 测试功能
python scripts/test_prompt_config.py
```

### 应用操作

```bash
# 启动应用
python -m app.main

# 测试配置加载
python -c "from app.prompts.manager import prompt_manager; print('配置数量:', len(prompt_manager.list_all()))"
```

## 🔌 API 接口

### 查询配置

```bash
# 获取所有配置
GET /api/prompt-config/list

# 获取单个配置
GET /api/prompt-config/{prompt_id}

# 按分类获取
GET /api/prompt-config/list?category=qa

# 只获取启用的
GET /api/prompt-config/list?enabled_only=true
```

### 修改配置

```bash
# 创建配置
POST /api/prompt-config/create

# 更新配置
PUT /api/prompt-config/{prompt_id}

# 删除配置
DELETE /api/prompt-config/{prompt_id}
```

### 同步操作

```bash
# 从文件同步到数据库
POST /api/prompt-config/sync-from-file

# 导出到文件
POST /api/prompt-config/export-to-file

# 重新加载配置
POST /api/prompt-config/reload
```

## 📊 当前配置

```
总数: 26 个
分类: 9 个
启用: 26 个

主要分类:
- suggestion: 6 个
- assistant: 4 个
- agent: 3 个
- qa: 3 个
- optimization: 3 个
- mcp: 3 个
- document: 2 个
- validation: 1 个
- memory: 1 个
```

## 🔑 关键配置

| ID | 名称 | 分类 | 用途 |
|----|------|------|------|
| qa_rag | RAG问答 | qa | 基础问答 |
| strict_qa | 严格问答 | qa | 防幻觉问答 |
| intent_detection | 意图识别 | agent | 识别用户意图 |
| leave_guide_v2 | 请假指引 | assistant | 多轮对话指引 |
| query_optimize | 查询优化 | optimization | 优化搜索查询 |

## 🛠️ 代码示例

### 获取配置

```python
from app.prompts.manager import prompt_manager

# 获取配置
config = prompt_manager.get("qa_rag")

# 渲染提示词
rendered = prompt_manager.render(
    "qa_rag",
    variables={
        "context": "知识库内容",
        "question": "用户问题"
    }
)
```

### 更新配置

```python
from app.services.prompt_config_service import prompt_config_service

# 更新配置
await prompt_config_service.update(
    "qa_rag",
    {"description": "新描述"},
    updated_by="admin"
)
```

## 🚨 故障排查

### 问题：配置未加载

```bash
# 1. 检查数据库连接
python -c "from app.core.mongodb import mongodb; print('已连接:', mongodb.is_connected)"

# 2. 检查配置数量
python scripts/check_prompts.py

# 3. 重新加载
curl -X POST http://localhost:8001/api/prompt-config/reload \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 问题：配置损坏

```bash
# 从文件恢复
python scripts/reset_prompts.py
```

### 问题：数据库未连接

```bash
# 应用会自动使用文件模式
# 无需特殊处理
```

## 📝 日志关键字

```bash
# 查看配置相关日志
tail -f logs/app.log | grep "提示词"

# 关键日志:
# - "从数据库加载 X 个提示词配置"
# - "从文件加载提示词配置"
# - "提示词同步任务已启动"
# - "提示词配置同步完成"
```

## 🔄 工作流程

### 开发流程

```
1. 修改 config.json
2. 运行 reset_prompts.py
3. 重启应用
4. 测试功能
```

### 生产流程

```
1. 通过 API 修改配置
2. 自动触发同步
3. 等待生效（最多 5 分钟）
4. 或手动触发 reload
```

## 📚 文档索引

| 文档 | 用途 |
|------|------|
| README_PROMPT_CONFIG.md | 完整文档 |
| QUICKSTART_PROMPT_CONFIG.md | 快速开始 |
| PROMPT_CONFIG_STARTUP.md | 启动说明 |
| PROMPT_CONFIG_RESET_GUIDE.md | 重置指南 |
| PROMPT_CONFIG_QUICK_FIX.md | 问题修复 |
| PROMPT_CONFIG_COMPLETE.md | 完成总结 |
| PROMPT_CONFIG_CHEATSHEET.md | 快速参考（本文档） |

## ⚡ 快速操作

### 重置配置

```bash
python scripts/reset_prompts.py
```

### 检查状态

```bash
python scripts/check_prompts.py
```

### 启动应用

```bash
python -m app.main
```

### 测试 API

```bash
curl http://localhost:8001/api/prompt-config/list \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 💡 提示

- ✅ 数据库未连接时会自动使用文件模式
- ✅ 配置修改后最多 5 分钟生效
- ✅ 可以手动触发 reload 立即生效
- ✅ 所有修改操作需要管理员权限
- ✅ 定期备份配置到文件

## 🎯 最佳实践

1. **开发环境** - 使用文件模式
2. **测试环境** - 使用数据库模式，定期重置
3. **生产环境** - 使用数据库模式，谨慎修改
4. **备份策略** - 每天导出配置到文件
5. **版本控制** - 将配置文件提交到 Git

---

**快速帮助**: 查看 `README_PROMPT_CONFIG.md` 获取详细文档
