"""
流程提取服务

从文档文本中使用 LLM 提取流程类知识，并处理重复检测。
"""

import uuid
import json
import logging
import re
from datetime import datetime
from typing import List, Optional

from app.models.flow_guide import FlowGuideCreate, FlowStep
from app.services.flow_guide_repository import get_flow_guide_repository
from app.core.mongodb import get_mongo_db
from app.core.llm import call_llm
from app.prompts.manager import prompt_manager

logger = logging.getLogger(__name__)


class FlowExtractor:
    """从文档中提取流程类知识的服务"""

    def __init__(self):
        self.repo = get_flow_guide_repository()

    async def extract_from_document(
        self,
        document_text: str,
        document_id: str,
        document_name: str,
    ) -> List[FlowGuideCreate]:
        """
        调用 LLM 提取文档中的流程类知识，返回提取到的流程列表（未保存）。
        """
        # 截取前 8000 字符，避免超出 LLM 上下文限制
        truncated_text = document_text[:8000]

        # 使用统一提示词管理
        result = prompt_manager.render("flow_extract", {"document_text": truncated_text})
        prompt = result.get("user", "")
        
        if not prompt:
            logger.error("[FlowExtractor] 未找到 flow_extract prompt 模板")
            return []

        try:
            raw_response = await call_llm(prompt)
        except Exception as e:
            logger.error(f"[FlowExtractor] LLM 调用失败 (doc={document_id}): {e}")
            return []

        # 解析 LLM 返回的 JSON
        guides: List[FlowGuideCreate] = []
        try:
            # 尝试从响应中提取 JSON 数组（LLM 可能包含额外文字）
            json_str = self._extract_json(raw_response)
            data = json.loads(json_str)

            if not isinstance(data, list):
                logger.warning(f"[FlowExtractor] LLM 返回非数组 JSON (doc={document_id})")
                return []

            for item in data:
                try:
                    steps = [
                        FlowStep(
                            sequence=s.get("sequence", idx + 1),
                            title=s.get("title", ""),
                            description=s.get("description", ""),
                        )
                        for idx, s in enumerate(item.get("steps", []))
                    ]
                    guide = FlowGuideCreate(
                        name=item.get("name", ""),
                        category=item.get("category", "其他"),
                        description=item.get("description", ""),
                        steps=steps,
                        status="active",
                        source_document_id=document_id,
                        source_document_name=document_name,
                    )
                    guides.append(guide)
                except Exception as parse_err:
                    logger.warning(f"[FlowExtractor] 单条流程解析失败: {parse_err}, item={item}")

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[FlowExtractor] JSON 解析失败 (doc={document_id}): {e}\n原始响应: {raw_response[:500]}")

        logger.info(f"[FlowExtractor] 从文档 '{document_name}' 提取到 {len(guides)} 个流程")
        return guides

    async def extract_and_save(
        self,
        document_text: str,
        document_id: str,
        document_name: str,
    ) -> None:
        """
        提取后检查重复：
        - 无重复：直接保存到 flow_guides
        - 有重复：写入 pending_duplicates 集合
        """
        guides = await self.extract_from_document(document_text, document_id, document_name)

        if not guides:
            logger.info(f"[FlowExtractor] 文档 '{document_name}' 未提取到流程，跳过保存")
            return

        db = get_mongo_db()

        for guide in guides:
            try:
                existing = await self.repo.find_by_name(guide.name)

                if existing is None:
                    # 无重复，直接保存
                    await self.repo.create(guide)
                    logger.info(f"[FlowExtractor] 已保存流程: '{guide.name}'")
                else:
                    # 有重复，写入 pending_duplicates
                    pending_doc = {
                        "id": str(uuid.uuid4()),
                        "document_id": document_id,
                        "document_name": document_name,
                        "existing_guide_id": existing.id,
                        "existing_guide_name": existing.name,
                        "new_guide_data": guide.model_dump(),
                        "resolved": False,
                        "created_at": datetime.utcnow(),
                    }
                    if db is not None:
                        await db.pending_duplicates.insert_one(pending_doc)
                    logger.info(
                        f"[FlowExtractor] 检测到重复流程 '{guide.name}'，已写入 pending_duplicates"
                    )

            except Exception as e:
                logger.error(f"[FlowExtractor] 保存流程 '{guide.name}' 时出错: {e}")

    # ------------------------------------------------------------------ #
    # 内部工具
    # ------------------------------------------------------------------ #

    def _extract_json(self, text: str) -> str:
        """从 LLM 响应文本中提取 JSON 数组字符串"""
        # 先尝试直接解析
        text = text.strip()
        if text.startswith("["):
            return text

        # 尝试用正则找到第一个 JSON 数组
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return match.group(0)

        # 找不到则原样返回，让调用方处理异常
        return text


# 单例
_extractor_instance: Optional[FlowExtractor] = None


def get_flow_extractor() -> FlowExtractor:
    global _extractor_instance
    if _extractor_instance is None:
        _extractor_instance = FlowExtractor()
    return _extractor_instance
