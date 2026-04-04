"""
流程指引 Pydantic 模型
"""

from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class StepEntryLink(BaseModel):
    """步骤入口链接（可选）"""
    external_link_id: Optional[str] = None
    label: Optional[str] = None
    url: Optional[str] = None
    open_in_new_tab: bool = True


class FlowStep(BaseModel):
    """流程步骤"""
    sequence: int
    title: str
    description: str
    entry_link: Optional[StepEntryLink] = None


class FlowGuide(BaseModel):
    """流程指引完整模型"""
    id: str
    name: str
    category: str
    description: str
    steps: List[FlowStep]
    status: Literal["active", "disabled"]
    source_document_id: Optional[str] = None
    source_document_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FlowGuideCreate(BaseModel):
    """创建流程指引"""
    name: str
    category: str
    description: str
    steps: List[FlowStep]
    status: Literal["active", "disabled"] = "active"
    source_document_id: Optional[str] = None
    source_document_name: Optional[str] = None


class FlowGuideUpdate(BaseModel):
    """更新流程指引（所有字段可选）"""
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    steps: Optional[List[FlowStep]] = None
    status: Optional[Literal["active", "disabled"]] = None
    source_document_id: Optional[str] = None
    source_document_name: Optional[str] = None
