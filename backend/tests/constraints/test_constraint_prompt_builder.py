"""
测试约束提示词构建器

验证 ConstraintPromptBuilder 是否正确应用各项约束配置。
"""

import pytest
from app.prompts.strict_qa import ConstraintPromptBuilder


class TestConstraintPromptBuilder:
    """测试约束提示词构建器"""
    
    def test_strict_mode_enabled(self):
        """测试启用严格模式"""
        context = "测试上下文"
        constraints = {
            'generation': {
                'strict_mode': True
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        assert "严格模式" in prompt
        assert "只基于提供的知识库内容回答" in prompt
        assert "不要添加任何推测或假设" in prompt
    
    def test_strict_mode_disabled(self):
        """测试禁用严格模式"""
        context = "测试上下文"
        constraints = {
            'generation': {
                'strict_mode': False
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        # 禁用严格模式时，不应包含严格模式说明
        assert "严格模式" not in prompt
    
    def test_allow_general_knowledge_false(self):
        """测试不允许通用知识"""
        context = "测试上下文"
        constraints = {
            'generation': {
                'allow_general_knowledge': False
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        assert "知识来源限制" in prompt
        assert "严格限制：只能使用上述知识库内容回答" in prompt
        assert "不要使用你的训练数据中的通用知识" in prompt
    
    def test_allow_general_knowledge_true(self):
        """测试允许通用知识"""
        context = "测试上下文"
        constraints = {
            'generation': {
                'allow_general_knowledge': True
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        assert "知识来源" in prompt
        assert "优先使用上述知识库内容" in prompt
        assert "可以适当补充通用知识" in prompt
    
    def test_require_citations_enabled(self):
        """测试启用引用要求"""
        context = "测试上下文"
        constraints = {
            'generation': {
                'require_citations': True
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        assert "引用要求" in prompt
        assert "必须在回答中标注信息来源" in prompt
        assert "[1]、[2]" in prompt
    
    def test_require_citations_disabled(self):
        """测试禁用引用要求"""
        context = "测试上下文"
        constraints = {
            'generation': {
                'require_citations': False
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        # 禁用引用要求时，不应包含引用要求说明
        assert "引用要求" not in prompt
    
    def test_forbidden_topics(self):
        """测试禁止主题"""
        context = "测试上下文"
        constraints = {
            'generation': {
                'forbidden_topics': ['薪资', '工资', '奖金']
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        assert "禁止回答的主题" in prompt
        assert "薪资" in prompt
        assert "工资" in prompt
        assert "奖金" in prompt
    
    def test_forbidden_keywords(self):
        """测试禁止关键词"""
        context = "测试上下文"
        constraints = {
            'generation': {
                'forbidden_keywords': ['工资', '薪水', '收入']
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        assert "禁止使用的关键词" in prompt
        assert "工资" in prompt
        assert "薪水" in prompt
        assert "收入" in prompt
    
    def test_multiple_constraints(self):
        """测试多个约束同时应用"""
        context = "测试上下文"
        constraints = {
            'generation': {
                'strict_mode': True,
                'allow_general_knowledge': False,
                'require_citations': True,
                'forbidden_topics': ['薪资'],
                'forbidden_keywords': ['工资']
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        # 验证所有约束都被应用
        assert "严格模式" in prompt
        assert "知识来源限制" in prompt
        assert "引用要求" in prompt
        assert "禁止回答的主题" in prompt
        assert "禁止使用的关键词" in prompt
        assert "薪资" in prompt
        assert "工资" in prompt
    
    def test_empty_constraints(self):
        """测试空约束"""
        context = "测试上下文"
        constraints = {}
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        # 应该返回基础提示词
        assert prompt is not None
        assert len(prompt) > 0
    
    def test_none_constraints(self):
        """测试 None 约束"""
        context = "测试上下文"
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, None)
        
        # 应该返回基础提示词
        assert prompt is not None
        assert len(prompt) > 0
    
    def test_context_in_prompt(self):
        """测试上下文是否包含在提示词中"""
        context = "这是一个测试上下文内容"
        constraints = {
            'generation': {
                'strict_mode': True
            }
        }
        
        prompt = ConstraintPromptBuilder.build_system_prompt(context, constraints)
        
        # 上下文应该被包含在提示词中
        assert context in prompt or "{context}" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
