"""
MCP 资源公开访问 - 数据库初始化脚本

创建必要的 MongoDB 集合和索引
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


async def init_mcp_collections():
    """初始化 MCP 相关的 MongoDB 集合和索引"""
    
    # 连接 MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    print("开始初始化 MCP 数据库集合和索引...")
    
    # 1. 创建 api_keys 集合和索引
    print("\n1. 创建 api_keys 集合...")
    api_keys_collection = db["api_keys"]
    
    # 创建索引
    await api_keys_collection.create_index("key", unique=True)
    print("  ✓ 创建唯一索引: key")
    
    await api_keys_collection.create_index("user_id")
    print("  ✓ 创建索引: user_id")
    
    await api_keys_collection.create_index("is_active")
    print("  ✓ 创建索引: is_active")
    
    # TTL 索引：自动清理过期记录
    await api_keys_collection.create_index(
        "expires_at",
        expireAfterSeconds=0
    )
    print("  ✓ 创建 TTL 索引: expires_at")
    
    # 2. 创建 audit_logs 集合和索引
    print("\n2. 创建 audit_logs 集合...")
    audit_logs_collection = db["audit_logs"]
    
    # 创建索引
    await audit_logs_collection.create_index(
        [("timestamp", -1)]  # 降序索引
    )
    print("  ✓ 创建降序索引: timestamp")
    
    await audit_logs_collection.create_index("user_id")
    print("  ✓ 创建索引: user_id")
    
    await audit_logs_collection.create_index("resource_uri")
    print("  ✓ 创建索引: resource_uri")
    
    await audit_logs_collection.create_index("success")
    print("  ✓ 创建索引: success")
    
    # 复合索引
    await audit_logs_collection.create_index(
        [("user_id", 1), ("timestamp", -1)]
    )
    print("  ✓ 创建复合索引: (user_id, timestamp)")
    
    # TTL 索引：90 天后自动清理
    await audit_logs_collection.create_index(
        "timestamp",
        expireAfterSeconds=7776000  # 90 天 = 90 * 24 * 60 * 60
    )
    print("  ✓ 创建 TTL 索引: timestamp (90 天自动清理)")
    
    # 3. 创建 rate_limit_records 集合和索引（可选）
    print("\n3. 创建 rate_limit_records 集合（可选）...")
    rate_limit_collection = db["rate_limit_records"]
    
    # 创建索引（不使用唯一索引，因为同一用户可以有多条记录）
    await rate_limit_collection.create_index("user_id")
    print("  ✓ 创建索引: user_id")
    
    # TTL 索引：1小时后自动清理
    await rate_limit_collection.create_index(
        "timestamp",
        expireAfterSeconds=3600  # 1 小时
    )
    print("  ✓ 创建 TTL 索引: timestamp (1 小时自动清理)")
    
    print("\n✅ 所有集合和索引创建完成！")
    
    # 验证索引
    print("\n验证索引...")
    print("\napi_keys 集合索引:")
    async for index in api_keys_collection.list_indexes():
        print(f"  - {index['name']}: {index.get('key', {})}")
    
    print("\naudit_logs 集合索引:")
    async for index in audit_logs_collection.list_indexes():
        print(f"  - {index['name']}: {index.get('key', {})}")
    
    print("\nrate_limit_records 集合索引:")
    async for index in rate_limit_collection.list_indexes():
        print(f"  - {index['name']}: {index.get('key', {})}")
    
    client.close()
    print("\n✅ 数据库初始化完成！")


if __name__ == "__main__":
    asyncio.run(init_mcp_collections())
