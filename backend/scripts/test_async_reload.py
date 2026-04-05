"""
测试异步重新加载功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from app.core.mongodb import connect_to_mongo, close_mongo_connection
from app.config import settings
from app.prompts.manager import prompt_manager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_reload():
    """测试异步重新加载"""
    try:
        # 连接数据库
        logger.info("连接数据库...")
        await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
        
        # 测试异步重新加载
        logger.info("\n测试异步重新加载...")
        await prompt_manager.reload_async()
        
        # 验证配置
        prompts = prompt_manager.list_all()
        logger.info(f"✓ 重新加载成功，共 {len(prompts)} 个提示词")
        
        # 测试获取配置
        qa_rag = prompt_manager.get("qa_rag")
        if qa_rag:
            logger.info(f"✓ 获取配置成功: {qa_rag['name']}")
        
        # 关闭连接
        await close_mongo_connection()
        logger.info("\n测试完成！")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_reload())
