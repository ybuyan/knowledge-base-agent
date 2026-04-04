"""
初始化提示词配置到数据库

将 prompts/config.json 中的配置同步到数据库
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from app.services.prompt_config_service import prompt_config_service
from app.core.mongodb import connect_to_mongo, close_mongo_connection
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
        
        # 同步配置
        logger.info("开始同步提示词配置...")
        result = prompt_config_service.sync_from_file()
        
        if result.get("success"):
            stats = result.get("stats", {})
            logger.info(f"同步完成:")
            logger.info(f"  - 创建: {stats.get('created', 0)} 个")
            logger.info(f"  - 更新: {stats.get('updated', 0)} 个")
            logger.info(f"  - 跳过: {stats.get('skipped', 0)} 个")
            logger.info(f"  - 错误: {stats.get('errors', 0)} 个")
        else:
            logger.error(f"同步失败: {result.get('error')}")
        
        # 关闭连接
        await close_mongo_connection()
        logger.info("数据库连接已关闭")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
