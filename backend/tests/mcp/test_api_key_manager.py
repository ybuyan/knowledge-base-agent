"""
API Key Manager 单元测试

测试 API Key 的生成、验证、撤销等功能
"""
import pytest
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

from app.mcp.api_key_manager import APIKey, APIKeyManager
from app.config import settings


@pytest.fixture
async def mongo_client():
    """创建测试用 MongoDB 客户端"""
    client = AsyncIOMotorClient(settings.mongo_url)
    yield client
    client.close()


@pytest.fixture
async def api_key_manager(mongo_client):
    """创建测试用 API Key Manager"""
    manager = APIKeyManager(mongo_client)
    
    # 清理测试数据
    await manager.collection.delete_many({})
    
    yield manager
    
    # 清理测试数据
    await manager.collection.delete_many({})


class TestAPIKeyGeneration:
    """测试 API Key 生成功能"""
    
    @pytest.mark.asyncio
    async def test_generate_api_key_basic(self, api_key_manager):
        """测试基本的 API Key 生成"""
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee"
        )
        
        # 验证格式
        assert api_key.key.startswith(settings.api_key_prefix)
        assert len(api_key.key) == len(settings.api_key_prefix) + 64  # prefix + 64 hex chars
        
        # 验证字段
        assert api_key.user_id == "user123"
        assert api_key.username == "testuser"
        assert api_key.role == "employee"
        assert api_key.is_active is True
        assert api_key.rate_limit == settings.api_key_default_rate_limit
        assert api_key.expires_at is None  # 默认不过期
        assert api_key.last_used_at is None
    
    @pytest.mark.asyncio
    async def test_generate_api_key_with_expiration(self, api_key_manager):
        """测试生成带过期时间的 API Key"""
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee",
            expires_days=30
        )
        
        # 验证过期时间
        assert api_key.expires_at is not None
        expected_expiry = datetime.utcnow() + timedelta(days=30)
        # 允许 1 秒误差
        assert abs((api_key.expires_at - expected_expiry).total_seconds()) < 1
    
    @pytest.mark.asyncio
    async def test_generate_api_key_with_custom_rate_limit(self, api_key_manager):
        """测试生成自定义速率限制的 API Key"""
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="admin",
            rate_limit=500
        )
        
        assert api_key.rate_limit == 500
    
    @pytest.mark.asyncio
    async def test_generate_api_key_with_permissions(self, api_key_manager):
        """测试生成带特殊权限的 API Key"""
        permissions = ["read:confidential", "write:internal"]
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee",
            permissions=permissions
        )
        
        assert api_key.permissions == permissions
    
    @pytest.mark.asyncio
    async def test_generate_api_key_with_description(self, api_key_manager):
        """测试生成带描述的 API Key"""
        description = "用于测试环境的 API Key"
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee",
            description=description
        )
        
        assert api_key.description == description
    
    @pytest.mark.asyncio
    async def test_generate_api_key_uniqueness(self, api_key_manager):
        """测试生成的 API Key 唯一性"""
        keys = set()
        
        # 生成 100 个 API Key
        for i in range(100):
            api_key = await api_key_manager.generate_api_key(
                user_id=f"user{i}",
                username=f"testuser{i}",
                role="employee"
            )
            keys.add(api_key.key)
        
        # 验证所有 Key 都是唯一的
        assert len(keys) == 100
    
    @pytest.mark.asyncio
    async def test_generate_api_key_invalid_role(self, api_key_manager):
        """测试使用无效角色生成 API Key"""
        with pytest.raises(ValueError, match="Invalid role"):
            await api_key_manager.generate_api_key(
                user_id="user123",
                username="testuser",
                role="invalid_role"
            )
    
    @pytest.mark.asyncio
    async def test_generate_api_key_all_roles(self, api_key_manager):
        """测试所有有效角色"""
        roles = ["guest", "employee", "admin"]
        
        for role in roles:
            api_key = await api_key_manager.generate_api_key(
                user_id=f"user_{role}",
                username=f"testuser_{role}",
                role=role
            )
            assert api_key.role == role


