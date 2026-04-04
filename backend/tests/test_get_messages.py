"""
测试 get_messages 函数
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.message_service import message_service
from app.core.mongodb import connect_to_mongo
from app.config import settings

DEFAULT_USER_ID = "default_user"


async def test():
    """测试 get_messages"""
    
    # 连接数据库
    await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
    
    session_id = "69cfc8340354995b014f3a4b"
    
    print("=" * 80)
    print(f"测试 get_messages(session_id='{session_id}', user_id='{DEFAULT_USER_ID}')")
    print("=" * 80)
    
    messages = await message_service.get_messages(session_id, DEFAULT_USER_ID)
    
    print(f"\n✅ 返回 {len(messages)} 条消息")
    
    if messages:
        for i, msg in enumerate(messages):
            role = msg.get("role")
            content = msg.get("content", "")[:50]
            print(f"   [{i}] {role:10s} | {content}...")
    else:
        print("   ❌ 没有消息")
    
    # 构建历史记录
    history = []
    for msg in messages[-12:]:
        history.append({"role": msg["role"], "content": msg["content"]})
    
    print(f"\n✅ 构建的历史记录: {len(history)} 条")
    
    # 检查触发词
    has_marriage = any("婚假" in msg["content"] for msg in history if msg["role"] == "user")
    print(f"✅ 包含'婚假': {has_marriage}")


if __name__ == "__main__":
    asyncio.run(test())
