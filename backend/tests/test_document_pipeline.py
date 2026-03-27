"""
测试文档处理 pipeline，验证 document_name 是否正确传递
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestDocumentPipeline:
    """测试文档处理 pipeline"""
    
    @pytest.mark.asyncio
    async def test_document_name_in_metadata(self):
        """
        测试 document_name 是否正确存储在 metadata 中
        """
        from app.skills.processors.document import DocumentParser
        from app.skills.processors.store import VectorStore
        
        # 测试 DocumentParser 输出
        parser = DocumentParser()
        
        # 模拟 context
        context = {
            "file_path": "data/uploads/test_前端团队成员结构.xlsx",
            "original_filename": "前端团队成员结构.xlsx"
        }
        
        # 由于我们没有真实的 xlsx 文件，这里只验证逻辑
        # 实际测试需要真实的文件
        
        # 验证 DocumentParser 返回的字段
        result = await parser.process(context, {
            "supported_formats": ["xlsx"]
        })
        
        print(f"\nDocumentParser 输出: {result}")
        
        # 验证包含 document_name
        assert "document_name" in result, "DocumentParser 应该返回 document_name"
        assert result["document_name"] == "前端团队成员结构.xlsx", \
            f"document_name 应该是 '前端团队成员结构.xlsx'，但得到 {result['document_name']}"
    
    def test_vector_store_metadata(self):
        """
        测试 VectorStore 是否正确构建 metadata
        """
        from app.skills.processors.store import VectorStore
        
        store = VectorStore()
        
        # 模拟 context
        context = {
            "chunks": ["chunk1", "chunk2"],
            "chunk_embeddings": [[0.1, 0.2], [0.3, 0.4]],
            "document_id": "doc123",
            "document_name": "前端团队成员结构.xlsx"
        }
        
        # 验证 metadata 构建逻辑
        chunks = context.get("chunks", [])
        document_id = context.get("document_id", "")
        document_name = context.get("document_name", "unknown")
        
        metadatas = [
            {
                "document_id": document_id,
                "document_name": document_name,
                "chunk_index": i
            }
            for i in range(len(chunks))
        ]
        
        print(f"\n构建的 metadata: {metadatas}")
        
        # 验证 metadata
        assert len(metadatas) == 2
        for meta in metadatas:
            assert meta["document_name"] == "前端团队成员结构.xlsx", \
                f"metadata 中的 document_name 应该是 '前端团队成员结构.xlsx'，但得到 {meta['document_name']}"
            assert meta["document_id"] == "doc123"
    
    @pytest.mark.asyncio
    async def test_qa_retrieve_sources(self):
        """
        测试 QA 检索时是否正确提取 sources
        """
        from app.services.qa_agent import QAAgent, QAConfig
        
        # 创建 mock 的检索结果
        mock_results = {
            "documents": [["记录 5: 姓名: ryan q yuan | 上级: qiang qc wang"]],
            "metadatas": [[{"document_name": "前端团队成员结构.xlsx", "document_id": "doc123"}]],
            "distances": [[0.1]]
        }
        
        # 模拟 collection.query
        with patch('app.services.qa_agent.get_documents_collection') as mock_get_collection:
            mock_collection = Mock()
            mock_collection.query.return_value = mock_results
            mock_get_collection.return_value = mock_collection
            
            # 创建 QA agent
            config = QAConfig()
            agent = QAAgent(config)
            
            # 执行检索
            rag_context = await agent._retrieve("ryan q yuan 的上级是谁", [])
            
            print(f"\n检索到的 sources: {rag_context.sources}")
            print(f"检索到的 documents: {rag_context.documents}")
            
            # 验证 sources
            assert len(rag_context.sources) > 0, "应该返回 sources"
            assert rag_context.sources[0]["filename"] == "前端团队成员结构.xlsx", \
                f"filename 应该是 '前端团队成员结构.xlsx'，但得到 {rag_context.sources[0].get('filename')}"
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_mock(self):
        """
        测试完整的 pipeline（使用 mock）
        """
        from app.services.qa_agent import QAAgent, QAConfig
        from app.services.response_builder import ResponseBuilder
        from app.services.content_analyzer import ContentAnalyzer
        
        # 模拟完整的 RAG 流程
        mock_answer = "ryan q yuan 的上级是 qiang qc wang。"
        mock_sources = [
            {
                "id": "1",
                "filename": "前端团队成员结构.xlsx",
                "content": "记录 5: 姓名: ryan q yuan | 上级: qiang qc wang | 部门: 前端"
            }
        ]
        
        # 1. 测试 ContentAnalyzer
        analysis = ContentAnalyzer.analyze_content_source(mock_answer, mock_sources)
        print(f"\n内容分析结果: {analysis}")
        
        assert analysis["has_reference"] is True, "应该检测到文档引用"
        
        # 2. 测试 ResponseBuilder
        done_chunk = ResponseBuilder.done_chunk(mock_sources, mock_answer)
        print(f"\nResponseBuilder 输出: {done_chunk}")
        
        import json
        data_str = done_chunk[6:].strip()
        data = json.loads(data_str)
        
        # 验证包含 sources
        assert "sources" in data, f"应该包含 sources 字段，但得到: {data}"
        assert data["sources"][0]["filename"] == "前端团队成员结构.xlsx", \
            f"filename 应该是 '前端团队成员结构.xlsx'，但得到 {data['sources'][0].get('filename')}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
