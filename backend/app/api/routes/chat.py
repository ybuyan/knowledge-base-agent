from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
import uuid
import json
import asyncio
import logging
import io
import re

from app.models.schemas import (
    SessionCreate, SessionUpdate, SessionResponse, SessionArchiveRequest,
    SessionSearchRequest, SessionStatsResponse,
    MessageCreate, MessageResponse, ChatStreamRequest
)
from app.services.session_service import session_service
from app.services.message_service import message_service
from app.core.llm import get_llm_async
from app.services.hybrid_memory import hybrid_memory_service
from app.services.pdf_service import create_pdf_export
from app.core.memory import get_memory_manager
from app.core.constraint_config import get_constraint_config
from app.prompts.strict_qa import StrictQAPrompt, ConstraintPromptBuilder
from app.services.response_builder import ResponseBuilder
from app.prompts.manager import prompt_manager

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_USER_ID = "default_user"


def log_constraint_check(query: str, similarity_score: float, document_count: int, passed: bool, reason: str):
    """Log constraint check result"""
    import os
    from datetime import datetime
    
    log_dir = "data/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "query": query[:100],
        "similarity_score": similarity_score,
        "document_count": document_count,
        "passed": passed,
        "reason": reason
    }
    
    log_file = os.path.join(log_dir, "constraints.log")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# ============================================================================
# 接口已废弃 - 2026-03-17
# 原因：前端已统一使用 /v2/ask/stream 接口，此接口不再使用
# 如需恢复，请取消下方注释
# ============================================================================
# @router.post("/ask/stream")
# async def ask_question_stream(request: ChatStreamRequest):
#     """Legacy endpoint - now uses QAAgent internally"""
#     from app.services.qa_agent import get_qa_agent
#     
#     async def generate():
#         try:
#             logger.info(f"[Legacy] Processing query: session={request.session_id}")
#             
#             # Get history from memory
#             history = []
#             if request.session_id:
#                 context_messages, memory = await hybrid_memory_service.build_context(
#                     session_id=request.session_id,
#                     query=request.question,
#                     user_id=DEFAULT_USER_ID,
#                     include_long_term=True
#                 )
#                 memory.add_message("user", request.question)
#                 for msg in memory.get_context(apply_strategy=True):
#                     if msg["role"] != "system":
#                         history.append(msg)
#             
#             # Use QAAgent
#             agent = get_qa_agent()
#             full_response = ""
#             sources = []
#             
#             async for chunk in agent.process(request.question, history):
#                 # Parse the chunk
#                 if chunk.startswith("data: "):
#                     data_str = chunk[6:].strip()
#                     if data_str:
#                         try:
#                             data = json.loads(data_str)
#                             if data.get("type") == "text":
#                                 full_response += data.get("content", "")
#                                 yield chunk
#                             elif data.get("type") == "done":
#                                 sources = data.get("sources", [])
#                                 # 发送 sources 给前端
#                                 yield chunk
#                         except:
#                             pass
#             
#             # Save to memory - await directly to ensure persistence
#             if request.session_id and full_response:
#                 try:
#                     await persist_conversation(
#                         session_id=request.session_id,
#                         user_id=DEFAULT_USER_ID,
#                         question=request.question,
#                         answer=full_response,
#                         sources=sources
#                     )
#                 except Exception as persist_error:
#                     logger.error(f"持久化对话失败: {persist_error}")
#             
#             yield "data: [DONE]\n\n"
#             
#         except Exception as e:
#             logger.error(f"流式处理错误: {e}", exc_info=True)
#             error_data = json.dumps({
#                 "type": "error",
#                 "message": str(e)
#             }, ensure_ascii=False)
#             yield f"data: {error_data}\n\n"
#     
#     return StreamingResponse(
#         generate(),
#         media_type="text/event-stream",
#         headers={
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#         }
#     )


