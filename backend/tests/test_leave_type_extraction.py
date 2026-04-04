"""
测试假期类型提取功能
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.api.dependencies import create_access_token, get_user_by_username
from app.agents.implementations.orchestrator_agent import OrchestratorAgent
from app.core.mongodb import connect_to_mongo
from app.config import settings


async def test_leave_type_extraction():
    """测试假期类型提取"""
    print("=" * 60)
    print("测试假期类型提取功能")
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
    
    # 测试用例
    test_cases = [
        ("我的年假还剩多少", "年假"),
        ("查询病假余额", "病假"),
        ("婚假还有多少天", "婚假"),
        ("我的假期余额", None),  # 没有指定类型
        ("查询我的假期", None),  # 没有指定类型
    ]
    
    orchestrator = OrchestratorAgent()
    
    for query, expected_type in test_cases:
        print(f"\n查询: '{query}'")
        print(f"预期类型: {expected_type or '全部'}")
        
        input_data = {
            "query": query,
            "session_id": "test_session",
            "history": [],
            "auth_context": auth_context
        }
        
        result = await orchestrator.run(input_data)
        
        if result.get("success"):
            balances = result.get("balances", [])
            print(f"返回假期数量: {len(balances)}")
            
            if expected_type:
                # 应该只返回一种假期
                if len(balances) == 1 and balances[0]["leave_type"] == expected_type:
                    print(f"✅ 正确 - 只返回了 {expected_type}")
                else:
                    print(f"❌ 错误 - 预期只返回 {expected_type}，实际返回了 {len(balances)} 种假期")
            else:
                # 应该返回所有假期
                if len(balances) > 1:
                    print(f"✅ 正确 - 返回了所有假期类型")
                else:
                    print(f"❌ 错误 - 预期返回所有假期，实际只返回了 {len(balances)} 种")
        else:
            print(f"❌ 查询失败: {result.get('error')}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_leave_type_extraction())
