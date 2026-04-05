"""
检查特定会话的历史记录
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.mongodb import mongodb, connect_to_mongo
from app.config import settings

DEFAULT_USER_ID = "default_user"


async def check_session():
    """检查特定会话"""
    
    # 连接数据库
    await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
    db = mongodb.get_database()
    
    # 最新的会话 ID
    from bson import ObjectId
    session_id_str = "69cfc8340354995b014f3a4b"
    session_id = ObjectId(session_id_str)
    
    print("=" * 80)
    print(f"检查会话: {session_id}")
    print("=" * 80)
    
    # 获取会话信息
    session = await db["sessions"].find_one({"_id": session_id})
    
    if not session:
        print(f"❌ 未找到会话: {session_id}")
        return
    
    print(f"\n✅ 会话信息:")
    print(f"   - title: {session.get('title')}")
    print(f"   - created_at: {session.get('created_at')}")
    print(f"   - message_count: {session.get('message_count', 0)}")
    
    # 获取该会话的所有消息
    messages = await db["messages"].find(
        {"session_id": session_id_str}  # messages 集合中 session_id 是字符串
    ).sort("created_at", 1).to_list(length=100)
    
    print(f"\n✅ 消息列表: {len(messages)} 条")
    print("-" * 80)
    
    for i, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        created_at = msg.get("created_at", "")
        
        # 截断内容
        if len(content) > 100:
            content_display = content[:100] + "..."
        else:
            content_display = content
        
        print(f"\n[{i+1}] {created_at} | {role}")
        print(f"    {content_display}")
    
    # 模拟 Chat API 获取历史记录
    print("\n" + "=" * 80)
    print("模拟 Chat API 获取历史记录（最近12条）")
    print("=" * 80)
    
    history = []
    for msg in messages[-12:]:
        history.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    print(f"\n✅ 构建的历史记录: {len(history)} 条")
    for i, msg in enumerate(history):
        content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
        print(f"   [{i}] {msg['role']:10s} | {content_preview}")
    
    # 检查是否包含触发词
    triggers = ["婚假", "年假", "病假", "事假", "产假", "陪产假", "高温假"]
    
    print(f"\n✅ 检查触发词:")
    for trigger in triggers:
        found = any(trigger in msg["content"] for msg in history if msg["role"] == "user")
        status = "✅" if found else "❌"
        print(f"   {status} '{trigger}': {found}")


if __name__ == "__main__":
    asyncio.run(check_session())