class TestAPIKeyValidation:
    """测试 API Key 验证功能"""
    
    @pytest.mark.asyncio
    async def test_validate_valid_api_key(self, api_key_manager):
        """测试验证有效的 API Key"""
        # 生成 API Key
        generated_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee"
        )
        
        # 验证
        validated_key = await api_key_manager.validate_api_key(generated_key.key)
        
        assert validated_key is not None
        assert validated_key.key == generated_key.key
        assert validated_key.user_id == "user123"
        assert validated_key.username == "testuser"
        assert validated_key.role == "employee"
    
    @pytest.mark.asyncio
    async def test_validate_nonexistent_api_key(self, api_key_manager):
        """测试验证不存在的 API Key"""
        fake_key = f"{settings.api_key_prefix}{'0' * 64}"
        validated_key = await api_key_manager.validate_api_key(fake_key)
        
        assert validated_key is None
    
    @pytest.mark.asyncio
    async def test_validate_expired_api_key(self, api_key_manager):
        """测试验证已过期的 API Key"""
        # 生成一个已过期的 API Key（过期时间设为过去）
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee",
            expires_days=1
        )
        
        # 手动设置为已过期
        await api_key_manager.collection.update_one(
            {"key": api_key.key},
            {"$set": {"expires_at": datetime.utcnow() - timedelta(days=1)}}
        )
        
        # 验证
        validated_key = await api_key_manager.validate_api_key(api_key.key)
        
        assert validated_key is None
    
    @pytest.mark.asyncio
    async def test_validate_revoked_api_key(self, api_key_manager):
        """测试验证已撤销的 API Key"""
        # 生成 API Key
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee"
        )
        
        # 撤销
        await api_key_manager.revoke_api_key(api_key.key)
        
        # 验证
        validated_key = await api_key_manager.validate_api_key(api_key.key)
        
        assert validated_key is None
    
    @pytest.mark.asyncio
    async def test_validate_updates_last_used_at(self, api_key_manager):
        """测试验证时更新 last_used_at"""
        # 生成 API Key
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee"
        )
        
        assert api_key.last_used_at is None
        
        # 第一次验证
        validated_key = await api_key_manager.validate_api_key(api_key.key)
        assert validated_key is not None
        
        # 从数据库读取，验证 last_used_at 已更新
        doc = await api_key_manager.collection.find_one({"key": api_key.key})
        assert doc["last_used_at"] is not None
        first_used_at = doc["last_used_at"]
        
        # 等待一小段时间
        import asyncio
        await asyncio.sleep(0.1)
        
        # 第二次验证
        await api_key_manager.validate_api_key(api_key.key)
        
        # 验证 last_used_at 已更新
        doc = await api_key_manager.collection.find_one({"key": api_key.key})
        second_used_at = doc["last_used_at"]
        assert second_used_at > first_used_at


class TestAPIKeyRevocation:
    """测试 API Key 撤销功能"""
    
    @pytest.mark.asyncio
    async def test_revoke_existing_api_key(self, api_key_manager):
        """测试撤销存在的 API Key"""
        # 生成 API Key
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee"
        )
        
        # 撤销
        result = await api_key_manager.revoke_api_key(api_key.key)
        
        assert result is True
        
        # 验证已撤销
        doc = await api_key_manager.collection.find_one({"key": api_key.key})
        assert doc["is_active"] is False
    
    @pytest.mark.asyncio
    async def test_revoke_nonexistent_api_key(self, api_key_manager):
        """测试撤销不存在的 API Key"""
        fake_key = f"{settings.api_key_prefix}{'0' * 64}"
        result = await api_key_manager.revoke_api_key(fake_key)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_revoke_already_revoked_api_key(self, api_key_manager):
        """测试撤销已经撤销的 API Key"""
        # 生成 API Key
        api_key = await api_key_manager.generate_api_key(
            user_id="user123",
            username="testuser",
            role="employee"
        )
        
        # 第一次撤销
        result1 = await api_key_manager.revoke_api_key(api_key.key)
        assert result1 is True
        
        # 第二次撤销
        result2 = await api_key_manager.revoke_api_key(api_key.key)
        assert result2 is False  # 没有修改任何文档


