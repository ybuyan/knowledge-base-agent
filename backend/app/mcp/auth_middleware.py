"""
认证中间件模块

负责拦截所有 MCP 请求，验证 API Key 或 OAuth2 Token，构建认证上下文
"""
from typing import Optional
from fastapi import Request, HTTPException, status
from pydantic import BaseModel

from app.mcp.api_key_manager import APIKeyManager


class AuthContext(BaseModel):
    """认证上下文，包含用户身份和权限信息"""
    user_id: str
    username: str
    role: str  # guest, employee, admin
    permissions: list[str]  # 特殊权限列表
    rate_limit: int  # 每分钟请求限制
    api_key: str  # 脱敏后的 API Key (前8位)


class MCPAuthMiddleware:
    """MCP 认证中间件"""
    
    def __init__(self, api_key_manager: APIKeyManager):
        """
        初始化认证中间件
        
        Args:
            api_key_manager: API Key 管理器实例
        """
        self.api_key_manager = api_key_manager
    
    async def authenticate_request(self, request: Request) -> AuthContext:
        """
        从请求中提取认证信息并验证
        
        支持两种认证方式：
        1. API Key: Header X-API-Key
        2. OAuth2: Header Authorization: Bearer <token>
        
        如果没有提供认证信息，返回 guest 上下文
        
        Args:
            request: FastAPI 请求对象
        
        Returns:
            AuthContext: 认证上下文
        
        Raises:
            HTTPException: 401 如果认证失败
        """
        # 尝试从 Header 提取 API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            auth_context = await self.validate_api_key(api_key)
            if auth_context:
                return auth_context
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired API Key"
                )
        
        # 尝试从 Header 提取 OAuth2 Token
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]  # 移除 "Bearer " 前缀
            auth_context = await self.validate_oauth_token(token)
            if auth_context:
                return auth_context
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired OAuth2 token"
                )
        
        # 没有提供认证信息，返回 guest 上下文
        return self.create_guest_context()
    
    async def validate_api_key(self, api_key: str) -> Optional[AuthContext]:
        """
        验证 API Key 并返回用户信息
        
        Args:
            api_key: API Key 字符串
        
        Returns:
            AuthContext: 如果有效返回认证上下文，否则返回 None
        """
        # 使用 APIKeyManager 验证
        api_key_obj = await self.api_key_manager.validate_api_key(api_key)
        
        if api_key_obj is None:
            return None
        
        # 构建认证上下文
        return AuthContext(
            user_id=api_key_obj.user_id,
            username=api_key_obj.username,
            role=api_key_obj.role,
            permissions=api_key_obj.permissions,
            rate_limit=api_key_obj.rate_limit,
            api_key=self._mask_api_key(api_key)
        )
    
    async def validate_oauth_token(self, token: str) -> Optional[AuthContext]:
        """
        验证 OAuth2 Token 并返回用户信息
        
        注意: 此功能为可选实现，当前版本返回 None
        
        Args:
            token: OAuth2 JWT Token
        
        Returns:
            AuthContext: 如果有效返回认证上下文，否则返回 None
        """
        # TODO: 实现 OAuth2 Token 验证
        # 1. 解析 JWT Token
        # 2. 验证签名
        # 3. 检查过期时间
        # 4. 提取用户信息
        # 5. 构建 AuthContext
        
        return None
    
    def create_guest_context(self) -> AuthContext:
        """
        创建 guest 用户上下文
        
        Guest 用户只能访问公开资源，有较低的速率限制
        
        Returns:
            AuthContext: Guest 用户的认证上下文
        """
        return AuthContext(
            user_id="guest",
            username="Guest User",
            role="guest",
            permissions=[],
            rate_limit=30,  # Guest 用户每分钟 30 次请求
            api_key="guest"
        )
    
    def _mask_api_key(self, api_key: str) -> str:
        """
        脱敏 API Key，只保留前 8 位
        
        Args:
            api_key: 完整的 API Key
        
        Returns:
            str: 脱敏后的 API Key
        """
        if len(api_key) <= 8:
            return api_key
        return api_key[:8] + "..." + api_key[-4:]
