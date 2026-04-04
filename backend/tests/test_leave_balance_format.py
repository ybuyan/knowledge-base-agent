"""
测试假期余额格式化输出
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.api.dependencies import get_user_by_username
from app.agents.implementations.orchestrator_agent import OrchestratorAgent
from app.core.mongodb import connect_to_mongo
from app.config import settings


async def test_format():
    """测试格式化输出"""
    print("=" * 60)
    print("测试假期余额格式化输出")
    print("=" * 60)
    
    # 初始化
    await connect_to_mongo(settings.MONGODB_URL, settings.MONGODB_DB_NAME)
    from app.tools.implementations import LeaveBalanceTool
    
    # 获取用户信息
    user = await get_user_by_username("hr")
    auth_context = {
        "username": "hr",
        "user_id": str(user["_id"]),
        "role": user.get("role", "user"),
        "is_active": user.get("is_active", True)
    }
    
    orchestrator = OrchestratorAgent()
    
    # 测试1：查询单个假期类型
    print("\n[测试 1] 查询单个假期类型（年假）")
    print("-" * 60)
    result = await orchestrator.run({
        "query": "我的年假还剩多少",
        "session_id": "test",
        "history": [],
        "auth_context": auth_context
    })
    print(result.get("message", ""))
    
    # 测试2：查询所有假期
    print("\n[测试 2] 查询所有假期")
    print("-" * 60)
    result = await orchestrator.run({
        "query": "我的假期余额",
        "session_id": "test",
        "history": [],
        "auth_context": auth_context
    })
    print(result.get("message", ""))
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_format())
