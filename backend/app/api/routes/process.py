"""
流程操作接口
POST /api/process/action — 处理 next/prev/restart/cancel/input 操作
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Dict, Optional
import logging

from app.api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


class ProcessActionRequest(BaseModel):
    session_id: str
    flow_id: str
    action: str                          # next / prev / restart / cancel / input
    input_data: Optional[Dict[str, Any]] = {}


@router.post("/action")
async def process_action(
    req: ProcessActionRequest,
    current_user: dict = Depends(get_current_user),
):
    from app.agents.base import agent_engine

    username = current_user.get("username", "")
    logger.info("process/action user=%s flow=%s action=%s", username, req.flow_id, req.action)

    result = await agent_engine.execute(
        "process_agent",
        {
            "query": "",
            "session_id": req.session_id,
            "flow_id": req.flow_id,
            "process_action": req.action,
            "process_input": req.input_data or {},
            "username": username,
        },
    )
    return result
