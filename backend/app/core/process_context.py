"""
流程上下文管理
- 存储用户当前流程状态到 MongoDB（TTL 24h）
- 支持恢复、更新、清除
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.core.mongodb import get_mongo_db

logger = logging.getLogger(__name__)

COLLECTION = "process_contexts"
TTL_HOURS = 24


async def get_process_context(session_id: str) -> Optional[Dict[str, Any]]:
    db = get_mongo_db()
    if db is None:
        return None
    doc = await db[COLLECTION].find_one({"session_id": session_id})
    if not doc:
        return None
    # 检查是否过期
    if doc.get("expires_at") and doc["expires_at"] < datetime.utcnow():
        await clear_process_context(session_id)
        return None
    return doc


async def save_process_context(session_id: str, data: Dict[str, Any]) -> None:
    db = get_mongo_db()
    if db is None:
        return
    payload = {
        "session_id": session_id,
        "expires_at": datetime.utcnow() + timedelta(hours=TTL_HOURS),
        "updated_at": datetime.utcnow(),
        **data,
    }
    await db[COLLECTION].update_one(
        {"session_id": session_id},
        {"$set": payload},
        upsert=True,
    )


async def clear_process_context(session_id: str) -> None:
    db = get_mongo_db()
    if db is None:
        return
    await db[COLLECTION].delete_one({"session_id": session_id})
