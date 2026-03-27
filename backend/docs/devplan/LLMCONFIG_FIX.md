# LLMConfig 修复说明

## 问题

用户遇到错误：
```
LLMConfig.__init__() got an unexpected keyword argument 'temperature'
```

## 原因

在统一模型配置时，我将 `LLMConfig` 从类属性改成了 `__init__` 方法：

```python
# 错误的修改
@dataclass
class LLMConfig:
    def __init__(self):
        from app.config import settings
        self.model: str = settings.llm_model
        self.temperature: float = 0.3
        self.max_tokens: int = 2000
    tool_decision_temperature: float = 0.1  # 这行语法错误
```

但代码中有地方在实例化时传入了参数：

```python
# backend/app/services/qa_agent.py
self._llm_client = get_llm_client(LLMConfig(
    temperature=self._config.answer_temperature,  # 传入了参数
    tool_decision_temperature=self._config.tool_decision_temperature
))
```

## 解决方案

使用 `@dataclass` 的 `__post_init__` 方法来设置默认值：

```python
@dataclass
class LLMConfig:
    """LLM配置"""
    model: str = None
    temperature: float = 0.3
    max_tokens: int = 2000
    tool_decision_temperature: float = 0.1
    
    def __post_init__(self):
        """初始化后处理，设置默认模型"""
        if self.model is None:
            from app.config import settings
            self.model = settings.llm_model
```

## 优势

这种方式的优势：

1. **支持默认值**：不传参数时，从 settings 读取
   ```python
   config = LLMConfig()  # model 从 settings 读取
   ```

2. **支持自定义**：可以传入自定义参数
   ```python
   config = LLMConfig(temperature=0.5)  # 自定义 temperature
   ```

3. **支持完全自定义**：可以指定所有参数
   ```python
   config = LLMConfig(
       model="qwen-turbo",
       temperature=0.5,
       max_tokens=1000
   )
   ```

## 使用示例

### 1. 使用默认配置

```python
from app.services.llm_client import LLMConfig, LLMClient

# 使用默认配置（model 从 settings 读取）
config = LLMConfig()
client = LLMClient(config)
```

### 2. 自定义部分参数

```python
# 只自定义 temperature，model 仍从 settings 读取
config = LLMConfig(temperature=0.5)
client = LLMClient(config)
```

### 3. 完全自定义

```python
# 完全自定义所有参数
config = LLMConfig(
    model="qwen-turbo",
    temperature=0.5,
    max_tokens=1000,
    tool_decision_temperature=0.1
)
client = LLMClient(config)
```

### 4. 在 QAAgent 中使用

```python
# backend/app/services/qa_agent.py
self._llm_client = get_llm_client(LLMConfig(
    temperature=self._config.answer_temperature,
    tool_decision_temperature=self._config.tool_decision_temperature
))
# model 会自动从 settings 读取
```

## 测试更新

测试文件也需要更新：

```python
# backend/tests/test_llm_client.py
def test_default_config(self):
    """测试默认配置"""
    config = LLMConfig()
    
    # 模型应该从 settings 读取
    from app.config import settings
    assert config.model == settings.llm_model  # ✅ 从 settings 读取
    assert config.temperature == 0.3
    assert config.max_tokens == 2000
```

## 相关文件

- `backend/app/services/llm_client.py` - LLMConfig 定义
- `backend/app/services/qa_agent.py` - 使用 LLMConfig
- `backend/tests/test_llm_client.py` - 测试文件

## 总结

修复后的 `LLMConfig`：
- ✅ 支持无参数实例化（使用默认值）
- ✅ 支持部分参数自定义
- ✅ 支持完全自定义
- ✅ model 默认从 settings 读取
- ✅ 保持了 dataclass 的所有优势
