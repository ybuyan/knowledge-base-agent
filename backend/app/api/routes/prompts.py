"""
提示词管理 API

提供提示词的查询、更新、重载等管理功能。
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.prompts.manager import prompt_manager

router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptUpdateRequest(BaseModel):
    """提示词更新请求"""
    template: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None
    description: Optional[str] = None


class PromptResponse(BaseModel):
    """提示词响应"""
    id: str
    name: str
    description: str
    category: str
    enabled: bool
    template: Dict[str, str]
    variables: List[str]


@router.get("", response_model=Dict[str, Any])
async def list_prompts(category: Optional[str] = None):
    """
    列出所有提示词
    
    Args:
        category: 可选的分类过滤
    """
    if category:
        prompts = prompt_manager.list_by_category(category)
    else:
        prompts = prompt_manager.list_all()
    
    categories = prompt_manager.get_categories()
    
    return {
        "prompts": prompts,
        "categories": categories
    }


@router.get("/categories")
async def get_categories():
    """获取所有提示词分类"""
    return prompt_manager.get_categories()


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(prompt_id: str):
    """
    获取指定提示词详情
    
    Args:
        prompt_id: 提示词ID
    """
    prompt = prompt_manager.get(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"提示词不存在: {prompt_id}")
    
    return PromptResponse(
        id=prompt_id,
        name=prompt.get("name", ""),
        description=prompt.get("description", ""),
        category=prompt.get("category", ""),
        enabled=prompt.get("enabled", True),
        template=prompt.get("template", {}),
        variables=prompt.get("variables", [])
    )


@router.put("/{prompt_id}")
async def update_prompt(prompt_id: str, request: PromptUpdateRequest):
    """
    更新提示词
    
    Args:
        prompt_id: 提示词ID
        request: 更新请求
    """
    updates = {}
    if request.template is not None:
        updates["template"] = request.template
    if request.enabled is not None:
        updates["enabled"] = request.enabled
    if request.description is not None:
        updates["description"] = request.description
    
    if not updates:
        raise HTTPException(status_code=400, detail="没有提供更新内容")
    
    success = prompt_manager.update(prompt_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail=f"提示词不存在: {prompt_id}")
    
    return {
        "success": True,
        "message": f"提示词 {prompt_id} 已更新"
    }


@router.post("/reload")
async def reload_prompts():
    """重新加载提示词配置"""
    prompt_manager.reload()
    return {
        "success": True,
        "message": "提示词配置已重新加载"
    }


@router.post("/{prompt_id}/render")
async def render_prompt(prompt_id: str, variables: Dict[str, str] = None):
    """
    渲染提示词模板
    
    Args:
        prompt_id: 提示词ID
        variables: 模板变量
    """
    try:
        result = prompt_manager.render(prompt_id, variables or {})
        return {
            "success": True,
            "rendered": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
