"""
资源访问控制模块

负责检查用户对特定资源的访问权限
"""
from enum import Enum
from typing import Optional

from app.mcp.auth_middleware import AuthContext
from app.mcp.base import MCPResource


class ResourceLevel(str, Enum):
    """资源访问级别"""
    PUBLIC = "public"        # 公开：任何人可访问
    INTERNAL = "internal"    # 内部：需要员工角色
    CONFIDENTIAL = "confidential"  # 机密：需要特殊权限


class ResourceAccessControl:
    """资源访问控制"""
    
    def parse_resource_level(self, uri: str) -> ResourceLevel:
        """
        从资源 URI 解析访问级别
        
        URI 格式约定：
        - knowledge://public/* -> PUBLIC
        - knowledge://internal/* -> INTERNAL
        - knowledge://confidential/* -> CONFIDENTIAL
        - document://public/* -> PUBLIC
        - document://internal/* -> INTERNAL
        - document://confidential/* -> CONFIDENTIAL
        
        默认: INTERNAL
        
        Args:
            uri: 资源 URI
        
        Returns:
            ResourceLevel: 资源访问级别
        """
        uri_lower = uri.lower()
        
        # 检查 URI 中是否包含级别关键字
        if "/public/" in uri_lower or uri_lower.endswith("/public"):
            return ResourceLevel.PUBLIC
        elif "/confidential/" in uri_lower or uri_lower.endswith("/confidential"):
            return ResourceLevel.CONFIDENTIAL
        elif "/internal/" in uri_lower or uri_lower.endswith("/internal"):
            return ResourceLevel.INTERNAL
        
        # 默认为内部级别
        return ResourceLevel.INTERNAL
    
    def check_access(self, uri: str, auth_context: AuthContext) -> bool:
        """
        检查用户是否有权访问指定资源
        
        访问规则：
        - PUBLIC: 所有用户可访问
        - INTERNAL: role in [employee, admin]
        - CONFIDENTIAL: "read:confidential" in permissions
        
        Args:
            uri: 资源 URI
            auth_context: 认证上下文
        
        Returns:
            bool: True 允许访问, False 拒绝访问
        """
        # 解析资源级别
        level = self.parse_resource_level(uri)
        
        # 公开资源：所有人可访问
        if level == ResourceLevel.PUBLIC:
            return True
        
        # 内部资源：需要员工或管理员角色
        if level == ResourceLevel.INTERNAL:
            return auth_context.role in ["employee", "admin"]
        
        # 机密资源：需要特殊权限
        if level == ResourceLevel.CONFIDENTIAL:
            # 管理员默认有所有权限
            if auth_context.role == "admin":
                return True
            # 检查是否有机密访问权限
            return "read:confidential" in auth_context.permissions
        
        # 默认拒绝访问
        return False
    
    def filter_resources(
        self, 
        resources: list[MCPResource], 
        auth_context: AuthContext
    ) -> list[MCPResource]:
        """
        根据用户权限过滤资源列表
        只返回用户有权访问的资源
        
        Args:
            resources: 资源列表
            auth_context: 认证上下文
        
        Returns:
            list[MCPResource]: 过滤后的资源列表
        """
        filtered = []
        
        for resource in resources:
            if self.check_access(resource.uri, auth_context):
                filtered.append(resource)
        
        return filtered
    
    def get_accessible_levels(self, auth_context: AuthContext) -> list[ResourceLevel]:
        """
        获取用户可访问的资源级别列表
        
        Args:
            auth_context: 认证上下文
        
        Returns:
            list[ResourceLevel]: 可访问的资源级别列表
        """
        levels = [ResourceLevel.PUBLIC]  # 所有人都可以访问公开资源
        
        # 员工和管理员可以访问内部资源
        if auth_context.role in ["employee", "admin"]:
            levels.append(ResourceLevel.INTERNAL)
        
        # 有特殊权限或管理员可以访问机密资源
        if auth_context.role == "admin" or "read:confidential" in auth_context.permissions:
            levels.append(ResourceLevel.CONFIDENTIAL)
        
        return levels
    
    def can_write_resource(self, uri: str, auth_context: AuthContext) -> bool:
        """
        检查用户是否有权写入指定资源
        
        写入规则：
        - PUBLIC: 需要 "write:public" 权限或 admin 角色
        - INTERNAL: 需要 "write:internal" 权限或 admin 角色
        - CONFIDENTIAL: 需要 "write:confidential" 权限或 admin 角色
        
        Args:
            uri: 资源 URI
            auth_context: 认证上下文
        
        Returns:
            bool: True 允许写入, False 拒绝写入
        """
        # 管理员默认有所有写入权限
        if auth_context.role == "admin":
            return True
        
        # 解析资源级别
        level = self.parse_resource_level(uri)
        
        # 检查对应的写入权限
        if level == ResourceLevel.PUBLIC:
            return "write:public" in auth_context.permissions
        elif level == ResourceLevel.INTERNAL:
            return "write:internal" in auth_context.permissions
        elif level == ResourceLevel.CONFIDENTIAL:
            return "write:confidential" in auth_context.permissions
        
        # 默认拒绝写入
        return False
