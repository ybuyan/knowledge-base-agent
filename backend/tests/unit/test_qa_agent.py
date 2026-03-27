import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestQAAgent:
    
    @pytest.mark.asyncio
    async def test_run_with_empty_query_raises_error(self):
        from app.agents.implementations.qa_agent import QAAgent
        agent = QAAgent()
        
        with pytest.raises(ValueError, match="question is required"):
            await agent.run({})
    
    @pytest.mark.asyncio
    async def test_run_with_none_query_raises_error(self):
        from app.agents.implementations.qa_agent import QAAgent
        agent = QAAgent()
        
        with pytest.raises(ValueError, match="question is required"):
            await agent.run({"question": None})
    
    @pytest.mark.asyncio
    async def test_run_returns_session_id(self, mock_embeddings, mock_chroma_collection):
        with patch('app.core.embeddings.get_embeddings', return_value=mock_embeddings), \
             patch('app.core.chroma.get_documents_collection', return_value=mock_chroma_collection):
            
            from app.agents.implementations.qa_agent import QAAgent
            agent = QAAgent()
            
            result = await agent.run({"question": "什么是RAG?"})
            
            assert "session_id" in result
            assert result["session_id"] is not None
    
    @pytest.mark.asyncio
    async def test_run_with_custom_session_id(self, mock_embeddings, mock_chroma_collection):
        with patch('app.core.embeddings.get_embeddings', return_value=mock_embeddings), \
             patch('app.core.chroma.get_documents_collection', return_value=mock_chroma_collection):
            
            from app.agents.implementations.qa_agent import QAAgent
            agent = QAAgent()
            
            custom_session_id = "custom-session-123"
            result = await agent.run({
                "question": "测试问题",
                "session_id": custom_session_id
            })
            
            assert result["session_id"] == custom_session_id
    
    @pytest.mark.asyncio
    async def test_agent_id(self):
        from app.agents.implementations.qa_agent import QAAgent
        agent = QAAgent()
        
        assert agent.agent_id == "qa_agent"
    
    @pytest.mark.asyncio
    async def test_agent_name(self):
        from app.agents.implementations.qa_agent import QAAgent
        agent = QAAgent()
        
        assert agent.name == "问答Agent"
