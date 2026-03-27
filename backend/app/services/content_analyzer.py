"""
Content Analyzer - 内容分析服务

用于分析 LLM 响应内容，智能判断是否存在文档引用
"""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """
    内容分析器 - 智能检测 LLM 响应中的文档引用
    
    功能：
    1. 检测响应中是否包含来自参考文档的内容
    2. 识别文档引用的模式（如[文档名]、根据...等）
    3. 判断响应是否基于知识库生成
    """
    
    # 文档引用指示词 - 表明内容来自参考文档
    DOCUMENT_REFERENCE_PATTERNS = [
        r'\[([^\]]+)\]',  # [文档名] 格式
        r'根据[^，。]+(?:规定|说明|指出|显示|记载)',
        r'(?:依据|按照|参照)[^，。]+(?:文件|文档|资料|制度)',
        r'(?:文档|文件|资料)[:：][^，。]+',
        r'(?:详见|参见|参考)[^，。]+',
        r'(?:第[一二三四五六七八九十\d]+[章节条款])',
    ]
    
    # 无文档引用指示词 - 表明内容不是来自参考文档
    NO_DOCUMENT_INDICATORS = [
        "抱歉",
        "对不起",
        "没有找到相关信息",
        "没有找到相关内容",
        "知识库中没有",
        "不在我的知识库范围内",
        "无法在知识库中找到",
        "无法回答",
        "我不知道",
        "作为AI助手",
        "我是一个AI",
    ]
    
    # 通用知识回答指示词 - 表明是模型自身知识
    GENERAL_KNOWLEDGE_INDICATORS = [
        "一般来说",
        "通常情况下",
        "一般而言",
        "通常",
        "一般来说，",
        "根据常识",
        "根据一般经验",
    ]
    
    @classmethod
    def has_document_reference(cls, content: str, sources: List[Dict] = None) -> bool:
        """
        检测内容是否包含文档引用
        
        参数:
            content (str): LLM 生成的响应内容
            sources (List[Dict], optional): 检索到的文档来源列表
            
        返回:
            bool: 是否包含文档引用
            
        判断逻辑:
            1. 首先检查是否包含无文档引用指示词（明确的无信息回答）
            2. 如果提供了 sources 且不为空，且内容不是无信息回答，则认为有文档引用
            3. 检查内容中是否包含文档引用模式
            4. 最后综合判断
        """
        if not content or not isinstance(content, str):
            return False
        
        content = content.strip()
        
        # 1. 检查是否明确表明没有相关信息
        for indicator in cls.NO_DOCUMENT_INDICATORS:
            if indicator in content:
                logger.debug(f"检测到无文档指示词: {indicator}")
                return False
        
        # 2. 如果提供了 sources 且不为空，且内容有效，则认为有文档引用
        # 这是主要判断逻辑：只要有检索结果且生成了有效回答，就显示 sources
        if sources and len(sources) > 0:
            logger.debug(f"检测到检索结果: {len(sources)} 个 sources")
            return True
        
        # 3. 检查是否包含文档引用模式（内容中的引用标记）
        for pattern in cls.DOCUMENT_REFERENCE_PATTERNS:
            if re.search(pattern, content):
                logger.debug(f"检测到文档引用模式: {pattern}")
                return True
        
        # 4. 检查是否是通用知识回答
        general_knowledge_score = 0
        for indicator in cls.GENERAL_KNOWLEDGE_INDICATORS:
            if indicator in content:
                general_knowledge_score += 1
        
        # 如果包含多个通用知识指示词，认为是通用知识回答
        if general_knowledge_score >= 2:
            logger.debug("检测到通用知识回答模式")
            return False
        
        # 5. 内容长度和结构分析
        # 如果内容很短（<50字），且没有引用模式，可能不是来自文档
        if len(content) < 50 and not re.search(r'[\[【]', content):
            return False
        
        # 默认情况下，如果内容较长且没有明确的无文档指示词，
        # 可能来自文档（保守策略）
        return True
    
    @classmethod
    def extract_document_citations(cls, content: str) -> List[str]:
        """
        提取内容中的文档引用
        
        参数:
            content (str): LLM 生成的响应内容
            
        返回:
            List[str]: 提取到的文档引用列表
        """
        citations = []
        
        # 提取 [文档名] 格式的引用
        bracket_matches = re.findall(r'\[([^\]]+)\]', content)
        citations.extend(bracket_matches)
        
        # 提取 "根据..." 格式的引用
        according_matches = re.findall(r'根据([^，。]+)(?:规定|说明|指出|显示|记载)', content)
        citations.extend(according_matches)
        
        # 去重并清理
        citations = list(set(c.strip() for c in citations if c.strip()))
        
        return citations
    
    @classmethod
    def analyze_content_source(cls, content: str, sources: List[Dict] = None) -> Dict[str, Any]:
        """
        全面分析内容来源
        
        参数:
            content (str): LLM 生成的响应内容
            sources (List[Dict], optional): 原始 sources 列表
            
        返回:
            Dict[str, Any]: 分析结果
                - has_reference (bool): 是否包含文档引用
                - citations (List[str]): 提取的引用
                - confidence (float): 置信度 (0-1)
                - reason (str): 判断理由
        """
        has_ref = cls.has_document_reference(content, sources)
        citations = cls.extract_document_citations(content) if has_ref else []
        
        # 计算置信度
        confidence = 0.0
        if has_ref:
            if citations:
                confidence = min(0.9 + len(citations) * 0.05, 1.0)
            else:
                confidence = 0.7
        else:
            # 检查是否明确是无文档回答
            for indicator in cls.NO_DOCUMENT_INDICATORS:
                if indicator in content:
                    confidence = 0.95
                    break
            else:
                confidence = 0.5
        
        # 生成判断理由
        if has_ref:
            if citations:
                reason = f"检测到文档引用: {', '.join(citations[:3])}"
            else:
                reason = "检测到文档引用模式"
        else:
            for indicator in cls.NO_DOCUMENT_INDICATORS:
                if indicator in content:
                    reason = f"检测到无文档指示词: {indicator}"
                    break
            else:
                reason = "未检测到文档引用模式"
        
        return {
            "has_reference": has_ref,
            "citations": citations,
            "confidence": confidence,
            "reason": reason
        }


# 全局实例
_content_analyzer: Optional[ContentAnalyzer] = None


def get_content_analyzer() -> ContentAnalyzer:
    """获取内容分析器实例"""
    global _content_analyzer
    if _content_analyzer is None:
        _content_analyzer = ContentAnalyzer()
    return _content_analyzer