class TestAPIKeyListing:
    """测试 API Key 列表功能"""
    
    @pytest.mark.asyncio
    async def test_list_user_api_keys(self, api_key_manager):
        """测试列出用户的 API Keys"""
        user_id = "user123"
        
        # 生成多个 API Keys
        for i in range(3):
            await api_key_manager.generate_api_key(
                user_id=user_id,
                username="testuser",
                role="employee",
                description=f"Key {i}"
            )
        
        # 列出
        api_keys = await api_key_manager.list_user_api_keys(user_id)
        
        assert len(api_keys) == 3
        assert all(key.user_id == user_id for key in api_keys)
    
    @pytest.mark.asyncio
    async def test_list_user_api_keys_empty(self, api_key_manager):
        """测试列出不存在用户的 API Keys"""
        api_keys = await api_key_manager.list_user_api_keys("nonexistent_user")
        
        assert len(api_keys) == 0
    
    @pytest.mark.asyncio
    async def test_list_user_api_keys_multiple_users(self, api_key_manager):
        """测试多用户场景下列出 API Keys"""
        # 为不同用户生成 API Keys
        await api_key_manager.generate_api_key(
            user_id="user1",
            username="testuser1",
            role="employee"
        )
        await api_key_manager.generate_api_key(
            user_id="user2",
            username="testuser2",
            role="employee"
        )
        await api_key_manager.generate_api_key(
            user_id="user1",
            username="testuser1",
            role="employee"
        )
        
        # 列出 user1 的 Keys
        user1_keys = await api_key_manager.list_user_api_keys("user1")
        assert len(user1_keys) == 2
        
        # 列出 user2 的 Keys
        user2_keys = await api_key_manager.list_user_api_keys("user2")
        assert len(user2_keys) == 1


class TestAPIKeyCleanup:
    """测试 API Key 清理功能"""
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_keys(self, api_key_manager):
        """测试清理过期的 API Keys"""
        # 生成一个已过期的 Key
        expired_key = await api_key_manager.generate_api_key(
            user_id="user1",
            username="testuser1",
            role="employee",
            expires_days=1
        )
        await api_key_manager.collection.update_one(
            {"key": expired_key.key},
            {"$set": {"expires_at": datetime.utcnow() - timedelta(days=1)}}
        )
        
        # 生成一个有效的 Key
        valid_key = await api_key_manager.generate_api_key(
            user_id="user2",
            username="testuser2",
            role="employee",
            expires_days=30
        )
        
        # 生成一个永不过期的 Key
        permanent_key = await api_key_manager.generate_api_key(
            user_id="user3",
            username="testuser3",
            role="employee"
        )
        
        # 清理
        deleted_count = await api_key_manager.cleanup_expired_keys()
        
        assert deleted_count == 1
        
        # 验证只有过期的被删除
        assert await api_key_manager.collection.find_one({"key": expired_key.key}) is None
        assert await api_key_manager.collection.find_one({"key": valid_key.key}) is not None
        assert await api_key_manager.collection.find_one({"key": permanent_key.key}) is not None
    
    @pytest.mark.asyncio
    async def test_cleanup_no_expired_keys(self, api_key_manager):
        """测试没有过期 Keys 时的清理"""
        # 生成一些有效的 Keys
        for i in range(3):
            await api_key_manager.generate_api_key(
                user_id=f"user{i}",
                username=f"testuser{i}",
                role="employee"
            )
        
        # 清理
        deleted_count = await api_key_manager.cleanup_expired_keys()
        
        assert deleted_count == 0


class TestAPIKeyModel:
    """测试 APIKey 数据模型"""
    
    def test_api_key_model_creation(self):
        """测试 APIKey 模型创建"""
        api_key = APIKey(
            key="mcp_test123",
            user_id="user123",
            username="testuser",
            role="employee",
            rate_limit=100
        )
        
        assert api_key.key == "mcp_test123"
        assert api_key.user_id == "user123"
        assert api_key.username == "testuser"
        assert api_key.role == "employee"
        assert api_key.rate_limit == 100
        assert api_key.is_active is True
        assert api_key.permissions == []
        assert api_key.description == ""
    
    def test_api_key_model_json_serialization(self):
        """测试 APIKey 模型 JSON 序列化"""
        api_key = APIKey(
            key="mcp_test123",
            user_id="user123",
            username="testuser",
            role="employee",
            rate_limit=100,
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        json_data = api_key.model_dump()
        
        assert json_data["key"] == "mcp_test123"
        assert json_data["user_id"] == "user123"
        assert isinstance(json_data["created_at"], datetime)
