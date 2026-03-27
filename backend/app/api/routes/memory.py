"""
记忆管理 API
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.core.memory.enhanced_manager import get_enhanced_memory_manager
from app.core.memory.types import MemoryType, MemoryMetadata, MemorySource, MemoryQuery

router = APIRouter(prefix="/api/memory", tags=["memory"])

DEFAULT_USER_ID = "default_user"


# ========== 请求模型 ==========

class CreateMemoryRequest(BaseModel):
    session_id: str
    content: str
    memory_type: MemoryType = MemoryType.SHORT_TERM
    title: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    expires_in_days: Optional[int] = None


class UpdateMemoryRequest(BaseModel):
    content: Optional[str] = None
    title: Optional[str] = None
    tags: Optional[List[str]] = None
    importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    is_active: Optional[bool] = None


class MarkTemporaryRequest(BaseModel):
    expires_in_days: int = Field(default=7, ge=1, le=365)
    importance: float = Field(default=0.8, ge=0.0, le=1.0)


class SavePermanentRequest(BaseModel):
    title: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class SearchMemoryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    min_weight: float = Field(default=0.1, ge=0.0, le=1.0)
    max_age_days: Optional[int] = None
    top_k: int = Field(default=10, ge=1, le=50)


# ========== API 端点 ==========

@router.post("/create")
async def create_memory(request: CreateMemoryRequest):
    """
    创建记忆
    
    支持的记忆类型：
    - working: 工作记忆（当前对话）
    - temporary: 临时记忆（有过期时间）
    - short_term: 短期记忆（最近对话）
    - long_term: 长期记忆（历史摘要）
    - permanent: 永久记忆（用户保存）
    """
    manager = get_enhanced_memory_manager()
    
    metadata = MemoryMetadata(
        title=request.title,
        tags=request.tags,
        source=MemorySource.USER_MARKED,
        importance=request.importance
    )
    
    memory = await manager.create_memory(
        user_id=DEFAULT_USER_ID,
        session_id=request.session_id,
        content=request.content,
        memory_type=request.memory_type,
        metadata=metadata,
        expires_in_days=request.expires_in_days
    )
    
    if memory is None:
        raise HTTPException(status_code=400, detail="记忆创建失败（可能是重复）")
    
    return {
        "success": True,
        "memory_id": memory.id,
        "weight": memory.weight,
        "expires_at": memory.expires_at
    }


@router.get("/get/{memory_id}")
async def get_memory(memory_id: str):
    """获取单个记忆"""
    manager = get_enhanced_memory_manager()
    memory = await manager.get_memory(memory_id, DEFAULT_USER_ID)
    
    if not memory:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    return memory.to_dict()


@router.post("/search")
async def search_memories(request: SearchMemoryRequest):
    """
    搜索记忆
    
    智能检索策略：
    1. 工作记忆优先（当前会话）
    2. 临时记忆高权重
    3. 按权重和相关性排序
    4. 自动过滤过期和低权重记忆
    """
    manager = get_enhanced_memory_manager()
    
    query = MemoryQuery(
        query_text=request.query,
        user_id=DEFAULT_USER_ID,
        session_id=request.session_id,
        memory_types=request.memory_types,
        tags=request.tags,
        min_weight=request.min_weight,
        max_age_days=request.max_age_days,
        top_k=request.top_k
    )
    
    memories = await manager.retrieve_memories(query)
    
    return {
        "total": len(memories),
        "memories": [m.to_dict() for m in memories]
    }


@router.put("/update/{memory_id}")
async def update_memory(memory_id: str, request: UpdateMemoryRequest):
    """更新记忆"""
    manager = get_enhanced_memory_manager()
    
    metadata = None
    if request.title or request.tags or request.importance:
        memory = await manager.get_memory(memory_id, DEFAULT_USER_ID)
        if not memory:
            raise HTTPException(status_code=404, detail="记忆不存在")
        
        metadata = memory.metadata
        if request.title:
            metadata.title = request.title
        if request.tags:
            metadata.tags = request.tags
        if request.importance:
            metadata.importance = request.importance
    
    success = await manager.update_memory(
        memory_id=memory_id,
        user_id=DEFAULT_USER_ID,
        content=request.content,
        metadata=metadata,
        is_active=request.is_active
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    return {"success": True}


@router.delete("/delete/{memory_id}")
async def delete_memory(memory_id: str):
    """删除记忆"""
    manager = get_enhanced_memory_manager()
    success = await manager.delete_memory(memory_id, DEFAULT_USER_ID)
    
    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    return {"success": True}


@router.post("/mark-temporary/{memory_id}")
async def mark_as_temporary(memory_id: str, request: MarkTemporaryRequest):
    """
    标记为临时记忆
    
    临时记忆特点：
    - 高权重（0.85基础权重）
    - 有过期时间
    - 适合短期重要信息
    """
    manager = get_enhanced_memory_manager()
    success = await manager.mark_as_temporary(
        memory_id=memory_id,
        user_id=DEFAULT_USER_ID,
        expires_in_days=request.expires_in_days,
        importance=request.importance
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    return {"success": True}


@router.post("/save-permanent/{memory_id}")
async def save_as_permanent(memory_id: str, request: SavePermanentRequest):
    """
    保存为永久记忆
    
    永久记忆特点：
    - 固定权重（0.5）
    - 不会过期
    - 不会时间衰减
    - 用户可管理
    """
    manager = get_enhanced_memory_manager()
    success = await manager.save_as_permanent(
        memory_id=memory_id,
        user_id=DEFAULT_USER_ID,
        title=request.title,
        tags=request.tags
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="记忆不存在")
    
    return {"success": True}


@router.get("/list")
async def list_memories(
    memory_type: Optional[MemoryType] = None,
    tags: Optional[str] = Query(None, description="逗号分隔的标签"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    列出记忆
    
    支持按类型和标签过滤
    """
    manager = get_enhanced_memory_manager()
    
    tag_list = tags.split(",") if tags else None
    
    memories = await manager.list_memories(
        user_id=DEFAULT_USER_ID,
        memory_type=memory_type,
        tags=tag_list,
        skip=skip,
        limit=limit
    )
    
    return {
        "total": len(memories),
        "memories": [m.to_dict() for m in memories]
    }


