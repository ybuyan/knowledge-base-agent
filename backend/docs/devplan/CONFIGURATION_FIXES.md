# 配置统一修复总结

## 问题发现

用户发现代码中大模型配置不统一，存在以下问题：

1. **硬编码模型名称**：多处直接写 `"qwen-plus"`
2. **错误的模型名称**：有的地方写 `"gpt-4"`（但实际用的是通义千问）
3. **配置分散**：有的用 `settings.llm_model`，有的硬编码
4. **难以切换模型**：修改模型需要改多个文件

## 修复内容

### 修复的文件列表

| 文件 | 问题 | 修复方式 |
|------|------|---------|
| `backend/app/services/llm_client.py` | 硬编码 `"qwen-plus"` | 改为 `settings.llm_model` |
| `backend/app/api/routes/chat.py` | 多处硬编码 `"qwen-plus"` | 改为 `settings.llm_model` |
| `backend/app/skills/processors/llm.py` | 硬编码 `"qwen-plus"` | 改为 `settings.llm_model` |
| `backend/app/core/memory/short_term.py` | 硬编码 `"gpt-4"` ❌ | 改为 `settings.llm_model` |

### 具体修复

#### 1. backend/app/services/llm_client.py

```python
# 修复前
class LLMConfig:
    """LLM配置"""
    model: str = "qwen-plus"  # ❌ 硬编码
    temperature: float = 0.3
    max_tokens: int = 2000

# 修复后
class LLMConfig:
    """LLM配置"""
    def __init__(self):
        from app.config import settings
        self.model: str = settings.llm_model  # ✅ 使用配置
        self.temperature: float = 0.3
        self.max_tokens: int = 2000
```

#### 2. backend/app/api/routes/chat.py

```python
# 修复前（第146行）
stream = await client.chat.completions.create(
    model="qwen-plus",  # ❌ 硬编码
    messages=messages,
    temperature=0.7,

# 修复后
from app.config import settings

stream = await client.chat.completions.create(
    model=settings.llm_model,  # ✅ 使用配置
    messages=messages,
    temperature=0.7,
```

```python
# 修复前（第570行）
response = await client.chat.completions.create(
    model="qwen-plus",  # ❌ 硬编码
    messages=[
        {"role": "system", "content": system_prompt},

# 修复后
from app.config import settings

response = await client.chat.completions.create(
    model=settings.llm_model,  # ✅ 使用配置
    messages=[
        {"role": "system", "content": system_prompt},
```

#### 3. backend/app/skills/processors/llm.py

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

#### 4. backend/app/core/memory/short_term.py

```python
# 修复前
@staticmethod
def _count_tokens(text: str, model: str = "gpt-4") -> int:  # ❌ 硬编码且错误
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

# 修复后
@staticmethod
def _count_tokens(text: str, model: str = None) -> int:
    """计算文本的 token 数量"""
    if model is None:
        from app.config import settings
        model = settings.llm_model  # ✅ 使用配置
    
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))
```

```python
# 修复前
def __init__(
    self,
    max_tokens: int = 4000,
    model: str = "gpt-4",  # ❌ 硬编码且错误
    strategy: Optional[MemoryStrategy] = None
):
    self.max_tokens = max_tokens
    self.model = model
    ...

# 修复后
def __init__(
    self,
    max_tokens: int = 4000,
    model: str = None,
    strategy: Optional[MemoryStrategy] = None
):
    if model is None:
        from app.config import settings
        model = settings.llm_model  # ✅ 使用配置
    
    self.max_tokens = max_tokens
    self.model = model
    ...
```

```python
# 修复前
response = await self.llm_client.chat.completions.create(
    model="gpt-4",  # ❌ 硬编码且错误
    messages=[{
        "role": "user", 
        "content": prompt
    }],

# 修复后
from app.config import settings

response = await self.llm_client.chat.completions.create(
    model=settings.llm_model,  # ✅ 使用配置
    messages=[{
        "role": "user", 
        "content": prompt
    }],
```

## 配置说明

### 配置文件位置

```
backend/.env
```

### 配置项

```env
# LLM 主模型配置
LLM_MODEL=qwen-plus

# Embedding 模型配置
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3

# API Key
DASHSCOPE_API_KEY=your_api_key_here
```

### 支持的模型

