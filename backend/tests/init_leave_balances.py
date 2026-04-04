"""
初始化假期余额集合和索引
创建 leave_balances 集合，并设置必要的索引和验证规则
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_leave_balances_collection():
    """初始化 leave_balances 集合"""
    # 连接 MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    collection_name = "leave_balances"
    
    try:
        # 检查集合是否已存在
        existing_collections = await db.list_collection_names()
        
        if collection_name in existing_collections:
            logger.info(f"集合 '{collection_name}' 已存在")
            collection = db[collection_name]
        else:
            # 创建集合并添加验证规则
            logger.info(f"创建集合 '{collection_name}'...")
            
            # 定义 JSON Schema 验证规则
            validator = {
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["user_id", "username", "leave_type", "year", "total_quota", "used_days", "remaining_days"],
                    "properties": {
                        "user_id": {
                            "bsonType": "string",
                            "description": "用户ID，必填"
                        },
                        "username": {
                            "bsonType": "string",
                            "description": "用户名，必填"
                        },
                        "leave_type": {
                            "bsonType": "string",
                            "enum": ["年假", "病假", "事假", "婚假", "产假", "陪产假", "高温假"],
                            "description": "假期类型，必填"
                        },
                        "year": {
                            "bsonType": "int",
                            "minimum": 2020,
                            "maximum": 2100,
                            "description": "年度，必填"
                        },
                        "total_quota": {
                            "bsonType": "double",
                            "description": "总额度（天），-1表示无限额，必填"
                        },
                        "used_days": {
                            "bsonType": "double",
                            "minimum": 0,
                            "description": "已使用天数，必填"
                        },
                        "remaining_days": {
                            "bsonType": "double",
                            "description": "剩余天数，-1表示无限额，必填"
                        },
                        "updated_at": {
                            "bsonType": "date",
                            "description": "最后更新时间"
                        },
                        "created_at": {
                            "bsonType": "date",
                            "description": "创建时间"
                        }
                    }
                }
            }
            
            await db.create_collection(
                collection_name,
                validator=validator,
                validationLevel="moderate",
                validationAction="error"
            )
            collection = db[collection_name]
            logger.info(f"集合 '{collection_name}' 创建成功")
        
        # 创建索引
        logger.info("创建索引...")
        
        # 1. 复合唯一索引：user_id + leave_type + year
        await collection.create_index(
            [("user_id", 1), ("leave_type", 1), ("year", 1)],
            unique=True,
            name="idx_user_leave_year_unique"
        )
        logger.info("✓ 创建复合唯一索引: (user_id, leave_type, year)")
        
        # 2. 单字段索引：user_id（用于查询用户所有余额）
        await collection.create_index(
            [("user_id", 1)],
            name="idx_user_id"
        )
        logger.info("✓ 创建单字段索引: user_id")
        
        # 3. 单字段索引：year（用于批量更新年度数据）
        await collection.create_index(
            [("year", 1)],
            name="idx_year"
        )
        logger.info("✓ 创建单字段索引: year")
        
        # 列出所有索引
        indexes = await collection.list_indexes().to_list(length=None)
        logger.info(f"\n当前索引列表:")
        for idx in indexes:
            logger.info(f"  - {idx['name']}: {idx.get('key', {})}")
        
        logger.info(f"\n✅ leave_balances 集合初始化完成!")
        
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(init_leave_balances_collection())
