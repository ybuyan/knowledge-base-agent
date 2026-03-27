"""
测试 retrieval.min_relevant_docs 配置

测试最小相关文档数检查功能
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.qa_agent import QAAgent
from app.core.constraint_config import ConstraintConfig


class TestMinRelevantDocs:
    """测试 min_relevant_docs 配置"""

    @pytest.mark.asyncio
    async def test_min_relevant_docs_sufficient(self):
        """测试文档数量满足最小要求"""
        agent = QAAgent()

        # Mock 配置
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.retrieval = {
            'enabled': True,
            'min_relevant_docs': 2,
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }
        mock_config.generation = {
            'strict_mode': True,
            'allow_general_knowledge': False,
            'require_citations': True,
            'max_answer_length': 1000,
            'forbidden_topics': [],
            'forbidden_keywords': []
        }
        mock_config.validation = {
            'enabled': True
        }
        mock_config.fallback = {
            'no_result_message': '未找到相关信息',
            'suggest_contact': False
        }
        mock_config.suggest_questions = {
            'enabled': False
        }

        with patch('app.services.qa_agent.get_constraint_config', return_value=mock_config):
            with patch.object(agent, '_retrieve') as mock_retrieve:
                # 模拟检索到 3 个文档（满足最小要求 2）
                mock_context = MagicMock()
                mock_context.documents = ['doc1', 'doc2', 'doc3']
                mock_context.context_text = 'context'
                mock_context.sources = []
                mock_retrieve.return_value = mock_context

                with patch.object(agent._llm_client, 'stream_chat') as mock_stream:
                    async def mock_gen():
                        yield '回答'
                    mock_stream.return_value = mock_gen()

                    with patch('app.services.qa_agent.get_answer_validator') as mock_validator:
                        mock_val = MagicMock()
                        mock_val.validate_answer.return_value = MagicMock(
                            is_valid=True,
                            confidence_score=0.9
                        )
                        mock_validator.return_value = mock_val

                        # 应该正常生成回答
                        result = []
                        async for chunk in agent._execute_rag_flow("测试问题", []):
                            result.append(chunk)

                        # 验证没有返回兜底消息
                        result_str = ''.join(str(r) for r in result)
                        assert '未找到相关信息' not in result_str

    @pytest.mark.asyncio
    async def test_min_relevant_docs_insufficient(self):
        """测试文档数量不足最小要求"""
        agent = QAAgent()

        # Mock 配置
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.retrieval = {
            'enabled': True,
            'min_relevant_docs': 3,  # 要求至少 3 个文档
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }
        mock_config.fallback = {
            'no_result_message': '未找到相关信息',
            'suggest_contact': False
        }

        with patch('app.services.qa_agent.get_constraint_config', return_value=mock_config):
            with patch.object(agent, '_retrieve') as mock_retrieve:
                # 模拟只检索到 1 个文档（不满足最小要求 3）
                mock_context = MagicMock()
                mock_context.documents = ['doc1']
                mock_context.context_text = 'context'
                mock_context.sources = []
                mock_retrieve.return_value = mock_context

                # 应该返回兜底消息
                result = []
                async for chunk in agent._execute_rag_flow("测试问题", []):
                    result.append(chunk)

                # 验证返回了兜底消息
                result_str = ''.join(str(r) for r in result)
                assert '未找到相关信息' in result_str

    @pytest.mark.asyncio
    async def test_min_relevant_docs_zero_documents(self):
        """测试没有检索到文档"""
        agent = QAAgent()

        # Mock 配置
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.retrieval = {
            'enabled': True,
            'min_relevant_docs': 1,
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }
        mock_config.fallback = {
            'no_result_message': '未找到相关信息',
            'suggest_contact': False
        }

        with patch('app.services.qa_agent.get_constraint_config', return_value=mock_config):
            with patch.object(agent, '_retrieve') as mock_retrieve:
                # 模拟没有检索到文档
                mock_context = MagicMock()
                mock_context.documents = []
                mock_context.context_text = ''
                mock_context.sources = []
                mock_retrieve.return_value = mock_context

                # 应该返回兜底消息
                result = []
                async for chunk in agent._execute_rag_flow("测试问题", []):
                    result.append(chunk)

                # 验证返回了兜底消息
                result_str = ''.join(str(r) for r in result)
                assert '未找到相关信息' in result_str

    @pytest.mark.asyncio
    async def test_min_relevant_docs_default_value(self):
        """测试默认值为 1"""
        agent = QAAgent()

        # Mock 配置（不设置 min_relevant_docs）
        mock_config = MagicMock(spec=ConstraintConfig)
        mock_config.retrieval = {
            'enabled': True,
            # 不设置 min_relevant_docs，应该默认为 1
            'min_similarity_score': 0.7,
            'max_relevant_docs': 5
        }
        mock_config.generation = {
            'strict_mode': True,
            'allow_general_knowledge': False,
            'require_citations': True,
            'max_answer_length': 1000,
            'forbidden_topics': [],
            'forbidden_keywords': []
        }
        mock_config.validation = {
            'enabled': True
        }
        mock_config.fallback = {
            'no_result_message': '未找到相关信息',
            'suggest_contact': False
        }
        mock_config.suggest_questions = {
            'enabled': False
        }

        with patch('app.services.qa_agent.get_constraint_config', return_value=mock_config):
            with patch.object(agent, '_retrieve') as mock_retrieve:
                # 模拟检索到 1 个文档（满足默认要求 1）
                mock_context = MagicMock()
                mock_context.documents = ['doc1']
                mock_context.context_text = 'context'
                mock_context.sources = []
                mock_retrieve.return_value = mock_context

                with patch.object(agent._llm_client, 'stream_chat') as mock_stream:
                    async def mock_gen():
                        yield '回答'
                    mock_stream.return_value = mock_gen()

                    with patch('app.services.qa_agent.get_answer_validator') as mock_validator:
                        mock_val = MagicMock()
                        mock_val.validate_answer.return_value = MagicMock(
                            is_valid=True,
                            confidence_score=0.9
                        )
                        mock_validator.return_value = mock_val

                        # 应该正常生成回答
                        result = []
                        async for chunk in agent._execute_rag_flow("测试问题", []):
                            result.append(chunk)

                        # 验证没有返回兜底消息
                        result_str = ''.join(str(r) for r in result)
                        assert '未找到相关信息' not in result_str


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
