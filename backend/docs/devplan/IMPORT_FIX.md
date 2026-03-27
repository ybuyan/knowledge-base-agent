# 导入错误修复

## 问题

运行清除脚本时出现导入错误：
```
Cannot import name 'DocumentDB' from 'app.models.database'
```

## 原因

`DocumentDB` 类实际位于 `app.models.document` 模块，而不是 `app.models.database` 模块。

## 修复

### 修改的文件

1. `backend/scripts/clear_all_data.py`
2. `backend/scripts/quick_check_vectors.py`
3. `backend/scripts/cleanup_orphaned_vectors.py`
4. `backend/tests/test_document_deletion.py`

### 修改内容

**错误的导入：**
```python
from app.models.database import DocumentDB
```

**正确的导入：**
```python
from app.models.document import DocumentDB
```

## 验证

运行测试确认修复成功：

```bash
cd backend
python scripts/clear_all_data.py --dry-run
```

预期输出：
```
============================================================
DRY RUN 模式 - 仅显示将要删除的内容
============================================================

数据库文档记录: X 条
文档向量数据: X 条
...
```

## 模块说明

### app.models.database

包含 SQLModel 数据库模型定义：
- `User` - 用户模型
- `Document` - 文档模型
- `ChatSession` - 会话模型
- `ChatMessage` - 消息模型
- `AuditLog` - 审计日志模型
- 等等

### app.models.document

包含文档操作类：
- `DocumentDB` - 文档数据库操作类
- `DocumentStatusModel` - 文档状态模型

## 总结

所有导入错误已修复，脚本现在可以正常运行。
