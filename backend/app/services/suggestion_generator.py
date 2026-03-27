"""
快捷提问生成服务

基于问题和回答内容生成相关的快捷提问。
"""

from typing import List, Dict, Any, Optional
import logging
import json

from app.core.constraint_config import get_constraint_config
from app.services.llm_client import get_llm_client
from app.prompts.manager import prompt_manager

logger = logging.getLogger(__name__)


class SuggestionGenerator:
    """
    快捷提问生成器
    
    基于问题和回答内容生成相关的快捷提问。
    支持根据类型生成不同风格的问题。
    """
    
    # 类型到提示词ID的映射
    TYPE_TO_PROMPT_ID = {
        '相关追问': 'suggestion_related',
        '深入探索': 'suggestion_deep',
        '对比分析': 'suggestion_compare',
        '实际应用': 'suggestion_practical',
        '背景原因': 'suggestion_background'
    }

    def __init__(self):
        self.config = get_constraint_config()
    
    async def generate(
        self,
        question: str,
        answer: str,
        count: Optional[int] = None
    ) -> List[str]:
        """
        生成快捷提问
        
        Args:
            question: 用户原始问题
            answer: AI 回答内容
            count: 生成数量（可选，默认使用配置）
            
        Returns:
            List[str]: 快捷提问列表
        """
        suggest_config = self.config.suggest_questions
        
        if not suggest_config.get("enabled", True):
            return []
        
        if count is None:
            count = suggest_config.get("count", 3)
        
        # 如果回答为空或包含"没有找到"，返回默认建议
        if not answer or self._is_no_info_answer(answer):
            return self._get_default_suggestions(question)
        
        try:
            # 检查是否配置了问题类型
            types = suggest_config.get('types', [])
            
            if types and len(types) > 0:
                # 按类型生成不同风格的问题
                suggestions = await self._generate_by_types(
                    question, answer, types, count
                )
            else:
                # 使用默认方式生成
                suggestions = await self._generate_default(
                    question, answer, count
                )
            
            logger.info(f"[快捷提问] 生成了 {len(suggestions)} 个建议")
            return suggestions
            
        except Exception as e:
            logger.error(f"[快捷提问] 生成失败: {e}")
            return self._get_default_suggestions(question)
    
    async def _generate_by_types(
        self,
        question: str,
        answer: str,
        types: List[str],
        count: int
    ) -> List[str]:
        """
        根据类型生成不同风格的问题
        
        Args:
            question: 用户问题
            answer: AI 回答
            types: 问题类型列表
            count: 生成数量
            
        Returns:
            List[str]: 生成的问题列表
        """
        suggestions = []
        llm_client = get_llm_client()
        
        # 只为需要的数量生成问题
        types_to_use = types[:count]
        
        # 为每个类型生成一个问题
        for i, question_type in enumerate(types_to_use):
            if len(suggestions) >= count:
                break
            
            try:
                suggestion = await self._generate_by_type(
                    llm_client,
                    question_type,
                    question,
                    answer
                )
                
                if suggestion:
                    suggestions.append(suggestion)
                    logger.debug(f"[快捷提问] 生成 {question_type} 类型问题: {suggestion}")
                
            except Exception as e:
                logger.warning(f"[快捷提问] 生成 {question_type} 类型问题失败: {e}")
                continue
        
        # 如果生成的问题不足，使用默认方式补充
        if len(suggestions) < count:
            remaining = count - len(suggestions)
            try:
                default_suggestions = await self._generate_default(
                    question, answer, remaining
                )
                suggestions.extend(default_suggestions)
            except Exception as e:
                logger.warning(f"[快捷提问] 补充默认建议失败: {e}")
        
        return suggestions[:count]
    
    async def _generate_by_type(
        self,
        llm_client,
        question_type: str,
        question: str,
        answer: str
    ) -> Optional[str]:
        """
        根据指定类型生成一个问题
        
        Args:
            llm_client: LLM 客户端
            question_type: 问题类型
            question: 用户问题
            answer: AI 回答
            
        Returns:
            Optional[str]: 生成的问题，失败返回 None
        """
        # 获取对应类型的提示词ID
        prompt_id = self.TYPE_TO_PROMPT_ID.get(question_type, 'suggestion_related')
        
        try:
            # 从配置获取提示词
            prompt_result = prompt_manager.render(prompt_id, {
                "question": question,
                "answer": answer[:500]  # 限制长度
            })
            
            prompt = prompt_result.get('user', '')
            
            response = await llm_client.chat(
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.8,
                max_tokens=100
            )
            
            # 清理和验证
            suggestion = response.strip()
            
            # 移除可能的编号
            for prefix in ['1.', '2.', '3.', '1、', '2、', '3、', '-', '•']:
                if suggestion.startswith(prefix):
                    suggestion = suggestion[len(prefix):].strip()
                    break
            
            # 验证问题质量
            if suggestion and len(suggestion) > 5 and len(suggestion) <= 50:
                return suggestion
            
            return None
        
        except Exception as e:
            logger.error(f"[快捷提问] LLM 生成失败: {e}")
            return None
    
    async def _generate_default(
        self,
        question: str,
        answer: str,
        count: int
    ) -> List[str]:
        """
        使用默认方式生成问题（向后兼容）
        
        Args:
            question: 用户问题
            answer: AI 回答
            count: 生成数量
            
        Returns:
            List[str]: 生成的问题列表
        """
        llm_client = get_llm_client()
        
        # 从配置获取提示词
        prompt_result = prompt_manager.render("suggestion_default", {
            "count": count,
            "question": question,
            "answer": answer[:500]
        })
        
        prompt = prompt_result.get('user', '')
        
        response = await llm_client.chat([
            {"role": "user", "content": prompt}
        ])
        
        return self._parse_suggestions(response, count)
    
    def _is_no_info_answer(self, answer: str) -> bool:
        """检查是否是无信息回答"""
        no_info_keywords = [
            "没有找到相关信息",
            "知识库中没有",
            "不在我的知识库范围内",
            "抱歉"
        ]
        return any(kw in answer for kw in no_info_keywords)
    
    def _get_default_suggestions(self, question: str) -> List[str]:
        """获取默认建议"""
        default_suggestions = [
            "还有其他相关信息吗？",
            "能详细解释一下吗？",
            "这个规定的依据是什么？"
        ]
        return default_suggestions[:self.config.suggest_questions.get("count", 3)]
    
    def _parse_suggestions(self, response: str, count: int) -> List[str]:
        """解析 LLM 响应中的建议"""
        lines = response.strip().split('\n')
        suggestions = []
        
        for line in lines:
            line = line.strip()
            # 移除编号
            if line and len(line) > 0:
                # 移除 "1." "1、" 等编号
                clean_line = line
                for prefix in ['1.', '2.', '3.', '4.', '5.', '1、', '2、', '3、', '4、', '5、']:
                    if clean_line.startswith(prefix):
                        clean_line = clean_line[len(prefix):].strip()
                        break
                
                if clean_line and len(clean_line) > 0:
                    suggestions.append(clean_line)
        
        return suggestions[:count]


# 单例实例
_generator_instance: Optional[SuggestionGenerator] = None


def get_suggestion_generator() -> SuggestionGenerator:
    """获取快捷提问生成器实例"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = SuggestionGenerator()
    return _generator_instance
