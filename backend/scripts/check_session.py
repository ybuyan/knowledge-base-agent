"""
检查会话数据
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from bson import ObjectId
from app.core.mongodb import get_mongo_db


async def check_session(session_id: str):
    """检查指定会话的数据"""
    db = get_mongo_db()
    if db is None:
        print("MongoDB 未连接")
        return
    
    print(f"\n=== 检查会话: {session_id} ===\n")
    
    try:
        # 尝试作为 ObjectId 查询
        session = await db.sessions.find_one({"_id": ObjectId(session_id)})
        
        if session:
            print("✓ 找到会话")
            print(f"\n会话信息:")
            print(f"  _id: {session['_id']}")
            print(f"  user_id: {session.get('user_id')} (类型: {type(session.get('user_id')).__name__})")
            print(f"  title: {session.get('title')}")
            print(f"  created_at: {session.get('created_at')}")
            print(f"  updated_at: {session.get('updated_at')}")
            print(f"  message_count: {session.get('message_count', 0)}")
            print(f"  is_archived: {session.get('is_archived', False)}")
            
            # 检查消息数量
            message_count = await db.messages.count_documents({"session_id": ObjectId(session_id)})
            print(f"\n消息数量: {message_count}")
            
            # 检查 user_id 格式
            user_id = session.get('user_id')
            if isinstance(user_id, ObjectId):
                print(f"\n⚠️  user_id 是 ObjectId 格式: {user_id}")
                print(f"   这可能导致删除失败，因为 DEFAULT_USER_ID='default_user' 是字符串")
            elif isinstance(user_id, str):
                print(f"\n✓ user_id 是字符串格式: {user_id}")
            else:
                print(f"\n⚠️  user_id 是未知格式: {type(user_id)}")
            
        else:
            print("✗ 未找到会话")
            
            # 尝试作为字符串查询
            session = await db.sessions.find_one({"_id": session_id})
            if session:
                print("  但找到了字符串 ID 的会话")
            else:
                print("  确认会话不存在")
    
    except Exception as e:
        print(f"✗ 查询失败: {e}")


async def list_all_sessions():
    """列出所有会话"""
    db = get_mongo_db()
    if db is None:
        print("MongoDB 未连接")
        return
    
    print("\n=== 所有会话列表 ===\n")
    
    try:
        cursor = db.sessions.find().sort("updated_at", -1).limit(20)
        sessions = await cursor.to_list(length=20)
        
        if not sessions:
            print("没有会话")
            return
        
        print(f"共 {len(sessions)} 个会话（最近20个）:\n")
        
        for i, session in enumerate(sessions, 1):
            user_id = session.get('user_id')
            user_id_type = type(user_id).__name__
            print(f"{i}. {session['_id']}")
            print(f"   标题: {session.get('title', '无标题')}")
            print(f"   user_id: {user_id} ({user_id_type})")
            print(f"   消息数: {session.get('message_count', 0)}")
            print(f"   更新时间: {session.get('updated_at')}")
            print()
    
    except Exception as e:
        print(f"✗ 查询失败: {e}")


async def fix_user_id_format():
    """修复 user_id 格式问题"""
    db = get_mongo_db()
    if db is None:
        print("MongoDB 未连接")
        return
    
    print("\n=== 修复 user_id 格式 ===\n")
    
    try:
        # 查找所有 user_id 是 ObjectId 的会话
        cursor = db.sessions.find({"user_id": {"$type": "objectId"}})
        sessions = await cursor.to_list(length=None)
        
        if not sessions:
            print("没有需要修复的会话")
            return
        
        print(f"找到 {len(sessions)} 个需要修复的会话\n")
        
        for session in sessions:
            session_id = session['_id']
            old_user_id = session['user_id']
            new_user_id = "default_user"
            
            result = await db.sessions.update_one(
                {"_id": session_id},
                {"$set": {"user_id": new_user_id}}
            )
            
            if result.modified_count > 0:
                print(f"✓ 修复会话 {session_id}")
                print(f"  {old_user_id} (ObjectId) -> {new_user_id} (string)")
            else:
                print(f"✗ 修复失败: {session_id}")
        
        print(f"\n完成！修复了 {len(sessions)} 个会话")
    
    except Exception as e:
        print(f"✗ 修复失败: {e}")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='检查和修复会话数据')
    parser.add_argument('--session-id', help='检查指定会话')
    parser.add_argument('--list', action='store_true', help='列出所有会话')
    parser.add_argument('--fix', action='store_true', help='修复 user_id 格式问题')
    
    args = parser.parse_args()
    
    if args.session_id:
        await check_session(args.session_id)
    elif args.list:
        await list_all_sessions()
    elif args.fix:
        await fix_user_id_format()
    else:
        print("请使用 --session-id <ID> 检查会话，或 --list 列出所有会话，或 --fix 修复格式问题")


if __name__ == "__main__":
    asyncio.run(main())
