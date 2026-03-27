from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Optional
import logging
import asyncio

logger = logging.getLogger(__name__)


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    database = None
    is_connected: bool = False
    
    def get_database(self):
        return self.database


mongodb = MongoDB()


async def connect_to_mongo(mongo_url: str = "mongodb://localhost:27017", db_name: str = "chat_app"):
    mongodb.client = AsyncIOMotorClient(
        mongo_url,
        maxPoolSize=10,
        minPoolSize=2,
        serverSelectionTimeoutMS=5000,
        retryWrites=True,
        retryReads=True
    )
    mongodb.database = mongodb.client[db_name]
    
    try:
        await mongodb.client.admin.command('ping')
        mongodb.is_connected = True
        logger.info(f"MongoDB 连接成功: {mongo_url}, 数据库: {db_name}")
    except Exception as e:
        logger.warning(f"MongoDB 连接失败，将使用纯短期记忆模式: {e}")
        mongodb.database = None
        mongodb.is_connected = False
        return False
    
    await _create_indexes()
    return True


async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()
        mongodb.is_connected = False
        logger.info("MongoDB 连接已关闭")


async def _create_indexes():
    if mongodb.database is None:
        return
    
    try:
        await mongodb.database.sessions.create_index([("user_id", 1), ("updated_at", -1)])
        await mongodb.database.sessions.create_index([("user_id", 1), ("_id", 1)])
        await mongodb.database.sessions.create_index([("user_id", 1), ("is_archived", 1), ("updated_at", -1)])
        
        try:
            await mongodb.database.sessions.create_index([("title", "text")])
            logger.info("MongoDB 会话文本索引创建成功")
        except Exception as e:
            logger.warning(f"会话文本索引创建失败（可能已存在）: {e}")
        
        await mongodb.database.messages.create_index([("session_id", 1), ("created_at", 1)])
        await mongodb.database.messages.create_index([("user_id", 1), ("created_at", -1)])
        await mongodb.database.messages.create_index([("session_id", 1), ("_id", 1)])
        
        try:
            await mongodb.database.messages.create_index([("content", "text")])
            logger.info("MongoDB 消息文本索引创建成功")
        except Exception as e:
            logger.warning(f"消息文本索引创建失败（可能已存在）: {e}")
        
        await mongodb.database.document_status.create_index([("id", 1)], unique=True)
        await mongodb.database.document_status.create_index([("created_at", -1)])
        await mongodb.database.document_status.create_index([("status", 1)])
        
        logger.info("MongoDB 索引创建完成")
    except Exception as e:
        logger.warning(f"MongoDB 索引创建失败: {e}")


def get_mongo_db():
    return mongodb.database


async def check_mongo_connection() -> bool:
    if mongodb.client is None:
        return False
    
    try:
        await mongodb.client.admin.command('ping')
        return True
    except Exception:
        return False


async def reconnect_mongo(mongo_url: str = "mongodb://localhost:27017", db_name: str = "chat_app") -> bool:
    if mongodb.is_connected:
        return True
    
    logger.info("尝试重新连接 MongoDB...")
    return await connect_to_mongo(mongo_url, db_name)
