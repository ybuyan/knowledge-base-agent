# 单一"新对话"功能

## 需求

确保"新对话"（New Chat）只能存在一个，避免创建多个空的新对话。

## 实现方案

### 1. 创建会话时检查

修改 `session_service.py` 中的 `create_session` 方法：

```python
async def create_session(self, user_id: str, title: str = "新对话"):
    # 如果标题是"新对话"，检查是否已存在空的新对话
    if title == "新对话":
        existing_empty_session = await db.sessions.find_one({
            "user_id": user_id,
            "title": "新对话",
            "message_count": 0,
            "is_archived": {"$ne": True}
        })
        
        if existing_empty_session:
            # 返回已存在的空新对话，不创建新的
            return existing_empty_session
    
    # 创建新会话
    ...
```

逻辑：
- 当创建标题为"新对话"的会话时
- 先检查是否已存在空的（message_count=0）"新对话"
- 如果存在，返回已有的会话
- 如果不存在，创建新的会话

### 2. 自动清理多余的空"新对话"

添加 `cleanup_empty_new_chats` 方法：

```python
async def cleanup_empty_new_chats(self, user_id: str) -> int:
    """清理多余的空"新对话"，只保留最新的一个"""
    # 查找所有空的"新对话"
    empty_sessions = await db.sessions.find({
        "user_id": user_id,
        "title": "新对话",
        "message_count": 0,
        "is_archived": {"$ne": True}
    }).sort("created_at", -1).to_list()
    
    if len(empty_sessions) <= 1:
        return 0  # 只有一个或没有，不需要清理
    
    # 保留最新的，删除其他的
    for session in empty_sessions[1:]:
        await db.sessions.delete_one({"_id": session["_id"]})
    
    return len(empty_sessions) - 1
```

### 3. 在获取会话列表时自动清理

修改 `get_sessions` 方法，在返回列表前自动清理：

```python
async def get_sessions(self, user_id: str, ...):
    # 先清理多余的空"新对话"
    await self.cleanup_empty_new_chats(user_id)
    
    # 然后返回会话列表
    ...
```

## 使用方法

### 清理现有的多余"新对话"

```bash
cd backend
python scripts/cleanup_empty_chats.py
```

输出示例：
```
=== 清理多余的空'新对话' ===

✓ MongoDB 已连接

找到 5 个空的'新对话'

空'新对话'列表:
1. ✓ 保留
   ID: 67a1b2c3d4e5f6g7h8i9j0k1
   创建时间: 2024-01-15 10:30:00

2. ✗ 删除
   ID: 67a1b2c3d4e5f6g7h8i9j0k2
   创建时间: 2024-01-15 09:30:00

...

将保留最新的1个，删除其他 4 个

✓ 清理完成，删除了 4 个空'新对话'
```

### 自动清理

修改后，系统会自动：
1. 创建"新对话"时，如果已存在空的，直接返回已有的
2. 获取会话列表时，自动清理多余的空"新对话"

## 行为说明

### 什么时候会创建新的"新对话"？

- 当前没有空的"新对话"时
- 已有的"新对话"有消息（message_count > 0）时

### 什么时候会复用已有的"新对话"？

- 已存在空的"新对话"（message_count = 0）时

### 示例场景

**场景 1：首次使用**
```
用户点击"New Chat" → 创建新的"新对话" → 显示空对话
```

**场景 2：已有空"新对话"**
```
用户点击"New Chat" → 返回已有的空"新对话" → 显示空对话
```

**场景 3：已有"新对话"但有消息**
```
用户点击"New Chat" → 创建新的"新对话" → 显示空对话
（因为已有的"新对话"有消息，不是空的）
```

**场景 4：多个空"新对话"（历史遗留）**
```
用户打开会话列表 → 自动清理，只保留最新的1个
```

## 验证

### 1. 测试创建"新对话"

```bash
# 多次点击"New Chat"按钮
# 应该只有一个空的"新对话"
```

### 2. 查看数据库

```bash
python scripts/list_sessions.py
```

应该只看到一个空的"新对话"。

### 3. 测试发送消息后

```bash
# 1. 在"新对话"中发送消息
# 2. 再次点击"New Chat"
# 3. 应该创建新的"新对话"（因为旧的已有消息）
```

## 相关文件

- `backend/app/services/session_service.py` - 会话服务
- `backend/scripts/cleanup_empty_chats.py` - 清理脚本
- `backend/docs/devplan/SINGLE_NEW_CHAT_FIX.md` - 本文档

## 注意事项

1. **不影响有消息的会话** - 只处理空的"新对话"
2. **保留最新的** - 清理时保留创建时间最新的
3. **自动清理** - 获取会话列表时自动执行
4. **用户无感知** - 用户体验不受影响

## 总结

实现了"新对话"单例模式：
- ✓ 创建时检查并复用已有的空"新对话"
- ✓ 自动清理多余的空"新对话"
- ✓ 提供手动清理脚本
- ✓ 不影响有消息的会话