async def stream_llm_with_messages(messages: list):
    from app.core.llm import get_llm_async
    
    client = await get_llm_async()
    
    from app.config import settings
    
    stream = await client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0.7,
        stream=True
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def persist_conversation(
    session_id: str,
    user_id: str,
    question: str,
    answer: str,
    sources: list,
    suggested_questions: list = None,
    related_links: list = None,
    ui_components: dict = None
) -> bool:
    """
    持久化对话到数据库
    返回: True 表示成功，False 表示失败
    """
    logger.info(f"开始持久化对话: session={session_id}, question_len={len(question)}, answer_len={len(answer)}")
    
    try:
        # 保存用户消息
        user_msg = await message_service.add_message(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=question
        )
        if user_msg is None:
            logger.error(f"保存用户消息失败: session={session_id}")
            return False
        logger.info(f"用户消息保存成功: id={user_msg.get('_id')}")
        
        # 保存AI回复
        assistant_msg = await message_service.add_message(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=answer,
            sources=sources,
            suggested_questions=suggested_questions,
            related_links=related_links,
            ui_components=ui_components
        )
        if assistant_msg is None:
            logger.error(f"保存AI回复失败: session={session_id}")
            return False
        logger.info(f"AI回复保存成功: id={assistant_msg.get('_id')}")
        
        # 更新会话活动状态
        activity_updated = await session_service.update_session_activity(session_id, answer)
        if not activity_updated:
            logger.warning(f"更新会话活动状态失败: session={session_id}")
        
        logger.info(f"对话持久化完成: session={session_id}")
        return True
        
    except Exception as e:
        logger.error(f"持久化对话失败: {e}", exc_info=True)
        return False


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 50,
    include_archived: bool = False
):
    sessions = await session_service.get_sessions(DEFAULT_USER_ID, skip, limit, include_archived)
    
    return [
        SessionResponse(
            _id=str(s["_id"]),
            title=s["title"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            message_count=s.get("message_count", 0),
            last_message=s.get("last_message"),
            is_archived=s.get("is_archived", False)
        )
        for s in sessions
    ]


@router.get("/sessions/search", response_model=List[SessionResponse])
async def search_sessions(
    keyword: str = Query("", min_length=0),
    include_archived: bool = False,
    skip: int = 0,
    limit: int = 50
):
    if not keyword:
        sessions = await session_service.get_sessions(DEFAULT_USER_ID, skip, limit, include_archived)
    else:
        sessions = await session_service.search_sessions(
            DEFAULT_USER_ID, keyword, include_archived, skip, limit
        )
    
    return [
        SessionResponse(
            _id=str(s["_id"]),
            title=s["title"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            message_count=s.get("message_count", 0),
            last_message=s.get("last_message"),
            is_archived=s.get("is_archived", False)
        )
        for s in sessions
    ]


@router.get("/sessions/stats", response_model=SessionStatsResponse)
async def get_session_stats():
    stats = await session_service.get_session_stats(DEFAULT_USER_ID)
    return SessionStatsResponse(**stats)


@router.get("/sessions/archived", response_model=List[SessionResponse])
async def list_archived_sessions(
    skip: int = 0,
    limit: int = 50
):
    sessions = await session_service.get_archived_sessions(DEFAULT_USER_ID, skip, limit)
    
    return [
        SessionResponse(
            _id=str(s["_id"]),
            title=s["title"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            message_count=s.get("message_count", 0),
            last_message=s.get("last_message"),
            is_archived=True
        )
        for s in sessions
    ]


@router.post("/sessions", response_model=SessionResponse)
async def create_session(data: SessionCreate):
    session = await session_service.create_session(
        user_id=DEFAULT_USER_ID,
        title=data.title
    )
    
    if session is None:
        session_id = str(uuid.uuid4())
        return SessionResponse(
            _id=session_id,
            title=data.title,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            message_count=0,
            is_archived=False
        )
    
    return SessionResponse(
        _id=str(session["_id"]),
        title=session["title"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        message_count=0,
        is_archived=False
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    session = await session_service.get_session(session_id, DEFAULT_USER_ID)
    
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        _id=str(session["_id"]),
        title=session["title"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        message_count=session.get("message_count", 0),
        last_message=session.get("last_message"),
        is_archived=session.get("is_archived", False)
    )


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, data: SessionUpdate):
    success = await session_service.update_session(
        session_id, DEFAULT_USER_ID, data.title
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True}


@router.patch("/sessions/{session_id}/archive")
async def archive_session(session_id: str, data: SessionArchiveRequest):
    success = await session_service.archive_session(
        session_id, DEFAULT_USER_ID, data.is_archived
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"success": True, "is_archived": data.is_archived}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    logger.info(f"Attempting to delete session: {session_id}")
    
    success = await session_service.delete_session(session_id, DEFAULT_USER_ID)
    
    if not success:
        logger.error(f"Failed to delete session: {session_id}")
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 删除内存中的数据
    try:
        await get_memory_manager().delete(session_id)
        logger.info(f"Deleted memory for session: {session_id}")
    except Exception as e:
        logger.warning(f"Failed to delete memory for session {session_id}: {e}")
    
    logger.info(f"Successfully deleted session: {session_id}")
    return {"success": True}


@router.get("/sessions/{session_id}/messages")
async def get_messages(session_id: str, before_id: Optional[str] = None, limit: int = 50):
    # Always get messages from database to ensure we have sources
    db_messages = await message_service.get_messages(
        session_id, DEFAULT_USER_ID, before_id, limit
    )
    
    if db_messages:
        await get_memory_manager().load_history(
            session_id,
            [{"role": m["role"], "content": m["content"]} for m in db_messages]
        )
    
    return {
        "messages": [
            {
                "id": str(m["_id"]),
                "role": m["role"],
                "content": m["content"],
                "sources": m.get("sources", []),
                "suggestedQuestions": m.get("suggested_questions", []),
                "relatedLinks": m.get("related_links", []),
                "uiComponents": m.get("ui_components"),
                "timestamp": m["created_at"].isoformat()
            }
            for m in db_messages
        ]
    }


@router.get("/sessions/{session_id}/messages/load-more")
async def load_more_messages(
    session_id: str,
    cursor: Optional[str] = None,
    limit: int = 20
):
    result = await message_service.get_messages_paginated(
        session_id, DEFAULT_USER_ID, cursor, limit, "before"
    )
    
    return {
        "messages": [
            {
                "id": str(m["_id"]),
                "role": m["role"],
                "content": m["content"],
                "sources": m.get("sources", []),
                "suggestedQuestions": m.get("suggested_questions", []),
                "relatedLinks": m.get("related_links", []),
                "uiComponents": m.get("ui_components"),
                "timestamp": m["created_at"].isoformat()
            }
            for m in result["messages"]
        ],
        "has_more": result["has_more"],
        "next_cursor": result["next_cursor"]
    }


@router.get("/messages/search")
async def search_messages(
    keyword: str = Query(..., min_length=1),
    session_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    messages = await message_service.search_messages(
        DEFAULT_USER_ID, keyword, session_id, skip, limit
    )
    
    return {
        "messages": [
            {
                "id": str(m["_id"]),
                "session_id": str(m["session_id"]),
                "role": m["role"],
                "content": m["content"],
                "timestamp": m["created_at"].isoformat()
            }
            for m in messages
        ]
    }


class ExportPdfRequest(BaseModel):
    message_id: str
    session_id: str
    title: Optional[str] = "AI问答导出"


@router.post("/export/pdf")
async def export_message_to_pdf(request: ExportPdfRequest):
    try:
        message = await message_service.get_message_by_id(
            request.message_id, 
            request.session_id,
            DEFAULT_USER_ID
        )
        
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        session = await session_service.get_session(request.session_id, DEFAULT_USER_ID)
        session_name = session.get("name", "未命名会话") if session else "未命名会话"
        
        pdf_bytes = create_pdf_export(
            title=request.title,
            content=message.get("content", ""),
            sources=message.get("sources", []),
            metadata={
                "session_name": session_name,
                "timestamp": message.get("created_at", datetime.now()).strftime("%Y-%m-%d %H:%M:%S") if isinstance(message.get("created_at"), datetime) else str(message.get("created_at", ""))
            }
        )
        
        filename = f"chat_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export PDF error: {e}")
        raise HTTPException(status_code=500, detail=f"导出PDF失败: {str(e)}")


@router.get("/documents/most-queried")
async def get_most_queried_documents(limit: int = Query(5, ge=1, le=20)):
    """获取被查询最多的文档"""
    try:
        documents = await message_service.get_most_queried_documents(limit)
        return {
            "documents": documents
        }
    except Exception as e:
        logger.error(f"获取热门文档失败: {e}")
        raise HTTPException(status_code=500, detail="获取热门文档失败")


class OptimizeQueryRequest(BaseModel):
    query: str


@router.post("/optimize-query")
async def optimize_query(request: OptimizeQueryRequest):
    """优化用户查询，提高检索准确度 - 使用缓存和混合策略"""
    try:
        from app.services.query_cache import query_cache
        from app.services.query_optimizer import query_optimizer
        from app.core.llm import get_llm_async
        
        # Step 1: Check cache
        cached_result = query_cache.get(request.query)
        if cached_result:
            logger.info(f"Cache hit for query: {request.query[:30]}...")
            return cached_result
        
        # Step 2: Local optimization (jieba + TF-IDF)
        local_result = query_optimizer.optimize_locally(request.query)
        
        # Step 3: Build enhanced prompt with local analysis
        enhanced_prompt = query_optimizer.build_enhanced_prompt(request.query, local_result)
        
        # Step 4: LLM optimization
        client = await get_llm_async()
        
        # 使用统一提示词管理
        system_prompt = prompt_manager.get_system_prompt("query_optimize") or """你是一个查询优化专家。你的任务是将用户的自然语言问题转化为更适合文档检索的结构化查询。

优化策略：
1. 关键词扩展：添加同义词、相关术语
2. 意图澄清：明确用户真正想了解的内容
3. 结构化：将模糊问题转化为具体查询
4. 保持原意：不要改变用户的原始意图

输出格式要求：
- 只输出优化后的查询文本
- 不要添加解释、前缀或后缀
- 使用中文关键词，用顿号或逗号分隔
- 尽量简洁，控制在50字以内

示例：
输入: "请假怎么弄"
输出: "员工请假申请流程、请假审批规定、请假天数限制、请假条模板"

输入: "工资什么时候发"
输出: "工资发放时间、薪资结算周期、薪酬发放规定、工资条查询"

输入: "报销需要什么"
输出: "费用报销材料、报销凭证要求、报销审批流程、报销时限规定\""""

        from app.config import settings
        
        response = await client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.3,
            max_tokens=100
        )
        
        optimized_query = response.choices[0].message.content.strip()
        
        result = {
            "original_query": request.query,
            "optimized_query": optimized_query,
            "query_type": local_result["query_type"],
            "keywords": local_result["keywords"],
            "from_cache": False
        }
        
        # Step 5: Cache the result
        query_cache.set(request.query, result)
        
        return result
        
    except Exception as e:
        logger.error(f"优化查询失败: {e}")
        
        # Fallback: Return local optimization result
        from app.services.query_optimizer import query_optimizer
        try:
            local_result = query_optimizer.optimize_locally(request.query)
            return {
                "original_query": request.query,
                "optimized_query": local_result["optimized_text"],
                "query_type": local_result["query_type"],
                "keywords": local_result["keywords"],
                "from_cache": False,
                "fallback": True
            }
        except Exception as fallback_error:
            logger.error(f"Fallback optimization also failed: {fallback_error}")
            raise HTTPException(status_code=500, detail=f"优化查询失败: {str(e)}")


@router.get("/optimize-cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    from app.services.query_cache import query_cache
    return query_cache.get_stats()


@router.post("/optimize-cache/clear")
async def clear_cache():
    """Clear query cache"""
    from app.services.query_cache import query_cache
    query_cache.clear()
    return {"message": "Cache cleared successfully"}


# ============================================================================
# New Architecture - QAAgent
# ============================================================================

@router.post("/v2/ask/stream")
async def ask_question_stream_v2(request: ChatStreamRequest, http_request: Request):
    """新架构：使用QAAgent处理查询"""
    from app.services.qa_agent import get_qa_agent

    # 从 Authorization header 解析登录用户名
    def _get_username() -> str:
        try:
            auth = http_request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return ""
            from app.api.dependencies import decode_token
            payload = decode_token(auth[7:])
            return payload.get("sub", "")
        except Exception:
            return ""

    current_username = _get_username()
    
    async def generate():
        try:
            # 验证 session_id
            if not request.session_id or request.session_id in ("undefined", "null", "None", ""):
                logger.warning(f"[V2] Invalid session_id: {request.session_id}, creating new session context")
            else:
                logger.info(f"[V2] Processing query: session={request.session_id}")
            
            # 获取历史消息
            history = []
            if request.session_id and request.session_id not in ("undefined", "null", "None", ""):
                messages = await message_service.get_messages(request.session_id, DEFAULT_USER_ID)
                for msg in messages[-12:]:
                    try:
                        role = msg["role"] if isinstance(msg, dict) else getattr(msg, "role", "user")
                        content = msg["content"] if isinstance(msg, dict) else getattr(msg, "content", "")
                        history.append({"role": role, "content": content})
                    except Exception as he:
                        logger.warning("history msg parse error: %s, msg type: %s, msg: %s", he, type(msg), repr(msg)[:100])
                
                # 添加调试日志
                logger.info(f"[V2] 获取到 {len(history)} 条历史消息")
                if history:
                    logger.info(f"[V2] 最后一条历史: role={history[-1]['role']}, content前50字={history[-1]['content'][:50]}")
            
            # 检查是否有进行中的流程（直接走 OrchestratorAgent，它会路由到 ProcessAgent）
            from app.agents.base import agent_engine as _agent_engine
            from app.core.process_context import get_process_context

            active_process = None
            if request.session_id and request.session_id not in ("undefined", "null", "None", ""):
                active_process = await get_process_context(request.session_id)

            # 使用QAAgent处理（或通过 Orchestrator 路由到 ProcessAgent）
            agent = get_qa_agent()
            full_response = ""
            sources = []
            suggested_questions = []
            related_links = []
            ui_components = None
            process_state = None

            # 统一走 OrchestratorAgent（意图路由：qa / process / memory / hybrid）
            orch_input = {
                "query": request.question,
                "session_id": request.session_id,
                "history": history,
                "username": current_username,
            }
            if active_process:
                orch_input["flow_id"] = active_process.get("flow_id", "")
                orch_input["process_action"] = "next"
                orch_input["process_input"] = {}

            orch_result = await _agent_engine.execute("orchestrator_agent", orch_input)

            # OrchestratorAgent 直接处理的结果（process / confirm / memory / hybrid / guide）
            # qa 意图不在这里处理，走下面的流式 QAAgent
            orch_handled = (
                orch_result.get("ui_components") is not None or
                orch_result.get("process_state") is not None or
                orch_result.get("intent") in ("confirm", "memory", "hybrid", "guide")
            )

            if orch_handled:
                full_response = orch_result.get("answer", "")
                ui_components = orch_result.get("ui_components")
                process_state = orch_result.get("process_state")
                if full_response:
                    yield ResponseBuilder.text_chunk(full_response)
                yield ResponseBuilder.done_chunk(
                    [], content=full_response,
                    ui_components=ui_components,
                    process_state=process_state,
                )
            else:
                # qa / memory / hybrid：走原有流式 QAAgent
                async for chunk in agent.process(request.question, history):
                    if chunk.startswith("data: "):
                        data_str = chunk[6:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                if data.get("type") == "text":
                                    full_response += data.get("content", "")
                                elif data.get("type") == "done":
                                    sources = data.get("sources", [])
                                    suggested_questions = data.get("suggested_questions", [])
                                    related_links = data.get("related_links", [])
                                    ui_components = data.get("ui_components")
                                    process_state = data.get("process_state")
                            except Exception:
                                pass
                    yield chunk
            
            # 保存消息到数据库
            if request.session_id and full_response:
                persist_result = await persist_conversation(
                    session_id=request.session_id,
                    user_id=DEFAULT_USER_ID,
                    question=request.question,
                    answer=full_response,
                    sources=sources,
                    suggested_questions=suggested_questions,
                    related_links=related_links,
                    ui_components=ui_components
                )
                if not persist_result:
                    logger.error(f"[V2] 持久化对话失败，数据可能丢失: session={request.session_id}")
                    # 发送错误提示给前端
                    error_notice = json.dumps({
                        "type": "warning",
                        "message": "消息保存失败，刷新页面后可能无法恢复此对话"
                    }, ensure_ascii=False)
                    yield f"data: {error_notice}\n\n"
            elif not full_response:
                logger.warning(f"[V2] 空响应，跳过持久化: session={request.session_id}")
                
        except Exception as e:
            import traceback as _tb
            _tb.print_exc()
            logger.error(f"[V2] Error processing query: {e}", exc_info=True)
            yield ResponseBuilder.error_chunk(str(e))

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/kb-optimizer/refresh")
async def refresh_kb_optimizer():
    """刷新知识库优化器 - 添加新文档后调用此接口"""
    from app.services.kb_query_optimizer import get_kb_optimizer
    
    optimizer = await get_kb_optimizer()
    result = await optimizer.refresh()
    
    return {
        "message": "知识库优化器已刷新",
        **result
    }


@router.get("/kb-optimizer/status")
async def get_kb_optimizer_status():
    """获取知识库优化器状态"""
    from app.services.kb_query_optimizer import get_kb_optimizer
    
    optimizer = await get_kb_optimizer()
    summary = optimizer.get_kb_summary()
    
    return {
        "message": "知识库优化器状态",
        **summary
    }
