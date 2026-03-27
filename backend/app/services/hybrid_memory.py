from typing import List, Dict, Optional, Tuple
import asyncio
import logging

from app.core.memory import ShortTermMemory, get_memory_manager
from app.services.session_service import session_service
from app.services.message_service import message_service
from app.rag.retriever import RAGRetriever
from app.core.chroma import get_conversations_collection
from app.prompts.manager import prompt_manager

logger = logging.getLogger(__name__)


class HybridMemoryService:
    def __init__(
        self,
        short_term_tokens: int = 3000,
        long_term_top_k: int = 3,
        system_prompt: str = None
    ):
        self.short_term_tokens = short_term_tokens
        self.long_term_top_k = long_term_top_k
        # 使用统一提示词管理
        self.system_prompt = system_prompt or prompt_manager.get_system_prompt("default_assistant") or (
            "你是一个专业的AI助手，请根据上下文和知识库回答用户问题。"
            "如果问题涉及之前的对话内容，请结合上下文进行回答。"
        )
        self._retriever: Optional[RAGRetriever] = None
    
    def _get_retriever(self) -> RAGRetriever:
        if self._retriever is None:
            self._retriever = RAGRetriever()
        return self._retriever
    
    async def get_or_create_memory(
        self,
        session_id: str,
        user_id: str = "default"
    ) -> ShortTermMemory:
        memory_manager = get_memory_manager()
        memory = await memory_manager.get(session_id)
        
        if memory is None:
            memory = await memory_manager.get_or_create(
                session_id,
                max_tokens=self.short_term_tokens,
                system_prompt=self.system_prompt
            )
            
            db_messages = await message_service.get_messages_for_context(session_id)
            if db_messages:
                memory.load_messages(db_messages)
                logger.debug(f"从数据库加载 {len(db_messages)} 条历史消息到短期记忆")
        
        return memory
    
    async def build_context(
        self,
        session_id: str,
        query: str,
        user_id: str = "default",
        include_long_term: bool = True
    ) -> Tuple[List[Dict], ShortTermMemory]:
        memory = await self.get_or_create_memory(session_id, user_id)
        
        context_messages = []
        
        if include_long_term:
            long_term_context = await self._retrieve_long_term(query, session_id)
            if long_term_context:
                context_messages.append({
                    "role": "system",
                    "content": f"[相关上下文]\n{long_term_context}"
                })
        
        short_term_context = memory.get_context(apply_strategy=True)
        context_messages.extend(short_term_context)
        
        return context_messages, memory
    
    async def _retrieve_long_term(
        self,
        query: str,
        current_session_id: str
    ) -> Optional[str]:
        try:
            retriever = self._get_retriever()
            
            docs_task = retriever.retrieve_documents(query, top_k=self.long_term_top_k)
            convs_task = self._retrieve_related_conversations(query, current_session_id)
            
            docs, convs = await asyncio.gather(docs_task, convs_task)
            
            parts = []
            
            if docs:
                parts.append("=== 相关文档 ===")
                for i, doc in enumerate(docs[:2], 1):
                    content = doc.get("content", "")[:500]
                    parts.append(f"[{i}] {content}")
            
            if convs:
                parts.append("\n=== 相关历史对话 ===")
                for conv in convs[:2]:
                    parts.append(conv.get("content", "")[:300])
            
            return "\n".join(parts) if parts else None
            
        except Exception as e:
            logger.warning(f"长期记忆检索失败: {e}")
            return None
    
    async def _retrieve_related_conversations(
        self,
        query: str,
        exclude_session_id: str
    ) -> List[Dict]:
        try:
            from app.core.embeddings import get_embeddings
            embeddings = get_embeddings()
            
            query_embedding = await embeddings.aembed_query(query)
            collection = get_conversations_collection()
            
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3,
                where={"session_id": {"$ne": exclude_session_id}}
            )
            
            conversations = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
                    conversations.append({
                        "content": doc,
                        "session_id": metadata.get("session_id")
                    })
            
            return conversations
            
        except Exception as e:
            logger.warning(f"检索相关对话失败: {e}")
            return []
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict]] = None,
        user_id: str = "default"
    ) -> None:
        memory = await self.get_or_create_memory(session_id, user_id)
        memory.add_message(role, content)
        
        try:
            await self._persist_message(session_id, user_id, role, content, sources)
        except Exception as e:
            logger.error(f"持久化消息失败: {e}")
    
    async def _persist_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict]]
    ) -> None:
        try:
            await message_service.add_message(
                session_id=session_id,
                user_id=user_id,
                role=role,
                content=content,
                sources=sources
            )
            
            await session_service.update_session_activity(session_id, content)
            
            if role == "assistant":
                await self._store_to_vector_db(session_id, content)
                
        except Exception as e:
            logger.error(f"持久化消息失败: {e}")
    
    async def _store_to_vector_db(
        self,
        session_id: str,
        answer: str
    ) -> None:
        try:
            memory = await get_memory_manager().get(session_id)
            if not memory:
                return
            
            messages = memory.get_messages()
            user_messages = [m for m in messages if m.role == "user"]
            
            if not user_messages:
                return
            
            last_question = user_messages[-1].content
            
            from app.core.embeddings import get_embeddings
            import uuid
            
            embeddings = get_embeddings()
            conv_text = f"Q: {last_question}\nA: {answer}"
            conv_embedding = await embeddings.aembed_query(conv_text)
            
            collection = get_conversations_collection()
            collection.add(
                ids=[str(uuid.uuid4())],
                embeddings=[conv_embedding],
                documents=[conv_text],
                metadatas=[{
                    "session_id": session_id,
                    "type": "qa_pair"
                }]
            )
            
        except Exception as e:
            logger.warning(f"存储对话到向量数据库失败: {e}")
    
    async def clear_session(self, session_id: str) -> None:
        memory_manager = get_memory_manager()
        await memory_manager.clear(session_id)


hybrid_memory_service = HybridMemoryService()