#### 通义千问系列
- `qwen-turbo` - 快速版本
- `qwen-plus` - 标准版本（默认）
- `qwen-max` - 高级版本

#### 其他模型（需修改 base_url）
- `gpt-4` - OpenAI GPT-4
- `gpt-3.5-turbo` - OpenAI GPT-3.5
- `claude-3-opus-20240229` - Anthropic Claude

## 切换模型

### 方法1：修改 .env 文件

```env
# 切换到 qwen-turbo
LLM_MODEL=qwen-turbo

# 切换到 qwen-max
LLM_MODEL=qwen-max
```

### 方法2：环境变量覆盖

```bash
# 临时使用 qwen-turbo
LLM_MODEL=qwen-turbo python main.py

# 测试时使用 qwen-turbo
LLM_MODEL=qwen-turbo pytest tests/
```

### 方法3：代码中动态指定（不推荐）

```python
# 仅在特殊情况下使用
from app.config import settings
settings.llm_model = "qwen-turbo"
```

## 验证修复

### 1. 搜索硬编码

```bash
# 搜索是否还有硬编码的模型名称
grep -r "qwen-plus" backend/app/ --include="*.py"
grep -r "gpt-4" backend/app/ --include="*.py"
grep -r "text-embedding" backend/app/ --include="*.py"
```

应该只在以下位置出现：
- `backend/app/config.py` - 默认值定义
- `backend/tests/` - 测试文件
- 注释和文档

### 2. 运行测试

```bash
# 测试配置加载
python -c "from app.config import settings; print(settings.llm_model)"

# 测试 LLM 连接
python -m pytest tests/test_llm.py -v
```

### 3. 检查日志

启动应用后，检查日志中使用的模型名称：

```bash
python main.py
# 查看日志输出，确认使用的是配置的模型
```

## 影响范围

### 受影响的功能

1. ✅ 所有 LLM 调用（问答、摘要、分析等）
2. ✅ Token 计数
3. ✅ 记忆系统
4. ✅ Skill 处理器

### 不受影响的功能

1. ✅ Embedding 生成（已有独立配置）
2. ✅ 向量检索
3. ✅ 数据库操作
4. ✅ 文档解析

## 后续建议

### 1. 添加配置验证

在 `backend/app/config.py` 中添加：

```python
@field_validator('llm_model')
@classmethod
def validate_llm_model(cls, v: str) -> str:
    supported_models = [
        'qwen-turbo', 'qwen-plus', 'qwen-max',
        'gpt-4', 'gpt-3.5-turbo',
        'claude-3-opus-20240229'
    ]
    if v not in supported_models:
        logger.warning(f"模型 {v} 可能不受支持")
    return v
```

### 2. 添加模型切换 API

```python
# backend/app/api/routes/admin.py
@router.post("/admin/switch-model")
async def switch_model(model: str):
    """动态切换模型"""
    from app.config import settings
    settings.llm_model = model
    return {"success": True, "model": model}
```

### 3. 添加配置文档

创建 `backend/docs/CONFIGURATION.md` 说明所有配置项。

### 4. 添加配置测试

```python
# tests/test_config.py
def test_model_configuration():
    from app.config import settings
    assert settings.llm_model is not None
    assert settings.embedding_model is not None
```

## 总结

### 修复前的问题

- ❌ 硬编码模型名称
- ❌ 使用错误的模型名称（gpt-4）
- ❌ 配置分散，难以管理
- ❌ 切换模型需要改多个文件

### 修复后的优势

- ✅ 统一使用 `settings.llm_model`
- ✅ 配置集中在 `.env` 文件
- ✅ 切换模型只需修改一处
- ✅ 支持环境变量覆盖
- ✅ 代码更易维护

### 文档

- `backend/docs/MODEL_CONFIGURATION.md` - 详细的配置说明
- `backend/docs/CONFIGURATION_FIXES.md` - 本文档

## 检查清单

在提交代码前，请确认：

- [x] 所有硬编码的模型名称已替换为 `settings.llm_model`
- [x] 错误的模型名称（gpt-4）已修复
- [x] 添加了配置文档
- [x] 测试通过
- [ ] 代码审查通过
- [ ] 更新了 CHANGELOG

## 相关 Issue

- 用户反馈：代码中关于大模型的配置没有统一配置
- 修复日期：2024-XX-XX
- 修复人：AI Assistant
