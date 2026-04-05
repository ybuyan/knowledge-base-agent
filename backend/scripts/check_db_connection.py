"""
检查数据库连接
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def check_db():
    """检查数据库连接"""
    
    print("=" * 80)
    print("检查数据库连接")
    print("=" * 80)
    
    # 检查 MongoDB 连接
    try:
        from app.core.mongodb import mongodb
        
        db = mongodb.get_database()
        
        if db is None:
            print("\n❌ MongoDB 数据库连接失败：mongodb.get_database() 返回 None")
            print("   可能原因：")
            print("   1. MongoDB 服务未启动")
            print("   2. .env 文件中的 MONGODB_URL 配置错误")
            print("   3. 数据库连接超时")
            print("   4. 后端服务未启动（数据库连接在启动时初始化）")
            print("\n   解决方案：")
            print("   1. 启动后端服务: uvicorn app.main:app --reload")
            print("   2. 或者手动初始化数据库连接")
            
            # 尝试手动连接
            print("\n尝试手动连接数据库...")
            from app.core.mongodb import connect_to_mongo
            from app.config import settings
            
            success = await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
            
            if not success:
                print("❌ 手动连接也失败")
                return False
            
            db = mongodb.get_database()
            if db is None:
                print("❌ 连接后仍然无法获取数据库")
                return False
            
            print("✅ 手动连接成功")
        
        print(f"\n✅ MongoDB 数据库连接成功")
        print(f"   数据库名称: {db.name}")
        
        # 列出所有集合
        collections = await db.list_collection_names()
        print(f"\n✅ 数据库中的集合: {len(collections)} 个")
        for coll in collections:
            count = await db[coll].count_documents({})
            print(f"   - {coll}: {count} 条记录")
        
        # 检查 sessions 集合
        if "sessions" in collections:
            sessions_count = await db["sessions"].count_documents({})
            print(f"\n✅ sessions 集合: {sessions_count} 条记录")
            
            if sessions_count > 0:
                # 显示最近的一条
                latest = await db["sessions"].find_one(sort=[("created_at", -1)])
                if latest:
                    print(f"   最新会话:")
                    print(f"   - _id: {latest.get('_id')}")
                    print(f"   - title: {latest.get('title')}")
                    print(f"   - created_at: {latest.get('created_at')}")
        else:
            print("\n❌ sessions 集合不存在")
        
        # 检查 messages 集合
        if "messages" in collections:
            messages_count = await db["messages"].count_documents({})
            print(f"\n✅ messages 集合: {messages_count} 条记录")
            
            if messages_count > 0:
                # 显示最近的一条
                latest = await db["messages"].find_one(sort=[("created_at", -1)])
                if latest:
                    print(f"   最新消息:")
                    print(f"   - _id: {latest.get('_id')}")
                    print(f"   - session_id: {latest.get('session_id')}")
                    print(f"   - role: {latest.get('role')}")
                    print(f"   - content: {latest.get('content', '')[:50]}...")
        else:
            print("\n❌ messages 集合不存在")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 检查数据库时出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(check_db())
