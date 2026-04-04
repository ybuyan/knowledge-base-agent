"""
检查数据库中的提示词配置
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from app.core.mongodb import connect_to_mongo, close_mongo_connection, get_mongo_db
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """主函数"""
    try:
        # 连接数据库
        logger.info("连接数据库...")
        await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
        
        db = get_mongo_db()
        if db is None:
            logger.error("数据库连接失败")
            return
        
        # 统计信息
        total = await db.prompts.count_documents({})
        enabled = await db.prompts.count_documents({"enabled": True})
        disabled = await db.prompts.count_documents({"enabled": False})
        
        logger.info(f"\n=== 提示词配置统计 ===")
        logger.info(f"总数: {total}")
        logger.info(f"启用: {enabled}")
        logger.info(f"禁用: {disabled}")
        
        # 按分类统计
        logger.info(f"\n=== 按分类统计 ===")
        pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        async for item in db.prompts.aggregate(pipeline):
            logger.info(f"{item['_id']:20s}: {item['count']} 个")
        
        # 列出所有配置
        logger.info(f"\n=== 所有提示词配置 ===")
        cursor = db.prompts.find().sort("category", 1)
        current_category = None
        async for prompt in cursor:
            if prompt['category'] != current_category:
                current_category = prompt['category']
                logger.info(f"\n[{current_category}]")
            
            status = "✓" if prompt['enabled'] else "✗"
            logger.info(f"  {status} {prompt['prompt_id']:30s} - {prompt['name']}")
        
        # 关闭连接
        await close_mongo_connection()
        logger.info("\n数据库连接已关闭")
        
    except Exception as e:
        logger.error(f"检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
