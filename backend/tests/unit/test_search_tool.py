import pytest
from unittest.mock import patch, MagicMock


class TestSearchKnowledgeTool:
    
    def test_tool_definition(self):
        from app.tools.implementations.search import SearchKnowledgeTool
        tool = SearchKnowledgeTool()
        
        definition = tool.definition
        assert definition.id == "search_knowledge"
        assert "query" in definition.parameters["properties"]
        assert "top_k" in definition.parameters["properties"]
        assert "collection" in definition.parameters["properties"]
    
    @pytest.mark.asyncio
    async def test_execute_with_documents_collection(self, mock_embeddings, mock_chroma_collection):
        with patch('app.tools.implementations.search.get_embeddings', return_value=mock_embeddings), \
             patch('app.tools.implementations.search.get_documents_collection', return_value=mock_chroma_collection):
            
            from app.tools.implementations.search import SearchKnowledgeTool
            tool = SearchKnowledgeTool()
            
            result = await tool.execute(query="测试查询", top_k=5, collection="documents")
            
            assert result["success"] is True
            assert "documents" in result
            assert result["collection"] == "documents"
    
    @pytest.mark.asyncio
    async def test_execute_with_conversations_collection(self, mock_embeddings, mock_chroma_collection):
        with patch('app.tools.implementations.search.get_embeddings', return_value=mock_embeddings), \
             patch('app.tools.implementations.search.get_documents_collection', return_value=mock_chroma_collection), \
             patch('app.tools.implementations.search.get_conversations_collection', return_value=mock_chroma_collection):
            
            from app.tools.implementations.search import SearchKnowledgeTool
            tool = SearchKnowledgeTool()
            
            result = await tool.execute(query="测试查询", top_k=3, collection="conversations")
            
            assert result["success"] is True
            assert result["collection"] == "conversations"
    
    @pytest.mark.asyncio
    async def test_execute_default_collection(self, mock_embeddings, mock_chroma_collection):
        with patch('app.tools.implementations.search.get_embeddings', return_value=mock_embeddings), \
             patch('app.tools.implementations.search.get_documents_collection', return_value=mock_chroma_collection):
            
            from app.tools.implementations.search import SearchKnowledgeTool
            tool = SearchKnowledgeTool()
            
            result = await tool.execute(query="测试查询")
            
            assert result["collection"] == "documents"
    
    @pytest.mark.asyncio
    async def test_execute_returns_correct_count(self, mock_embeddings, mock_chroma_collection):
        with patch('app.tools.implementations.search.get_embeddings', return_value=mock_embeddings), \
             patch('app.tools.implementations.search.get_documents_collection', return_value=mock_chroma_collection):
            
            from app.tools.implementations.search import SearchKnowledgeTool
            tool = SearchKnowledgeTool()
            
            result = await tool.execute(query="测试查询", top_k=5)
            
            assert result["count"] == len(result["documents"])
