# 配置系统说明

## 概述

项目使用**双层配置系统**：

1. **环境配置** (`.env` + `config.py`) - 环境相关
2. **功能配置** (`config.json` + `config_loader.py`) - 功能参数

## 1. 环境配置 (.env + config.py)

### 用途
- 环境相关的配置
- 敏感信息（API Key、数据库密码）
- 不同环境有不同值的配置

### 文件位置
```
backend/
├── .env              # 实际配置（不提交到 git）
├── .env.example      # 配置模板
└── app/
    └── config.py     # 配置类定义
```

### 配置项

```env
# .env 文件
DASHSCOPE_API_KEY=sk-your-key-here
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v3
MONGO_URL=mongodb://localhost:27017
```

### 使用方式

```python
from app.config import settings

# 读取配置
model = settings.llm_model
api_key = settings.dashscope_api_key
```

### 特点
- ✅ 支持环境变量覆盖
- ✅ 类型验证（Pydantic）
- ✅ 敏感信息保护
- ✅ 不同环境不同配置

## 2. 功能配置 (config.json + config_loader.py)

### 用途
- 功能参数配置
- 不包含敏感信息
- 相对固定的配置

### 文件位置
```
backend/app/
├── core/
│   └── config.json       # 核心配置
├── skills/
│   └── config.json       # Skill 配置
├── prompts/
│   └── config.json       # Prompt 配置
├── tools/
│   └── config.json       # Tool 配置
└── agents/
    └── config.json       # Agent 配置
```

### 配置项

```json
// backend/app/core/config.json
{
  "llm": {
    "temperature": 0.7,
    "max_tokens": 4096,
    "debug": true
  },
  "retrieval": {
    "default_top_k": 5,
    "score_threshold": 0.7
  }
}
```

### 使用方式

```python
from app.core.config_loader import config_loader

# 读取配置
temperature = config_loader.get_setting("llm.temperature", 0.7)
top_k = config_loader.get_setting("retrieval.default_top_k", 5)
```

### 特点
- ✅ 分模块配置
- ✅ 支持嵌套结构
- ✅ 易于版本控制
- ✅ 可以热重载

## 配置优先级

### 模型配置

```
环境变量 > .env 文件 > config.py 默认值
```

**示例**:
```bash
# 1. config.py 默认值
llm_model: str = "qwen-plus"

# 2. .env 文件覆盖
LLM_MODEL=qwen-turbo

# 3. 环境变量覆盖（最高优先级）
$ LLM_MODEL=qwen-max python main.py
```

### 功能参数

```
代码传参 > config.json > 代码默认值
```

**示例**:
```python
# 1. config.json 默认值
{"llm": {"temperature": 0.7}}

# 2. 代码中读取
temperature = config_loader.get_setting("llm.temperature", 0.5)  # 0.7

# 3. 代码传参覆盖（最高优先级）
response = await client.chat(messages, temperature=0.9)  # 0.9
```

## 配置对比表

| 配置项 | 环境配置 (.env) | 功能配置 (config.json) |
|--------|----------------|----------------------|
| **模型名称** | ✅ `LLM_MODEL` | ❌ 已移除 |
| **API Key** | ✅ `DASHSCOPE_API_KEY` | ❌ 不应该放这里 |
| **Temperature** | ❌ 不适合 | ✅ `llm.temperature` |
| **Top K** | ❌ 不适合 | ✅ `retrieval.default_top_k` |
| **Debug 模式** | ✅ `APP_DEBUG` | ✅ `llm.debug` |
| **数据库 URL** | ✅ `MONGO_URL` | ❌ 不应该放这里 |

## 最佳实践

### 1. 模型配置统一使用 .env

```env
# ✅ 正确：在 .env 中配置
LLM_MODEL=qwen-plus
EMBEDDING_MODEL=text-embedding-v3
```

```json
// ❌ 错误：不要在 config.json 中配置模型
{
  "llm": {
    "model": "qwen-plus"  // 已移除
  }
}
```

### 2. 功能参数使用 config.json

```json
// ✅ 正确：功能参数在 config.json
{
  "llm": {
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

```env
# ❌ 错误：不要在 .env 中配置功能参数
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

### 3. 敏感信息只放 .env

```env
# ✅ 正确：敏感信息在 .env
DASHSCOPE_API_KEY=sk-xxx
MONGO_URL=mongodb://user:pass@host
```

```json
// ❌ 错误：不要在 config.json 中放敏感信息
{
  "api_key": "sk-xxx"  // 危险！
}
```

## 配置修改指南

### 修改模型

```bash
# 1. 编辑 .env 文件
vim backend/.env

# 2. 修改 LLM_MODEL
LLM_MODEL=qwen-turbo

# 3. 重启应用
python main.py
```

### 修改功能参数

```bash
# 1. 编辑 config.json
vim backend/app/core/config.json

# 2. 修改参数
{
  "llm": {
    "temperature": 0.5
  }
}

# 3. 重启应用（或热重载）
python main.py
```

## 配置检查

### 检查环境配置

```bash
python backend/scripts/check_config.py
```

### 检查功能配置

```python
from app.core.config_loader import config_loader

# 查看所有配置
settings = config_loader.load("settings")
print(settings)
```

## 常见问题

### Q1: 为什么有两套配置系统？

A: 
- **环境配置**: 处理环境差异（开发/生产）和敏感信息
- **功能配置**: 管理功能参数，便于调整和版本控制

### Q2: 模型配置应该放哪里？

A: **只放在 .env 文件中**，通过 `LLM_MODEL` 配置。

### Q3: config.json 中的 model 字段还有用吗？

A: **已移除**，统一使用 .env 中的配置。

### Q4: 如何在代码中获取模型名称？

A:
```python
from app.config import settings
model = settings.llm_model  # 从 .env 读取
```

### Q5: 两套配置会冲突吗？

A: 不会，它们管理不同类型的配置：
- `.env`: 环境和敏感信息
- `config.json`: 功能参数

## 配置文件清单

### 必需的配置文件

```
backend/
├── .env                          # ✅ 必需（不提交）
├── .env.example                  # ✅ 必需（提交）
└── app/
    ├── config.py                 # ✅ 必需
    ├── core/
    │   └── config.json          # ✅ 必需
    ├── skills/
    │   └── config.json          # ✅ 必需
    ├── prompts/
    │   └── config.json          # ✅ 必需
    ├── tools/
    │   └── config.json          # ✅ 必需
    └── agents/
        └── config.json          # ✅ 必需
```

## 总结

- **模型配置**: 只在 `.env` 中配置 `LLM_MODEL`
- **功能参数**: 在 `config.json` 中配置
- **敏感信息**: 只在 `.env` 中配置
- **不要重复**: 同一配置项不要在两个地方都配置

## 相关文档

- [环境变量配置](./ENV_CONFIGURATION.md)
- [模型配置说明](./MODEL_CONFIGURATION.md)
- [配置修复记录](./CONFIGURATION_FIXES.md)
