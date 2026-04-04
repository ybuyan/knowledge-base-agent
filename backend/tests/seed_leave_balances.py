"""
假期余额种子数据脚本
为测试用户生成假期余额数据
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 假期类型配置
LEAVE_TYPES_CONFIG = {
    "年假": {"total_quota": 10.0, "unlimited": False},
    "病假": {"total_quota": -1, "unlimited": True},
    "事假": {"total_quota": -1, "unlimited": True},
    "婚假": {"total_quota": 10.0, "unlimited": False},
    "产假": {"total_quota": 98.0, "unlimited": False},
    "陪产假": {"total_quota": 15.0, "unlimited": False},
    "高温假": {"total_quota": 5.0, "unlimited": False},
}


async def seed_leave_balances():
    """为测试用户生成假期余额数据"""
    # 连接 MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    try:
        # 获取所有用户
        users_collection = db["users"]  # 修复：使用 "users" 而不是 "user"
        users = await users_collection.find({}).to_list(length=None)
        
        if not users:
            logger.warning("未找到用户，请先运行 seed_users.py")
            return
        
        logger.info(f"找到 {len(users)} 个用户")
        
        # 获取当前年度
        current_year = datetime.now().year
        
        # leave_balances 集合
        balances_collection = db["leave_balances"]
        
        # 为每个用户创建假期余额
        total_created = 0
        total_skipped = 0
        
        for user in users:
            user_id = user.get("id") or user.get("_id")
            username = user.get("username", "未知用户")
            
            logger.info(f"\n处理用户: {username} (ID: {user_id})")
            
            for leave_type, config in LEAVE_TYPES_CONFIG.items():
                # 检查是否已存在
                existing = await balances_collection.find_one({
                    "user_id": user_id,
                    "leave_type": leave_type,
                    "year": current_year
                })
                
                if existing:
                    logger.info(f"  ⊘ {leave_type}: 已存在，跳过")
                    total_skipped += 1
                    continue
                
                # 创建余额记录
                total_quota = config["total_quota"]
                used_days = 0.0 if config["unlimited"] else (total_quota * 0.3)  # 已使用30%
                remaining_days = -1 if config["unlimited"] else (total_quota - used_days)
                
                balance_doc = {
                    "user_id": user_id,
                    "username": username,
                    "leave_type": leave_type,
                    "year": current_year,
                    "total_quota": total_quota,
                    "used_days": used_days,
                    "remaining_days": remaining_days,
                    "updated_at": datetime.utcnow(),
                    "created_at": datetime.utcnow()
                }
                
                await balances_collection.insert_one(balance_doc)
                
                if config["unlimited"]:
                    logger.info(f"  ✓ {leave_type}: 无限额")
                else:
                    logger.info(f"  ✓ {leave_type}: 总额 {total_quota} 天, 已用 {used_days} 天, 剩余 {remaining_days} 天")
                
                total_created += 1
        
        logger.info(f"\n✅ 种子数据生成完成!")
        logger.info(f"   - 创建: {total_created} 条记录")
        logger.info(f"   - 跳过: {total_skipped} 条记录（已存在）")
        logger.info(f"   - 年度: {current_year}")
        
    except Exception as e:
        logger.error(f"❌ 生成种子数据失败: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(seed_leave_balances())
