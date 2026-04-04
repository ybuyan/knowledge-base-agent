"""
审计日志模块

负责记录所有 MCP 访问行为到 MongoDB
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import Request

from app.mcp.auth_middleware import AuthContext
from app.config import settings


class AuditEvent(BaseModel):
    """审计事件"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="事件时间")
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    api_key: str = Field(..., description="脱敏后的 API Key")
    method: str = Field(..., description="JSON-RPC 方法名")
    resource_uri: Optional[str] = Field(None, description="访问的资源 URI")
    tool_name: Optional[str] = Field(None, description="调用的工具名")
    success: bool = Field(..., description="是否成功")
    error_code: Optional[int] = Field(None, description="错误码")
    error_message: Optional[str] = Field(None, description="错误信息")
    ip_address: str = Field(..., description="客户端 IP 地址")
    user_agent: str = Field(..., description="User-Agent")
    response_time_ms: int = Field(..., description="响应时间（毫秒）")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, mongo_client: Optional[AsyncIOMotorClient] = None):
        """
        初始化审计日志记录器
        
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
        self.collection = self.db["audit_logs"]
        
        # 异步批量写入队列
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self.batch_task: Optional[asyncio.Task] = None
        self._running = False
    
    def start_batch_writer(self):
        """启动后台批量写入任务"""
        if not self._running:
            self._running = True
            self.batch_task = asyncio.create_task(self._batch_write_loop())
    
    async def stop_batch_writer(self):
        """停止后台批量写入任务"""
        self._running = False
        if self.batch_task:
            await self.batch_task
    
    async def _batch_write_loop(self):
        """后台批量写入循环"""
        batch = []
        last_write_time = datetime.utcnow()
        
        while self._running or not self.event_queue.empty():
            try:
                # 尝试从队列获取事件，超时时间为批量超时
                timeout = settings.audit_log_batch_timeout
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=timeout
                )
                batch.append(event.model_dump())
                
                # 检查是否达到批量大小或超时
                current_time = datetime.utcnow()
                time_elapsed = (current_time - last_write_time).total_seconds()
                
                if len(batch) >= settings.audit_log_batch_size or time_elapsed >= timeout:
                    await self._write_batch(batch)
                    batch = []
                    last_write_time = current_time
            
            except asyncio.TimeoutError:
                # 超时，写入当前批次
                if batch:
                    await self._write_batch(batch)
                    batch = []
                    last_write_time = datetime.utcnow()
            
            except Exception as e:
                # 记录错误但不中断循环
                print(f"Error in batch write loop: {e}")
        
        # 写入剩余的事件
        if batch:
            await self._write_batch(batch)
    
    async def _write_batch(self, batch: list[dict]):
        """批量写入事件到 MongoDB"""
        if not batch:
            return
        
        try:
            await self.collection.insert_many(batch, ordered=False)
        except Exception as e:
            print(f"Error writing audit log batch: {e}")
    
    async def log_access(
        self,
        auth_context: AuthContext,
        method: str,
        resource_uri: Optional[str],
        tool_name: Optional[str],
        success: bool,
        error_code: Optional[int],
        error_message: Optional[str],
        request: Request,
        response_time_ms: int
    ) -> None:
        """
        记录访问事件到 MongoDB audit_logs 集合
        
        Args:
            auth_context: 认证上下文
            method: JSON-RPC 方法名
            resource_uri: 访问的资源 URI
            tool_name: 调用的工具名
            success: 是否成功
            error_code: 错误码
            error_message: 错误信息
            request: FastAPI 请求对象
            response_time_ms: 响应时间（毫秒）
        """
        # 提取客户端信息
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        # 创建审计事件
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            user_id=auth_context.user_id,
            username=auth_context.username,
            api_key=auth_context.api_key,
            method=method,
            resource_uri=resource_uri,
            tool_name=tool_name,
            success=success,
            error_code=error_code,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            response_time_ms=response_time_ms
        )
        
        # 添加到队列（异步批量写入）
        try:
            self.event_queue.put_nowait(event)
        except asyncio.QueueFull:
            # 队列满，直接写入
            await self.collection.insert_one(event.model_dump())
    
    async def log_failed_auth(
        self,
        api_key: str,
        request: Request,
        error_message: str
    ) -> None:
        """
        记录认证失败事件
        
        Args:
            api_key: 失败的 API Key（脱敏）
            request: FastAPI 请求对象
            error_message: 错误信息
        """
        # 提取客户端信息
        ip_address = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "Unknown")
        
        # 创建审计事件
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            user_id="unknown",
            username="Unknown",
            api_key=self._mask_api_key(api_key),
            method="authentication",
            resource_uri=None,
            tool_name=None,
            success=False,
            error_code=401,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
            response_time_ms=0
        )
        
        # 认证失败事件直接写入（不使用批量）
        await self.collection.insert_one(event.model_dump())
    
    async def get_user_access_history(
        self,
        user_id: str,
        limit: int = 100
    ) -> list[AuditEvent]:
        """
        查询用户访问历史
        
        Args:
            user_id: 用户ID
            limit: 返回记录数量限制
        
        Returns:
            list[AuditEvent]: 审计事件列表，按时间倒序
        """
        cursor = self.collection.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit)
        
        events = []
        async for doc in cursor:
            events.append(AuditEvent(**doc))
        
        return events
    
    async def get_resource_access_stats(
        self,
        resource_uri: str,
        days: int = 7
    ) -> dict:
        """
        获取资源访问统计
        
        Args:
            resource_uri: 资源 URI
            days: 统计天数
        
        Returns:
            dict: 统计信息
                - total_accesses: 总访问次数
                - successful_accesses: 成功访问次数
                - failed_accesses: 失败访问次数
                - unique_users: 唯一用户数
                - avg_response_time_ms: 平均响应时间
        """
        # 计算时间范围
        start_time = datetime.utcnow() - timedelta(days=days)
        
        # 聚合查询
        pipeline = [
            {
                "$match": {
                    "resource_uri": resource_uri,
                    "timestamp": {"$gte": start_time}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_accesses": {"$sum": 1},
                    "successful_accesses": {
                        "$sum": {"$cond": ["$success", 1, 0]}
                    },
                    "failed_accesses": {
                        "$sum": {"$cond": ["$success", 0, 1]}
                    },
                    "unique_users": {"$addToSet": "$user_id"},
                    "avg_response_time_ms": {"$avg": "$response_time_ms"}
                }
            }
        ]
        
        result = await self.collection.aggregate(pipeline).to_list(length=1)
        
        if not result:
            return {
                "total_accesses": 0,
                "successful_accesses": 0,
                "failed_accesses": 0,
                "unique_users": 0,
                "avg_response_time_ms": 0
            }
        
        stats = result[0]
        return {
            "total_accesses": stats["total_accesses"],
            "successful_accesses": stats["successful_accesses"],
            "failed_accesses": stats["failed_accesses"],
            "unique_users": len(stats["unique_users"]),
            "avg_response_time_ms": int(stats["avg_response_time_ms"])
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端 IP 地址
        
        优先从 X-Forwarded-For 获取（支持代理）
        
        Args:
            request: FastAPI 请求对象
        
        Returns:
            str: 客户端 IP 地址
        """
        # 尝试从 X-Forwarded-For 获取
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For 可能包含多个 IP，取第一个
            return forwarded_for.split(",")[0].strip()
        
        # 尝试从 X-Real-IP 获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 使用直接连接的 IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
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
    
    def close(self):
        """关闭数据库连接"""
        if self._own_client:
            self.client.close()
