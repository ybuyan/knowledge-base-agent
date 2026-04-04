"""
重置提示词配置

1. 删除数据库中的所有 prompts
2. 从 config.json 重新导入
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from app.services.prompt_config_service import prompt_config_service
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
        
        # 1. 删除所有现有的 prompts
        logger.info("删除数据库中的所有 prompts...")
        result = await db.prompts.delete_many({})
        logger.info(f"已删除 {result.deleted_count} 个提示词配置")
        
        # 2. 从配置文件同步
        logger.info("从配置文件同步提示词...")
        sync_result = await prompt_config_service.sync_from_file()
        
        if sync_result.get("success"):
            stats = sync_result.get("stats", {})
            logger.info(f"同步完成:")
            logger.info(f"  - 创建: {stats.get('created', 0)} 个")
            logger.info(f"  - 更新: {stats.get('updated', 0)} 个")
            logger.info(f"  - 跳过: {stats.get('skipped', 0)} 个")
            logger.info(f"  - 错误: {stats.get('errors', 0)} 个")
            
            # 3. 验证结果
            logger.info("\n验证结果...")
            count = await db.prompts.count_documents({})
            logger.info(f"数据库中现有 {count} 个提示词配置")
            
            # 显示前几个配置
            logger.info("\n前 5 个配置:")
            cursor = db.prompts.find().limit(5)
            async for prompt in cursor:
                logger.info(f"  - {prompt['prompt_id']}: {prompt['name']}")
            
            logger.info("\n✓ 重置完成！")
        else:
            logger.error(f"同步失败: {sync_result.get('error')}")
        
        # 关闭连接
        await close_mongo_connection()
        logger.info("\n数据库连接已关闭")
        
    except Exception as e:
        logger.error(f"重置失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
