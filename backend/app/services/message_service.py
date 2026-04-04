from datetime import datetime
from bson import ObjectId
from typing import List, Optional, Dict
import logging

from app.core.mongodb import get_mongo_db

logger = logging.getLogger(__name__)


class MessageService:
    async def add_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        sources: Optional[List[Dict]] = None,
        suggested_questions: Optional[List[str]] = None,
        related_links: Optional[List[Dict]] = None,
        ui_components: Optional[Dict] = None
    ) -> Optional[Dict]:
        db = get_mongo_db()
        if db is None:
            logger.error(f"数据库连接不可用，无法保存消息: session_id={session_id}, role={role}")
            return None
        
        message_doc = {
            "session_id": ObjectId(session_id),
            "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
            "role": role,
            "content": content,
            "sources": sources or [],
            "suggested_questions": suggested_questions or [],
            "related_links": related_links or [],
            "ui_components": ui_components or None,
            "created_at": datetime.utcnow()
        }
        
        try:
            result = await db.messages.insert_one(message_doc)
            if result.inserted_id:
                message_doc["_id"] = result.inserted_id
                logger.info(f"消息保存成功: id={result.inserted_id}, session={session_id}, role={role}")
                return message_doc
            else:
                logger.error(f"消息保存失败: inserted_id 为空")
                return None
        except Exception as e:
            logger.error(f"添加消息失败: {e}", exc_info=True)
            return None
    
    async def get_messages(
        self,
        session_id: str,
        user_id: str,
        before_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        db = get_mongo_db()
        if db is None:
            return []
        
        try:
            query = {
                "session_id": ObjectId(session_id),
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            }
            
            if before_id and ObjectId.is_valid(before_id):
                query["_id"] = {"$lt": ObjectId(before_id)}
            
            cursor = db.messages.find(query).sort("created_at", 1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"获取消息列表失败: {e}")
            return []
    
    async def get_messages_paginated(
        self,
        session_id: str,
        user_id: str,
        cursor: Optional[str] = None,
        limit: int = 20,
        direction: str = "before"
    ) -> Dict:
        db = get_mongo_db()
        if db is None:
            return {"messages": [], "has_more": False, "next_cursor": None}
        
        try:
            query = {
                "session_id": ObjectId(session_id),
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            }
            
            sort_direction = -1 if direction == "before" else 1
            
            if cursor and ObjectId.is_valid(cursor):
                if direction == "before":
                    query["_id"] = {"$lt": ObjectId(cursor)}
                else:
                    query["_id"] = {"$gt": ObjectId(cursor)}
            
            fetch_limit = limit + 1
            cursor_obj = db.messages.find(query).sort("_id", sort_direction).limit(fetch_limit)
            messages = await cursor_obj.to_list(length=fetch_limit)
            
            has_more = len(messages) > limit
            if has_more:
                messages = messages[:limit]
            
            if direction == "before":
                messages = messages[::-1]
            
            next_cursor = None
            if has_more and messages:
                next_cursor = str(messages[-1]["_id"]) if direction == "before" else str(messages[0]["_id"])
            
            return {
                "messages": messages,
                "has_more": has_more,
                "next_cursor": next_cursor
            }
        except Exception as e:
            logger.error(f"分页获取消息失败: {e}")
            return {"messages": [], "has_more": False, "next_cursor": None}
    
    async def search_messages(
        self,
        user_id: str,
        keyword: str,
        session_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict]:
        db = get_mongo_db()
        if db is None:
            return []
        
        try:
            query = {
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id,
                "content": {"$regex": keyword, "$options": "i"}
            }
            
            if session_id:
                query["session_id"] = ObjectId(session_id)
            
            cursor = db.messages.find(query).sort("created_at", -1).skip(skip).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"搜索消息失败: {e}")
            return []
    
    async def get_messages_for_context(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict]:
        db = get_mongo_db()
        if db is None:
            return []
        
        try:
            cursor = db.messages.find(
                {"session_id": ObjectId(session_id)}
            ).sort("created_at", 1).limit(limit)
            messages = await cursor.to_list(length=limit)
            
            return [
                {"role": m["role"], "content": m["content"]}
                for m in messages
            ]
        except Exception as e:
            logger.error(f"获取上下文消息失败: {e}")
            return []
    
    async def get_message(self, message_id: str, user_id: str) -> Optional[Dict]:
        db = get_mongo_db()
        if db is None:
            return None
        
        try:
            return await db.messages.find_one({
                "_id": ObjectId(message_id),
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            })
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return None
    
    async def get_message_by_id(self, message_id: str, session_id: str, user_id: str) -> Optional[Dict]:
        db = get_mongo_db()
        if db is None:
            return None
        
        try:
            return await db.messages.find_one({
                "_id": ObjectId(message_id),
                "session_id": ObjectId(session_id),
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            })
        except Exception as e:
            logger.error(f"获取消息失败: {e}")
            return None
    
    async def delete_message(self, message_id: str, user_id: str) -> bool:
        db = get_mongo_db()
        if db is None:
            return False
        
        try:
            result = await db.messages.delete_one({
                "_id": ObjectId(message_id),
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"删除消息失败: {e}")
            return False
    
    async def get_message_count(self, session_id: str) -> int:
        db = get_mongo_db()
        if db is None:
            return 0
        
        try:
            return await db.messages.count_documents(
                {"session_id": ObjectId(session_id)}
            )
        except Exception as e:
            logger.error(f"获取消息数量失败: {e}")
            return 0
    
    async def get_recent_messages(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        db = get_mongo_db()
        if db is None:
            return []
        
        try:
            cursor = db.messages.find({
                "user_id": ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            }).sort("created_at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"获取最近消息失败: {e}")
            return []
    
    async def get_most_queried_documents(self, limit: int = 5) -> List[Dict]:
        """获取被查询最多的文档"""
        db = get_mongo_db()
        if db is None:
            return []
        
        try:
            pipeline = [
                {"$match": {"sources": {"$exists": True, "$ne": []}}},
                {"$unwind": "$sources"},
                {"$group": {
                    "_id": "$sources.filename",
                    "count": {"$sum": 1},
                    "last_queried": {"$max": "$created_at"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit},
                {"$project": {
                    "filename": "$_id",
                    "query_count": "$count",
                    "last_queried": 1,
                    "_id": 0
                }}
            ]
            
            cursor = db.messages.aggregate(pipeline)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"获取热门文档失败: {e}")
            return []


message_service = MessageService()
