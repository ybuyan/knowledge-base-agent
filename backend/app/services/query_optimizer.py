"""
Query Optimizer Service
Implements hybrid optimization strategy combining:
1. Keyword extraction (jieba)
2. TF-IDF weighting
3. LLM semantic expansion
"""

import jieba
import jieba.analyse
from typing import List, Dict, Any, Optional, Tuple
import logging
import re

from app.prompts.manager import prompt_manager

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Hybrid query optimizer combining multiple strategies.
    """
    
    def __init__(self):
        self._init_jieba()
        self._domain_terms = self._load_domain_terms()
    
    def _init_jieba(self):
        """Initialize jieba with custom dictionary"""
        try:
            jieba.initialize()
            for term in self._load_domain_terms():
                jieba.add_word(term)
            logger.info("Jieba initialized with domain terms")
        except Exception as e:
            logger.warning(f"Jieba initialization warning: {e}")
    
    def _load_domain_terms(self) -> List[str]:
        """Load domain-specific terms for better segmentation"""
        return [
            "请假", "休假", "年假", "病假", "事假", "婚假", "产假",
            "报销", "费用报销", "差旅费", "交通费", "住宿费",
            "入职", "离职", "转正", "试用期",
            "薪资", "工资", "奖金", "绩效", "提成",
            "考勤", "打卡", "加班", "调休",
            "培训", "晋升", "调岗",
            "合同", "协议", "保密协议",
            "社保", "公积金", "五险一金"
        ]
    
    def extract_keywords(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Extract keywords using TF-IDF.
        Returns list of (keyword, weight) tuples.
        """
        try:
            keywords = jieba.analyse.extract_tags(query, topK=top_k, withWeight=True)
            return keywords
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def expand_keywords(self, keywords: List[str]) -> List[str]:
        """
        Expand keywords with synonyms and related terms.
        """
        expansion_map = {
            "请假": ["休假", "假期申请", "请假流程"],
            "工资": ["薪资", "薪酬", "收入"],
            "报销": ["费用报销", "报销申请", "报销流程"],
            "入职": ["新员工入职", "入职手续", "入职流程"],
            "离职": ["辞职", "离职手续", "离职流程"],
            "加班": ["加班申请", "加班费", "调休"],
            "培训": ["员工培训", "培训课程", "技能培训"],
            "合同": ["劳动合同", "合同签订", "合同续签"],
            "绩效": ["绩效考核", "绩效评估", "KPI"],
            "考勤": ["打卡", "签到", "考勤记录"]
        }
        
        expanded = set(keywords)
        for kw in keywords:
            if kw in expansion_map:
                expanded.update(expansion_map[kw])
        
        return list(expanded)
    
    def classify_query(self, query: str) -> str:
        """
        Classify query type for targeted optimization.
        Returns: 'factual', 'procedural', 'conceptual', or 'general'
        """
        procedural_patterns = [
            r"怎么", r"如何", r"流程", r"步骤", r"方法",
            r"怎样", r"操作", r"办理"
        ]
        
        conceptual_patterns = [
            r"什么是", r"定义", r"概念", r"意思",
            r"解释", r"介绍"
        ]
        
        factual_patterns = [
            r"多少", r"何时", r"哪里", r"谁",
            r"时间", r"地点", r"金额", r"天数"
        ]
        
        for pattern in procedural_patterns:
            if re.search(pattern, query):
                return "procedural"
        
        for pattern in conceptual_patterns:
            if re.search(pattern, query):
                return "conceptual"
        
        for pattern in factual_patterns:
            if re.search(pattern, query):
                return "factual"
        
        return "general"
    
    def get_strategy_for_type(self, query_type: str) -> Dict[str, Any]:
        """
        Get optimization strategy based on query type.
        """
        strategies = {
            "procedural": {
                "focus": "steps_and_flow",
                "prompt_suffix": "重点提取流程步骤、申请方式、审批环节等关键词。",
                "keyword_boost": ["流程", "步骤", "申请", "审批", "办理"]
            },
            "conceptual": {
                "focus": "definitions_and_explanations",
                "prompt_suffix": "重点提取定义、概念解释、相关规定等关键词。",
                "keyword_boost": ["定义", "规定", "政策", "说明", "解释"]
            },
            "factual": {
                "focus": "specific_information",
                "prompt_suffix": "重点提取具体数值、时间、地点等事实信息关键词。",
                "keyword_boost": ["时间", "金额", "天数", "标准", "规定"]
            },
            "general": {
                "focus": "general_search",
                "prompt_suffix": "全面提取相关关键词。",
                "keyword_boost": []
            }
        }
        return strategies.get(query_type, strategies["general"])
    
    def optimize_locally(self, query: str) -> Dict[str, Any]:
        """
        Perform local optimization without LLM.
        Useful for fallback or pre-processing.
        """
        keywords_with_weights = self.extract_keywords(query)
        keywords = [kw for kw, _ in keywords_with_weights]
        
        expanded_keywords = self.expand_keywords(keywords)
        
        query_type = self.classify_query(query)
        strategy = self.get_strategy_for_type(query_type)
        
        boost_keywords = strategy.get("keyword_boost", [])
        all_keywords = list(set(expanded_keywords + boost_keywords))
        
        return {
            "keywords": keywords,
            "keywords_with_weights": keywords_with_weights,
            "expanded_keywords": all_keywords,
            "query_type": query_type,
            "strategy": strategy,
            "optimized_text": "、".join(all_keywords[:8])
        }
    
    def build_enhanced_prompt(self, query: str, local_result: Dict[str, Any]) -> str:
        """
        Build enhanced prompt with local analysis results.
        """
        query_type = local_result["query_type"]
        strategy = local_result["strategy"]
        keywords = local_result["keywords"]
        
        # 使用统一提示词管理
        result = prompt_manager.render("query_optimizer_enhance", {
            "query": query,
            "query_type": query_type,
            "keywords": ', '.join(keywords),
            "strategy": strategy['prompt_suffix']
        })
        
        if not result.get("user"):
            raise ValueError("未找到 query_optimizer_enhance prompt 模板")
        
        return result["user"]


query_optimizer = QueryOptimizer()
