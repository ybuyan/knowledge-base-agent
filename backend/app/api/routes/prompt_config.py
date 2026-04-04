"""
提示词配置管理 API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.prompt_config_service import prompt_config_service
from app.prompts.manager import prompt_manager
from app.tasks.prompt_sync_task import prompt_sync_task
from app.api.dependencies import get_current_user
from app.models.database import User

router = APIRouter(prefix="/api/prompt-config", tags=["prompt-config"])


class PromptConfigCreate(BaseModel):
    """创建提示词配置"""
    prompt_id: str
    name: str
    description: Optional[str] = None
    enabled: bool = True
    category: str
    template: Dict[str, Any]
    variables: List[str] = []
    version: str = "1.0"


class PromptConfigUpdate(BaseModel):
    """更新提示词配置"""
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    category: Optional[str] = None
    template: Optional[Dict[str, Any]] = None
    variables: Optional[List[str]] = None


@router.get("/list")
async def list_prompts(
    enabled_only: bool = False,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    获取提示词配置列表
    
    - enabled_only: 是否只返回启用的配置
    - category: 按分类筛选
    """
    try:
        if category:
            prompts = await prompt_config_service.get_by_category(category, enabled_only)
        else:
            prompts = await prompt_config_service.get_all(enabled_only)
        
        return {
            "success": True,
            "data": prompts,
            "total": len(prompts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{prompt_id}")
async def get_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user)
):
    """获取单个提示词配置"""
    prompt = await prompt_config_service.get_by_id(prompt_id)
    
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词配置不存在")
    
    return {
        "success": True,
        "data": prompt
    }


@router.post("/create")
async def create_prompt(
    prompt_data: PromptConfigCreate,
    current_user: User = Depends(get_current_user)
):
    """创建新的提示词配置"""
    # 检查权限（仅管理员）
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        prompt_id = await prompt_config_service.create(
            prompt_data.dict(),
            created_by=current_user.username
        )
        
        if not prompt_id:
            raise HTTPException(status_code=400, detail="创建失败")
        
        # 触发同步
        prompt_sync_task.trigger_sync()
        
        return {
            "success": True,
            "data": {"prompt_id": prompt_id},
            "message": "创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{prompt_id}")
async def update_prompt(
    prompt_id: str,
    updates: PromptConfigUpdate,
    current_user: User = Depends(get_current_user)
):
    """更新提示词配置"""
    # 检查权限（仅管理员）
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="权限不足")
    
    # 过滤 None 值
    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="没有需要更新的内容")
    
    success = await prompt_config_service.update(
        prompt_id,
        update_data,
        updated_by=current_user.username
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="提示词配置不存在")
    
    # 触发同步
    prompt_sync_task.trigger_sync()
    
    return {
        "success": True,
        "message": "更新成功"
    }


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: str,
    current_user: User = Depends(get_current_user)
):
    """删除提示词配置"""
    # 检查权限（仅管理员）
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="权限不足")
    
    success = await prompt_config_service.delete(prompt_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="提示词配置不存在")
    
    # 触发同步
    prompt_sync_task.trigger_sync()
    
    return {
        "success": True,
        "message": "删除成功"
    }


@router.post("/sync-from-file")
async def sync_from_file(
    current_user: User = Depends(get_current_user)
):
    """从配置文件同步到数据库"""
    # 检查权限（仅管理员）
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="权限不足")
    
    result = await prompt_config_service.sync_from_file()
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "同步失败"))
    
    # 触发同步到内存
    prompt_sync_task.trigger_sync()
    
    return {
        "success": True,
        "data": result.get("stats"),
        "message": "同步成功"
    }


@router.post("/export-to-file")
async def export_to_file(
    current_user: User = Depends(get_current_user)
):
    """导出配置到文件"""
    # 检查权限（仅管理员）
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="权限不足")
    
    success = await prompt_config_service.export_to_file()
    
    if not success:
        raise HTTPException(status_code=500, detail="导出失败")
    
    return {
        "success": True,
        "message": "导出成功"
    }


@router.post("/reload")
async def reload_config(
    current_user: User = Depends(get_current_user)
):
    """手动重新加载配置"""
    # 检查权限（仅管理员）
    if "admin" not in current_user.roles:
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        prompt_manager.reload()
        return {
            "success": True,
            "message": "配置已重新加载"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories(
    current_user: User = Depends(get_current_user)
):
    """获取所有分类"""
    categories = prompt_manager.get_categories()
    
    return {
        "success": True,
        "data": categories
    }
