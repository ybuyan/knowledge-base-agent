"""
测试 fallback.suggest_contact 配置

测试联系信息显示开关功能
"""

import pytest
from unittest.mock import MagicMock
from app.prompts.strict_qa import StrictQAPrompt
from app.core.constraint_config import ConstraintConfig


class TestSuggestContact:
    """测试 suggest_contact 配置"""

    def test_suggest_contact_enabled(self):
        """测试启用联系信息建议"""
        config = MagicMock(spec=ConstraintConfig)
        config.fallback = {
            'no_result_message': '未找到相关信息',
            'suggest_contact': True,
            'contact_info': '请联系：support@company.com'
        }

        message = StrictQAPrompt.get_fallback_message(config)

        assert '未找到相关信息' in message
        assert 'support@company.com' in message

    def test_suggest_contact_disabled(self):
        """测试禁用联系信息建议"""
        config = MagicMock(spec=ConstraintConfig)
        config.fallback = {
            'no_result_message': '未找到相关信息',
            'suggest_contact': False,
            'contact_info': '请联系：support@company.com'
        }

        message = StrictQAPrompt.get_fallback_message(config)

        assert '未找到相关信息' in message
        assert 'support@company.com' not in message

    def test_suggest_contact_default_true(self):
        """测试默认启用联系信息"""
        config = MagicMock(spec=ConstraintConfig)
        config.fallback = {
            'no_result_message': '未找到相关信息',
            # 不设置 suggest_contact，应该默认为 True
            'contact_info': '请联系：support@company.com'
        }

        message = StrictQAPrompt.get_fallback_message(config)

        assert '未找到相关信息' in message
        assert 'support@company.com' in message

    def test_suggest_contact_no_contact_info(self):
        """测试没有联系信息时"""
        config = MagicMock(spec=ConstraintConfig)
        config.fallback = {
            'no_result_message': '未找到相关信息',
            'suggest_contact': True,
            'contact_info': ''
        }

        message = StrictQAPrompt.get_fallback_message(config)

        assert '未找到相关信息' in message
        # 没有联系信息，不应该添加空行
        assert message == '未找到相关信息'

    def test_backward_compatibility(self):
        """测试向后兼容性"""
        # 不传 config，使用旧的参数方式
        message = StrictQAPrompt.get_fallback_message(
            contact_info="请联系管理员"
        )

        # 应该能正常工作
        assert isinstance(message, str)
        assert len(message) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
