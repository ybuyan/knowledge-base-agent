"""
检查 messages 集合中的数据格式
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.mongodb import mongodb, connect_to_mongo
from app.config import settings


async def check_messages():
    """检查 messages 格式"""
    
    # 连接数据库
    await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
    db = mongodb.get_database()
    
    print("=" * 80)
    print("检查 messages 集合的数据格式")
    print("=" * 80)
    
    # 获取最近的 5 条消息
    messages = await db["messages"].find().sort("created_at", -1).limit(5).to_list(length=5)
    
    print(f"\n✅ 最近的 {len(messages)} 条消息:")
    print("-" * 80)
    
    for i, msg in enumerate(messages):
        print(f"\n[{i+1}] 消息详情:")
        print(f"   _id: {msg.get('_id')} (type: {type(msg.get('_id'))})")
        print(f"   session_id: {msg.get('session_id')} (type: {type(msg.get('session_id'))})")
        print(f"   user_id: {msg.get('user_id')}")
        print(f"   role: {msg.get('role')}")
        print(f"   content: {msg.get('content', '')[:50]}...")
        print(f"   created_at: {msg.get('created_at')}")
    
    # 检查特定 session 的消息
    target_session = "69cfc8340354995b014f3a4b"
    
    print(f"\n" + "=" * 80)
    print(f"查找 session_id = '{target_session}' 的消息")
    print("=" * 80)
    
    # 尝试不同的查询方式
    from bson import ObjectId
    
    # 方式1: 字符串查询
    count1 = await db["messages"].count_documents({"session_id": target_session})
    print(f"\n方式1 (字符串): {count1} 条")
    
    # 方式2: ObjectId 查询
    try:
        count2 = await db["messages"].count_documents({"session_id": ObjectId(target_session)})
        print(f"方式2 (ObjectId): {count2} 条")
    except Exception as e:
        print(f"方式2 (ObjectId): 失败 - {e}")
    
    # 获取所有不同的 session_id
    print(f"\n" + "=" * 80)
    print("所有不同的 session_id (最近10个):")
    print("=" * 80)
    
    pipeline = [
        {"$group": {"_id": "$session_id"}},
        {"$limit": 10}
    ]
    
    session_ids = await db["messages"].aggregate(pipeline).to_list(length=10)
    
    for sid in session_ids:
        session_id_value = sid["_id"]
        count = await db["messages"].count_documents({"session_id": session_id_value})
        print(f"   {session_id_value} (type: {type(session_id_value)}): {count} 条消息")


if __name__ == "__main__":
    asyncio.run(check_messages())
