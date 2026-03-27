"""
外部链接管理 API
"""

from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.link_service import get_link_service


class LinkCreate(BaseModel):
    id: str
    title: str
    url: str
    description: str = ""
    keywords: List[str] = []
    enabled: bool = True
    priority: int = 99


class LinkUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = None


router = APIRouter()


@router.get("")
async def get_links():
    """获取所有链接"""
    service = get_link_service()
    links = await service.get_all_links()
    return {"links": links}


@router.post("")
async def create_link(link: LinkCreate):
    """创建链接"""
    service = get_link_service()
    result = await service.create_link(link.dict())
    
    if result:
        return {"success": True, "link": result}
    return {"success": False, "message": "创建失败"}


@router.put("/{link_id}")
async def update_link(link_id: str, link: LinkUpdate):
    """更新链接"""
    service = get_link_service()
    result = await service.update_link(link_id, link.dict(exclude_unset=True))
    
    if result:
        return {"success": True}
    return {"success": False, "message": "更新失败"}


@router.delete("/{link_id}")
async def delete_link(link_id: str):
    """删除链接"""
    service = get_link_service()
    result = await service.delete_link(link_id)
    
    if result:
        return {"success": True}
    return {"success": False, "message": "删除失败"}
