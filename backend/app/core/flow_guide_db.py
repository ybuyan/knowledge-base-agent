"""
流程指引数据库索引管理
"""

import logging
from app.core.mongodb import get_mongo_db

logger = logging.getLogger(__name__)


async def ensure_flow_guide_indexes():
    """在 flow_guides 集合上创建索引"""
    db = get_mongo_db()
    if db is None:
        logger.warning("[FlowGuideDB] MongoDB 未连接，跳过索引创建")
        return

    try:
        # name + category 联合索引（唯一）
        await db.flow_guides.create_index(
            [("name", 1), ("category", 1)],
            unique=True,
            name="name_category_unique"
        )
        # status 索引
        await db.flow_guides.create_index(
            [("status", 1)],
            name="status_idx"
        )
        logger.info("[FlowGuideDB] flow_guides 索引创建完成")
    except Exception as e:
        logger.warning(f"[FlowGuideDB] flow_guides 索引创建失败（可能已存在）: {e}")


async def ensure_pending_duplicate_indexes():
    """在 pending_duplicates 集合上创建索引"""
    db = get_mongo_db()
    if db is None:
        logger.warning("[FlowGuideDB] MongoDB 未连接，跳过索引创建")
        return

    try:
        # document_id 索引，用于按文档查询待处理重复
        await db.pending_duplicates.create_index(
            [("document_id", 1)],
            name="document_id_idx"
        )
        # resolved 状态索引
        await db.pending_duplicates.create_index(
            [("resolved", 1)],
            name="resolved_idx"
        )
        # 创建时间索引，用于清理过期记录
        await db.pending_duplicates.create_index(
            [("created_at", 1)],
            name="created_at_idx"
        )
        logger.info("[FlowGuideDB] pending_duplicates 索引创建完成")
    except Exception as e:
        logger.warning(f"[FlowGuideDB] pending_duplicates 索引创建失败（可能已存在）: {e}")
