"""
答案验证器测试

测试 AnswerValidator 类的各种验证功能
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.answer_validator import (
    AnswerValidator,
    ValidationResult,
    get_answer_validator
)
from app.core.constraint_config import ConstraintConfig


class TestAnswerValidatorSingleton:
    """测试验证器单例"""
    
    def test_get_answer_validator_returns_singleton(self):
        """测试获取验证器单例"""
        validator1 = get_answer_validator()
        validator2 = get_answer_validator()
        assert validator1 is validator2


class TestRetrievalValidation:
    """测试检索验证功能"""
    
    @pytest.fixture
    def validator(self):
        return AnswerValidator()
    
    @pytest.fixture
    def sample_documents(self):
        return [
            "这是第一个文档内容",
            "这是第二个文档内容",
            "这是第三个文档内容"
        ]
    
    @pytest.fixture
    def sample_metadatas(self):
        return [
            {"source": "doc1.pdf", "page": 1},
            {"source": "doc2.pdf", "page": 2},
            {"source": "doc3.pdf", "page": 3}
        ]
    
    def test_validate_retrieval_filters_low_similarity(self, validator, sample_documents, sample_metadatas):
        """测试过滤低相似度文档"""
        distances = [0.2, 0.8, 1.5]  # 相似度: 0.9, 0.6, 0.25
        
        with patch.object(validator.config, 'retrieval', {
            'enabled': True,
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }):
            filtered_docs, filtered_contents = validator.validate_retrieval(
                sample_documents, sample_metadatas, distances
            )
            
            # 只有第一个文档相似度 >= 0.7
            assert len(filtered_docs) == 1
            assert filtered_docs[0]['similarity'] >= 0.7
            assert filtered_docs[0]['content'] == "这是第一个文档内容"
    
    def test_validate_retrieval_respects_max_docs(self, validator, sample_documents, sample_metadatas):
        """测试最大文档数限制"""
        distances = [0.1, 0.2, 0.3]  # 所有相似度都很高
        
        with patch.object(validator.config, 'retrieval', {
            'enabled': True,
            'min_similarity_score': 0.5,
            'max_relevant_docs': 2
        }):
            filtered_docs, filtered_contents = validator.validate_retrieval(
                sample_documents, sample_metadatas, distances
            )
            
            # 最多保留 2 个文档
            assert len(filtered_docs) == 2
            assert len(filtered_contents) == 2
    
    def test_validate_retrieval_disabled(self, validator, sample_documents, sample_metadatas):
        """测试检索验证禁用时返回所有文档"""
        distances = [0.5, 1.0, 1.5]
        
        with patch.object(validator.config, 'retrieval', {
            'enabled': False,
            'min_similarity_score': 0.9,
            'max_relevant_docs': 1
        }):
            filtered_docs, filtered_contents = validator.validate_retrieval(
                sample_documents, sample_metadatas, distances
            )
            
            # 禁用时返回所有文档
            assert len(filtered_docs) == 3
            assert len(filtered_contents) == 3
    
    def test_validate_retrieval_empty_input(self, validator):
        """测试空输入"""
        filtered_docs, filtered_contents = validator.validate_retrieval([], [], [])
        
        assert filtered_docs == []
        assert filtered_contents == []


class TestSourceAttributionCheck:
    """测试来源归属检查"""
    
    @pytest.fixture
    def validator(self):
        return AnswerValidator()
    
    def test_check_source_attribution_with_citations(self, validator):
        """测试包含引用标记的回答"""
        answer = "根据文档[1]，公司政策规定员工需要遵守考勤制度。"
        sources = [{"content": "考勤制度规定", "source": "doc1.pdf"}]
        
        with patch.object(validator.config, 'validation', {
            'check_source_attribution': True
        }):
            has_attribution, warnings = validator.check_source_attribution(answer, sources)
            
            assert has_attribution == True
            assert len(warnings) == 0
    
    def test_check_source_attribution_without_citations(self, validator):
        """测试不包含引用标记的回答"""
        answer = "公司政策规定员工需要遵守考勤制度。"
        sources = [{"content": "考勤制度规定", "source": "doc1.pdf"}]
        
        with patch.object(validator.config, 'validation', {
            'check_source_attribution': True
        }):
            has_attribution, warnings = validator.check_source_attribution(answer, sources)
            
            assert has_attribution == False
            assert any("没有引用标记" in w for w in warnings)
    
    def test_check_source_attribution_no_sources(self, validator):
        """测试没有来源的回答"""
        answer = "这是一个回答"
        sources = []
        
        with patch.object(validator.config, 'validation', {
            'check_source_attribution': True
        }):
            has_attribution, warnings = validator.check_source_attribution(answer, sources)
            
            assert has_attribution == False
            assert any("没有引用来源" in w for w in warnings)
    
    def test_check_source_attribution_disabled(self, validator):
        """测试来源检查禁用"""
        answer = "这是一个回答"
        sources = []
        
        with patch.object(validator.config, 'validation', {
            'check_source_attribution': False
        }):
            has_attribution, warnings = validator.check_source_attribution(answer, sources)
            
            assert has_attribution == True
            assert len(warnings) == 0
    
    def test_check_source_attribution_low_overlap(self, validator):
        """测试回答与来源内容重叠度低"""
        answer = "完全不相关的内容"
        sources = [{"content": "这是来源文档的内容", "source": "doc1.pdf"}]
        
        with patch.object(validator.config, 'validation', {
            'check_source_attribution': True
        }):
            has_attribution, warnings = validator.check_source_attribution(answer, sources)
            
            assert any("重叠度较低" in w for w in warnings)


class TestHallucinationDetection:
    """测试幻觉检测"""
    
    @pytest.fixture
    def validator(self):
        return AnswerValidator()
    
    def test_detect_hallucination_with_uncertainty_words(self, validator):
        """测试检测不确定性词汇"""
        answer = "我猜测这个政策可能是这样的，大概需要3天时间。"
        context = "政策规定"
        
        with patch.object(validator.config, 'validation', {
            'hallucination_detection': True
        }):
            has_hallucination, indicators, confidence = validator.detect_hallucination(answer, context)
            
            assert has_hallucination == True
            assert len(indicators) > 0
            assert confidence < 1.0
    
    def test_detect_hallucination_with_unsupported_content(self, validator):
        """测试检测缺乏上下文支持的内容"""
        answer = "公司规定员工每天工作8小时，周末双休，享受15天年假。"
        context = "公司有考勤制度"
        
        with patch.object(validator.config, 'validation', {
            'hallucination_detection': True
        }):
            has_hallucination, indicators, confidence = validator.detect_hallucination(answer, context)
            
            # 回答中的具体信息在上下文中找不到
            assert len(indicators) > 0
    
    def test_detect_hallucination_with_numbers_not_in_context(self, validator):
        """测试检测上下文中不存在的数字"""
        answer = "员工需要工作8小时，工资5000元。"
        context = "员工需要遵守考勤制度"
        
        with patch.object(validator.config, 'validation', {
            'hallucination_detection': True
        }):
            has_hallucination, indicators, confidence = validator.detect_hallucination(answer, context)
            
            # 数字不在上下文中
            assert any("数字" in i for i in indicators)
    
    def test_detect_hallucination_disabled(self, validator):
        """测试幻觉检测禁用"""
        answer = "我猜测这个政策可能是这样的"
        context = "政策规定"
        
        with patch.object(validator.config, 'validation', {
            'hallucination_detection': False
        }):
            has_hallucination, indicators, confidence = validator.detect_hallucination(answer, context)
            
            assert has_hallucination == False
            assert len(indicators) == 0
            assert confidence == 1.0
    
    def test_detect_hallucination_clean_answer(self, validator):
        """测试没有幻觉的回答"""
        answer = "根据文档，公司有考勤制度。"
        context = "公司有考勤制度，员工需要遵守。"
        
        with patch.object(validator.config, 'validation', {
            'hallucination_detection': True
        }):
            has_hallucination, indicators, confidence = validator.detect_hallucination(answer, context)
            
            assert has_hallucination == False
            assert confidence > 0.7


class TestConfidenceCalculation:
    """测试置信度计算"""
    
    @pytest.fixture
    def validator(self):
        return AnswerValidator()
    
    def test_calculate_confidence_high_quality(self, validator):
        """测试高质量回答的置信度"""
        answer = "根据文档[1]，公司规定员工需要遵守考勤制度。这包括按时上下班和请假流程。"
        sources = [
            {"content": "考勤制度规定员工需要按时上下班", "source": "doc1.pdf"},
            {"content": "请假流程说明", "source": "doc2.pdf"}
        ]
        context = "考勤制度规定员工需要按时上下班。请假流程说明。"
        
        confidence = validator.calculate_confidence(answer, sources, context, retrieval_quality=0.9)
        
        assert confidence > 0.8
    
    def test_calculate_confidence_short_answer(self, validator):
        """测试过短回答的置信度惩罚"""
        answer = "是的"
        sources = [{"content": "内容", "source": "doc1.pdf"}]
        context = "内容"
        
        confidence = validator.calculate_confidence(answer, sources, context, retrieval_quality=1.0)
        
        # 过短的回答应该有惩罚
        assert confidence < 0.8
    
    def test_calculate_confidence_long_answer(self, validator):
        """测试过长回答的置信度惩罚"""
        answer = "这是一个非常长的回答。" * 200  # 超过 2000 字符
        sources = [{"content": "内容", "source": "doc1.pdf"}]
        context = "内容"
        
        confidence = validator.calculate_confidence(answer, sources, context, retrieval_quality=1.0)
        
        # 过长的回答应该有轻微惩罚
        assert confidence < 1.0
    
    def test_calculate_confidence_with_hallucination(self, validator):
        """测试有幻觉风险的回答置信度"""
        answer = "我猜测可能是这样的，大概需要3天。"
        sources = [{"content": "内容", "source": "doc1.pdf"}]
        context = "内容"
        
        confidence = validator.calculate_confidence(answer, sources, context, retrieval_quality=1.0)
        
        # 有幻觉风险应该降低置信度
        assert confidence < 0.8
    
    def test_calculate_confidence_multiple_sources_bonus(self, validator):
        """测试多来源加分"""
        answer = "根据多个文档的说明"
        sources = [
            {"content": "内容1", "source": "doc1.pdf"},
            {"content": "内容2", "source": "doc2.pdf"},
            {"content": "内容3", "source": "doc3.pdf"}
        ]
        context = "内容1 内容2 内容3"
        
        confidence = validator.calculate_confidence(answer, sources, context, retrieval_quality=0.8)
        
        # 多来源应该提高置信度
        assert confidence >= 0.8


class TestValidateAnswer:
    """测试综合答案验证"""
    
    @pytest.fixture
    def validator(self):
        return AnswerValidator()
    
    def test_validate_answer_valid(self, validator):
        """测试验证有效回答"""
        answer = "根据文档[1]，公司规定员工需要遵守考勤制度。"
        sources = [{"content": "考勤制度规定员工需要遵守", "source": "doc1.pdf"}]
        context = "考勤制度规定员工需要遵守"
        
        with patch.object(validator.config, 'validation', {
            'enabled': True,
            'check_source_attribution': True,
            'min_confidence_score': 0.6,
            'hallucination_detection': True
        }):
            result = validator.validate_answer(answer, sources, context, retrieval_quality=0.9)
            
            assert isinstance(result, ValidationResult)
            assert result.is_valid == True
            assert result.confidence_score >= 0.6
            assert result.has_source_attribution == True
    
    def test_validate_answer_invalid_low_confidence(self, validator):
        """测试验证低置信度回答"""
        answer = "我猜测可能是这样的"
        sources = []
        context = ""
        
        with patch.object(validator.config, 'validation', {
            'enabled': True,
            'check_source_attribution': True,
            'min_confidence_score': 0.6,
            'hallucination_detection': True
        }):
            result = validator.validate_answer(answer, sources, context, retrieval_quality=0.3)
            
            assert result.is_valid == False
            assert result.confidence_score < 0.6
            assert len(result.warnings) > 0
    
    def test_validate_answer_disabled(self, validator):
        """测试验证禁用时总是返回有效"""
        answer = "任意回答"
        sources = []
        context = ""
        
        with patch.object(validator.config, 'validation', {
            'enabled': False
        }):
            result = validator.validate_answer(answer, sources, context)
            
            assert result.is_valid == True
            assert result.confidence_score == 1.0
    
    def test_validate_answer_with_hallucination(self, validator):
        """测试验证有幻觉的回答"""
        answer = "我猜测这个政策可能是这样的，大概需要3天时间。"
        sources = [{"content": "政策说明", "source": "doc1.pdf"}]
        context = "政策说明"
        
        with patch.object(validator.config, 'validation', {
            'enabled': True,
            'check_source_attribution': True,
            'min_confidence_score': 0.6,
            'hallucination_detection': True
        }):
            result = validator.validate_answer(answer, sources, context)
            
            assert result.potential_hallucination == True
            assert len(result.warnings) > 0


class TestHallucinationIndicators:
    """测试幻觉指示词"""
    
    def test_hallucination_indicators_list(self):
        """测试幻觉指示词列表"""
        indicators = AnswerValidator.HALLUCINATION_INDICATORS
        
        assert "我猜测" in indicators
        assert "可能" in indicators
        assert "大概" in indicators
        assert "也许" in indicators
        assert "不确定" in indicators


class TestNoInfoKeywords:
    """测试无信息关键词"""
    
    def test_no_info_keywords_list(self):
        """测试无信息关键词列表"""
        keywords = AnswerValidator.NO_INFO_KEYWORDS
        
        assert "没有找到相关信息" in keywords
        assert "知识库中没有" in keywords
        assert "抱歉" in keywords
        assert "未找到" in keywords


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
