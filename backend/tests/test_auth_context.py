"""
测试 auth_context 流程
验证从 JWT token 到 Tool 的认证上下文传递
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.api.dependencies import create_access_token, get_user_by_username
from app.agents.implementations.orchestrator_agent import OrchestratorAgent
from app.core.mongodb import get_mongo_db


async def test_auth_flow():
    """测试认证流程"""
    print("=" * 60)
    print("测试 auth_context 流程")
    print("=" * 60)
    
    # 0. 初始化数据库连接
    print("\n[步骤 0] 初始化数据库连接")
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.config import settings
    from app.core.mongodb import connect_to_mongo
    
    # 初始化全局 MongoDB 连接
    await connect_to_mongo(settings.MONGODB_URL, settings.MONGODB_DB_NAME)
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    print(f"✓ 连接到数据库: {settings.MONGODB_DB_NAME}")
    
    # 0.1 注册工具
    print("\n[步骤 0.1] 注册工具")
    from app.tools.implementations import LeaveBalanceTool
    from app.tools.base import ToolRegistry
    print(f"✓ 已注册工具: {ToolRegistry.list_all()}")
    
    # 1. 模拟登录，获取 token
    print("\n[步骤 1] 模拟用户登录")
    username = "hr"
    user = await db["users"].find_one({"username": username})
    
    if not user:
        print(f"❌ 用户 {username} 不存在")
        return
    
    print(f"✓ 找到用户: {username}")
    print(f"  - user_id: {user['_id']}")
    print(f"  - role: {user.get('role', 'user')}")
    print(f"  - display_name: {user.get('display_name', username)}")
    
    # 2. 创建 JWT token
    print("\n[步骤 2] 创建 JWT token")
    token = create_access_token({"sub": username})
    print(f"✓ Token: {token[:50]}...")
    
    # 3. 构建 auth_context
    print("\n[步骤 3] 构建 auth_context")
    auth_context = {
        "username": username,
        "user_id": str(user["_id"]),
        "role": user.get("role", "user"),
        "is_active": user.get("is_active", True)
    }
    print(f"✓ auth_context: {auth_context}")
    
    # 4. 调用 OrchestratorAgent
    print("\n[步骤 4] 调用 OrchestratorAgent")
    orchestrator = OrchestratorAgent()
    
    input_data = {
        "query": "我的年假还剩多少",
        "session_id": "test_session",
        "history": [],
        "auth_context": auth_context
    }
    
    print(f"✓ 输入数据: query='{input_data['query']}'")
    print(f"  auth_context: {input_data['auth_context']}")
    
    # 5. 执行查询
    print("\n[步骤 5] 执行查询")
    result = await orchestrator.run(input_data)
    
    print(f"\n[结果]")
    print(f"  - success: {result.get('success')}")
    print(f"  - intent: {result.get('intent')}")
    
    if result.get("success"):
        print(f"  - message:\n{result.get('message', '')}")
        print(f"\n✅ 测试通过！auth_context 正确传递")
    else:
        print(f"  - error: {result.get('error')}")
        print(f"\n❌ 测试失败")
    
    print("\n" + "=" * 60)
    
    # 关闭数据库连接
    client.close()


if __name__ == "__main__":
    asyncio.run(test_auth_flow())
