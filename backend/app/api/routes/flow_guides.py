"""
流程指引 CRUD API
"""

import logging
from datetime import datetime
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.models.flow_guide import FlowGuideCreate, FlowGuideUpdate
from app.services.flow_guide_repository import get_flow_guide_repository
from app.services.link_service import get_link_service
from app.core.mongodb import get_mongo_db

logger = logging.getLogger(__name__)

router = APIRouter()


# ------------------------------------------------------------------ #
# 请求/响应模型
# ------------------------------------------------------------------ #

class StatusUpdateRequest(BaseModel):
    status: Literal["active", "disabled"]


class ResolveDuplicateRequest(BaseModel):
    action: Literal["overwrite", "keep", "save_as_new"]
    pending_id: str


# ------------------------------------------------------------------ #
# 列表 & 分组
# ------------------------------------------------------------------ #

@router.get("")
async def list_flow_guides(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    """获取流程指引列表，支持按 status / category 过滤"""
    repo = get_flow_guide_repository()
    guides = await repo.get_all(status=status, category=category)
    return [g.model_dump() for g in guides]


@router.get("/grouped")
async def get_grouped_flow_guides():
    """按分类分组返回（供 QuickPromptButton 使用）"""
    repo = get_flow_guide_repository()
    return await repo.get_grouped()


@router.get("/external-links")
async def get_external_links():
    """返回 external_links 中 enabled=true 的条目，供前端选择"""
    link_service = get_link_service()
    links = await link_service.get_enabled_links()
    return [
        {
            "id": lnk.get("id"),
            "title": lnk.get("title"),
            "url": lnk.get("url"),
            "description": lnk.get("description", ""),
        }
        for lnk in links
    ]


@router.get("/pending-duplicates")
async def get_pending_duplicates():
    """获取未处理的重复记录"""
    db = get_mongo_db()
    if db is None:
        raise HTTPException(status_code=503, detail="数据库未连接")
    try:
        cursor = db.pending_duplicates.find({"resolved": False}).sort("created_at", -1)
        docs = await cursor.to_list(length=100)
        for doc in docs:
            doc.pop("_id", None)
        return docs
    except Exception as e:
        logger.error(f"[FlowGuidesAPI] get_pending_duplicates 失败: {e}")
        raise HTTPException(status_code=500, detail="查询失败")


# ------------------------------------------------------------------ #
# 处理重复确认
# ------------------------------------------------------------------ #

@router.post("/resolve-duplicate")
async def resolve_duplicate(req: ResolveDuplicateRequest):
    """
    处理重复确认：
    - overwrite: 用 new_guide_data 更新 existing_guide_id 对应的流程
    - keep: 直接标记 pending 为 resolved，不做任何修改
    - save_as_new: 用 new_guide_data 创建新流程（name 加时间戳后缀）
    """
    db = get_mongo_db()
    if db is None:
        raise HTTPException(status_code=503, detail="数据库未连接")

    # 查找 pending 记录
    pending = await db.pending_duplicates.find_one({"id": req.pending_id, "resolved": False})
    if not pending:
        raise HTTPException(status_code=404, detail="未找到待处理的重复记录")

    repo = get_flow_guide_repository()

    try:
        if req.action == "keep":
            # 直接标记为已处理
            pass

        elif req.action == "overwrite":
            existing_id = pending.get("existing_guide_id")
            new_data = pending.get("new_guide_data", {})
            if not existing_id:
                raise HTTPException(status_code=400, detail="缺少 existing_guide_id")

            update = FlowGuideUpdate(**{k: v for k, v in new_data.items()
                                        if k in FlowGuideUpdate.model_fields})
            result = await repo.update(existing_id, update)
            if not result:
                raise HTTPException(status_code=404, detail="目标流程不存在")

        elif req.action == "save_as_new":
            new_data = pending.get("new_guide_data", {})
            if not new_data:
                raise HTTPException(status_code=400, detail="缺少 new_guide_data")

            # name 加时间戳后缀避免重复
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            new_data["name"] = f"{new_data.get('name', '未命名')}_{timestamp}"

            from app.models.flow_guide import FlowStep, StepEntryLink
            steps_raw = new_data.get("steps", [])
            steps = []
            for s in steps_raw:
                entry_link_raw = s.get("entry_link")
                entry_link = StepEntryLink(**entry_link_raw) if entry_link_raw else None
                steps.append(FlowStep(
                    sequence=s.get("sequence", 0),
                    title=s.get("title", ""),
                    description=s.get("description", ""),
                    entry_link=entry_link,
                ))

            create_data = FlowGuideCreate(
                name=new_data["name"],
                category=new_data.get("category", "其他"),
                description=new_data.get("description", ""),
                steps=steps,
                status=new_data.get("status", "active"),
                source_document_id=new_data.get("source_document_id"),
                source_document_name=new_data.get("source_document_name"),
            )
            await repo.create(create_data)

        # 标记 pending 为已处理
        await db.pending_duplicates.update_one(
            {"id": req.pending_id},
            {"$set": {"resolved": True, "resolved_at": datetime.utcnow(), "action": req.action}}
        )

        return {"success": True, "action": req.action}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[FlowGuidesAPI] resolve_duplicate 失败: {e}")
        raise HTTPException(status_code=500, detail="处理失败")


# ------------------------------------------------------------------ #
# 单个资源 CRUD
# ------------------------------------------------------------------ #

@router.post("")
async def create_flow_guide(data: FlowGuideCreate):
    """创建流程指引"""
    repo = get_flow_guide_repository()
    try:
        guide = await repo.create(data)
        return guide.model_dump()
    except Exception as e:
        logger.error(f"[FlowGuidesAPI] create 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}")
async def get_flow_guide(id: str):
    """获取单个流程指引，自动解析 entry_link"""
    repo = get_flow_guide_repository()
    guide = await repo.get_by_id(id)
    if not guide:
        raise HTTPException(status_code=404, detail="流程指引不存在")

    link_service = get_link_service()
    resolved_steps = await repo.resolve_entry_links(guide.steps, link_service)
    guide.steps = resolved_steps
    return guide.model_dump()


@router.put("/{id}")
async def update_flow_guide(id: str, data: FlowGuideUpdate):
    """更新流程指引"""
    repo = get_flow_guide_repository()
    guide = await repo.update(id, data)
    if not guide:
        raise HTTPException(status_code=404, detail="流程指引不存在")
    return guide.model_dump()


@router.delete("/{id}")
async def delete_flow_guide(id: str):
    """删除流程指引"""
    repo = get_flow_guide_repository()
    success = await repo.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="流程指引不存在")
    return {"success": True}


@router.patch("/{id}/status")
async def toggle_flow_guide_status(id: str, req: StatusUpdateRequest):
    """启用/禁用流程指引"""
    repo = get_flow_guide_repository()
    success = await repo.toggle_status(id, req.status)
    if not success:
        raise HTTPException(status_code=404, detail="流程指引不存在")
    return {"success": True, "status": req.status}
