"""
导出数据库中的提示词配置到文件

将数据库中的配置导出为 JSON 文件
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
        
        # 导出配置
        logger.info("开始导出提示词配置...")
        output_path = project_root / "app" / "prompts" / "config_export.json"
        
        success = prompt_config_service.export_to_file(str(output_path))
        
        if success:
            logger.info(f"导出成功: {output_path}")
        else:
            logger.error("导出失败")
        
        # 关闭连接
        await close_mongo_connection()
        logger.info("数据库连接已关闭")
        
    except Exception as e:
        logger.error(f"导出失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
