"""
删除 rate_limit_records 集合以重新创建索引
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


async def drop_collection():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    print("删除 rate_limit_records 集合...")
    await db.drop_collection("rate_limit_records")
    print("✓ 集合已删除")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(drop_collection())
