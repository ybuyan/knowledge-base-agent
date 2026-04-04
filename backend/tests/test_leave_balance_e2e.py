"""
端到端测试：假期余额查询
验证从 HTTP 请求到返回结果的完整流程
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.api.dependencies import create_access_token
from app.core.mongodb import connect_to_mongo
from app.config import settings


async def test_e2e():
    """端到端测试"""
    print("=" * 60)
    print("端到端测试：假期余额查询")
    print("=" * 60)
    
    # 1. 初始化
    print("\n[步骤 1] 初始化环境")
    await connect_to_mongo(settings.MONGODB_URL, settings.MONGODB_DB_NAME)
    
    # 注册工具
    from app.tools.implementations import LeaveBalanceTool
    print("✓ 工具已注册")
    
    # 2. 模拟 HTTP 请求
    print("\n[步骤 2] 模拟 HTTP 请求")
    username = "hr"
    token = create_access_token({"sub": username})
    print(f"✓ 生成 JWT token: {token[:50]}...")
    
    # 3. 模拟 chat route 的处理流程
    print("\n[步骤 3] 模拟 chat route 处理")
    
    # 3.1 提取 auth_context
    from app.api.dependencies import decode_token, get_user_by_username
    
    payload = decode_token(token)
    username = payload.get("sub", "")
    user = await get_user_by_username(username)
    
    auth_context = {
        "username": username,
        "user_id": str(user["_id"]),
        "role": user.get("role", "user"),
        "is_active": user.get("is_active", True)
    }
    print(f"✓ auth_context: {auth_context}")
    
    # 3.2 调用 OrchestratorAgent
    print("\n[步骤 4] 调用 OrchestratorAgent")
    from app.agents.implementations.orchestrator_agent import OrchestratorAgent
    
    orchestrator = OrchestratorAgent()
    input_data = {
        "query": "我的年假还剩多少",
        "session_id": "test_session",
        "history": [],
        "auth_context": auth_context
    }
    
    result = await orchestrator.run(input_data)
    
    # 4. 验证结果
    print("\n[步骤 5] 验证结果")
    print(f"  - intent: {result.get('intent')}")
    print(f"  - success: {result.get('success')}")
    
    if result.get("success"):
        # 模拟 chat route 的响应处理
        full_response = result.get("answer") or result.get("message", "")
        print(f"\n[响应内容]")
        print(full_response)
        print(f"\n✅ 端到端测试通过！")
    else:
        print(f"  - error: {result.get('error')}")
        print(f"\n❌ 测试失败")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_e2e())
