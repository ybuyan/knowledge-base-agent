"""
测试删除会话功能
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
from bson import ObjectId
from app.core.mongodb import get_mongo_db, connect_to_mongo
from app.services.session_service import session_service
from app.config import settings


async def test_delete(session_id: str):
    """测试删除指定会话"""
    print(f"\n=== 测试删除会话: {session_id} ===\n")
    
    # 连接数据库
    await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
    
    db = get_mongo_db()
    if db is None:
        print("✗ MongoDB 未连接")
        return
    
    print("✓ MongoDB 已连接")
    
    # 检查会话是否存在
    try:
        session = await db.sessions.find_one({"_id": ObjectId(session_id)})
        if session:
            print(f"✓ 找到会话")
            print(f"  标题: {session.get('title')}")
            print(f"  user_id: {session.get('user_id')}")
        else:
            print(f"✗ 会话不存在")
            return
    except Exception as e:
        print(f"✗ 查询失败: {e}")
        return
    
    # 执行删除
    print(f"\n开始删除...")
    try:
        success = await session_service.delete_session(session_id, "default_user")
        
        if success:
            print(f"✓ 删除成功")
            
            # 验证删除
            session = await db.sessions.find_one({"_id": ObjectId(session_id)})
            if session:
                print(f"✗ 验证失败：会话仍然存在")
            else:
                print(f"✓ 验证成功：会话已删除")
        else:
            print(f"✗ 删除失败")
    except Exception as e:
        print(f"✗ 删除异常: {e}")
        import traceback
        traceback.print_exc()


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='测试删除会话')
    parser.add_argument('session_id', help='要删除的会话 ID')
    
    args = parser.parse_args()
    
    await test_delete(args.session_id)


if __name__ == "__main__":
    asyncio.run(main())
