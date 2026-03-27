# 文件扩展名统一管理重构

## 概述

将分散在多个文件中的文件扩展名定义统一到 `app/core/constants.py` 中的 `DocumentConstants` 类，实现集中管理和维护。

## 问题背景

之前文件扩展名定义分散在多个地方：
- `batch_processor.py` - 定义了 `SUPPORTED_EXTENSIONS` 字典
- `documents.py` - 硬编码了 `allowed_types` 列表
- `watch.json` - 配置文件中硬编码扩展名列表
- `document.py` - 使用 `DocumentConstants.SUPPORTED_FORMATS`

这导致：
1. 维护困难 - 添加新格式需要修改多处
2. 不一致风险 - 不同地方可能定义不同
3. 代码重复 - 相同的扩展名列表重复定义

## 解决方案

### 1. 增强 DocumentConstants 类

在 `backend/app/core/constants.py` 中统一定义：

```python
class DocumentConstants:
    """文档处理相关常量"""

    # 支持的文档格式（不带点）
    SUPPORTED_FORMATS: List[str] = [
        "pdf", "docx", "txt", "md",
        "xlsx", "xls", "pptx",
        "png", "jpg", "jpeg", "gif", "bmp", "webp"
    ]

    # 支持的扩展名（带点）
    SUPPORTED_EXTENSIONS: List[str] = [f".{fmt}" for fmt in SUPPORTED_FORMATS]
    
    # 扩展名集合（用于快速查找）
    SUPPORTED_EXTENSIONS_SET: Set[str] = set(SUPPORTED_EXTENSIONS)

    # 扩展名到格式类型的映射
    EXTENSION_TO_TYPE: Dict[str, str] = {
        '.pdf': 'pdf',
        '.doc': 'docx',
        '.docx': 'docx',
        '.txt': 'txt',
        '.md': 'txt',
        '.xlsx': 'xlsx',
        '.xls': 'xlsx',
        '.pptx': 'pptx',
        '.png': 'image',
        '.jpg': 'image',
        '.jpeg': 'image',
        '.gif': 'image',
        '.bmp': 'image',
        '.webp': 'image'
    }

    # 文档类型分类
    DOCUMENT_TYPES: Dict[str, List[str]] = {
        'text': ['pdf', 'docx', 'txt', 'md'],
        'spreadsheet': ['xlsx', 'xls'],
        'presentation': ['pptx'],
        'image': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']
    }

    # HTML accept 属性值
    ACCEPT_TYPES: str = ",".join(SUPPORTED_EXTENSIONS)

    # 文件大小限制
    MAX_FILE_SIZE_MB: int = 50

    # 分块参数
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 50
```

### 2. 更新各模块使用统一常量

#### batch_processor.py
```python
from app.core.constants import DocumentConstants

class BatchProcessor:
    # 使用统一的扩展名映射
    SUPPORTED_EXTENSIONS = DocumentConstants.EXTENSION_TO_TYPE
    
    # 命令行参数默认值
    parser.add_argument("--extensions", "-e", nargs="+", 
                       default=DocumentConstants.SUPPORTED_EXTENSIONS)
```

#### documents.py (API路由)
```python
from app.core.constants import DocumentConstants

async def upload_document(...):
    allowed_types = DocumentConstants.SUPPORTED_EXTENSIONS
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}. 支持的类型: {', '.join(allowed_types)}"
        )
```

#### file_watcher.py
```python
from app.core.constants import DocumentConstants

class Config:
    @property
    def watch_dirs(self) -> List[Dict[str, Any]]:
        """Get watch directories with auto extension resolution"""
        dirs = self.config.get("watch_dirs", [])
        # 处理 extensions: "auto" 的情况
        for dir_config in dirs:
            if dir_config.get("extensions") == "auto":
                dir_config["extensions"] = DocumentConstants.SUPPORTED_EXTENSIONS
        return dirs
```

#### watch.json (配置文件)
```json
{
  "watch_dirs": [
    {
      "path": "...",
      "enabled": true,
      "recursive": true,
      "extensions": "auto"
    }
  ]
}
```

使用 `"extensions": "auto"` 自动使用 `DocumentConstants.SUPPORTED_EXTENSIONS`

## 优势

### 1. 单一数据源
- 所有扩展名定义在一个地方
- 添加新格式只需修改 `constants.py`

### 2. 类型安全
- 提供多种数据结构（列表、集合、字典）
- 满足不同使用场景的需求

### 3. 易于维护
- 集中管理，减少遗漏
- 自动生成派生数据（如 ACCEPT_TYPES）

### 4. 灵活配置
- 配置文件支持 `"auto"` 自动引用
- 也可以手动指定特定扩展名

### 5. 文档分类
- 提供 `DOCUMENT_TYPES` 分类
- 便于按类型处理文档

## 使用示例

### 检查文件是否支持
```python
from app.core.constants import DocumentConstants

# 方式1：使用集合（O(1)查找）
if file_ext in DocumentConstants.SUPPORTED_EXTENSIONS_SET:
    process_file(file_path)

# 方式2：使用列表
if file_ext in DocumentConstants.SUPPORTED_EXTENSIONS:
    process_file(file_path)
```

### 获取文件类型
```python
file_type = DocumentConstants.EXTENSION_TO_TYPE.get(file_ext)
if file_type == 'pdf':
    parse_pdf(file_path)
elif file_type == 'xlsx':
    parse_xlsx(file_path)
```

### 按类型过滤
```python
# 只处理文本文档
text_formats = DocumentConstants.DOCUMENT_TYPES['text']
if file_format in text_formats:
    process_text_document(file_path)
```

### HTML表单
```python
# 在前端使用
<input type="file" accept="{{ DocumentConstants.ACCEPT_TYPES }}" />
```

## 迁移清单

- [x] 增强 `DocumentConstants` 类
- [x] 更新 `batch_processor.py`
- [x] 更新 `documents.py` API路由
- [x] 更新 `file_watcher.py`
- [x] 更新 `watch.json` 配置
- [x] 创建迁移文档

## 未来扩展

添加新文件格式时，只需：

1. 在 `DocumentConstants.SUPPORTED_FORMATS` 中添加格式名
2. 在 `EXTENSION_TO_TYPE` 中添加映射关系
3. 在 `DOCUMENT_TYPES` 中分类（可选）
4. 实现对应的解析方法

所有使用这些常量的模块会自动支持新格式。

## 注意事项

1. `SUPPORTED_FORMATS` 使用不带点的格式名（如 "pdf"）
2. `SUPPORTED_EXTENSIONS` 使用带点的扩展名（如 ".pdf"）
3. 配置文件中使用 `"auto"` 会自动引用最新的扩展名列表
4. 手动指定扩展名列表仍然有效，用于特殊场景
