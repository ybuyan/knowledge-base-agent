"""
KeywordIndexBuilder - 文档上传流水线中的倒排索引构建处理器
"""

import logging
from typing import Dict, Any

from app.skills.base import BaseProcessor, ProcessorRegistry
from app.rag.keyword_index import build_keyword_index

logger = logging.getLogger(__name__)


@ProcessorRegistry.register("KeywordIndexBuilder")
class KeywordIndexBuilder(BaseProcessor):
    """
    在文档上传流水线中，对已切分的 chunks 构建倒排索引。

    期望 context 包含:
        document_id (str): 文档 ID
        chunks (list): 切分后的文本块列表
    """

    @property
    def name(self) -> str:
        return "KeywordIndexBuilder"

    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        doc_id: str = context.get("document_id", "")
        chunks: list = context.get("chunks", [])

        if not doc_id or not chunks:
            logger.warning("KeywordIndexBuilder: 缺少 document_id 或 chunks，跳过")
            return context

        count = await build_keyword_index(doc_id, chunks)
        context["keyword_index_count"] = count
        logger.info("KeywordIndexBuilder: 完成，共 %d 条索引", count)
        return context
