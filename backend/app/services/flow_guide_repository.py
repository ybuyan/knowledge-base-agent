"""
流程指引数据仓库

封装 flow_guides 集合的 CRUD 操作。
"""

import uuid
import logging
from datetime import datetime
from typing import List, Optional, Any

from app.core.mongodb import get_mongo_db
from app.models.flow_guide import FlowGuide, FlowGuideCreate, FlowGuideUpdate, FlowStep

logger = logging.getLogger(__name__)


class FlowGuideRepository:
    """流程指引数据仓库"""

    # ------------------------------------------------------------------ #
    # 内部工具方法
    # ------------------------------------------------------------------ #

    def _doc_to_model(self, doc: dict) -> FlowGuide:
        """将 MongoDB 文档转换为 FlowGuide 模型"""
        doc.pop("_id", None)
        return FlowGuide(**doc)

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #

    async def create(self, data: FlowGuideCreate) -> FlowGuide:
        """创建流程指引"""
        db = get_mongo_db()
        now = datetime.utcnow()
        doc = {
            "id": str(uuid.uuid4()),
            **data.model_dump(),
            "created_at": now,
            "updated_at": now,
        }
        # steps 需要序列化为 dict
        doc["steps"] = [s.model_dump() for s in data.steps]

        await db.flow_guides.insert_one(doc)
        logger.info(f"[FlowGuideRepo] 创建流程指引: {doc['id']} - {data.name}")
        return self._doc_to_model(doc)

    async def get_by_id(self, id: str) -> Optional[FlowGuide]:
        """按 ID 查询"""
        db = get_mongo_db()
        if db is None:
            return None
        try:
            doc = await db.flow_guides.find_one({"id": id})
            if doc:
                return self._doc_to_model(doc)
            return None
        except Exception as e:
            logger.error(f"[FlowGuideRepo] get_by_id 失败: {e}")
            return None

    async def get_all(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[FlowGuide]:
        """查询所有流程指引，支持按 status / category 过滤"""
        db = get_mongo_db()
        if db is None:
            return []
        try:
            query: dict = {}
            if status:
                query["status"] = status
            if category:
                query["category"] = category

            cursor = db.flow_guides.find(query).sort("created_at", -1)
            docs = await cursor.to_list(length=1000)
            return [self._doc_to_model(d) for d in docs]
        except Exception as e:
            logger.error(f"[FlowGuideRepo] get_all 失败: {e}")
            return []

    async def get_grouped(self) -> List[dict]:
        """按 category 分组，返回 [{category, guides:[{id,name,description}]}]"""
        db = get_mongo_db()
        if db is None:
            return []
        try:
            cursor = db.flow_guides.find({"status": "active"}).sort("name", 1)
            docs = await cursor.to_list(length=1000)

            groups: dict[str, list] = {}
            for doc in docs:
                cat = doc.get("category", "其他")
                if cat not in groups:
                    groups[cat] = []
                groups[cat].append({
                    "id": doc.get("id"),
                    "name": doc.get("name"),
                    "description": doc.get("description", ""),
                })

            return [
                {"category": cat, "guides": guides}
                for cat, guides in groups.items()
            ]
        except Exception as e:
            logger.error(f"[FlowGuideRepo] get_grouped 失败: {e}")
            return []

    async def update(self, id: str, data: FlowGuideUpdate) -> Optional[FlowGuide]:
        """更新流程指引"""
        db = get_mongo_db()
        if db is None:
            return None
        try:
            update_fields = data.model_dump(exclude_none=True)
            if "steps" in update_fields and data.steps is not None:
                update_fields["steps"] = [s.model_dump() for s in data.steps]
            update_fields["updated_at"] = datetime.utcnow()

            result = await db.flow_guides.update_one(
                {"id": id},
                {"$set": update_fields}
            )
            if result.matched_count == 0:
                return None
            return await self.get_by_id(id)
        except Exception as e:
            logger.error(f"[FlowGuideRepo] update 失败: {e}")
            return None

    async def delete(self, id: str) -> bool:
        """删除流程指引"""
        db = get_mongo_db()
        if db is None:
            return False
        try:
            result = await db.flow_guides.delete_one({"id": id})
            success = result.deleted_count > 0
            if success:
                logger.info(f"[FlowGuideRepo] 删除流程指引: {id}")
            return success
        except Exception as e:
            logger.error(f"[FlowGuideRepo] delete 失败: {e}")
            return False

    async def toggle_status(self, id: str, status: str) -> bool:
        """切换流程指引状态"""
        db = get_mongo_db()
        if db is None:
            return False
        try:
            result = await db.flow_guides.update_one(
                {"id": id},
                {"$set": {"status": status, "updated_at": datetime.utcnow()}}
            )
            # matched_count > 0 表示文档存在（即使状态相同 modified_count 也可能为 0）
            return result.matched_count > 0
        except Exception as e:
            logger.error(f"[FlowGuideRepo] toggle_status 失败: {e}")
            return False

    async def find_by_name(self, name: str) -> Optional[FlowGuide]:
        """按名称查询（精确匹配）"""
        db = get_mongo_db()
        if db is None:
            return None
        try:
            doc = await db.flow_guides.find_one({"name": name})
            if doc:
                return self._doc_to_model(doc)
            return None
        except Exception as e:
            logger.error(f"[FlowGuideRepo] find_by_name 失败: {e}")
            return None

    async def resolve_entry_links(
        self,
        steps: List[FlowStep],
        link_service: Any,
    ) -> List[FlowStep]:
        """
        将步骤中的 external_link_id 解析为 label + url。
        手动配置（step.entry_link.label / url 已填写）优先，
        否则从 link_service 中按 id 查找。
        """
        enabled_links = await link_service.get_enabled_links()
        link_map = {lnk.get("id"): lnk for lnk in enabled_links}

        resolved: List[FlowStep] = []
        for step in steps:
            if step.entry_link and step.entry_link.external_link_id:
                el = step.entry_link
                # 手动配置优先：label 和 url 都已填写则直接使用
                if el.label and el.url:
                    resolved.append(step)
                    continue
                # 从 link_service 解析
                link_data = link_map.get(el.external_link_id)
                if link_data:
                    from app.models.flow_guide import StepEntryLink
                    new_link = StepEntryLink(
                        external_link_id=el.external_link_id,
                        label=link_data.get("title", el.label),
                        url=link_data.get("url", el.url),
                        open_in_new_tab=el.open_in_new_tab,
                    )
                    resolved.append(FlowStep(
                        sequence=step.sequence,
                        title=step.title,
                        description=step.description,
                        entry_link=new_link,
                    ))
                else:
                    resolved.append(step)
            else:
                resolved.append(step)

        return resolved


# 单例
_repo_instance: Optional[FlowGuideRepository] = None


def get_flow_guide_repository() -> FlowGuideRepository:
    global _repo_instance
    if _repo_instance is None:
        _repo_instance = FlowGuideRepository()
    return _repo_instance
