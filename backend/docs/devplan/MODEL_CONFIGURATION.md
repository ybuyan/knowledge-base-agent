# 大模型配置统一管理

## 问题说明

之前代码中存在模型配置不统一的问题：
- 有的地方硬编码 `"qwen-plus"`
- 有的地方硬编码 `"gpt-4"`（错误）
- 有的地方使用 `settings.llm_model`（正确）

## 统一配置方案

### 1. 配置文件（.env）

```env
# LLM 配置
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_MODEL=qwen-plus
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3

# 通用 LLM 配置（与 DASHSCOPE 共用）
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

### 2. 配置类（backend/app/config.py）

```python
class Settings(BaseSettings):
    # DashScope 配置
    dashscope_api_key: Optional[str] = Field(default=None)
    dashscope_model: str = "qwen-plus"
    dashscope_embedding_model: str = "text-embedding-v3"
    
    # 通用 LLM 配置
    llm_api_key: Optional[str] = Field(default=None)
    llm_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"
    
    @property
    def embedding_api_key(self) -> Optional[str]:
        return self.dashscope_api_key or self.llm_api_key
    
    @property
    def embedding_model(self) -> str:
        return self.dashscope_embedding_model
```

### 3. 正确使用方式

#### ✅ 正确：使用 settings

```python
from app.config import settings

# 在 LLM 调用中
response = await client.chat.completions.create(
    model=settings.llm_model,  # ✅ 使用配置
    messages=messages
)

# 在 Embedding 调用中
response = await client.embeddings.create(
    model=settings.embedding_model,  # ✅ 使用配置
    input=text
)
```

#### ❌ 错误：硬编码

```python
# ❌ 不要这样做
response = await client.chat.completions.create(
    model="qwen-plus",  # ❌ 硬编码
    messages=messages
)

# ❌ 不要这样做
response = await client.chat.completions.create(
    model="gpt-4",  # ❌ 硬编码且模型错误
    messages=messages
)
```

## 已修复的文件

### 1. backend/app/services/llm_client.py

```python
# 修复前
class LLMConfig:
    model: str = "qwen-plus"  # ❌ 硬编码

# 修复后
class LLMConfig:
    def __init__(self):
        from app.config import settings
        self.model: str = settings.llm_model  # ✅ 使用配置
```

### 2. backend/app/api/routes/chat.py

```python
# 修复前（多处）
model="qwen-plus"  # ❌ 硬编码

# 修复后
from app.config import settings
model=settings.llm_model  # ✅ 使用配置
```

### 3. backend/app/skills/processors/llm.py

```python
# 修复前
return {
    "answer": answer,
    "model": "qwen-plus"  # ❌ 硬编码
}

# 修复后
from app.config import settings
return {
    "answer": answer,
    "model": settings.llm_model  # ✅ 使用配置
}
```

### 4. backend/app/core/memory/short_term.py

```python
# 修复前
def _count_tokens(text: str, model: str = "gpt-4"):  # ❌ 硬编码且错误
    ...

def __init__(self, max_tokens: int = 4000, model: str = "gpt-4"):  # ❌ 硬编码且错误
    ...

# 修复后
def _count_tokens(text: str, model: str = None):
    if model is None:
        from app.config import settings
        model = settings.llm_model  # ✅ 使用配置
    ...

def __init__(self, max_tokens: int = 4000, model: str = None):
    if model is None:
        from app.config import settings
        model = settings.llm_model  # ✅ 使用配置
    ...
```

## 切换模型

如果需要切换到其他模型（如 GPT-4、Claude 等），只需修改 `.env` 文件：

### 切换到 GPT-4

```env
LLM_API_KEY=sk-your-openai-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

### 切换到 Claude

```env
LLM_API_KEY=sk-your-anthropic-api-key
LLM_BASE_URL=https://api.anthropic.com/v1
LLM_MODEL=claude-3-opus-20240229
```

### 切换到其他通义千问模型

```env
DASHSCOPE_API_KEY=your_api_key
LLM_MODEL=qwen-turbo  # 或 qwen-max, qwen-plus
```

## 最佳实践

### 1. 永远不要硬编码模型名称

```python
# ❌ 不要这样
model="qwen-plus"

# ✅ 应该这样
from app.config import settings
model=settings.llm_model
```

### 2. 在类初始化时获取配置

```python
class MyService:
    def __init__(self):
        from app.config import settings
        self.model = settings.llm_model
        self.embedding_model = settings.embedding_model
```

### 3. 提供默认值但允许覆盖

```python
def process(self, model: str = None):
    if model is None:
        from app.config import settings
        model = settings.llm_model
    # 使用 model
```

### 4. 在测试中使用配置

```python
# tests/test_llm.py
def test_llm():
    from app.config import settings
    assert settings.llm_model in ["qwen-plus", "qwen-turbo", "qwen-max"]
```

## 配置优先级

```
环境变量 > .env 文件 > 默认值
```

例如：
```bash
# 临时覆盖模型
LLM_MODEL=qwen-turbo python main.py
```

## 检查清单

在添加新的 LLM 调用代码时，请检查：

- [ ] 是否使用了 `settings.llm_model` 而不是硬编码？
- [ ] 是否使用了 `settings.embedding_model` 而不是硬编码？
- [ ] 是否在类初始化时获取了配置？
- [ ] 是否提供了合理的默认值？
- [ ] 是否在文档中说明了配置项？

## 相关文件

- `backend/app/config.py` - 配置类定义
- `backend/.env` - 环境变量配置
- `backend/app/core/llm.py` - LLM 客户端
- `backend/app/core/embeddings.py` - Embedding 客户端

## 常见问题

### Q: 为什么有 dashscope_model 和 llm_model 两个配置？

A: 为了兼容性。`dashscope_*` 是专门给阿里云通义千问用的，`llm_*` 是通用配置。实际使用时优先使用 `llm_model`。

### Q: 如何在不同环境使用不同模型？

A: 使用不同的 `.env` 文件：
```bash
# 开发环境
cp .env.development .env

# 生产环境
cp .env.production .env
```

### Q: 如何临时测试其他模型？

A: 使用环境变量覆盖：
```bash
LLM_MODEL=qwen-turbo python -m pytest tests/
```

## 总结

统一配置管理的好处：
1. ✅ 易于切换模型
2. ✅ 避免硬编码
3. ✅ 配置集中管理
4. ✅ 便于测试和部署
5. ✅ 减少错误（如使用错误的模型名）
