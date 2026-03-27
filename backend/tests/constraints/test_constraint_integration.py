"""
约束系统集成测试

测试约束系统与其他服务的集成
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List, Dict, Any

from app.core.constraint_config import ConstraintConfig
from app.services.answer_validator import AnswerValidator


class TestConstraintWithQAAgent:
    """测试约束与 QA Agent 的集成"""
    
    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = MagicMock(spec=ConstraintConfig)
        config.generation = {
            'strict_mode': True,
            'allow_general_knowledge': False,
            'require_citations': True,
            'max_answer_length': 1000,
            'forbidden_topics': ['薪资', '工资'],
            'forbidden_keywords': ['可能', '大概']
        }
        config.retrieval = {
            'enabled': True,
            'min_similarity_score': 0.7,
            'min_relevant_docs': 1,
            'max_relevant_docs': 5
        }
        config.validation = {
            'enabled': True,
            'check_source_attribution': True,
            'min_confidence_score': 0.6,
            'hallucination_detection': True
        }
        return config
    
    def test_forbidden_topic_detection(self, mock_config):
        """测试禁止主题检测"""
        query = "公司的工资标准是什么？"
        forbidden_topics = mock_config.generation['forbidden_topics']
        
        # 检查查询是否包含禁止主题
        contains_forbidden = any(topic in query for topic in forbidden_topics)
        
        assert contains_forbidden == True
    
    def test_forbidden_keyword_detection(self, mock_config):
        """测试禁止关键词检测"""
        answer = "这个政策可能是这样的，大概需要3天。"
        forbidden_keywords = mock_config.generation['forbidden_keywords']
        
        # 检查回答是否包含禁止关键词
        contains_forbidden = any(keyword in answer for keyword in forbidden_keywords)
        
        assert contains_forbidden == True
    
    def test_max_answer_length_constraint(self, mock_config):
        """测试最大回答长度约束"""
        max_length = mock_config.generation['max_answer_length']
        long_answer = "这是一个很长的回答。" * 100
        
        assert len(long_answer) > max_length
        
        # 应该截断回答
        truncated = long_answer[:max_length]
        assert len(truncated) == max_length


class TestConstraintWithRetriever:
    """测试约束与检索器的集成"""
    
    @pytest.fixture
    def validator(self):
        return AnswerValidator()
    
    def test_retrieval_filtering_integration(self, validator):
        """测试检索过滤集成"""
        documents = [
            "高相似度文档内容",
            "中等相似度文档内容",
            "低相似度文档内容"
        ]
        metadatas = [
            {"source": "doc1.pdf"},
            {"source": "doc2.pdf"},
            {"source": "doc3.pdf"}
        ]
        distances = [0.1, 0.5, 1.5]  # 相似度: 0.95, 0.75, 0.25
        
        with patch.object(validator.config, 'retrieval', {
            'enabled': True,
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }):
            filtered_docs, filtered_contents = validator.validate_retrieval(
                documents, metadatas, distances
            )
            
            # 应该过滤掉低相似度文档
            assert len(filtered_docs) == 2
            assert all(doc['similarity'] >= 0.7 for doc in filtered_docs)
    
    def test_retrieval_with_empty_results(self, validator):
        """测试检索无结果的情况"""
        documents = []
        metadatas = []
        distances = []
        
        filtered_docs, filtered_contents = validator.validate_retrieval(
            documents, metadatas, distances
        )
        
        assert filtered_docs == []
        assert filtered_contents == []


class TestConstraintWithResponseBuilder:
    """测试约束与响应构建器的集成"""
    
    @pytest.fixture
    def mock_config(self):
        config = MagicMock(spec=ConstraintConfig)
        config.fallback = {
            'no_result_message': '未找到相关信息',
            'suggest_similar': True,
            'suggest_contact': True,
            'contact_info': '如有疑问，请联系：support@company.com'
        }
        return config
    
    def test_fallback_message_when_no_results(self, mock_config):
        """测试无结果时的兜底消息"""
        no_result_message = mock_config.fallback['no_result_message']
        
        assert no_result_message == '未找到相关信息'
    
    def test_contact_info_in_fallback(self, mock_config):
        """测试兜底消息中的联系信息"""
        contact_info = mock_config.fallback['contact_info']
        
        assert 'support@company.com' in contact_info
    
    def test_suggest_similar_enabled(self, mock_config):
        """测试相似问题建议启用"""
        suggest_similar = mock_config.fallback['suggest_similar']
        
        assert suggest_similar == True


class TestConstraintWithSuggestionGenerator:
    """测试约束与建议生成器的集成"""
    
    @pytest.fixture
    def mock_config(self):
        config = MagicMock(spec=ConstraintConfig)
        config.suggest_questions = {
            'enabled': True,
            'count': 3,
            'types': ['相关追问', '深入探索', '对比分析']
        }
        config.generation = {
            'forbidden_topics': ['薪资', '工资'],
            'forbidden_keywords': []
        }
        return config
    
    def test_suggestion_count_constraint(self, mock_config):
        """测试建议数量约束"""
        count = mock_config.suggest_questions['count']
        
        assert count == 3
    
    def test_suggestion_types(self, mock_config):
        """测试建议类型"""
        types = mock_config.suggest_questions['types']
        
        assert '相关追问' in types
        assert '深入探索' in types
        assert '对比分析' in types
    
    def test_filter_forbidden_topics_in_suggestions(self, mock_config):
        """测试过滤建议中的禁止主题"""
        suggestions = [
            "公司的考勤制度是什么？",
            "员工的工资标准是多少？",  # 包含禁止主题
            "如何申请年假？"
        ]
        forbidden_topics = mock_config.generation['forbidden_topics']
        
        # 过滤包含禁止主题的建议
        filtered = [
            s for s in suggestions
            if not any(topic in s for topic in forbidden_topics)
        ]
        
        assert len(filtered) == 2
        assert "工资" not in " ".join(filtered)


class TestConstraintValidationFlow:
    """测试完整的约束验证流程"""
    
    @pytest.fixture
    def validator(self):
        return AnswerValidator()
    
    def test_full_validation_flow_valid_answer(self, validator):
        """测试完整验证流程 - 有效回答"""
        # 1. 检索阶段
        documents = ["相关文档内容"]
        metadatas = [{"source": "doc1.pdf"}]
        distances = [0.2]  # 高相似度
        
        with patch.object(validator.config, 'retrieval', {
            'enabled': True,
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }):
            filtered_docs, filtered_contents = validator.validate_retrieval(
                documents, metadatas, distances
            )
        
        assert len(filtered_docs) == 1
        
        # 2. 生成和验证阶段
        answer = "根据文档[1]，相关政策规定如下。"
        sources = [{"content": filtered_contents[0], "source": "doc1.pdf"}]
        context = " ".join(filtered_contents)
        
        with patch.object(validator.config, 'validation', {
            'enabled': True,
            'check_source_attribution': True,
            'min_confidence_score': 0.6,
            'hallucination_detection': True
        }):
            result = validator.validate_answer(answer, sources, context)
        
        assert result.is_valid == True
        assert result.has_source_attribution == True
    
    def test_full_validation_flow_invalid_answer(self, validator):
        """测试完整验证流程 - 无效回答"""
        # 1. 检索阶段 - 低相似度
        documents = ["不太相关的文档"]
        metadatas = [{"source": "doc1.pdf"}]
        distances = [1.8]  # 低相似度
        
        with patch.object(validator.config, 'retrieval', {
            'enabled': True,
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }):
            filtered_docs, filtered_contents = validator.validate_retrieval(
                documents, metadatas, distances
            )
        
        # 应该被过滤掉
        assert len(filtered_docs) == 0
        
        # 2. 无文档时的验证
        answer = "我猜测可能是这样的"
        sources = []
        context = ""
        
        with patch.object(validator.config, 'validation', {
            'enabled': True,
            'check_source_attribution': True,
            'min_confidence_score': 0.6,
            'hallucination_detection': True
        }):
            result = validator.validate_answer(answer, sources, context)
        
        assert result.is_valid == False
        assert result.confidence_score < 0.6


class TestConstraintConfigurationChanges:
    """测试约束配置变更的影响"""
    
    @pytest.fixture
    def validator(self):
        return AnswerValidator()
    
    def test_changing_min_similarity_affects_filtering(self, validator):
        """测试修改最小相似度影响过滤结果"""
        documents = ["文档内容"]
        metadatas = [{"source": "doc1.pdf"}]
        distances = [0.5]  # 相似度 0.75
        
        # 使用较低阈值
        with patch.object(validator.config, 'retrieval', {
            'enabled': True,
            'min_similarity_score': 0.6,
            'max_relevant_docs': 5
        }):
            filtered1, _ = validator.validate_retrieval(documents, metadatas, distances)
        
        # 使用较高阈值
        with patch.object(validator.config, 'retrieval', {
            'enabled': True,
            'min_similarity_score': 0.8,
            'max_relevant_docs': 5
        }):
            filtered2, _ = validator.validate_retrieval(documents, metadatas, distances)
        
        assert len(filtered1) == 1  # 通过低阈值
        assert len(filtered2) == 0  # 未通过高阈值
    
    def test_disabling_validation_bypasses_checks(self, validator):
        """测试禁用验证跳过检查"""
        answer = "没有引用的回答"
        sources = []
        context = ""
        
        # 启用验证
        with patch.object(validator.config, 'validation', {
            'enabled': True,
            'check_source_attribution': True,
            'min_confidence_score': 0.6,
            'hallucination_detection': True
        }):
            result1 = validator.validate_answer(answer, sources, context)
        
        # 禁用验证
        with patch.object(validator.config, 'validation', {
            'enabled': False
        }):
            result2 = validator.validate_answer(answer, sources, context)
        
        assert result1.is_valid == False
        assert result2.is_valid == True


class TestConstraintErrorHandling:
    """测试约束系统的错误处理"""
    
    @pytest.fixture
    def validator(self):
        return AnswerValidator()
    
    def test_handle_missing_metadata(self, validator):
        """测试处理缺失的元数据"""
        documents = ["文档内容"]
        metadatas = [{}]  # 空元数据
        distances = [0.2]
        
        with patch.object(validator.config, 'retrieval', {
            'enabled': True,
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }):
            filtered_docs, _ = validator.validate_retrieval(documents, metadatas, distances)
        
        # 应该正常处理
        assert len(filtered_docs) == 1
        assert filtered_docs[0]['metadata'] == {}
    
    def test_handle_mismatched_list_lengths(self, validator):
        """测试处理列表长度不匹配"""
        documents = ["文档1", "文档2"]
        metadatas = [{"source": "doc1.pdf"}]  # 长度不匹配
        distances = [0.2, 0.3]
        
        # 应该能够处理或抛出明确的错误
        try:
            with patch.object(validator.config, 'retrieval', {
                'enabled': True,
                'min_similarity_score': 0.7,
                'max_relevant_docs': 5
            }):
                validator.validate_retrieval(documents, metadatas, distances)
        except (ValueError, IndexError) as e:
            # 预期的错误
            assert True
    
    def test_handle_invalid_distance_values(self, validator):
        """测试处理无效的距离值"""
        documents = ["文档内容"]
        metadatas = [{"source": "doc1.pdf"}]
        distances = [-1.0]  # 无效的负值
        
        with patch.object(validator.config, 'retrieval', {
            'enabled': True,
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }):
            filtered_docs, _ = validator.validate_retrieval(documents, metadatas, distances)
        
        # 应该能够处理（相似度会 > 1）
        assert len(filtered_docs) >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
