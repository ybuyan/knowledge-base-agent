from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def clear():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client['agent']
    
    r1 = await db.messages.delete_many({})
    r2 = await db.sessions.delete_many({})
    
    print(f"已删除 {r1.deleted_count} 条消息, {r2.deleted_count} 个会话")
    client.close()

asyncio.run(clear())
