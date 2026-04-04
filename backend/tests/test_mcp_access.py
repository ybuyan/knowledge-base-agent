"""
MCP 资源公开访问功能测试脚本

测试以下功能：
1. 数据库初始化
2. API Key 生成和验证
3. 资源访问控制
4. 速率限制
5. 审计日志
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.mcp.api_key_manager import APIKeyManager
from app.mcp.auth_middleware import MCPAuthMiddleware
from app.mcp.access_control import ResourceAccessControl
from app.mcp.audit_logger import AuditLogger
from app.mcp.rate_limiter import RateLimiter
from app.mcp.base import MCPResource


async def test_database_initialization():
    """测试数据库初始化"""
    print("\n=== 测试 1: 数据库初始化 ===")
    
    client = AsyncIOMotorClient(settings.mongo_url)
    db = client[settings.mongo_db_name]
    
    # 检查集合是否存在
    collections = await db.list_collection_names()
    
    required_collections = ["api_keys", "audit_logs", "rate_limit_records"]
    for collection_name in required_collections:
        if collection_name in collections:
            print(f"✓ 集合 {collection_name} 已存在")
        else:
            print(f"✗ 集合 {collection_name} 不存在")
    
    client.close()


async def test_api_key_generation():
    """测试 API Key 生成和验证"""
    print("\n=== 测试 2: API Key 生成和验证 ===")
    
    manager = APIKeyManager()
    
    # 生成 API Key
    print("\n生成 API Key...")
    api_key = await manager.generate_api_key(
        user_id="test_user_001",
        username="Test User",
        role="employee",
        permissions=["read:confidential"],
        rate_limit=100,
        expires_days=30,
        description="测试用 API Key"
    )
    
    print(f"✓ API Key 生成成功: {api_key.key[:20]}...")
    print(f"  用户ID: {api_key.user_id}")
    print(f"  角色: {api_key.role}")
    print(f"  速率限制: {api_key.rate_limit}/分钟")
    
    # 验证 API Key
    print("\n验证 API Key...")
    validated = await manager.validate_api_key(api_key.key)
    
    if validated:
        print(f"✓ API Key 验证成功")
        print(f"  用户名: {validated.username}")
        print(f"  角色: {validated.role}")
    else:
        print(f"✗ API Key 验证失败")
    
    # 测试无效的 API Key
    print("\n测试无效的 API Key...")
    invalid = await manager.validate_api_key("mcp_invalid_key_12345")
    
    if invalid is None:
        print(f"✓ 无效 API Key 正确被拒绝")
    else:
        print(f"✗ 无效 API Key 未被拒绝")
    
    # 撤销 API Key
    print("\n撤销 API Key...")
    revoked = await manager.revoke_api_key(api_key.key)
    
    if revoked:
        print(f"✓ API Key 撤销成功")
    else:
        print(f"✗ API Key 撤销失败")
    
    # 验证已撤销的 API Key
    print("\n验证已撤销的 API Key...")
    revoked_validated = await manager.validate_api_key(api_key.key)
    
    if revoked_validated is None:
        print(f"✓ 已撤销的 API Key 正确被拒绝")
    else:
        print(f"✗ 已撤销的 API Key 未被拒绝")
    
    manager.close()


async def test_access_control():
    """测试资源访问控制"""
    print("\n=== 测试 3: 资源访问控制 ===")
    
    access_control = ResourceAccessControl()
    
    # 创建测试资源
    public_resource = MCPResource(
        uri="knowledge://public/faq",
        name="常见问题",
        description="公开的常见问题"
    )
    
    internal_resource = MCPResource(
        uri="knowledge://internal/policy",
        name="内部政策",
        description="内部政策文档"
    )
    
    confidential_resource = MCPResource(
        uri="knowledge://confidential/salary",
        name="薪酬政策",
        description="机密的薪酬政策"
    )
    
    resources = [public_resource, internal_resource, confidential_resource]
    
    # 测试 guest 用户
    print("\n测试 guest 用户访问权限...")
    from app.mcp.auth_middleware import AuthContext
    
    guest_context = AuthContext(
        user_id="guest",
        username="Guest User",
        role="guest",
        permissions=[],
        rate_limit=30,
        api_key="guest"
    )
    
    guest_resources = access_control.filter_resources(resources, guest_context)
    print(f"✓ Guest 用户可访问 {len(guest_resources)} 个资源:")
    for r in guest_resources:
        print(f"  - {r.name} ({r.uri})")
    
    # 测试 employee 用户
    print("\n测试 employee 用户访问权限...")
    employee_context = AuthContext(
        user_id="emp001",
        username="Employee User",
        role="employee",
        permissions=[],
        rate_limit=100,
        api_key="mcp_employee"
    )
    
    employee_resources = access_control.filter_resources(resources, employee_context)
    print(f"✓ Employee 用户可访问 {len(employee_resources)} 个资源:")
    for r in employee_resources:
        print(f"  - {r.name} ({r.uri})")
    
    # 测试 admin 用户
    print("\n测试 admin 用户访问权限...")
    admin_context = AuthContext(
        user_id="admin001",
        username="Admin User",
        role="admin",
        permissions=["read:confidential"],
        rate_limit=500,
        api_key="mcp_admin"
    )
    
    admin_resources = access_control.filter_resources(resources, admin_context)
    print(f"✓ Admin 用户可访问 {len(admin_resources)} 个资源:")
    for r in admin_resources:
        print(f"  - {r.name} ({r.uri})")


async def test_rate_limiter():
    """测试速率限制"""
    print("\n=== 测试 4: 速率限制 ===")
    
    rate_limiter = RateLimiter()
    
    user_id = "test_rate_limit_user"
    rate_limit = 5  # 每分钟 5 次请求
    
    print(f"\n测试速率限制（限制: {rate_limit} 次/分钟）...")
    
    # 发送请求直到超出限制
    success_count = 0
    for i in range(rate_limit + 2):
        try:
            await rate_limiter.check_rate_limit(user_id, rate_limit, window_seconds=60)
            success_count += 1
            print(f"✓ 请求 {i+1} 通过")
        except Exception as e:
            print(f"✗ 请求 {i+1} 被拒绝: {str(e)}")
    
    print(f"\n总结: {success_count}/{rate_limit + 2} 个请求通过")
    
    # 查询剩余配额
    remaining = await rate_limiter.get_remaining_quota(user_id, rate_limit, window_seconds=60)
    print(f"✓ 剩余配额: {remaining}")
    
    # 重置配额
    print("\n重置用户配额...")
    await rate_limiter.reset_user_quota(user_id)
    
    remaining_after_reset = await rate_limiter.get_remaining_quota(user_id, rate_limit, window_seconds=60)
    print(f"✓ 重置后剩余配额: {remaining_after_reset}")
    
    rate_limiter.close()


async def test_audit_logger():
    """测试审计日志"""
    print("\n=== 测试 5: 审计日志 ===")
    
    audit_logger = AuditLogger()
    
    # 创建测试认证上下文
    from app.mcp.auth_middleware import AuthContext
    
    auth_context = AuthContext(
        user_id="test_audit_user",
        username="Test Audit User",
        role="employee",
        permissions=[],
        rate_limit=100,
        api_key="mcp_test..."
    )
    
    # 创建模拟请求
    class MockRequest:
        def __init__(self):
            self.headers = {"User-Agent": "Test Client"}
            self.client = type('obj', (object,), {'host': '127.0.0.1'})()
    
    mock_request = MockRequest()
    
    # 记录访问日志
    print("\n记录访问日志...")
    await audit_logger.log_access(
        auth_context=auth_context,
        method="resources/read",
        resource_uri="knowledge://public/faq",
        tool_name=None,
        success=True,
        error_code=None,
        error_message=None,
        request=mock_request,
        response_time_ms=150
    )
    print("✓ 访问日志记录成功")
    
    # 等待批量写入
    await asyncio.sleep(2)
    
    # 查询用户访问历史
    print("\n查询用户访问历史...")
    history = await audit_logger.get_user_access_history(auth_context.user_id, limit=10)
    
    print(f"✓ 找到 {len(history)} 条访问记录")
    for log in history[:3]:  # 只显示前3条
        print(f"  - {log.timestamp}: {log.method} -> {log.resource_uri} (成功: {log.success})")
    
    # 获取资源访问统计
    print("\n获取资源访问统计...")
    stats = await audit_logger.get_resource_access_stats(
        "knowledge://public/faq",
        days=7
    )
    
    print(f"✓ 资源访问统计:")
    print(f"  - 总访问次数: {stats['total_accesses']}")
    print(f"  - 成功访问: {stats['successful_accesses']}")
    print(f"  - 失败访问: {stats['failed_accesses']}")
    print(f"  - 唯一用户数: {stats['unique_users']}")
    print(f"  - 平均响应时间: {stats['avg_response_time_ms']}ms")
    
    await audit_logger.stop_batch_writer()
    audit_logger.close()


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("MCP 资源公开访问功能测试")
    print("=" * 60)
    
    try:
        await test_database_initialization()
        await test_api_key_generation()
        await test_access_control()
        await test_rate_limiter()
        await test_audit_logger()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
