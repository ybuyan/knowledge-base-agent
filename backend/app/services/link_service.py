"""
外部链接服务

管理外部链接的 CRUD 操作。
"""

from datetime import datetime
from bson import ObjectId
from typing import List, Optional, Dict, Any
import logging

from app.core.mongodb import get_mongo_db

logger = logging.getLogger(__name__)


DEFAULT_LINKS = [
    {
        "id": "leave_request",
        "keywords": ["请假", "休假", "年假", "病假", "事假"],
        "title": "请假申请系统",
        "url": "/leave",
        "description": "在线提交请假申请",
        "enabled": True,
        "priority": 1
    },
    {
        "id": "expense_claim",
        "keywords": ["报销", "费用", "发票"],
        "title": "费用报销系统",
        "url": "/expense",
        "description": "在线提交费用报销",
        "enabled": True,
        "priority": 2
    },
    {
        "id": "referral",
        "keywords": ["内推", "推荐", "招聘"],
        "title": "内部推荐",
        "url": "/referral",
        "description": "提交内部推荐候选人",
        "enabled": True,
        "priority": 3
    },
    {
        "id": "handbook",
        "keywords": ["员工手册", "规章制度", "制度"],
        "title": "员工手册",
        "url": "/handbook",
        "description": "查看公司规章制度",
        "enabled": True,
        "priority": 4
    },
    {
        "id": "it_support",
        "keywords": ["IT", "电脑", "网络", "软件"],
        "title": "IT支持",
        "url": "/it-support",
        "description": "提交IT支持请求",
        "enabled": True,
        "priority": 5
    }
]


class LinkService:
    """外部链接服务"""
    
    def __init__(self):
        self._initialized = False
    
    async def _ensure_initialized(self):
        """确保默认链接已初始化"""
        if self._initialized:
            return
        
        db = get_mongo_db()
        if db is None:
            return
        
        try:
            count = await db.external_links.count_documents({})
            if count == 0:
                for link in DEFAULT_LINKS:
                    link_doc = {
                        **link,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    await db.external_links.insert_one(link_doc)
                logger.info(f"[LinkService] 初始化了 {len(DEFAULT_LINKS)} 个默认链接")
            self._initialized = True
        except Exception as e:
            logger.error(f"[LinkService] 初始化失败: {e}")
    
    async def get_all_links(self) -> List[Dict[str, Any]]:
        """获取所有链接"""
        await self._ensure_initialized()
        
        db = get_mongo_db()
        if db is None:
            return []
        
        try:
            cursor = db.external_links.find().sort("priority", 1)
            links = await cursor.to_list(length=100)
            
            return [
                {
                    "id": link.get("id"),
                    "title": link.get("title"),
                    "url": link.get("url"),
                    "description": link.get("description"),
                    "keywords": link.get("keywords", []),
                    "enabled": link.get("enabled", True),
                    "priority": link.get("priority", 99)
                }
                for link in links
            ]
        except Exception as e:
            logger.error(f"[LinkService] 获取链接失败: {e}")
            return []
    
    async def get_enabled_links(self) -> List[Dict[str, Any]]:
        """获取启用的链接"""
        await self._ensure_initialized()
        
        db = get_mongo_db()
        if db is None:
            return []
        
        try:
            cursor = db.external_links.find({"enabled": True}).sort("priority", 1)
            links = await cursor.to_list(length=100)
            return links
        except Exception as e:
            logger.error(f"[LinkService] 获取启用链接失败: {e}")
            return []
    
    async def create_link(self, link_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建链接"""
        db = get_mongo_db()
        if db is None:
            return None
        
        try:
            link_doc = {
                "id": link_data.get("id"),
                "title": link_data.get("title"),
                "url": link_data.get("url"),
                "description": link_data.get("description", ""),
                "keywords": link_data.get("keywords", []),
                "enabled": link_data.get("enabled", True),
                "priority": link_data.get("priority", 99),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await db.external_links.insert_one(link_doc)
            if result.inserted_id:
                link_doc["_id"] = result.inserted_id
                logger.info(f"[LinkService] 创建链接成功: {link_doc.get('id')}")
                return link_doc
            return None
        except Exception as e:
            logger.error(f"[LinkService] 创建链接失败: {e}")
            return None
    
    async def update_link(self, link_id: str, link_data: Dict[str, Any]) -> bool:
        """更新链接"""
        db = get_mongo_db()
        if db is None:
            return False
        
        try:
            update_data = {
                **link_data,
                "updated_at": datetime.utcnow()
            }
            
            result = await db.external_links.update_one(
                {"id": link_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"[LinkService] 更新链接成功: {link_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"[LinkService] 更新链接失败: {e}")
            return False
    
    async def delete_link(self, link_id: str) -> bool:
        """删除链接"""
        db = get_mongo_db()
        if db is None:
            return False
        
        try:
            result = await db.external_links.delete_one({"id": link_id})
            if result.deleted_count > 0:
                logger.info(f"[LinkService] 删除链接成功: {link_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"[LinkService] 删除链接失败: {e}")
            return False


_link_service_instance: Optional[LinkService] = None


def get_link_service() -> LinkService:
    """获取链接服务实例"""
    global _link_service_instance
    if _link_service_instance is None:
        _link_service_instance = LinkService()
    return _link_service_instance
