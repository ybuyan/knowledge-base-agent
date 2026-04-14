"""
速率限制模块

防止 API 滥用和 DDoS 攻击，使用滑动窗口算法
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings


class RateLimitExceeded(Exception):
    """速率限制超出异常"""

    def __init__(self, user_id: str, retry_after: int):
        """
        初始化异常

        Args:
            user_id: 用户ID
            retry_after: 多少秒后可以重试
        """
        self.user_id = user_id
        self.retry_after = retry_after
        super().__init__(
            f"Rate limit exceeded for user {user_id}. Retry after {retry_after} seconds."
        )


class RateLimiter:
    """速率限制器（基于滑动窗口算法）"""

    def __init__(
        self, mongo_client: Optional[AsyncIOMotorClient] = None, use_redis: bool = False
    ):
        """
        初始化速率限制器

        Args:
            mongo_client: MongoDB 客户端，如果为 None 则创建新连接
            use_redis: 是否使用 Redis（可选，用于性能优化）
        """
        self.use_redis = use_redis and settings.redis_url is not None

        if self.use_redis:
            # TODO: 实现 Redis 支持
            # import redis.asyncio as redis
            # self.redis = redis.from_url(settings.redis_url)
            pass

        # 使用 MongoDB 作为存储
        if mongo_client is None:
            self.client = AsyncIOMotorClient(settings.mongo_url)
            self._own_client = True
        else:
            self.client = mongo_client
            self._own_client = False

        self.db = self.client[settings.mongo_db_name]
        self.collection = self.db["rate_limit_records"]

        # 内存缓存（用于快速检查）
        self._memory_cache: Dict[str, List[Tuple[datetime, int]]] = {}

    async def check_rate_limit(
        self, user_id: str, rate_limit: int, window_seconds: int = 60
    ) -> bool:
        """
        检查用户是否超出速率限制

        算法: 滑动窗口
        - 记录用户在时间窗口内的请求次数
        - 超出限制返回 False
        - 未超出限制返回 True 并记录本次请求

        Args:
            user_id: 用户ID
            rate_limit: 每个时间窗口的请求限制
            window_seconds: 时间窗口大小（秒）

        Returns:
            bool: True 允许请求, False 拒绝请求

        Raises:
            RateLimitExceeded: 如果超出速率限制
        """
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window_seconds)

        # 查询时间窗口内的请求次数
        count = await self._get_request_count(user_id, window_start, current_time)

        # 检查是否超出限制
        if count >= rate_limit:
            # 计算需要等待的时间
            retry_after = await self._calculate_retry_after(
                user_id, window_start, window_seconds
            )
            raise RateLimitExceeded(user_id, retry_after)

        # 记录本次请求
        await self._record_request(user_id, current_time)

        return True

    async def _get_request_count(
        self, user_id: str, window_start: datetime, current_time: datetime
    ) -> int:
        """
        获取时间窗口内的请求次数

        Args:
            user_id: 用户ID
            window_start: 窗口开始时间
            current_time: 当前时间

        Returns:
            int: 请求次数
        """
        # 查询 MongoDB
        count = await self.collection.count_documents(
            {
                "user_id": user_id,
                "timestamp": {"$gte": window_start, "$lte": current_time},
            }
        )

        return count

    async def _record_request(self, user_id: str, timestamp: datetime) -> None:
        """
        记录请求

        Args:
            user_id: 用户ID
            timestamp: 请求时间
        """
        # 使用 insert_one 而不是依赖唯一索引
        # 每个请求都是独立的记录
        await self.collection.insert_one({"user_id": user_id, "timestamp": timestamp})

    async def _calculate_retry_after(
        self, user_id: str, window_start: datetime, window_seconds: int
    ) -> int:
        """
        计算需要等待的时间

        Args:
            user_id: 用户ID
            window_start: 窗口开始时间
            window_seconds: 时间窗口大小（秒）

        Returns:
            int: 需要等待的秒数
        """
        # 查询最早的请求时间
        earliest_request = await self.collection.find_one(
            {"user_id": user_id, "timestamp": {"$gte": window_start}},
            sort=[("timestamp", 1)],
        )

        if not earliest_request:
            return window_seconds

        # 计算最早请求到现在的时间差
        earliest_time = earliest_request["timestamp"]
        current_time = datetime.utcnow()
        elapsed = (current_time - earliest_time).total_seconds()

        # 需要等待的时间 = 窗口大小 - 已经过去的时间
        retry_after = max(1, int(window_seconds - elapsed))

        return retry_after

    async def get_remaining_quota(
        self, user_id: str, rate_limit: int, window_seconds: int = 60
    ) -> int:
        """
        获取用户剩余配额

        Args:
            user_id: 用户ID
            rate_limit: 每个时间窗口的请求限制
            window_seconds: 时间窗口大小（秒）

        Returns:
            int: 剩余配额
        """
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(seconds=window_seconds)

        # 查询时间窗口内的请求次数
        count = await self._get_request_count(user_id, window_start, current_time)

        # 计算剩余配额
        remaining = max(0, rate_limit - count)

        return remaining

    async def reset_user_quota(self, user_id: str) -> None:
        """
        重置用户配额（管理员操作）

        删除用户的所有速率限制记录

        Args:
            user_id: 用户ID
        """
        await self.collection.delete_many({"user_id": user_id})

        # 清理内存缓存
        if user_id in self._memory_cache:
            del self._memory_cache[user_id]
