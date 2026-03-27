# KeywordIndexBuilder 处理器未注册问题修复

## 问题描述

在解析 xlsx 文件时报错：
```
ValueError: Processor not found: KeywordIndexBuilder
```

## 根本原因

`KeywordIndexBuilder` 处理器虽然已经实现并在配置文件中使用，但没有在 `app/skills/processors/__init__.py` 中导入，导致处理器注册装饰器没有被执行。

同时发现 `SmartTextSplitter` 处理器也存在相同问题。

## 问题分析

### 1. 处理器注册机制

处理器使用装饰器模式注册：

```python
@ProcessorRegistry.register("KeywordIndexBuilder")
class KeywordIndexBuilder(BaseProcessor):
    ...
```

这个装饰器在类定义时执行，将处理器实例注册到 `ProcessorRegistry._processors` 字典中。

### 2. 导入触发注册

只有当模块被导入时，类定义才会执行，装饰器才会运行。如果模块没有被导入，处理器就不会被注册。

### 3. 配置文件使用

`skills/config.json` 中的 `document_upload` 技能流水线使用了 `KeywordIndexBuilder`：

```json
{
  "step": "build_keyword_index",
  "processor": "KeywordIndexBuilder",
  "comment": "步骤5: 构建关键词索引",
  "params": {}
}
```

但由于处理器未注册，运行时会抛出 `ValueError`。

## 修复方案

在 `app/skills/processors/__init__.py` 中添加导入：

```python
from .document import DocumentParser, TextSplitter, SmartTextSplitter  # 添加 SmartTextSplitter
from .embedding import EmbeddingProcessor
from .retriever import VectorRetriever
from .store import VectorStore
from .llm import LLMGenerator
from .context import ContextBuilder
from .keyword_index import KeywordIndexBuilder  # 新增

__all__ = [
    "DocumentParser",
    "TextSplitter",
    "SmartTextSplitter",  # 新增
    "EmbeddingProcessor",
    "VectorRetriever",
    "VectorStore",
    "LLMGenerator",
    "ContextBuilder",
    "KeywordIndexBuilder"  # 新增
]
```

## 已注册的处理器列表

修复后，系统中所有已注册的处理器：

1. `DocumentParser` - 文档解析器
2. `TextSplitter` - 文本分割器
3. `SmartTextSplitter` - 智能文本分割器
4. `EmbeddingProcessor` - 向量化处理器
5. `VectorRetriever` - 向量检索器
6. `VectorStore` - 向量存储器
7. `LLMGenerator` - LLM 生成器
8. `ContextBuilder` - 上下文构建器
9. `KeywordIndexBuilder` - 关键词索引构建器

## 验证修复

### 方法 1: 运行测试脚本

```bash
python backend/scripts/test_processor_registry.py
```

这个脚本会：
1. 列出所有已注册的处理器
2. 测试每个处理器是否可以获取
3. 验证配置文件中使用的处理器是否都已注册

### 方法 2: Python 交互式测试

```python
from app.skills.processors import KeywordIndexBuilder
from app.skills.base import ProcessorRegistry

# 检查是否注册
print(ProcessorRegistry.list_all())
# 应该包含 'KeywordIndexBuilder'

# 获取处理器
processor = ProcessorRegistry.get("KeywordIndexBuilder")
print(processor.name)  # 应该输出 'KeywordIndexBuilder'
```

### 方法 3: 实际文档上传测试

上传一个 xlsx 文件，应该能够成功完成整个流水线，包括关键词索引构建。

## 相关文件

### 修改的文件
- `backend/app/skills/processors/__init__.py` - 添加 KeywordIndexBuilder 导入

### 相关文件
- `backend/app/skills/processors/keyword_index.py` - KeywordIndexBuilder 实现
- `backend/app/skills/config.json` - 使用 KeywordIndexBuilder 的配置
- `backend/app/skills/base.py` - ProcessorRegistry 实现
- `backend/app/rag/keyword_index.py` - 关键词索引构建逻辑

### 新增文件
- `backend/scripts/test_processor_registry.py` - 处理器注册测试脚本

## 最佳实践

### 1. 添加新处理器的步骤

当添加新的处理器时，必须：

1. 创建处理器类并使用 `@ProcessorRegistry.register()` 装饰器
2. 在 `processors/__init__.py` 中导入处理器
3. 将处理器添加到 `__all__` 列表中
4. 在配置文件中使用处理器

### 2. 处理器命名规范

- 类名使用 PascalCase（如 `KeywordIndexBuilder`）
- 注册名称与类名保持一致
- 配置文件中使用注册名称

### 3. 测试验证

添加新处理器后，运行测试脚本验证：

```bash
python backend/scripts/test_processor_registry.py
```

## 技术细节

### ProcessorRegistry 工作原理

```python
class ProcessorRegistry:
    _processors: Dict[str, BaseProcessor] = {}
    
    @classmethod
    def register(cls, name: str):
        def decorator(processor_class):
            instance = processor_class()  # 创建实例
            cls._processors[name] = instance  # 注册到字典
            return processor_class
        return decorator
    
    @classmethod
    def get(cls, name: str) -> BaseProcessor:
        processor = cls._processors.get(name)
        if not processor:
            raise ValueError(f"Processor not found: {name}")
        return processor
```

### 装饰器执行时机

```python
# 当模块被导入时，这行代码会执行
@ProcessorRegistry.register("KeywordIndexBuilder")
class KeywordIndexBuilder(BaseProcessor):
    pass

# 等价于：
class KeywordIndexBuilder(BaseProcessor):
    pass
KeywordIndexBuilder = ProcessorRegistry.register("KeywordIndexBuilder")(KeywordIndexBuilder)
```

### 为什么需要在 __init__.py 中导入

Python 的模块导入机制：
- 只有被导入的模块才会执行
- 装饰器在类定义时执行
- 如果模块没有被导入，装饰器不会执行
- 因此必须在 `__init__.py` 中导入所有处理器

## 影响范围

- 修复后，文档上传流水线可以正常构建关键词索引
- xlsx 文件解析不再报错
- 混合检索（向量检索 + 关键词检索）功能正常工作

## 总结

这是一个典型的 Python 模块导入和装饰器执行时机的问题。修复方法很简单，但理解背后的机制很重要，可以避免类似问题再次发生。

记住：**所有使用装饰器注册的处理器都必须在 `__init__.py` 中导入！**
