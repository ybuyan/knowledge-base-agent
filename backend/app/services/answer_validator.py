"""
回答验证服务

实现回答质量验证功能，包括：
1. 检索验证 - 过滤低相似度文档
2. 来源归属检查 - 验证回答是否引用了正确的来源
3. 置信度评估 - 评估回答的可信度
4. 幻觉检测 - 检测回答是否包含编造内容
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
import logging

from app.core.constraint_config import get_constraint_config

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    confidence_score: float
    has_source_attribution: bool
    potential_hallucination: bool
    warnings: List[str]
    filtered_documents: List[Dict[str, Any]]
    filtered_sources: List[Dict[str, Any]]


class AnswerValidator:
    """
    回答验证器
    
    根据约束配置验证回答质量。
    """
    
    # 幻觉检测关键词
    HALLUCINATION_INDICATORS = [
        "我猜测", "我估计", "可能", "大概", "也许",
        "应该", "我想", "似乎", "好像", "不确定"
    ]
    
    # 无信息关键词
    NO_INFO_KEYWORDS = [
        "没有找到相关信息",
        "没有找到相关内容",
        "知识库中没有",
        "不在我的知识库范围内",
        "无法在知识库中找到",
        "抱歉",
        "未找到"
    ]
    
    def __init__(self):
        self.config = get_constraint_config()
    
    def validate_retrieval(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        distances: List[float]
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        验证检索结果
        
        Args:
            documents: 文档内容列表
            metadatas: 元数据列表
            distances: 距离列表（越小越相似）
            
        Returns:
            Tuple[List[Dict], List[str]]: (过滤后的文档列表, 过滤后的内容列表)
        """
        # 从约束配置中读取检索相关参数
        retrieval_config = self.config.retrieval
        
        # 若检索约束未启用，直接返回全部文档，跳过相似度过滤
        if not retrieval_config.get("enabled", True):
            return self._format_all_documents(documents, metadatas), documents
        
        # 最低相似度阈值：低于此值的文档视为不相关，默认 0.7
        min_similarity = retrieval_config.get("min_similarity_score", 0.7)
        # 最大保留文档数：控制传入 LLM 的上下文长度，默认 5
        max_docs = retrieval_config.get("max_relevant_docs", 5)
        
        # 将距离转换为相似度 (假设距离范围 0-2，相似度 = 1 - distance/2)
        filtered_docs = []
        filtered_contents = []
        
        for i, (doc, meta, distance) in enumerate(zip(documents, metadatas, distances)):
            similarity = 1 - (distance / 2)
            
            if similarity >= min_similarity:
                filtered_docs.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": distance,
                    "similarity": similarity,
                    "index": i
                })
                filtered_contents.append(doc)
                
                logger.debug(f"[验证] 文档 {i} 相似度 {similarity:.3f} >= {min_similarity}, 保留")
            else:
                logger.debug(f"[验证] 文档 {i} 相似度 {similarity:.3f} < {min_similarity}, 过滤")
        
        # 限制最大文档数
        if len(filtered_docs) > max_docs:
            filtered_docs = filtered_docs[:max_docs]
            filtered_contents = filtered_contents[:max_docs]
        
        logger.info(f"[验证] 检索验证: {len(documents)} -> {len(filtered_docs)} 个文档")
        
        return filtered_docs, filtered_contents
    
    def check_source_attribution(
        self,
        answer: str,
        sources: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """
        检查来源归属
        
        Args:
            answer: 生成的回答
            sources: 引用来源列表
            
        Returns:
            Tuple[bool, List[str]]: (是否有来源归属, 警告列表)
        """
        validation_config = self.config.validation
        
        if not validation_config.get("check_source_attribution", True):
            return True, []
        
        warnings = []
        
        # 检查是否有来源
        if not sources:
            warnings.append("回答没有引用来源")
            return False, warnings
        
        # 检查回答中是否包含引用标记
        has_citation = bool(re.search(r'\[\d+\]|\[来源|\[文档', answer))
        
        if not has_citation:
            warnings.append("回答中没有引用标记")
        
        # 检查回答内容是否与来源相关
        source_content = " ".join([s.get("content", "") for s in sources])
        answer_words = set(answer.split())
        source_words = set(source_content.split())
        
        overlap = len(answer_words & source_words)
        overlap_ratio = overlap / len(answer_words) if answer_words else 0
        
        if overlap_ratio < 0.1:
            warnings.append(f"回答与来源内容重叠度较低 ({overlap_ratio:.1%})")
        
        return has_citation, warnings
    
    def detect_hallucination(
        self,
        answer: str,
        context: str
    ) -> Tuple[bool, List[str], float]:
        """
        检测幻觉
        
        Args:
            answer: 生成的回答
            context: 上下文（检索到的文档内容）
            
        Returns:
            Tuple[bool, List[str], float]: (是否有幻觉风险, 风险指标, 置信度)
        """
        validation_config = self.config.validation
        
        if not validation_config.get("hallucination_detection", True):
            return False, [], 1.0
        
        risk_indicators = []
        hallucination_score = 0.0
        
        # 1. 检查不确定性词汇
        uncertainty_count = 0
        for indicator in self.HALLUCINATION_INDICATORS:
            if indicator in answer:
                uncertainty_count += 1
                risk_indicators.append(f"包含不确定性词汇: '{indicator}'")
        
        if uncertainty_count > 0:
            hallucination_score += uncertainty_count * 0.1
        
        # 2. 检查回答内容是否在上下文中
        context_lower = context.lower()
        answer_sentences = re.split(r'[。！？\n]', answer)
        
        unsupported_sentences = 0
        for sentence in answer_sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            # 检查句子中的关键词是否在上下文中
            words = sentence.split()
            word_matches = sum(1 for w in words if w.lower() in context_lower)
            
            if word_matches < len(words) * 0.3:
                unsupported_sentences += 1
        
        if unsupported_sentences > 0:
            risk_indicators.append(f"{unsupported_sentences} 个句子可能缺乏上下文支持")
            hallucination_score += unsupported_sentences * 0.15
        
        # 3. 检查是否包含具体数字或日期（容易幻觉）
        numbers = re.findall(r'\d+(?:\.\d+)?(?:%|元|天|小时|年|月|日)?', answer)
        for num in numbers:
            if num not in context:
                risk_indicators.append(f"数字 '{num}' 未在上下文中找到")
                hallucination_score += 0.05
        
        # 计算置信度
        confidence = max(0, 1.0 - hallucination_score)
        
        has_hallucination_risk = hallucination_score > 0.3
        
        if has_hallucination_risk:
            logger.warning(f"[验证] 幻觉检测: 风险分数 {hallucination_score:.2f}, 置信度 {confidence:.2f}")
        
        return has_hallucination_risk, risk_indicators, confidence
    
    def calculate_confidence(
        self,
        answer: str,
        sources: List[Dict[str, Any]],
        context: str,
        retrieval_quality: float = 1.0
    ) -> float:
        """
        计算回答置信度
        
        Args:
            answer: 生成的回答
            sources: 引用来源
            context: 上下文
            retrieval_quality: 检索质量分数
            
        Returns:
            float: 置信度分数 (0-1)
        """
        # 基础分数
        base_score = retrieval_quality
        
        # 1. 来源数量加分
        source_bonus = min(len(sources) * 0.1, 0.2)
        
        # 2. 回答长度合理性
        length_penalty = 0
        if len(answer) < 20:
            length_penalty = 0.3
        elif len(answer) > 2000:
            length_penalty = 0.1
        
        # 3. 幻觉检测影响
        has_hallucination, _, _ = self.detect_hallucination(answer, context)
        hallucination_penalty = 0.2 if has_hallucination else 0
        
        # 计算最终置信度
        confidence = base_score + source_bonus - length_penalty - hallucination_penalty
        confidence = max(0, min(1, confidence))
        
        logger.info(f"[验证] 置信度计算: 基础={base_score:.2f}, 来源加分={source_bonus:.2f}, "
                   f"长度惩罚={length_penalty:.2f}, 幻觉惩罚={hallucination_penalty:.2f}, "
                   f"最终={confidence:.2f}")
        
        return confidence
    
    def validate_answer(
        self,
        answer: str,
        sources: List[Dict[str, Any]],
        context: str,
        retrieval_quality: float = 1.0
    ) -> ValidationResult:
        """
        综合验证回答
        
        Args:
            answer: 生成的回答
            sources: 引用来源
            context: 上下文
            retrieval_quality: 检索质量分数
            
        Returns:
            ValidationResult: 验证结果
        """
        validation_config = self.config.validation
        
        if not validation_config.get("enabled", True):
            return ValidationResult(
                is_valid=True,
                confidence_score=1.0,
                has_source_attribution=True,
                potential_hallucination=False,
                warnings=[],
                filtered_documents=[],
                filtered_sources=sources
            )
        
        warnings = []
        
        # 1. 检查来源归属
        has_attribution, attribution_warnings = self.check_source_attribution(answer, sources)
        warnings.extend(attribution_warnings)
        
        # 2. 检测幻觉
        has_hallucination, hallucination_warnings, _ = self.detect_hallucination(answer, context)
        warnings.extend(hallucination_warnings)
        
        # 3. 计算置信度
        confidence = self.calculate_confidence(answer, sources, context, retrieval_quality)
        
        # 4. 判断是否有效
        is_valid = confidence >= validation_config.get("min_confidence_score", 0.6) and not has_hallucination
        
        if not is_valid:
            min_confidence = validation_config.get("min_confidence_score", 0.6)
            warnings.append(f"回答置信度 ({confidence:.2f}) 低于阈值 ({min_confidence})")
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_score=confidence,
            has_source_attribution=has_attribution,
            potential_hallucination=has_hallucination,
            warnings=warnings,
            filtered_documents=[],
            filtered_sources=sources
        )
    
    def _format_all_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """格式化所有文档"""
        return [
            {
                "content": doc,
                "metadata": meta,
                "index": i
            }
            for i, (doc, meta) in enumerate(zip(documents, metadatas))
        ]


# 单例实例
_validator_instance: Optional[AnswerValidator] = None


def get_answer_validator() -> AnswerValidator:
    """获取验证器实例"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = AnswerValidator()
    return _validator_instance
