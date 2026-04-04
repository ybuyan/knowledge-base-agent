"""
严格知识库问答提示词

此文件已重构，提示词已迁移到 config.json 统一管理。
保留此文件是为了向后兼容和提供便捷导入。
"""

from typing import List, Dict, Any
from app.prompts.manager import prompt_manager


class StrictQAPrompt:
    """
    严格知识库问答提示词类

    提供构建问答提示词的静态方法。
    """

    @staticmethod
    def get_fallback_message(
        config=None,
        contact_info: str = "",
        similar_questions: str = ""
    ) -> str:
        """
        获取兜底提示消息

        Args:
            config: 约束配置对象（可选）
            contact_info: 联系信息（已废弃，使用 config）
            similar_questions: 相似问题列表（已废弃，使用 config）

        Returns:
            渲染后的兜底消息
        """
        # 如果提供了 config，使用配置中的值
        if config is not None:
            from app.core.constraint_config import ConstraintConfig
            if isinstance(config, ConstraintConfig):
                fallback_config = config.fallback

                # 基础消息
                message = fallback_config.get(
                    'no_result_message',
                    '抱歉，我在知识库中没有找到相关信息。'
                )

                # 只有当 suggest_contact 为 true 时才添加联系信息
                if fallback_config.get('suggest_contact', True):
                    contact = fallback_config.get('contact_info', '')
                    if contact:
                        message += f"\n\n{contact}"

                return message

        # 向后兼容：使用传入的参数
        result = prompt_manager.render("fallback", {
            "contact_info": contact_info,
            "similar_questions": similar_questions
        })
        return result.get("content", "抱歉，我在知识库中没有找到相关信息。")
    
    @staticmethod
    def build_messages(
        context: str, 
        query: str, 
        history: List[Dict[str, Any]] = None,
        forbidden_topics: str = "无"
    ) -> List[Dict[str, str]]:
        """
        构建问答消息列表
        
        Args:
            context: 知识库上下文
            query: 用户问题
            history: 对话历史
            forbidden_topics: 禁止主题
            
        Returns:
            消息列表 [{"role": "system", "content": ...}, ...]
        """
        # 获取系统提示词
        system_template = prompt_manager.get_system_prompt("strict_qa")
        if not system_template:
            raise ValueError("未找到 strict_qa prompt 模板")
        
        system_content = system_template.format(
            context=context, 
            forbidden_topics=forbidden_topics
        )
        
        messages = [{"role": "system", "content": system_content}]
        
        # 添加历史消息
        if history:
            for msg in history:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role in ["user", "assistant"]:
                    messages.append({"role": role, "content": content})
        
        # 添加当前问题
        messages.append({"role": "user", "content": query})
        
        return messages


class ConstraintPromptBuilder:
    """
    约束提示词构建器
    
    用于根据约束配置构建提示词。
    """
    
    @staticmethod
    def build_system_prompt(
        context: str,
        constraints: Dict[str, Any] = None
    ) -> str:
        """
        构建带约束的系统提示词
        
        Args:
            context: 知识库上下文
            constraints: 约束配置
            
        Returns:
            系统提示词
        """
        constraints = constraints or {}
        generation = constraints.get("generation", {})
        
        # 基础提示词
        base_prompt = prompt_manager.get_system_prompt("strict_qa") or ""
        
        # 1. 严格模式
        if generation.get('strict_mode', True):
            base_prompt += """

## 严格模式
- 只基于提供的知识库内容回答
- 不要添加任何推测或假设
- 如果信息不完整，明确说明
- 保持回答的准确性和可靠性"""
        
        # 2. 通用知识限制
        if not generation.get('allow_general_knowledge', False):
            base_prompt += """

## 知识来源限制
- 严格限制：只能使用上述知识库内容回答
- 不要使用你的训练数据中的通用知识
- 如果知识库中没有相关信息，明确告知用户"""
        else:
            base_prompt += """

## 知识来源
- 优先使用上述知识库内容
- 如果知识库信息不足，可以适当补充通用知识
- 明确区分知识库内容和通用知识"""
        
        # 3. 引用要求
        if generation.get('require_citations', True):
            base_prompt += """

## 引用要求
- 必须在回答中标注信息来源
- 使用 [1]、[2] 等数字标记引用
- 每个关键信息都要有对应的引用"""
        
        # 4. 添加禁止主题
        forbidden_topics = generation.get("forbidden_topics", [])
        if forbidden_topics:
            topics_str = "、".join(forbidden_topics)
            base_prompt += f"\n\n## 禁止回答的主题\n请不要回答与以下主题相关的问题：{topics_str}"
        
        # 5. 添加禁止关键词
        forbidden_keywords = generation.get("forbidden_keywords", [])
        if forbidden_keywords:
            keywords_str = "、".join(forbidden_keywords)
            base_prompt += f"\n\n## 禁止使用的关键词\n回答中请不要使用以下关键词：{keywords_str}"
        
        return base_prompt.format(context=context, forbidden_topics="无")


# 向后兼容的函数
def get_strict_qa_prompt(context: str, forbidden_topics: str = "无") -> str:
    """
    获取严格问答提示词
    
    Args:
        context: 知识库上下文
        forbidden_topics: 禁止主题
        
    Returns:
        渲染后的系统提示词
    """
    return StrictQAPrompt.build_messages(context, "", forbidden_topics=forbidden_topics)[0].get("content", "")


def get_fallback_message(
    config=None,
    contact_info: str = "",
    similar_questions: str = ""
) -> str:
    """
    获取兜底提示消息

    Args:
        config: 约束配置对象（可选）
        contact_info: 联系信息（已废弃）
        similar_questions: 相似问题列表（已废弃）

    Returns:
        渲染后的兜底消息
    """
    return StrictQAPrompt.get_fallback_message(config, contact_info, similar_questions)
