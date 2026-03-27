# XLSX 解析失败问题修复

## 问题描述

文件监听服务器无法处理 `.xlsx` 文件，导致 Excel 文件上传后无法被解析和索引。

## 根本原因

1. **batch_processor.py 缺少 xlsx 支持**
   - `SUPPORTED_EXTENSIONS` 字典中没有包含 `.xlsx` 和 `.xls` 扩展名
   - 缺少 `_parse_xlsx()` 方法来解析 Excel 文件
   - `_parse_document()` 方法中没有处理 xlsx 的分支

2. **watch.json 配置缺失**
   - 监听目录的 `extensions` 列表中没有包含 `.xlsx` 和 `.xls`

3. **扩展名定义分散**
   - 文件扩展名定义分散在多个文件中，维护困难

## 修复内容

### 1. 统一扩展名管理（重构）

创建统一的常量管理系统 `app/core/constants.py`：

```python
class DocumentConstants:
    """文档处理相关常量"""

    # 支持的文档格式（不带点）
    SUPPORTED_FORMATS: List[str] = [
        "pdf", "docx", "txt", "md",
        "xlsx", "xls", "pptx",  # 包含 Excel 支持
        "png", "jpg", "jpeg", "gif", "bmp", "webp"
    ]

    # 扩展名到格式类型的映射
    EXTENSION_TO_TYPE: Dict[str, str] = {
        '.pdf': 'pdf',
        '.doc': 'docx',
        '.docx': 'docx',
        '.txt': 'txt',
        '.md': 'txt',
        '.xlsx': 'xlsx',  # 新增
        '.xls': 'xlsx',   # 新增
        '.pptx': 'pptx',
        # ... 其他格式
    }
```

### 2. 更新 batch_processor.py

#### 使用统一常量
```python
from app.core.constants import DocumentConstants

class BatchProcessor:
    # 使用统一的扩展名映射
    SUPPORTED_EXTENSIONS = DocumentConstants.EXTENSION_TO_TYPE
```

#### 添加 _parse_xlsx 方法
```python
def _parse_xlsx(self, file_path: str) -> str:
    """Parse Excel file"""
    from openpyxl import load_workbook
    
    filename = os.path.basename(file_path)
    text_parts = []
    
    wb = load_workbook(file_path, data_only=True)
    
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        text_parts.append(f"[{filename} - 工作表: {sheet_name}]")
        
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            continue
        
        # 第一行作为表头
        headers = [str(cell) if cell is not None else f"列{i+1}" 
                   for i, cell in enumerate(rows[0])]
        text_parts.append(f"表头: {' | '.join(headers)}")
        text_parts.append("")
        
        # 处理数据行 - 每行作为一个完整的记录块
        for row_idx, row in enumerate(rows[1:], 2):
            if not any(cell is not None for cell in row):
                continue
            
            # 构建键值对格式的行记录
            row_data = []
            for i, (header, cell) in enumerate(zip(headers, row)):
                if cell is not None:
                    row_data.append(f"{header}: {cell}")
            
            if row_data:
                record_text = f"记录 {row_idx-1}: " + " | ".join(row_data)
                text_parts.append(record_text)
        
        text_parts.append("")
    
    return "\n".join(text_parts)
```

#### 更新 _parse_document 方法
```python
def _parse_document(self, file_path: str) -> str:
    """Parse document and extract text"""
    file_type = self._get_file_type(file_path)
    
    if file_type == 'pdf':
        return self._parse_pdf(file_path)
    elif file_type == 'docx':
        return self._parse_docx(file_path)
    elif file_type == 'txt':
        return self._parse_txt(file_path)
    elif file_type == 'xlsx':  # 新增
        return self._parse_xlsx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
```

#### 更新默认扩展名列表
```python
# 使用统一常量
parser.add_argument("--extensions", "-e", nargs="+", 
                   default=DocumentConstants.SUPPORTED_EXTENSIONS)
```

### 3. 更新 watch.json 配置

使用 `"auto"` 自动引用统一的扩展名列表：

```json
{
  "watch_dirs": [
    {
      "path": "c:/D/code/learning/Agent/AI-assistent/backend/docs",
      "enabled": true,
      "recursive": true,
      "extensions": "auto"
    }
  ]
}
```

### 4. 更新 file_watcher.py

支持配置文件中的 `"auto"` 选项：

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

## 设计特点

xlsx 解析采用与 `app/skills/processors/document.py` 中相同的设计：

1. **保持行数据完整性** - 每行数据作为一个完整的记录块
2. **键值对格式** - 使用 "表头: 值" 格式增强语义关联
3. **多工作表支持** - 处理 Excel 文件中的所有工作表
4. **空值处理** - 跳过空行和空单元格

## 测试

使用提供的测试脚本验证 xlsx 解析：

```bash
python backend/scripts/test_xlsx_parsing.py <path_to_xlsx_file>
```

## 依赖

确保已安装 openpyxl：

```bash
pip install openpyxl
```

## 影响范围

- 文件监听服务现在可以自动处理 `.xlsx` 和 `.xls` 文件
- 批处理器支持手动处理 Excel 文件
- 与现有的文档处理流程完全兼容
- 所有扩展名定义统一管理，便于维护

## 相关文档

- [文件扩展名统一管理重构](./FILE_EXTENSIONS_REFACTOR.md) - 详细说明扩展名统一管理的设计和实现
