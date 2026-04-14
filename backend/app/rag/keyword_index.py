"""
KeywordIndex - 倒排索引检索（Vectorless RAG 第三路）

将文档分词后存入 MongoDB keyword_index 集合，
检索时基于词频交集打分，不依赖向量化。
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

COLLECTION_NAME = "keyword_index"


def _tokenize(text: str) -> List[str]:
    """简单分词：优先 jieba，回退逐字"""
    try:
        import jieba

        tokens = list(jieba.cut(text))
    except ImportError:
        tokens = list(text)
    return [t.strip().lower() for t in tokens if t.strip() and len(t.strip()) > 1]


async def build_keyword_index(doc_id: str, chunks: List[Dict[str, Any]]) -> int:
    """
    为文档的所有 chunk 构建倒排索引，写入 MongoDB。

    参数:
        doc_id: 文档 ID
        chunks: [{"content": str, "metadata": dict}, ...]

    返回:
        写入的 chunk 数量
    """
    from app.core.mongodb import get_mongo_db

    db = get_mongo_db()
    if db is None:
        logger.warning("KeywordIndex: MongoDB 未连接，跳过索引构建")
        return 0

    collection = db[COLLECTION_NAME]

    # 删除旧索引（重新上传时覆盖）
    await collection.delete_many({"doc_id": doc_id})

    records = []
    for i, chunk in enumerate(chunks):
        # 处理两种格式：字符串或字典
        if isinstance(chunk, str):
            content = chunk
            metadata = {}
        elif isinstance(chunk, dict):
            content = chunk.get("content", "")
            metadata = chunk.get("metadata", {})
        else:
            logger.warning(f"KeywordIndex: 跳过无效的 chunk 类型: {type(chunk)}")
            continue

        if not content:
            continue

        tokens = _tokenize(content)
        term_freq: Dict[str, int] = {}
        for t in tokens:
            term_freq[t] = term_freq.get(t, 0) + 1

        records.append(
            {
                "doc_id": doc_id,
                "chunk_index": i,
                "content": content,
                "metadata": metadata,
                "terms": list(term_freq.keys()),
                "term_freq": term_freq,
            }
        )

    if records:
        await collection.insert_many(records)

    logger.info("KeywordIndex: 文档 %s 写入 %d 条索引", doc_id, len(records))
    return len(records)


async def delete_keyword_index(doc_id: str) -> int:
    """
    删除文档的关键词索引。

    参数:
        doc_id: 文档 ID

    返回:
        删除的记录数量
    """
    from app.core.mongodb import get_mongo_db

    db = get_mongo_db()
    if db is None:
        logger.warning("KeywordIndex: MongoDB 未连接，跳过删除")
        return 0

    collection = db[COLLECTION_NAME]
    result = await collection.delete_many({"doc_id": doc_id})

    deleted_count = result.deleted_count
    logger.info("KeywordIndex: 文档 %s 删除 %d 条索引", doc_id, deleted_count)
    return deleted_count
