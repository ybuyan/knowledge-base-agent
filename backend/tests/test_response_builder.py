"""
Unit tests for ResponseBuilder
"""

import json

import pytest
from app.services.response_builder import ResponseBuilder


class TestResponseBuilder:
    """ResponseBuilder测试"""

    def test_text_chunk(self):
        """测试文本块构建"""
        result = ResponseBuilder.text_chunk("Hello, world!")

        assert result.startswith("data: ")
        data = json.loads(result[6:])
        assert data["type"] == "text"
        assert data["content"] == "Hello, world!"

    def test_done_chunk_with_sources(self):
        """测试完成块构建（带sources）"""
        sources = [
            {"id": "1", "filename": "test.pdf", "content": "test.pdf"},
            {"id": "2", "filename": "doc.docx", "content": "doc.docx"},
        ]
        result = ResponseBuilder.done_chunk(sources)

        assert result.startswith("data: ")
        data = json.loads(result[6:])
        assert data["type"] == "done"
        assert len(data["sources"]) == 2

    def test_done_chunk_empty_sources(self):
        """测试完成块构建（空sources）"""
        result = ResponseBuilder.done_chunk([])

        data = json.loads(result[6:])
        assert data["type"] == "done"
        assert data["sources"] == []

    def test_error_chunk(self):
        """测试错误块构建"""
        result = ResponseBuilder.error_chunk("Something went wrong")

        data = json.loads(result[6:])
        assert data["type"] == "error"
        assert data["content"] == "Something went wrong"

    def test_build_sources_from_documents(self):
        """测试从文档列表构建sources"""
        documents = [
            {"filename": "test1.pdf", "id": "1"},
            {"filename": "test2.pdf", "id": "2"},
        ]

        sources = ResponseBuilder.build_sources_from_documents(documents)

        assert len(sources) == 2
        assert sources[0]["id"] == "1"
        assert sources[0]["filename"] == "test1.pdf"
        assert sources[1]["id"] == "2"

    def test_build_sources_from_rag_results(self):
        """测试从RAG结果构建sources"""
        documents = ["This is document 1 content", "This is document 2 content"]
        metadatas = [{"document_name": "doc1.pdf"}, {"filename": "doc2.pdf"}]

        sources = ResponseBuilder.build_sources_from_rag_results(documents, metadatas)

        assert len(sources) == 2
        assert sources[0]["filename"] == "doc1.pdf"
        assert sources[1]["filename"] == "doc2.pdf"

    def test_build_sources_from_rag_results_long_content(self):
        """测试长内容截断"""
        long_content = "A" * 500
        documents = [long_content]
        metadatas = [{}]

        sources = ResponseBuilder.build_sources_from_rag_results(documents, metadatas)

        assert len(sources[0]["content"]) == 203  # 200 + "..."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
