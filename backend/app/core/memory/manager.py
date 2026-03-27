from typing import Dict, Optional
from datetime import datetime
import asyncio
from collections import OrderedDict
import logging

from .short_term import ShortTermMemory, SlidingWindowStrategy

logger = logging.getLogger(__name__)


class ConversationMemoryManager:
    def __init__(self, max_sessions: int = 1000, max_tokens_per_session: int = 4000):
        self._conversations: OrderedDict[str, ShortTermMemory] = OrderedDict()
        self._last_access: Dict[str, datetime] = {}
        self._max_sessions = max_sessions
        self._max_tokens = max_tokens_per_session
        self._lock = asyncio.Lock()
    
    async def get_or_create(
        self,
        session_id: str,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None
    ) -> ShortTermMemory:
        async with self._lock:
            if session_id in self._conversations:
                self._conversations.move_to_end(session_id)
                self._last_access[session_id] = datetime.utcnow()
                return self._conversations[session_id]
            
            if len(self._conversations) >= self._max_sessions:
                await self._evict_oldest()
            
            memory = ShortTermMemory(
                max_tokens=max_tokens or self._max_tokens,
                strategy=SlidingWindowStrategy()
            )
            
            if system_prompt:
                memory.add_system_prompt(system_prompt)
            
            self._conversations[session_id] = memory
            self._last_access[session_id] = datetime.utcnow()
            
            logger.debug(f"创建新会话记忆: {session_id}")
            return memory
    
    async def get(self, session_id: str) -> Optional[ShortTermMemory]:
        async with self._lock:
            memory = self._conversations.get(session_id)
            if memory:
                self._conversations.move_to_end(session_id)
                self._last_access[session_id] = datetime.utcnow()
            return memory
    
    async def delete(self, session_id: str) -> bool:
        async with self._lock:
            if session_id in self._conversations:
                del self._conversations[session_id]
                del self._last_access[session_id]
                logger.debug(f"删除会话记忆: {session_id}")
                return True
            return False
    
    async def clear(self, session_id: str) -> bool:
        async with self._lock:
            memory = self._conversations.get(session_id)
            if memory:
                memory.clear()
                return True
            return False
    
    async def load_history(
        self,
        session_id: str,
        messages: list,
        system_prompt: Optional[str] = None
    ) -> ShortTermMemory:
        memory = await self.get_or_create(
            session_id,
            system_prompt=system_prompt
        )
        
        if messages:
            memory.load_messages(messages)
        
        return memory
    
    async def _evict_oldest(self) -> None:
        if not self._last_access:
            return
        
        oldest_id = min(self._last_access, key=self._last_access.get)
        await self.delete(oldest_id)
        logger.info(f"LRU淘汰会话记忆: {oldest_id}")
    
    def get_active_count(self) -> int:
        return len(self._conversations)
    
    def get_session_ids(self) -> list:
        return list(self._conversations.keys())
    
    def get_stats(self) -> Dict:
        return {
            "active_sessions": len(self._conversations),
            "max_sessions": self._max_sessions,
            "total_tokens": sum(m.get_token_count() for m in self._conversations.values())
        }


_memory_manager: Optional[ConversationMemoryManager] = None


def get_memory_manager() -> ConversationMemoryManager:
    global _memory_manager
    if _memory_manager is None:
        from app.config import settings
        _memory_manager = ConversationMemoryManager(
            max_sessions=settings.memory_max_sessions,
            max_tokens_per_session=settings.memory_max_tokens
        )
    return _memory_manager
