"""
Knowledge-Based Query Optimizer - 基于知识库的查询优化器

根据实际知识库内容动态优化查询
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import jieba
import jieba.analyse
import re

from app.models.document import DocumentDB
from app.core.chroma import get_documents_collection

logger = logging.getLogger(__name__)


@dataclass
class KBOptimizationResult:
    """知识库优化结果"""
    original_query: str
    optimized_query: str
    keywords: List[str]
    related_docs: List[str]
    query_type: str
    confidence: float


class KBQueryOptimizer:
    """基于知识库的查询优化器"""
    
    def __init__(self):
        self._kb_terms: set = set()
        self._doc_names: List[str] = []
        self._initialized = False
        self._last_refresh_time: float = 0
        self._refresh_interval: int = 300  # 5分钟自动刷新一次
    
    async def _should_refresh(self) -> bool:
        """检查是否需要刷新"""
        import time
        if not self._initialized:
            return True
        return (time.time() - self._last_refresh_time) > self._refresh_interval
    
    async def initialize(self, force: bool = False):
        """初始化/刷新 - 从知识库加载术语"""
        if not force and self._initialized:
            return
        
        try:
            import time
            
            # 1. 从MongoDB加载文档名称
            docs, _ = await DocumentDB.list(page=1, page_size=1000)
            self._doc_names = [doc.filename for doc in docs]
            
            # 2. 从ChromaDB加载关键词
            collection = get_documents_collection()
            results = collection.get()
            
            # 清空旧术语
            self._kb_terms.clear()
            
            for metadata in results.get("metadatas", []):
                if metadata:
                    doc_name = metadata.get("document_name", "")
                    if doc_name:
                        # 提取文档名中的关键词
                        terms = self._extract_terms_from_filename(doc_name)
                        self._kb_terms.update(terms)
            
            # 3. 添加到jieba词典
            for term in self._kb_terms:
                jieba.add_word(term)
            
            self._initialized = True
            self._last_refresh_time = time.time()
            logger.info(f"KBQueryOptimizer refreshed with {len(self._kb_terms)} terms from {len(self._doc_names)} documents")
            
        except Exception as e:
            logger.error(f"Failed to initialize KBQueryOptimizer: {e}")
    
    async def refresh(self):
        """手动刷新知识库术语"""
        await self.initialize(force=True)
        return {
            "success": True,
            "document_count": len(self._doc_names),
            "term_count": len(self._kb_terms)
        }
    
    def _extract_terms_from_filename(self, filename: str) -> List[str]:
        """从文件名提取术语"""
        # 移除扩展名
        name = filename.replace(".pdf", "").replace(".docx", "").replace(".doc", "")
        # 分词
        terms = list(jieba.cut(name))
        # 过滤短词
        return [t for t in terms if len(t) >= 2]
    
    async def optimize(self, query: str) -> KBOptimizationResult:
        """优化查询"""
        # 检查是否需要自动刷新
        if await self._should_refresh():
            await self.initialize(force=True)
        
        await self.initialize()
        
        # 1. 分析查询类型
        query_type = self._classify_query(query)
        
        # 2. 提取关键词
        keywords = self._extract_keywords(query)
        
        # 3. 匹配相关文档
        related_docs = self._match_related_documents(query, keywords)
        
        # 4. 生成优化查询
        optimized_query = self._build_optimized_query(query, keywords, related_docs)
        
        # 5. 计算置信度
        confidence = self._calculate_confidence(query, keywords, related_docs)
        
        return KBOptimizationResult(
            original_query=query,
            optimized_query=optimized_query,
            keywords=keywords,
            related_docs=related_docs,
            query_type=query_type,
            confidence=confidence
        )
    
    def _classify_query(self, query: str) -> str:
        """分类查询类型"""
        patterns = {
            "list": [r"有哪些", r"有什么", r"列出", r"全部", r"所有"],
            "detail": [r"是什么", r"什么是", r"解释", r"介绍", r"详细"],
            "procedure": [r"怎么", r"如何", r"流程", r"步骤", r"办理"],
            "compare": [r"区别", r"不同", r"对比", r"比较"],
            "factual": [r"多少", r"多久", r"几天", r"金额", r"时间"]
        }
        
        for qtype, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, query):
                    return qtype
        
        return "general"
    
    def _extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        # 使用jieba提取关键词
        keywords = jieba.analyse.extract_tags(query, topK=5, withWeight=False)
        
        # 过滤停用词
        stopwords = {"你好", "请问", "谢谢", "的", "了", "是", "在", "我", "有"}
        keywords = [k for k in keywords if k not in stopwords and len(k) >= 2]
        
        # 匹配知识库术语
        kb_matches = [term for term in self._kb_terms if term in query]
        
        # 合并并去重
        all_keywords = list(dict.fromkeys(kb_matches + keywords))
        
        return all_keywords[:8]  # 最多8个关键词
    
    def _match_related_documents(self, query: str, keywords: List[str]) -> List[str]:
        """匹配相关文档"""
        related = []
        
        for doc_name in self._doc_names:
            # 检查查询或关键词是否匹配文档名
            if any(kw in doc_name for kw in keywords):
                related.append(doc_name)
            elif any(kw in query for kw in self._extract_terms_from_filename(doc_name)):
                related.append(doc_name)
        
        return related[:5]  # 最多5个相关文档
    
    def _build_optimized_query(self, original: str, keywords: List[str], related_docs: List[str]) -> str:
        """构建优化后的查询"""
        parts = [original]
        
        # 添加关键词提示
        if keywords:
            parts.append(f"相关关键词：{', '.join(keywords)}")
        
        # 添加相关文档提示
        if related_docs:
            parts.append(f"可能涉及的文档：{', '.join(related_docs)}")
        
        return "；".join(parts)
    
    def _calculate_confidence(self, query: str, keywords: List[str], related_docs: List[str]) -> float:
        """计算优化置信度"""
        score = 0.5  # 基础分
        
        # 有知识库术语匹配加分
        if any(term in query for term in self._kb_terms):
            score += 0.2
        
        # 有关键词提取加分
        if keywords:
            score += 0.1 * min(len(keywords) / 3, 0.3)
        
        # 有相关文档匹配加分
        if related_docs:
            score += 0.2
        
        return min(score, 1.0)
    
    def get_kb_summary(self) -> Dict[str, Any]:
        """获取知识库摘要"""
        return {
            "document_count": len(self._doc_names),
            "term_count": len(self._kb_terms),
            "documents": self._doc_names[:10],  # 前10个文档
            "terms": list(self._kb_terms)[:20]  # 前20个术语
        }


# 全局实例
_kb_optimizer: Optional[KBQueryOptimizer] = None


async def get_kb_optimizer() -> KBQueryOptimizer:
    """获取知识库优化器实例"""
    global _kb_optimizer
    if _kb_optimizer is None:
        _kb_optimizer = KBQueryOptimizer()
        await _kb_optimizer.initialize()
    return _kb_optimizer
