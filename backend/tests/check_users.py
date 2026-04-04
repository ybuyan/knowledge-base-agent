"""检查用户数据"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def check_users():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    users = await db['user'].find({}).to_list(length=100)
    print(f"Found {len(users)} users:")
    for u in users:
        print(f"  - {u.get('username')} (ID: {u.get('id') or u.get('_id')})")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_users())
