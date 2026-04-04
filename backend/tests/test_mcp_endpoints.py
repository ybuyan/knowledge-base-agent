"""
测试 MCP 端点功能

测试：
1. 公开资源列表
2. 使用 API Key 访问资源
3. 管理员创建 API Key
"""
import asyncio
import httpx
from app.mcp.api_key_manager import APIKeyManager


async def test_public_resources():
    """测试公开资源列表"""
    print("\n=== 测试 1: 公开资源列表 ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/mcp/public/resources")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 获取公开资源成功，共 {len(data['resources'])} 个资源:")
            for resource in data['resources']:
                print(f"  - {resource['name']}: {resource['uri']}")
        else:
            print(f"✗ 获取公开资源失败: {response.status_code}")


async def test_mcp_with_api_key():
    """测试使用 API Key 访问 MCP 资源"""
    print("\n=== 测试 2: 使用 API Key 访问 MCP 资源 ===")
    
    # 创建一个测试 API Key
    manager = APIKeyManager()
    api_key = await manager.generate_api_key(
        user_id="test_mcp_user",
        username="Test MCP User",
        role="employee",
        permissions=[],
        rate_limit=100,
        expires_days=1,
        description="测试 MCP 访问"
    )
    print(f"✓ 创建测试 API Key: {api_key.key[:20]}...")
    
    # 使用 API Key 访问 MCP 端点
    async with httpx.AsyncClient() as client:
        # 测试 resources/list
        print("\n测试 resources/list...")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "resources/list",
                "params": {}
            },
            headers={"X-API-Key": api_key.key}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                resources = data["result"]["resources"]
                print(f"✓ Employee 用户可访问 {len(resources)} 个资源:")
                for resource in resources[:5]:  # 只显示前5个
                    print(f"  - {resource['name']}: {resource['uri']}")
            else:
                print(f"✗ 响应格式错误: {data}")
        else:
            print(f"✗ 请求失败: {response.status_code}")
        
        # 测试 resources/read (公开资源)
        print("\n测试 resources/read (公开资源)...")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/read",
                "params": {"uri": "knowledge://public/faq"}
            },
            headers={"X-API-Key": api_key.key}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                content = data["result"]["contents"][0]["text"]
                print(f"✓ 读取公开资源成功:")
                print(f"  {content[:100]}...")
            else:
                print(f"✗ 响应格式错误: {data}")
        else:
            print(f"✗ 请求失败: {response.status_code}")
        
        # 测试 resources/read (内部资源)
        print("\n测试 resources/read (内部资源)...")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "resources/read",
                "params": {"uri": "knowledge://internal/policy"}
            },
            headers={"X-API-Key": api_key.key}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                content = data["result"]["contents"][0]["text"]
                print(f"✓ 读取内部资源成功:")
                print(f"  {content[:100]}...")
            else:
                print(f"✗ 响应格式错误: {data}")
        else:
            print(f"✗ 请求失败: {response.status_code}")
        
        # 测试 resources/read (机密资源 - 应该被拒绝)
        print("\n测试 resources/read (机密资源 - 应该被拒绝)...")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {"uri": "knowledge://confidential/salary"}
            },
            headers={"X-API-Key": api_key.key}
        )
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"✓ 正确拒绝访问机密资源: {data['error']['message']}")
            else:
                print(f"✗ 应该拒绝访问但没有: {data}")
        else:
            print(f"✗ 请求失败: {response.status_code}")
    
    # 清理测试 API Key
    await manager.revoke_api_key(api_key.key)
    manager.close()


async def test_guest_access():
    """测试 guest 用户访问"""
    print("\n=== 测试 3: Guest 用户访问 ===")
    
    async with httpx.AsyncClient() as client:
        # 不提供 API Key，应该以 guest 身份访问
        print("\n测试 resources/list (无 API Key)...")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "resources/list",
                "params": {}
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if "result" in data:
                resources = data["result"]["resources"]
                print(f"✓ Guest 用户可访问 {len(resources)} 个资源:")
                for resource in resources:
                    print(f"  - {resource['name']}: {resource['uri']}")
            else:
                print(f"✗ 响应格式错误: {data}")
        else:
            print(f"✗ 请求失败: {response.status_code}")
        
        # 尝试访问内部资源（应该被拒绝）
        print("\n测试 resources/read (内部资源 - 应该被拒绝)...")
        response = await client.post(
            "http://localhost:8000/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "resources/read",
                "params": {"uri": "knowledge://internal/policy"}
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"✓ 正确拒绝 guest 访问内部资源: {data['error']['message']}")
            else:
                print(f"✗ 应该拒绝访问但没有: {data}")
        else:
            print(f"✗ 请求失败: {response.status_code}")


async def main():
    """运行所有测试"""
    print("=" * 60)
    print("MCP 端点功能测试")
    print("=" * 60)
    
    try:
        await test_public_resources()
        await test_mcp_with_api_key()
        await test_guest_access()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
    
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