@router.post("/convert-working/{session_id}")
async def convert_working_to_short_term(session_id: str):
    """
    将工作记忆转换为短期记忆
    
    通常在会话结束时调用
    """
    manager = get_enhanced_memory_manager()
    await manager.convert_working_to_short_term(session_id, DEFAULT_USER_ID)
    
    return {"success": True}


@router.post("/archive")
async def archive_old_memories():
    """
    归档旧记忆
    
    将超过30天的短期记忆转换为长期记忆（摘要）
    """
    manager = get_enhanced_memory_manager()
    await manager.archive_old_memories(DEFAULT_USER_ID)
    
    return {"success": True}


@router.post("/cleanup")
async def cleanup_expired_memories():
    """
    清理过期记忆
    
    删除已过期的临时记忆
    """
    manager = get_enhanced_memory_manager()
    await manager.cleanup_expired_memories(DEFAULT_USER_ID)
    
    return {"success": True}


@router.get("/stats")
async def get_memory_stats():
    """
    获取记忆统计
    
    返回各类型记忆的数量和权重分布
    """
    manager = get_enhanced_memory_manager()
    
    stats = {
        "by_type": {},
        "total_count": 0,
        "avg_weight": 0.0
    }
    
    for memory_type in MemoryType:
        memories = await manager.list_memories(
            user_id=DEFAULT_USER_ID,
            memory_type=memory_type,
            limit=1000
        )
        
        count = len(memories)
        avg_weight = sum(m.weight for m in memories) / count if count > 0 else 0
        
        stats["by_type"][memory_type.value] = {
            "count": count,
            "avg_weight": round(avg_weight, 3)
        }
        
        stats["total_count"] += count
    
    return stats
