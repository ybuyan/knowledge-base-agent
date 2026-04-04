"""
测试提示词配置管理功能

测试数据库存储、同步和 API 功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from app.services.prompt_config_service import prompt_config_service
from app.prompts.manager import prompt_manager
from app.core.mongodb import connect_to_mongo, close_mongo_connection
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_sync_from_file():
    """测试从文件同步到数据库"""
    logger.info("\n=== 测试：从文件同步到数据库 ===")
    result = prompt_config_service.sync_from_file()
    
    if result.get("success"):
        stats = result.get("stats", {})
        logger.info(f"✓ 同步成功")
        logger.info(f"  创建: {stats.get('created', 0)}")
        logger.info(f"  更新: {stats.get('updated', 0)}")
        logger.info(f"  错误: {stats.get('errors', 0)}")
    else:
        logger.error(f"✗ 同步失败: {result.get('error')}")
    
    return result.get("success", False)


async def test_get_all():
    """测试获取所有配置"""
    logger.info("\n=== 测试：获取所有配置 ===")
    prompts = prompt_config_service.get_all()
    logger.info(f"✓ 获取到 {len(prompts)} 个配置")
    
    if prompts:
        logger.info(f"  示例: {prompts[0]['id']} - {prompts[0]['name']}")
    
    return len(prompts) > 0


async def test_get_by_id():
    """测试根据ID获取配置"""
    logger.info("\n=== 测试：根据ID获取配置 ===")
    prompt = prompt_config_service.get_by_id("qa_rag")
    
    if prompt:
        logger.info(f"✓ 获取成功: {prompt['name']}")
        logger.info(f"  分类: {prompt['category']}")
        logger.info(f"  启用: {prompt['enabled']}")
        return True
    else:
        logger.error("✗ 获取失败")
        return False


async def test_get_by_category():
    """测试根据分类获取配置"""
    logger.info("\n=== 测试：根据分类获取配置 ===")
    prompts = prompt_config_service.get_by_category("qa")
    logger.info(f"✓ 获取到 {len(prompts)} 个 QA 类配置")
    
    return len(prompts) > 0


async def test_update():
    """测试更新配置"""
    logger.info("\n=== 测试：更新配置 ===")
    
    # 更新描述
    success = prompt_config_service.update(
        "qa_rag",
        {"description": "测试更新 - RAG问答提示词"},
        updated_by="test_user"
    )
    
    if success:
        logger.info("✓ 更新成功")
        
        # 验证更新
        prompt = prompt_config_service.get_by_id("qa_rag")
        if prompt and "测试更新" in prompt.get("description", ""):
            logger.info("✓ 更新验证成功")
            return True
    
    logger.error("✗ 更新失败")
    return False


async def test_create_and_delete():
    """测试创建和删除配置"""
    logger.info("\n=== 测试：创建和删除配置 ===")
    
    # 创建测试配置
    test_prompt = {
        "prompt_id": "test_prompt",
        "name": "测试提示词",
        "description": "这是一个测试提示词",
        "enabled": True,
        "category": "test",
        "template": {
            "system": "测试系统提示词",
            "user": "测试用户提示词"
        },
        "variables": ["test_var"],
        "version": "1.0"
    }
    
    prompt_id = prompt_config_service.create(test_prompt, created_by="test_user")
    
    if prompt_id:
        logger.info(f"✓ 创建成功: {prompt_id}")
        
        # 验证创建
        prompt = prompt_config_service.get_by_id(prompt_id)
        if prompt:
            logger.info("✓ 创建验证成功")
            
            # 删除测试配置
            if prompt_config_service.delete(prompt_id):
                logger.info("✓ 删除成功")
                return True
    
    logger.error("✗ 创建或删除失败")
    return False


async def test_export():
    """测试导出到文件"""
    logger.info("\n=== 测试：导出到文件 ===")
    
    output_path = project_root / "app" / "prompts" / "config_test_export.json"
    success = prompt_config_service.export_to_file(str(output_path))
    
    if success:
        logger.info(f"✓ 导出成功: {output_path}")
        
        # 检查文件是否存在
        if output_path.exists():
            logger.info(f"✓ 文件验证成功，大小: {output_path.stat().st_size} 字节")
            return True
    
    logger.error("✗ 导出失败")
    return False


async def test_prompt_manager():
    """测试 PromptManager 从数据库加载"""
    logger.info("\n=== 测试：PromptManager 从数据库加载 ===")
    
    # 重新加载配置
    prompt_manager.reload()
    
    # 测试获取配置
    prompt = prompt_manager.get("qa_rag")
    if prompt:
        logger.info(f"✓ 获取配置成功: {prompt.get('name')}")
        
        # 测试渲染
        rendered = prompt_manager.render(
            "qa_rag",
            variables={
                "context": "测试知识库内容",
                "question": "测试问题"
            }
        )
        
        if rendered and "system" in rendered:
            logger.info("✓ 渲染成功")
            logger.info(f"  System: {rendered['system'][:50]}...")
            return True
    
    logger.error("✗ PromptManager 测试失败")
    return False


async def main():
    """主测试函数"""
    try:
        # 连接数据库
        logger.info("连接数据库...")
        await connect_to_mongo(settings.mongo_url, settings.mongo_db_name)
        
        # 运行测试
        results = {}
        
        results["sync_from_file"] = await test_sync_from_file()
        results["get_all"] = await test_get_all()
        results["get_by_id"] = await test_get_by_id()
        results["get_by_category"] = await test_get_by_category()
        results["update"] = await test_update()
        results["create_and_delete"] = await test_create_and_delete()
        results["export"] = await test_export()
        results["prompt_manager"] = await test_prompt_manager()
        
        # 统计结果
        logger.info("\n" + "=" * 50)
        logger.info("测试结果汇总")
        logger.info("=" * 50)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ 通过" if result else "✗ 失败"
            logger.info(f"{test_name:20s}: {status}")
        
        logger.info("=" * 50)
        logger.info(f"总计: {passed}/{total} 通过")
        logger.info("=" * 50)
        
        # 关闭连接
        await close_mongo_connection()
        logger.info("\n数据库连接已关闭")
        
        return passed == total
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
