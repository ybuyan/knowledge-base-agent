"""
测试 suggest_questions.types 配置

测试根据类型生成不同风格的建议问题
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.suggestion_generator import SuggestionGenerator
from app.core.constraint_config import ConstraintConfig


class TestSuggestionTypes:
    """测试 suggest_questions.types 配置"""

    @pytest.mark.asyncio
    async def test_generate_with_types(self):
        """测试使用类型配置生成问题"""
        generator = SuggestionGenerator()
        
        # Mock 配置
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.suggest_questions = {
            'enabled': True,
            'count': 3,
            'types': ['相关追问', '深入探索', '对比分析']
        }
        
        with patch('app.services.suggestion_generator.get_constraint_config', return_value=mock_config):
            with patch('app.services.suggestion_generator.get_llm_client') as mock_llm:
                # Mock LLM 响应
                mock_client = AsyncMock()
                mock_client.chat = AsyncMock(side_effect=[
                    '这个政策的具体内容是什么？',
                    '详细的申请流程有哪些步骤？',
                    '与其他类似政策有什么区别？'
                ])
                mock_llm.return_value = mock_client
                
                # 生成建议
                suggestions = await generator.generate(
                    question="公司的年假政策是什么？",
                    answer="公司年假政策规定：入职满1年享受5天年假。"
                )
                
                # 验证
                assert len(suggestions) == 3
                assert all(isinstance(s, str) for s in suggestions)
                assert all(len(s) > 0 for s in suggestions)

    @pytest.mark.asyncio
    async def test_generate_without_types(self):
        """测试不使用类型配置（向后兼容）"""
        generator = SuggestionGenerator()
        
        # Mock 配置（不设置 types）
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.suggest_questions = {
            'enabled': True,
            'count': 3,
            'types': []  # 空列表
        }
        
        with patch('app.services.suggestion_generator.get_constraint_config', return_value=mock_config):
            with patch('app.services.suggestion_generator.get_llm_client') as mock_llm:
                # Mock LLM 响应（默认方式）
                mock_client = AsyncMock()
                mock_client.chat = AsyncMock(return_value="""1. 年假如何申请？
2. 年假可以累积吗？
3. 年假的有效期是多久？""")
                mock_llm.return_value = mock_client
                
                # 生成建议
                suggestions = await generator.generate(
                    question="公司的年假政策是什么？",
                    answer="公司年假政策规定：入职满1年享受5天年假。"
                )
                
                # 验证
                assert len(suggestions) == 3
                # 验证包含预期的问题（可能有编号被移除）
                assert any('年假如何申请' in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_different_question_types(self):
        """测试不同类型生成不同风格的问题"""
        generator = SuggestionGenerator()
        
        # Mock 配置
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.suggest_questions = {
            'enabled': True,
            'count': 3,  # 只要3个
            'types': ['相关追问', '深入探索', '对比分析', '实际应用', '背景原因']
        }
        
        with patch('app.services.suggestion_generator.get_constraint_config', return_value=mock_config):
            with patch('app.services.suggestion_generator.get_llm_client') as mock_llm:
                # Mock LLM 响应（只会调用前3个类型）
                mock_client = AsyncMock()
                mock_client.chat = AsyncMock(side_effect=[
                    '年假的计算方式是怎样的？',  # 相关追问
                    '年假申请需要提前多久？',  # 深入探索
                    '年假和病假有什么区别？',  # 对比分析
                ])
                mock_llm.return_value = mock_client
                
                # 生成建议
                suggestions = await generator.generate(
                    question="公司的年假政策是什么？",
                    answer="公司年假政策规定：入职满1年享受5天年假。"
                )
                
                # 验证
                assert len(suggestions) == 3
                # 验证不同类型的问题风格不同
                assert any('计算' in s or '怎样' in s for s in suggestions)
                assert any('申请' in s or '提前' in s for s in suggestions)

    @pytest.mark.asyncio
    async def test_fallback_when_type_generation_fails(self):
        """测试类型生成失败时的降级处理"""
        generator = SuggestionGenerator()
        
        # Mock 配置
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.suggest_questions = {
            'enabled': True,
            'count': 3,
            'types': ['相关追问', '深入探索', '对比分析']
        }
        
        with patch('app.services.suggestion_generator.get_constraint_config', return_value=mock_config):
            with patch('app.services.suggestion_generator.get_llm_client') as mock_llm:
                # Mock LLM 响应（部分失败）
                mock_client = AsyncMock()
                mock_client.chat = AsyncMock(side_effect=[
                    '年假如何申请？',  # 成功
                    Exception('LLM error'),  # 失败
                    '年假和病假的区别？',  # 成功
                    '年假可以累积吗？'  # 补充
                ])
                mock_llm.return_value = mock_client
                
                # 生成建议
                suggestions = await generator.generate(
                    question="公司的年假政策是什么？",
                    answer="公司年假政策规定：入职满1年享受5天年假。"
                )
                
                # 验证：即使部分失败，仍然返回足够的建议
                assert len(suggestions) >= 2

    @pytest.mark.asyncio
    async def test_unknown_type_uses_default(self):
        """测试未知类型使用默认模板"""
        generator = SuggestionGenerator()
        
        # Mock 配置（包含未知类型）
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.suggest_questions = {
            'enabled': True,
            'count': 2,
            'types': ['未知类型', '相关追问']
        }
        
        with patch('app.services.suggestion_generator.get_constraint_config', return_value=mock_config):
            with patch('app.services.suggestion_generator.get_llm_client') as mock_llm:
                # Mock LLM 响应
                mock_client = AsyncMock()
                mock_client.chat = AsyncMock(side_effect=[
                    '这个政策什么时候生效？',  # 未知类型使用默认
                    '年假如何申请？'  # 相关追问
                ])
                mock_llm.return_value = mock_client
                
                # 生成建议
                suggestions = await generator.generate(
                    question="公司的年假政策是什么？",
                    answer="公司年假政策规定：入职满1年享受5天年假。"
                )
                
                # 验证：未知类型也能正常生成
                assert len(suggestions) >= 2  # 至少2个
                assert len(suggestions) <= 2  # 最多2个

    @pytest.mark.asyncio
    async def test_count_limits_suggestions(self):
        """测试 count 参数限制建议数量"""
        generator = SuggestionGenerator()
        
        # Mock 配置
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.suggest_questions = {
            'enabled': True,
            'count': 2,  # 只要 2 个
            'types': ['相关追问', '深入探索', '对比分析']  # 配置了 3 个类型
        }
        
        with patch('app.services.suggestion_generator.get_constraint_config', return_value=mock_config):
            with patch('app.services.suggestion_generator.get_llm_client') as mock_llm:
                # Mock LLM 响应（只会调用前2个）
                mock_client = AsyncMock()
                mock_client.chat = AsyncMock(side_effect=[
                    '年假如何申请？',
                    '详细的申请流程？'
                ])
                mock_llm.return_value = mock_client
                
                # 生成建议
                suggestions = await generator.generate(
                    question="公司的年假政策是什么？",
                    answer="公司年假政策规定：入职满1年享受5天年假。"
                )
                
                # 验证：只返回 2 个
                assert len(suggestions) == 2
                # 验证返回的是正确的建议
                assert '年假如何申请？' in suggestions
                assert '详细的申请流程？' in suggestions


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
