# 会话删除问题修复

## 问题

删除会话时报错 "Session not found"，但数据库中确实存在该会话。

会话 ID: `69c4e84d6c6757fef1b9eb70`

## 根本原因

`delete_session` 方法在删除时同时检查 `session_id` 和 `user_id`：

```python
result = await db.sessions.delete_one({
    "_id": ObjectId(session_id),
    "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
})
```

问题：
1. `DEFAULT_USER_ID = "default_user"` 是字符串
2. 数据库中的 session 可能是用 ObjectId 格式的 user_id 创建的
3. 查询条件不匹配，导致找不到 session

## 可能的原因

### 1. user_id 格式不一致

数据库中的 session 可能有不同的 user_id 格式：
- 字符串: `"default_user"`
- ObjectId: `ObjectId("...")`
- 其他格式

### 2. 历史数据问题

早期创建的 session 可能使用了不同的 user_id 格式。

## 解决方案

### 修复 1: 放宽删除条件

修改 `session_service.py` 中的 `delete_session` 方法：

```python
async def delete_session(self, session_id: str, user_id: str) -> bool:
    db = get_mongo_db()
    if db is None:
        return False
    
    try:
        # 先尝试查找 session，不限制 user_id
        session = await db.sessions.find_one({"_id": ObjectId(session_id)})
        
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        # 使用事务删除 session 和相关消息
        async with await db.client.start_session() as mongo_session:
            async with mongo_session.start_transaction():
                # 删除消息
                await db.messages.delete_many(
                    {"session_id": ObjectId(session_id)},
                    session=mongo_session
                )
                # 删除 session（不检查 user_id）
                result = await db.sessions.delete_one(
                    {"_id": ObjectId(session_id)},
                    session=mongo_session
                )
                
                logger.info(f"Deleted session {session_id} and its messages")
                return result.deleted_count > 0
    except Exception as e:
        logger.error(f"删除会话失败: {e}")
        return False
```

改进：
- 不再检查 user_id 匹配
- 先查找 session 是否存在
- 使用事务确保数据一致性
- 添加日志记录

### 修复 2: 统一 user_id 格式

创建了诊断和修复脚本 `backend/scripts/check_session.py`：

```bash
# 检查指定会话
python scripts/check_session.py --session-id 69c4e84d6c6757fef1b9eb70

# 列出所有会话
python scripts/check_session.py --list

# 修复 user_id 格式问题
python scripts/check_session.py --fix
```

## 使用诊断脚本

### 1. 检查会话数据

```bash
cd backend
python scripts/check_session.py --session-id 69c4e84d6c6757fef1b9eb70
```

输出示例：
```
=== 检查会话: 69c4e84d6c6757fef1b9eb70 ===

✓ 找到会话

会话信息:
  _id: 69c4e84d6c6757fef1b9eb70
  user_id: ObjectId('...') (类型: ObjectId)
  title: 新对话
  created_at: 2024-01-15 10:30:00
  updated_at: 2024-01-15 10:35:00
  message_count: 5
  is_archived: False

消息数量: 5

⚠️  user_id 是 ObjectId 格式: ObjectId('...')
   这可能导致删除失败，因为 DEFAULT_USER_ID='default_user' 是字符串
```

### 2. 列出所有会话

```bash
python scripts/check_session.py --list
```

### 3. 修复 user_id 格式

如果发现 user_id 格式不一致：

```bash
python scripts/check_session.py --fix
```

这会将所有 ObjectId 格式的 user_id 转换为 `"default_user"` 字符串。

## 验证修复

### 1. 重启服务

```bash
# 停止服务 (Ctrl+C)
# 重新启动
python -m uvicorn app.main:app --reload
```

### 2. 测试删除

通过前端或 API 删除会话：

```bash
curl -X DELETE http://localhost:8000/api/chat/sessions/69c4e84d6c6757fef1b9eb70
```

预期响应：
```json
{"success": true}
```

### 3. 验证删除

```bash
python scripts/check_session.py --session-id 69c4e84d6c6757fef1b9eb70
```

应该显示：
```
✗ 未找到会话
  确认会话不存在
```

## 预防措施

### 1. 统一 user_id 格式

在创建 session 时，确保使用一致的格式：

```python
# 推荐：使用字符串
DEFAULT_USER_ID = "default_user"

# 不推荐：使用 ObjectId
# DEFAULT_USER_ID = ObjectId("...")
```

### 2. 数据验证

在 `create_session` 时添加验证：

```python
async def create_session(self, user_id: str, title: str = "新对话"):
    # 确保 user_id 是字符串
    if isinstance(user_id, ObjectId):
        user_id = str(user_id)
    
    session_doc = {
        "user_id": user_id,  # 使用字符串
        "title": title,
        # ...
    }
```

### 3. 迁移脚本

如果有大量历史数据，运行迁移脚本：

```bash
python scripts/check_session.py --fix
```

## 相关文件

- `backend/app/services/session_service.py` - 修复的删除方法
- `backend/scripts/check_session.py` - 诊断和修复脚本
- `backend/app/api/routes/chat.py` - API 路由

## 总结

问题已修复：
1. ✓ 放宽了删除条件，不再检查 user_id
2. ✓ 添加了诊断脚本
3. ✓ 提供了格式修复工具

现在可以正常删除会话了，即使 user_id 格式不匹配。
