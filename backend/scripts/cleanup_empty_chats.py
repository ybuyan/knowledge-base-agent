"""
清理多余的空"新对话"
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from app.core.mongodb import get_mongo_db, connect_to_mongo
from app.services.session_service import session_service
from app.config import settings


async def cleanup():
    """清理多余的空新对话"""
    print("\n=== 清理多余的空'新对话' ===\n")
    
    # 连接数据库
    await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
    
    db = get_mongo_db()
    if db is None:
        print("✗ MongoDB 未连接")
        return
    
    print("✓ MongoDB 已连接\n")
    
    # 查找所有空的"新对话"
    try:
        cursor = db.sessions.find({
            "title": "新对话",
            "message_count": 0,
            "is_archived": {"$ne": True}
        }).sort("created_at", -1)
        
        empty_sessions = await cursor.to_list(length=None)
        
        print(f"找到 {len(empty_sessions)} 个空的'新对话'\n")
        
        if len(empty_sessions) == 0:
            print("没有需要清理的会话")
            return
        
        if len(empty_sessions) == 1:
            print("只有一个空'新对话'，不需要清理")
            session = empty_sessions[0]
            print(f"  ID: {session['_id']}")
            print(f"  创建时间: {session.get('created_at')}")
            return
        
        # 显示所有空"新对话"
        print("空'新对话'列表:")
        for i, session in enumerate(empty_sessions, 1):
            marker = "✓ 保留" if i == 1 else "✗ 删除"
            print(f"{i}. {marker}")
            print(f"   ID: {session['_id']}")
            print(f"   创建时间: {session.get('created_at')}")
            print(f"   user_id: {session.get('user_id')}")
            print()
        
        # 执行清理
        print(f"将保留最新的1个，删除其他 {len(empty_sessions) - 1} 个\n")
        
        # 使用 session_service 的清理方法
        # 假设使用 default_user
        deleted_count = await session_service.cleanup_empty_new_chats("default_user")
        
        print(f"✓ 清理完成，删除了 {deleted_count} 个空'新对话'")
        
    except Exception as e:
        print(f"✗ 清理失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(cleanup())
