import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from bson import ObjectId

from app.core.mongodb import get_mongo_db

logger = logging.getLogger(__name__)


class SessionService:
    async def create_session(
        self, user_id: str, title: str = "新对话"
    ) -> Optional[Dict]:
        db = get_mongo_db()
        if db is None:
            return None

        # 如果标题是"新对话"，检查是否已存在空的新对话
        if title == "新对话":
            existing_empty_session = await db.sessions.find_one(
                {
                    "user_id": ObjectId(user_id)
                    if ObjectId.is_valid(user_id)
                    else user_id,
                    "title": "新对话",
                    "message_count": 0,
                    "is_archived": {"$ne": True},
                }
            )

            if existing_empty_session:
                logger.info(
                    f"Found existing empty '新对话' session: {existing_empty_session['_id']}"
                )
                return existing_empty_session

        session_doc = {
            "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
            "title": title,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "message_count": 0,
            "last_message": None,
            "is_archived": False,
        }

        try:
            result = await db.sessions.insert_one(session_doc)
            session_doc["_id"] = result.inserted_id
            logger.info(f"Created new session: {session_doc['_id']}, title: {title}")
            return session_doc
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None

    async def get_sessions(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        include_archived: bool = False,
    ) -> List[Dict]:
        db = get_mongo_db()
        if db is None:
            return []

        try:
            # 先清理多余的空"新对话"
            await self.cleanup_empty_new_chats(user_id)

            query = {
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            }

            if not include_archived:
                query["is_archived"] = {"$ne": True}

            cursor = (
                db.sessions.find(query).sort("updated_at", -1).skip(skip).limit(limit)
            )
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return []

    async def search_sessions(
        self,
        user_id: str,
        keyword: str,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Dict]:
        db = get_mongo_db()
        if db is None:
            return []

        try:
            query = {
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
                "title": {"$regex": keyword, "$options": "i"},
            }

            if not include_archived:
                query["is_archived"] = {"$ne": True}

            cursor = (
                db.sessions.find(query).sort("updated_at", -1).skip(skip).limit(limit)
            )
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"搜索会话失败: {e}")
            return []

    async def get_session(self, session_id: str, user_id: str) -> Optional[Dict]:
        db = get_mongo_db()
        if db is None:
            return None

        try:
            return await db.sessions.find_one(
                {
                    "_id": ObjectId(session_id),
                    "user_id": ObjectId(user_id)
                    if ObjectId.is_valid(user_id)
                    else user_id,
                }
            )
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None

    async def update_session(self, session_id: str, user_id: str, title: str) -> bool:
        db = get_mongo_db()
        if db is None:
            return False

        try:
            result = await db.sessions.update_one(
                {
                    "_id": ObjectId(session_id),
                    "user_id": ObjectId(user_id)
                    if ObjectId.is_valid(user_id)
                    else user_id,
                },
                {"$set": {"title": title, "updated_at": datetime.utcnow()}},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            return False

    async def archive_session(
        self, session_id: str, user_id: str, is_archived: bool = True
    ) -> bool:
        db = get_mongo_db()
        if db is None:
            return False

        try:
            result = await db.sessions.update_one(
                {
                    "_id": ObjectId(session_id),
                    "user_id": ObjectId(user_id)
                    if ObjectId.is_valid(user_id)
                    else user_id,
                },
                {"$set": {"is_archived": is_archived, "updated_at": datetime.utcnow()}},
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"归档会话失败: {e}")
            return False

    async def update_session_activity(self, session_id: str, last_message: str) -> bool:
        db = get_mongo_db()
        if db is None:
            return False

        try:
            result = await db.sessions.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "updated_at": datetime.utcnow(),
                        "last_message": last_message[:100],
                    },
                    "$inc": {"message_count": 1},
                },
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"更新会话活动状态失败: {e}")
            return False

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        db = get_mongo_db()
        if db is None:
            logger.error("MongoDB connection is None, cannot delete session")
            return False

        try:
            # 验证 session_id 格式
            if not ObjectId.is_valid(session_id):
                logger.error(f"Invalid session_id format: {session_id}")
                return False

            # 先尝试查找 session，不限制 user_id
            session = await db.sessions.find_one({"_id": ObjectId(session_id)})

            if not session:
                logger.warning(f"Session not found in database: {session_id}")
                return False

            logger.info(
                f"Found session to delete: {session_id}, user_id: {session.get('user_id')}"
            )

            # 不使用事务，直接删除（单机 MongoDB 不支持事务）
            # 先删除消息
            msg_result = await db.messages.delete_many(
                {"session_id": ObjectId(session_id)}
            )
            logger.info(
                f"Deleted {msg_result.deleted_count} messages for session {session_id}"
            )

            # 再删除 session
            result = await db.sessions.delete_one({"_id": ObjectId(session_id)})

            if result.deleted_count > 0:
                logger.info(f"Successfully deleted session {session_id}")
                return True
            else:
                logger.error(f"Failed to delete session {session_id}, deleted_count=0")
                return False
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
            return False
            logger.error(f"删除会话失败: {e}")
            return False

    async def cleanup_empty_new_chats(self, user_id: str) -> int:
        """
        清理多余的空"新对话"，只保留最新的一个

        返回：删除的会话数量
        """
        db = get_mongo_db()
        if db is None:
            return 0

        try:
            # 查找所有空的"新对话"
            cursor = db.sessions.find(
                {
                    "user_id": ObjectId(user_id)
                    if ObjectId.is_valid(user_id)
                    else user_id,
                    "title": "新对话",
                    "message_count": 0,
                    "is_archived": {"$ne": True},
                }
            ).sort("created_at", -1)  # 按创建时间降序

            empty_sessions = await cursor.to_list(length=None)

            if len(empty_sessions) <= 1:
                return 0  # 只有一个或没有，不需要清理

            # 保留最新的，删除其他的
            sessions_to_delete = empty_sessions[1:]
            deleted_count = 0

            for session in sessions_to_delete:
                result = await db.sessions.delete_one({"_id": session["_id"]})
                if result.deleted_count > 0:
                    deleted_count += 1
                    logger.info(f"Cleaned up empty '新对话' session: {session['_id']}")

            return deleted_count
        except Exception as e:
            logger.error(f"清理空新对话失败: {e}")
            return 0

    async def get_session_stats(self, user_id: str) -> Dict:
        db = get_mongo_db()
        if db is None:
            return {
                "total_sessions": 0,
                "archived_sessions": 0,
                "today_sessions": 0,
                "week_sessions": 0,
                "total_messages": 0,
            }

        try:
            user_oid = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id

            now = datetime.utcnow()
            today_start = datetime(now.year, now.month, now.day)
            week_start = today_start - timedelta(days=7)

            total_sessions = await db.sessions.count_documents({"user_id": user_oid})

            archived_sessions = await db.sessions.count_documents(
                {"user_id": user_oid, "is_archived": True}
            )

            today_sessions = await db.sessions.count_documents(
                {"user_id": user_oid, "created_at": {"$gte": today_start}}
            )

            week_sessions = await db.sessions.count_documents(
                {"user_id": user_oid, "created_at": {"$gte": week_start}}
            )

            total_messages = await db.messages.count_documents({"user_id": user_oid})

            return {
                "total_sessions": total_sessions,
                "archived_sessions": archived_sessions,
                "today_sessions": today_sessions,
                "week_sessions": week_sessions,
                "total_messages": total_messages,
            }
        except Exception as e:
            logger.error(f"获取会话统计失败: {e}")
            return {
                "total_sessions": 0,
                "archived_sessions": 0,
                "today_sessions": 0,
                "week_sessions": 0,
                "total_messages": 0,
            }

    async def get_archived_sessions(
        self, user_id: str, skip: int = 0, limit: int = 50
    ) -> List[Dict]:
        db = get_mongo_db()
        if db is None:
            return []

        try:
            cursor = (
                db.sessions.find(
                    {
                        "user_id": ObjectId(user_id)
                        if ObjectId.is_valid(user_id)
                        else user_id,
                        "is_archived": True,
                    }
                )
                .sort("updated_at", -1)
                .skip(skip)
                .limit(limit)
            )
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"获取归档会话列表失败: {e}")
            return []


session_service = SessionService()
