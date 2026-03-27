"""
增强记忆管理器
"""
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from .types import Memory, MemoryType, MemoryMetadata, MemorySource, MemoryQuery
from app.core.mongodb import get_mongo_db
from app.core.chroma import get_conversations_collection
from app.core.embeddings import get_embeddings

logger = logging.getLogger(__name__)


class EnhancedMemoryManager:
    """
    增强记忆管理器
    
    功能：
    1. 多层次记忆管理（工作/临时/短期/长期/永久）
    2. 智能权重计算和时间衰减
    3. 记忆检索和排序
    4. 记忆生命周期管理
    5. 防止记忆混乱
    """
    
    def __init__(self):
        self._working_memories: Dict[str, List[Memory]] = defaultdict(list)
        self._similarity_threshold = 0.95  # 去重阈值
    
    async def create_memory(
        self,
        user_id: str,
        session_id: str,
        content: str,
        memory_type: MemoryType,
        metadata: Optional[MemoryMetadata] = None,
        expires_in_days: Optional[int] = None
    ) -> Memory:
        """
        创建新记忆
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            content: 记忆内容
            memory_type: 记忆类型
            metadata: 元数据
            expires_in_days: 过期天数（仅临时记忆）
        """
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        if metadata is None:
            metadata = MemoryMetadata()
        
        # 计算过期时间
        expires_at = None
        if memory_type == MemoryType.TEMPORARY and expires_in_days:
            expires_at = now + timedelta(days=expires_in_days)
        
        memory = Memory(
            id=memory_id,
            user_id=user_id,
            session_id=session_id,
            memory_type=memory_type,
            content=content,
            metadata=metadata,
            created_at=now,
            updated_at=now,
            expires_at=expires_at
        )
        
        # 计算初始权重
        memory.weight = memory.calculate_weight()
        
        # 检查重复
        if await self._is_duplicate(memory):
            logger.info(f"检测到重复记忆，跳过创建: {content[:50]}")
            return None
        
        # 工作记忆存储在内存中
        if memory_type == MemoryType.WORKING:
            self._working_memories[session_id].append(memory)
            logger.debug(f"创建工作记忆: session={session_id}")
            return memory
        
        # 其他记忆持久化
        await self._persist_memory(memory)
        
        logger.info(f"创建记忆: type={memory_type.value}, id={memory_id}")
        return memory
    
    async def get_memory(self, memory_id: str, user_id: str) -> Optional[Memory]:
        """获取单个记忆"""
        db = get_mongo_db()
        if db is None:
            return None
        
        try:
            doc = await db.memories.find_one({
                "id": memory_id,
                "user_id": user_id
            })
            
            if doc:
                memory = Memory.from_dict(doc)
                memory.increment_access()
                await self._update_memory(memory)
                return memory
            
            return None
        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            return None
    
    async def retrieve_memories(self, query: MemoryQuery) -> List[Memory]:
        """
        检索记忆
        
        检索策略：
        1. 工作记忆（当前会话）- 全部返回
        2. 临时记忆 - 向量检索 + 未过期
        3. 短期记忆 - 向量检索 + 时间过滤
        4. 永久记忆 - 向量检索
        5. 长期记忆 - 向量检索（低优先级）
        """
        memories = []
        
        # 1. 工作记忆
        if query.session_id:
            working = self._working_memories.get(query.session_id, [])
            memories.extend(working)
        
        # 2. 向量检索其他类型记忆
        vector_memories = await self._vector_search(query)
        memories.extend(vector_memories)
        
        # 3. 过滤和排序
        memories = self._filter_memories(memories, query)
        memories = self._rank_memories(memories, query)
        
        # 4. 更新访问记录
        for memory in memories[:query.top_k]:
            memory.increment_access()
            if memory.memory_type != MemoryType.WORKING:
                await self._update_memory(memory)
        
        return memories[:query.top_k]
    
    async def update_memory(
        self,
        memory_id: str,
        user_id: str,
        content: Optional[str] = None,
        metadata: Optional[MemoryMetadata] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """更新记忆"""
        memory = await self.get_memory(memory_id, user_id)
        if not memory:
            return False
        
        if content:
            memory.content = content
        if metadata:
            memory.metadata = metadata
        if is_active is not None:
            memory.is_active = is_active
        
        memory.updated_at = datetime.utcnow()
        memory.weight = memory.calculate_weight()
        
        await self._update_memory(memory)
        
        # 如果内容变化，更新向量
        if content and memory.vector_id:
            await self._update_vector(memory)
        
        logger.info(f"更新记忆: id={memory_id}")
        return True
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """删除记忆"""
        memory = await self.get_memory(memory_id, user_id)
        if not memory:
            return False
        
        # 从数据库删除
        db = get_mongo_db()
        if db:
            await db.memories.delete_one({"id": memory_id, "user_id": user_id})
        
        # 从向量库删除
        if memory.vector_id:
            try:
                collection = get_conversations_collection()
                collection.delete(ids=[memory.vector_id])
            except Exception as e:
                logger.warning(f"删除向量失败: {e}")
        
        logger.info(f"删除记忆: id={memory_id}")
        return True
    
    async def mark_as_temporary(
        self,
        memory_id: str,
        user_id: str,
        expires_in_days: int = 7,
        importance: float = 0.8
    ) -> bool:
        """标记为临时记忆"""
        memory = await self.get_memory(memory_id, user_id)
        if not memory:
            return False
        
        memory.memory_type = MemoryType.TEMPORARY
        memory.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        memory.metadata.importance = importance
        memory.metadata.source = MemorySource.USER_MARKED
        memory.weight = memory.calculate_weight()
        
        await self._update_memory(memory)
        logger.info(f"标记为临时记忆: id={memory_id}, expires_in={expires_in_days}天")
        return True
    
    async def save_as_permanent(
        self,
        memory_id: str,
        user_id: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """保存为永久记忆"""
        memory = await self.get_memory(memory_id, user_id)
        if not memory:
            return False
        
        memory.memory_type = MemoryType.PERMANENT
        memory.expires_at = None
        memory.metadata.source = MemorySource.USER_MARKED
        
        if title:
            memory.metadata.title = title
        if tags:
            memory.metadata.tags = tags
        
        memory.weight = memory.calculate_weight()
        
        await self._update_memory(memory)
        logger.info(f"保存为永久记忆: id={memory_id}, title={title}")
        return True
    
    async def convert_working_to_short_term(self, session_id: str, user_id: str):
        """将工作记忆转换为短期记忆（会话结束时调用）"""
        working_memories = self._working_memories.get(session_id, [])
        
        for memory in working_memories:
            memory.memory_type = MemoryType.SHORT_TERM
            memory.weight = memory.calculate_weight()
            await self._persist_memory(memory)
        
        # 清空工作记忆
        self._working_memories[session_id] = []
        
        logger.info(f"转换工作记忆为短期记忆: session={session_id}, count={len(working_memories)}")
    
    async def archive_old_memories(self, user_id: str):
        """归档旧记忆（短期 → 长期）"""
        db = get_mongo_db()
        if db is None:
            return
        
        try:
            # 查找需要归档的短期记忆
            cursor = db.memories.find({
                "user_id": user_id,
                "memory_type": MemoryType.SHORT_TERM.value,
                "is_active": True
            })
            
            archived_count = 0
            async for doc in cursor:
                memory = Memory.from_dict(doc)
                
                if memory.should_archive():
                    # 生成摘要（简化版，实际可调用LLM）
                    summary = await self._generate_summary(memory.content)
                    
                    # 创建长期记忆
                    await self.create_memory(
                        user_id=user_id,
                        session_id=memory.session_id,
                        content=summary,
                        memory_type=MemoryType.LONG_TERM,
                        metadata=MemoryMetadata(
                            title=f"归档: {memory.metadata.title or '对话'}",
                            tags=memory.metadata.tags,
                            source=MemorySource.AUTO_GENERATED,
                            related_memories=[memory.id]
                        )
                    )
                    
                    # 删除原短期记忆
                    await self.delete_memory(memory.id, user_id)
                    archived_count += 1
            
            logger.info(f"归档记忆完成: user={user_id}, count={archived_count}")
        
        except Exception as e:
            logger.error(f"归档记忆失败: {e}")
    
    async def cleanup_expired_memories(self, user_id: str):
        """清理过期记忆"""
        db = get_mongo_db()
        if db is None:
            return
        
        try:
            # 删除过期的临时记忆
            result = await db.memories.delete_many({
                "user_id": user_id,
                "memory_type": MemoryType.TEMPORARY.value,
                "expires_at": {"$lt": datetime.utcnow()}
            })
            
            logger.info(f"清理过期记忆: user={user_id}, count={result.deleted_count}")
        
        except Exception as e:
            logger.error(f"清理过期记忆失败: {e}")
    
    async def list_memories(
        self,
        user_id: str,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Memory]:
        """列出记忆"""
        db = get_mongo_db()
        if db is None:
            return []
        
        try:
            query = {"user_id": user_id, "is_active": True}
            
            if memory_type:
                query["memory_type"] = memory_type.value
            
            if tags:
                query["metadata.tags"] = {"$in": tags}
            
            cursor = db.memories.find(query).sort("weight", -1).skip(skip).limit(limit)
            
            memories = []
            async for doc in cursor:
                memories.append(Memory.from_dict(doc))
            
            return memories
        
        except Exception as e:
            logger.error(f"列出记忆失败: {e}")
            return []
    
    # ========== 私有方法 ==========
    
    async def _persist_memory(self, memory: Memory):
        """持久化记忆到数据库和向量库"""
        db = get_mongo_db()
        if db is None:
            return
        
        try:
            # 保存到 MongoDB
            await db.memories.insert_one(memory.to_dict())
            
            # 保存到向量库
            await self._store_vector(memory)
        
        except Exception as e:
            logger.error(f"持久化记忆失败: {e}")
    
    async def _update_memory(self, memory: Memory):
        """更新记忆"""
        db = get_mongo_db()
        if db is None:
            return
        
        try:
            await db.memories.update_one(
                {"id": memory.id},
                {"$set": memory.to_dict()}
            )
        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
    
    async def _store_vector(self, memory: Memory):
        """存储向量"""
        try:
            embeddings = get_embeddings()
            embedding = await embeddings.aembed_query(memory.content)
            
            collection = get_conversations_collection()
            vector_id = str(uuid.uuid4())
            
            collection.add(
                ids=[vector_id],
                embeddings=[embedding],
                documents=[memory.content],
                metadatas=[{
                    "memory_id": memory.id,
                    "memory_type": memory.memory_type.value,
                    "user_id": memory.user_id,
                    "session_id": memory.session_id,
                    "weight": memory.weight,
                    "created_at": memory.created_at.isoformat()
                }]
            )
            
            memory.vector_id = vector_id
            await self._update_memory(memory)
        
        except Exception as e:
            logger.error(f"存储向量失败: {e}")
    
    async def _update_vector(self, memory: Memory):
        """更新向量"""
        if not memory.vector_id:
            return
        
        try:
            # 删除旧向量
            collection = get_conversations_collection()
            collection.delete(ids=[memory.vector_id])
            
            # 创建新向量
            await self._store_vector(memory)
        
        except Exception as e:
            logger.error(f"更新向量失败: {e}")
    
    async def _vector_search(self, query: MemoryQuery) -> List[Memory]:
        """向量检索"""
        try:
            embeddings = get_embeddings()
            query_embedding = await embeddings.aembed_query(query.query_text)
            
            collection = get_conversations_collection()
            
            # 构建过滤条件
            where_filter = {"user_id": query.user_id}
            
            if query.memory_types:
                where_filter["memory_type"] = {
                    "$in": [mt.value for mt in query.memory_types]
                }
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=query.top_k * 2,  # 多检索一些，后续过滤
                where=where_filter
            )
            
            memories = []
            if results and results.get("metadatas"):
                for metadata in results["metadatas"][0]:
                    memory_id = metadata.get("memory_id")
                    if memory_id:
                        memory = await self.get_memory(memory_id, query.user_id)
                        if memory:
                            memories.append(memory)
            
            return memories
        
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
    
    def _filter_memories(self, memories: List[Memory], query: MemoryQuery) -> List[Memory]:
        """过滤记忆"""
        filtered = []
        
        for memory in memories:
            # 过滤非活跃记忆
            if not memory.is_active and not query.include_inactive:
                continue
            
            # 过滤过期记忆
            if memory.is_expired():
                continue
            
            # 过滤低权重记忆
            if memory.weight < query.min_weight:
                continue
            
            # 过滤超龄记忆
            if query.max_age_days:
                days_old = (datetime.utcnow() - memory.created_at).days
                if days_old > query.max_age_days:
                    continue
            
            # 标签过滤
            if query.tags:
                if not any(tag in memory.metadata.tags for tag in query.tags):
                    continue
            
            filtered.append(memory)
        
        return filtered
    
    def _rank_memories(self, memories: List[Memory], query: MemoryQuery) -> List[Memory]:
        """记忆排序"""
        # 按权重降序排序
        memories.sort(key=lambda m: m.weight, reverse=True)
        return memories
    
    async def _is_duplicate(self, memory: Memory) -> bool:
        """检查是否重复"""
        # 简化版：检查相同会话中是否有相似内容
        # 实际可以使用向量相似度
        db = get_mongo_db()
        if db is None:
            return False
        
        try:
            similar = await db.memories.find_one({
                "user_id": memory.user_id,
                "session_id": memory.session_id,
                "content": memory.content,
                "is_active": True
            })
            
            return similar is not None
        
        except Exception as e:
            logger.error(f"检查重复失败: {e}")
            return False
    
    async def _generate_summary(self, content: str) -> str:
        """生成摘要（简化版）"""
        # 实际应该调用 LLM 生成摘要
        # 这里简单截取前200字符
        return content[:200] + "..." if len(content) > 200 else content


# 全局实例
_enhanced_memory_manager: Optional[EnhancedMemoryManager] = None


def get_enhanced_memory_manager() -> EnhancedMemoryManager:
    """获取增强记忆管理器实例"""
    global _enhanced_memory_manager
    if _enhanced_memory_manager is None:
        _enhanced_memory_manager = EnhancedMemoryManager()
    return _enhanced_memory_manager
