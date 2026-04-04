"""
API Key 管理模块

负责 API Key 的生成、验证、撤销等操作
"""
import secrets
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings


class APIKey(BaseModel):
    """API Key 数据模型"""
    key: str = Field(..., description="API Key，格式: mcp_<64位十六进制>")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    role: str = Field(..., description="用户角色: guest, employee, admin")
    permissions: list[str] = Field(default_factory=list, description="特殊权限列表")
    rate_limit: int = Field(..., description="每分钟请求限制")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间，None 表示永不过期")
    is_active: bool = Field(True, description="是否激活")
    last_used_at: Optional[datetime] = Field(None, description="最后使用时间")
    description: str = Field("", description="API Key 用途描述")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class APIKeyManager:
    """API Key 管理器"""
    
    def __init__(self, mongo_client: Optional[AsyncIOMotorClient] = None):
        """
        初始化 API Key 管理器
        
        Args:
            mongo_client: MongoDB 客户端，如果为 None 则创建新连接
        """
        if mongo_client is None:
            self.client = AsyncIOMotorClient(settings.mongo_url)
            self._own_client = True
        else:
            self.client = mongo_client
            self._own_client = False
        
        self.db = self.client[settings.mongo_db_name]
        self.collection = self.db["api_keys"]
    
    async def generate_api_key(
        self,
        user_id: str,
        username: str,
        role: str,
        permissions: Optional[list[str]] = None,
        rate_limit: Optional[int] = None,
        expires_days: Optional[int] = None,
        description: str = ""
    ) -> APIKey:
        """
        生成新的 API Key
        
        Args:
            user_id: 用户ID
            username: 用户名
            role: 用户角色 (guest, employee, admin)
            permissions: 特殊权限列表
            rate_limit: 每分钟请求限制，None 使用默认值
            expires_days: 过期天数，None 表示永不过期
            description: API Key 用途描述
        
        Returns:
            APIKey: 生成的 API Key 对象
        
        Raises:
            ValueError: 如果角色不合法
        """
        # 验证角色
        if role not in ["guest", "employee", "admin"]:
            raise ValueError(f"Invalid role: {role}. Must be one of: guest, employee, admin")
        
        # 使用默认值
        if permissions is None:
            permissions = []
        if rate_limit is None:
            rate_limit = settings.api_key_default_rate_limit
        
        # 生成安全的随机密钥
        while True:
            # 生成 32 字节 (256 位) 的随机数据
            random_bytes = secrets.token_bytes(32)
            # 转换为 64 位十六进制字符串
            key_suffix = random_bytes.hex()
            key = f"{settings.api_key_prefix}{key_suffix}"
            
            # 检查密钥唯一性
            existing = await self.collection.find_one({"key": key})
            if not existing:
                break
        
        # 计算过期时间
        created_at = datetime.utcnow()
        expires_at = None
        if expires_days is not None and expires_days > 0:
            expires_at = created_at + timedelta(days=expires_days)
        
        # 创建 API Key 对象
        api_key = APIKey(
            key=key,
            user_id=user_id,
            username=username,
            role=role,
            permissions=permissions,
            rate_limit=rate_limit,
            created_at=created_at,
            expires_at=expires_at,
            is_active=True,
            last_used_at=None,
            description=description
        )
        
        # 保存到数据库
        await self.collection.insert_one(api_key.model_dump())
        
        return api_key
    
    async def validate_api_key(self, key: str) -> Optional[APIKey]:
        """
        验证 API Key 并返回关联信息
        
        检查:
        - Key 是否存在
        - 是否已过期
        - 是否被撤销
        
        副作用: 更新 last_used_at
        
        Args:
            key: API Key 字符串
        
        Returns:
            APIKey: 如果有效返回 API Key 对象，否则返回 None
        """
        # 查询数据库
        doc = await self.collection.find_one({"key": key})
        if not doc:
            return None
        
        api_key = APIKey(**doc)
        
        # 检查是否激活
        if not api_key.is_active:
            return None
        
        # 检查是否过期
        if api_key.expires_at is not None:
            if datetime.utcnow() > api_key.expires_at:
                return None
        
        # 更新最后使用时间
        await self.collection.update_one(
            {"key": key},
            {"$set": {"last_used_at": datetime.utcnow()}}
        )
        
        return api_key
    
    async def revoke_api_key(self, key: str) -> bool:
        """
        撤销 API Key
        
        Args:
            key: API Key 字符串
        
        Returns:
            bool: 成功返回 True，Key 不存在返回 False
        """
        result = await self.collection.update_one(
            {"key": key},
            {"$set": {"is_active": False}}
        )
        
        return result.modified_count > 0
    
    async def list_user_api_keys(self, user_id: str) -> list[APIKey]:
        """
        列出用户的所有 API Keys
        
        Args:
            user_id: 用户ID
        
        Returns:
            list[APIKey]: API Key 列表
        """
        cursor = self.collection.find({"user_id": user_id})
        api_keys = []
        
        async for doc in cursor:
            api_keys.append(APIKey(**doc))
        
        return api_keys
    
    async def cleanup_expired_keys(self) -> int:
        """
        清理过期的 API Keys
        
        注意: MongoDB TTL 索引会自动清理过期记录，
        此方法用于手动清理或在没有 TTL 索引时使用
        
        Returns:
            int: 清理的数量
        """
        current_time = datetime.utcnow()
        
        result = await self.collection.delete_many({
            "expires_at": {"$ne": None, "$lt": current_time}
        })
        
        return result.deleted_count
    
    def close(self):
        """关闭数据库连接"""
        if self._own_client:
            self.client.close()
