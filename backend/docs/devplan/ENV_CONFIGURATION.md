# 环境变量配置说明

## 问题：修改 .env 文件中的模型配置不生效

### 原因

代码中实际使用的是 `LLM_MODEL`，而不是 `DASHSCOPE_MODEL`。

```python
# config.py 中的定义
class Settings(BaseSettings):
    llm_model: str = "qwen-plus"  # ← 实际使用这个
```

```python
# 代码中的使用
from app.config import settings
model = settings.llm_model  # ← 读取 llm_model
```

### 环境变量映射规则

`pydantic_settings` 会自动将环境变量名转换为小写：

| 环境变量 | 配置字段 | 说明 |
|---------|---------|------|
| `LLM_MODEL` | `llm_model` | ✅ 实际使用 |
| `DASHSCOPE_MODEL` | `dashscope_model` | ❌ 已废弃 |
| `EMBEDDING_MODEL` | `embedding_model` | ✅ 实际使用 |
| `DASHSCOPE_EMBEDDING_MODEL` | `dashscope_embedding_model` | ❌ 已废弃 |

## 正确的配置方式

### .env 文件配置

```env
# API Key
DASHSCOPE_API_KEY=sk-your-api-key-here

# LLM 模型配置（实际使用）
LLM_MODEL=qwen-math-turbo
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Embedding 模型配置
EMBEDDING_MODEL=text-embedding-v3
```

### 支持的模型

#### 通义千问系列
```env
LLM_MODEL=qwen-turbo      # 快速版本
LLM_MODEL=qwen-plus       # 标准版本（默认）
LLM_MODEL=qwen-max        # 高级版本
LLM_MODEL=qwen-math-turbo # 数学专用版本
```

#### 切换到 OpenAI
```env
LLM_API_KEY=sk-your-openai-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

#### 切换到其他兼容 OpenAI API 的服务
```env
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://your-api-endpoint/v1
LLM_MODEL=your-model-name
```

## 配置优先级

```
环境变量 > .env 文件 > 代码中的默认值
```

### 示例

```python
# config.py 中的默认值
llm_model: str = "qwen-plus"  # 默认值

# .env 文件中的配置
LLM_MODEL=qwen-turbo  # 覆盖默认值

# 环境变量（最高优先级）
$ LLM_MODEL=qwen-max python main.py  # 临时覆盖
```

## 验证配置

### 方法1：Python 脚本

```python
from app.config import settings

print(f"LLM Model: {settings.llm_model}")
print(f"LLM Base URL: {settings.llm_base_url}")
print(f"Embedding Model: {settings.embedding_model}")
print(f"API Key: {settings.api_key[:10]}...")
```

### 方法2：命令行

```bash
cd backend
python -c "from app.config import settings; print(f'Model: {settings.llm_model}')"
```

### 方法3：启动应用查看日志

```bash
python main.py
# 查看启动日志中的模型配置
```

## 配置文件结构

```
backend/
├── .env                 # 实际配置（不提交到 git）
├── .env.example         # 配置模板（提交到 git）
└── app/
    └── config.py        # 配置类定义
```

## 完整的 .env 示例

```env
# ===========================================
# AI Assistant Configuration
# ===========================================

# Application
APP_ENV=development
APP_DEBUG=true

# Security
SECRET_KEY=dev-secret-key-for-development-only-32ch

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# API Key
DASHSCOPE_API_KEY=sk-your-api-key-here

# LLM 模型配置
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# Embedding 模型配置
EMBEDDING_MODEL=text-embedding-v3

# MongoDB
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=agent

# ChromaDB
CHROMA_PERSIST_DIR=./data/chroma

# Memory
MEMORY_MAX_TOKENS=4000
MEMORY_MAX_SESSIONS=1000
```

## 常见问题

### Q1: 修改 .env 后不生效？

A: 需要重启应用。配置在应用启动时加载，修改后需要重启。

```bash
# 停止应用
Ctrl+C

# 重新启动
python main.py
```

### Q2: 如何临时测试其他模型？

A: 使用环境变量覆盖：

```bash
LLM_MODEL=qwen-turbo python main.py
```

### Q3: 如何知道当前使用的是哪个模型？

A: 查看应用启动日志，或者：

```python
from app.config import settings
print(settings.llm_model)
```

### Q4: DASHSCOPE_MODEL 和 LLM_MODEL 有什么区别？

A: 
- `DASHSCOPE_MODEL` 是旧的配置字段，已废弃
- `LLM_MODEL` 是新的统一配置字段，实际使用
- 建议只使用 `LLM_MODEL`

### Q5: 为什么有两个 API Key 配置？

A:
- `DASHSCOPE_API_KEY` - 阿里云通义千问的 API Key
- `LLM_API_KEY` - 通用 LLM API Key（如 OpenAI）
- 代码会优先使用 `DASHSCOPE_API_KEY`，如果没有则使用 `LLM_API_KEY`

## 配置最佳实践

### 1. 开发环境

```env
APP_ENV=development
APP_DEBUG=true
LLM_MODEL=qwen-turbo  # 使用快速版本节省成本
```

### 2. 生产环境

```env
APP_ENV=production
APP_DEBUG=false
SECRET_KEY=<生成的安全密钥>
LLM_MODEL=qwen-plus  # 使用标准版本
```

### 3. 测试环境

```env
APP_ENV=test
LLM_MODEL=qwen-turbo
MEMORY_MAX_SESSIONS=100  # 减少资源占用
```

## 配置变更历史

### v2.0 (当前版本)
- ✅ 统一使用 `LLM_MODEL`
- ✅ 移除 `DASHSCOPE_MODEL`（已废弃）
- ✅ 简化配置结构

### v1.0 (旧版本)
- ❌ 使用 `DASHSCOPE_MODEL`
- ❌ 配置分散

## 相关文档

- [模型配置说明](./MODEL_CONFIGURATION.md)
- [配置修复记录](./CONFIGURATION_FIXES.md)
- [LLMConfig 修复说明](./LLMCONFIG_FIX.md)
