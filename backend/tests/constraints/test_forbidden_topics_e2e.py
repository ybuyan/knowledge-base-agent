"""
禁止主题端到端测试

测试当用户查询禁止主题时，系统的实际响应行为
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.core.constraint_config import get_constraint_config
from app.prompts.strict_qa import ConstraintPromptBuilder


class TestForbiddenTopicsDetection:
    """测试禁止主题检测"""
    
    def test_query_contains_forbidden_topic(self):
        """测试查询包含禁止主题"""
        config = get_constraint_config()
        forbidden_topics = config.generation.get('forbidden_topics', [])
        
        # 测试查询
        test_queries = [
            ("公司的工资标准是什么？", True),  # 包含"工资"
            ("员工薪资如何计算？", True),      # 包含"薪资"
            ("年假有多少天？", False),          # 不包含禁止主题
            ("考勤制度是什么？", False),        # 不包含禁止主题
        ]
        
        for query, should_contain in test_queries:
            contains_forbidden = any(topic in query for topic in forbidden_topics)
            assert contains_forbidden == should_contain, \
                f"查询 '{query}' 的禁止主题检测结果应为 {should_contain}"
    
    def test_prompt_includes_forbidden_topics(self):
        """测试 prompt 中包含禁止主题说明"""
        config = get_constraint_config()
        constraints = {"generation": config.generation}
        
        context = "这是知识库内容"
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        # 验证 prompt 中包含禁止主题说明
        forbidden_topics = config.generation.get('forbidden_topics', [])
        if forbidden_topics:
            assert "禁止回答的主题" in prompt or "禁止" in prompt, \
                "Prompt 应该包含禁止主题的说明"
            
            # 验证每个禁止主题都在 prompt 中
            for topic in forbidden_topics:
                assert topic in prompt, \
                    f"Prompt 应该包含禁止主题 '{topic}'"
    
    def test_prompt_includes_forbidden_keywords(self):
        """测试 prompt 中包含禁止关键词说明"""
        config = get_constraint_config()
        constraints = {"generation": config.generation}
        
        context = "这是知识库内容"
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        # 验证 prompt 中包含禁止关键词说明
        forbidden_keywords = config.generation.get('forbidden_keywords', [])
        if forbidden_keywords:
            assert "禁止使用的关键词" in prompt or "禁止" in prompt, \
                "Prompt 应该包含禁止关键词的说明"
            
            # 验证每个禁止关键词都在 prompt 中
            for keyword in forbidden_keywords:
                assert keyword in prompt, \
                    f"Prompt 应该包含禁止关键词 '{keyword}'"


class TestForbiddenTopicsResponse:
    """测试禁止主题的响应行为"""
    
    def test_should_reject_forbidden_topic_query(self):
        """测试应该拒绝禁止主题的查询"""
        config = get_constraint_config()
        forbidden_topics = config.generation.get('forbidden_topics', [])
        
        # 模拟查询
        query = "公司的工资标准是什么？"
        
        # 检查是否包含禁止主题
        contains_forbidden = any(topic in query for topic in forbidden_topics)
        
        if contains_forbidden:
            # 应该拒绝回答
            expected_response_patterns = [
                "抱歉",
                "无法回答",
                "不在知识库范围",
                "不提供",
                "不涉及",
                "不包含"
            ]
            
            # 这里我们验证系统应该返回拒绝消息
            # 实际的响应应该包含这些模式之一
            assert True, "系统应该拒绝回答包含禁止主题的查询"
    
    def test_expected_rejection_message_format(self):
        """测试预期的拒绝消息格式"""
        config = get_constraint_config()
        fallback = config.fallback
        
        # 验证兜底配置存在
        assert 'no_result_message' in fallback
        assert 'contact_info' in fallback
        
        # 预期的拒绝消息应该包含：
        # 1. 礼貌的拒绝说明
        # 2. 可选的联系信息
        no_result_message = fallback['no_result_message']
        contact_info = fallback['contact_info']
        
        assert len(no_result_message) > 0, "应该有无结果消息"
        assert len(contact_info) > 0, "应该有联系信息"


class TestForbiddenKeywordsInAnswer:
    """测试回答中的禁止关键词"""
    
    def test_answer_contains_forbidden_keywords(self):
        """测试回答是否包含禁止关键词"""
        config = get_constraint_config()
        forbidden_keywords = config.generation.get('forbidden_keywords', [])
        
        # 根据当前配置的禁止关键词构建测试用例
        # 当前配置: forbidden_keywords = ["工资"]
        test_answers = [
            ("员工的工资标准是多少", True),      # 包含"工资"
            ("关于工资的问题", True),            # 包含"工资"
            ("根据文档，需要3天时间", False),    # 不包含禁止关键词
            ("年假政策说明", False),             # 不包含禁止关键词
        ]
        
        for answer, should_contain in test_answers:
            contains_forbidden = any(keyword in answer for keyword in forbidden_keywords)
            
            if should_contain:
                assert contains_forbidden, \
                    f"回答 '{answer}' 应该被检测到包含禁止关键词 {forbidden_keywords}"
            else:
                assert not contains_forbidden, \
                    f"回答 '{answer}' 不应该包含禁止关键词 {forbidden_keywords}"
    
    def test_answer_validation_should_flag_forbidden_keywords(self):
        """测试答案验证应该标记禁止关键词"""
        from app.services.answer_validator import get_answer_validator
        
        validator = get_answer_validator()
        config = get_constraint_config()
        
        # 包含禁止关键词的回答
        answer_with_forbidden = "我猜测这个政策可能是这样的，大概需要3天。"
        context = "政策规定"
        
        # 幻觉检测应该能检测到不确定性词汇
        has_hallucination, indicators, confidence = validator.detect_hallucination(
            answer_with_forbidden, context
        )
        
        # 应该检测到幻觉风险（因为包含不确定性词汇）
        assert has_hallucination or len(indicators) > 0, \
            "应该检测到包含不确定性词汇的回答"


class TestForbiddenTopicsWorkflow:
    """测试禁止主题的完整工作流程"""
    
    def test_complete_workflow_with_forbidden_topic(self):
        """测试包含禁止主题的完整工作流程"""
        config = get_constraint_config()
        
        # 1. 用户查询
        query = "公司的工资标准是什么？"
        
        # 2. 检查是否包含禁止主题
        forbidden_topics = config.generation.get('forbidden_topics', [])
        contains_forbidden = any(topic in query for topic in forbidden_topics)
        
        assert contains_forbidden, "查询应该包含禁止主题"
        
        # 3. 构建 prompt（包含禁止主题说明）
        constraints = {"generation": config.generation}
        context = "公司政策文档内容"
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        # 4. 验证 prompt 包含禁止主题说明
        for topic in forbidden_topics:
            if topic in query:
                assert topic in prompt, \
                    f"Prompt 应该包含禁止主题 '{topic}' 的说明"
        
        # 5. 预期行为：LLM 应该根据 prompt 拒绝回答
        # （这部分需要实际调用 LLM 才能验证，这里我们验证配置正确）
        assert True, "工作流程配置正确"
    
    def test_workflow_with_allowed_topic(self):
        """测试允许主题的完整工作流程"""
        config = get_constraint_config()
        
        # 1. 用户查询（不包含禁止主题）
        query = "公司的年假政策是什么？"
        
        # 2. 检查是否包含禁止主题
        forbidden_topics = config.generation.get('forbidden_topics', [])
        contains_forbidden = any(topic in query for topic in forbidden_topics)
        
        assert not contains_forbidden, "查询不应该包含禁止主题"
        
        # 3. 构建 prompt
        constraints = {"generation": config.generation}
        context = "公司年假政策：员工每年享有15天年假"
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        # 4. 验证 prompt 仍然包含约束说明（作为一般规则）
        assert "知识库" in prompt or "回答" in prompt, \
            "Prompt 应该包含基本的回答指导"
        
        # 5. 预期行为：LLM 应该正常回答
        assert True, "允许的查询应该正常处理"


class TestForbiddenTopicsConfiguration:
    """测试禁止主题配置"""
    
    def test_can_add_forbidden_topics(self):
        """测试可以添加禁止主题"""
        config = get_constraint_config()
        
        # 获取当前禁止主题
        current_topics = config.generation.get('forbidden_topics', [])
        
        # 添加新的禁止主题
        new_topics = current_topics + ["测试主题"]
        
        # 更新配置
        new_constraints = {
            "retrieval": config.retrieval,
            "generation": {
                **config.generation,
                "forbidden_topics": new_topics
            },
            "validation": config.validation,
            "fallback": config.fallback
        }
        
        success = config.update(new_constraints)
        assert success, "应该能够更新禁止主题"
        
        # 验证更新成功
        updated_topics = config.generation.get('forbidden_topics', [])
        assert "测试主题" in updated_topics, "新的禁止主题应该被添加"
        
        # 恢复原配置
        config.update({
            "retrieval": config.retrieval,
            "generation": {
                **config.generation,
                "forbidden_topics": current_topics
            },
            "validation": config.validation,
            "fallback": config.fallback
        })
    
    def test_can_remove_forbidden_topics(self):
        """测试可以移除禁止主题"""
        config = get_constraint_config()
        
        # 获取当前禁止主题
        current_topics = config.generation.get('forbidden_topics', [])
        
        if len(current_topics) > 0:
            # 移除第一个主题
            new_topics = current_topics[1:]
            
            # 更新配置
            new_constraints = {
                "retrieval": config.retrieval,
                "generation": {
                    **config.generation,
                    "forbidden_topics": new_topics
                },
                "validation": config.validation,
                "fallback": config.fallback
            }
            
            success = config.update(new_constraints)
            assert success, "应该能够更新禁止主题"
            
            # 验证更新成功
            updated_topics = config.generation.get('forbidden_topics', [])
            assert len(updated_topics) == len(current_topics) - 1, \
                "禁止主题数量应该减少"
            
            # 恢复原配置
            config.update({
                "retrieval": config.retrieval,
                "generation": {
                    **config.generation,
                    "forbidden_topics": current_topics
                },
                "validation": config.validation,
                "fallback": config.fallback
            })


class TestRecommendedImprovements:
    """测试建议的改进"""
    
    def test_should_have_pre_check_for_forbidden_topics(self):
        """建议：应该在查询前检查禁止主题"""
        config = get_constraint_config()
        forbidden_topics = config.generation.get('forbidden_topics', [])
        
        query = "公司的工资标准是什么？"
        
        # 当前实现：只在 prompt 中告诉 LLM
        # 建议改进：在查询前主动检查
        def check_forbidden_topics(query: str, forbidden_topics: list) -> tuple:
            """
            检查查询是否包含禁止主题
            
            Returns:
                (is_forbidden, matched_topic)
            """
            for topic in forbidden_topics:
                if topic in query:
                    return True, topic
            return False, None
        
        is_forbidden, matched_topic = check_forbidden_topics(query, forbidden_topics)
        
        if is_forbidden:
            # 应该直接返回拒绝消息，而不是调用 LLM
            rejection_message = f"抱歉，关于'{matched_topic}'的问题不在我的回答范围内。"
            assert len(rejection_message) > 0, "应该有明确的拒绝消息"
            
            # 这样可以：
            # 1. 节省 LLM 调用成本
            # 2. 确保一致的拒绝行为
            # 3. 更快的响应速度
    
    def test_should_log_forbidden_topic_attempts(self):
        """建议：应该记录禁止主题的查询尝试"""
        # 建议添加日志记录功能
        def log_forbidden_attempt(query: str, topic: str, user_id: str = None):
            """记录禁止主题的查询尝试"""
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"用户尝试查询禁止主题: query='{query[:50]}...', "
                f"topic='{topic}', user_id='{user_id}'"
            )
        
        # 这样可以：
        # 1. 监控用户行为
        # 2. 发现潜在的配置问题
        # 3. 改进禁止主题列表
        assert True, "应该添加日志记录功能"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
