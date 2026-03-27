"""
Content Analyzer 单元测试

测试内容分析服务的各项功能
"""

import pytest
from app.services.content_analyzer import ContentAnalyzer


class TestContentAnalyzer:
    """测试 ContentAnalyzer 类"""
    
    def test_has_document_reference_with_citation(self):
        """测试检测到文档引用的情况"""
        content = "根据[员工手册]的规定，员工享有年假权利。"
        assert ContentAnalyzer.has_document_reference(content) is True
        
        content = "详见《考勤管理制度》第3条规定。"
        assert ContentAnalyzer.has_document_reference(content) is True
        
        content = "根据公司制度文件显示，请假需要提前申请。"
        assert ContentAnalyzer.has_document_reference(content) is True
    
    def test_has_document_reference_no_info(self):
        """测试无相关信息的情况"""
        content = "抱歉，我在知识库中没有找到相关信息。"
        assert ContentAnalyzer.has_document_reference(content) is False
        
        content = "对不起，我无法回答这个问题。"
        assert ContentAnalyzer.has_document_reference(content) is False
        
        content = "没有找到相关内容，请尝试其他问题。"
        assert ContentAnalyzer.has_document_reference(content) is False
    
    def test_has_document_reference_general_knowledge(self):
        """测试通用知识回答的情况"""
        content = "一般来说，Python 是一种流行的编程语言。"
        assert ContentAnalyzer.has_document_reference(content) is False
        
        content = "通常情况下，天气晴朗时适合户外活动。"
        assert ContentAnalyzer.has_document_reference(content) is False
    
    def test_has_document_reference_empty_content(self):
        """测试空内容的情况"""
        assert ContentAnalyzer.has_document_reference("") is False
        assert ContentAnalyzer.has_document_reference(None) is False
        assert ContentAnalyzer.has_document_reference("   ") is False
    
    def test_extract_document_citations(self):
        """测试提取文档引用"""
        content = "根据[员工手册]和[考勤制度]的规定。"
        citations = ContentAnalyzer.extract_document_citations(content)
        assert "员工手册" in citations
        assert "考勤制度" in citations
        
        content = "根据公司规定说明，员工应遵守制度。"
        citations = ContentAnalyzer.extract_document_citations(content)
        assert len(citations) > 0
    
    def test_analyze_content_source_with_reference(self):
        """测试全面分析 - 有文档引用的情况"""
        content = "根据[员工手册]第3条规定，员工享有5天年假。"
        sources = [{"id": "1", "filename": "员工手册.pdf"}]
        
        result = ContentAnalyzer.analyze_content_source(content, sources)
        
        assert result["has_reference"] is True
        assert len(result["citations"]) > 0
        assert result["confidence"] > 0.7
        assert "员工手册" in result["reason"]
    
    def test_analyze_content_source_no_reference(self):
        """测试全面分析 - 无文档引用的情况"""
        content = "抱歉，我在知识库中没有找到相关信息。"
        sources = []
        
        result = ContentAnalyzer.analyze_content_source(content, sources)
        
        assert result["has_reference"] is False
        assert len(result["citations"]) == 0
        assert result["confidence"] > 0.9
        assert "抱歉" in result["reason"] or "无文档" in result["reason"]
    
    def test_analyze_content_source_with_sources(self):
        """测试全面分析 - 有 sources 的情况"""
        content = "根据文档内容，qiang wang 的团队成员包括..."
        sources = [{"id": "1", "filename": "前端团队成员结构.xlsx"}]
        
        result = ContentAnalyzer.analyze_content_source(content, sources)
        
        # 只要有 sources 且内容不是无信息回答，就应该返回 True
        assert result["has_reference"] is True
        assert result["confidence"] > 0.5
    
    def test_analyze_content_source_general_knowledge(self):
        """测试全面分析 - 通用知识的情况"""
        content = "一般来说，Python 和 Java 都是流行的编程语言。"
        sources = []
        
        result = ContentAnalyzer.analyze_content_source(content, sources)
        
        # 通用知识应该返回 False
        assert result["has_reference"] is False
        assert result["confidence"] >= 0.5  # 置信度可能为 0.5
    
    def test_complex_content_analysis(self):
        """测试复杂内容的分析"""
        # 包含文档引用和详细说明的内容
        content = """
        根据[员工手册]的规定，员工请假流程如下：
        1. 提前3天提交申请
        2. 上级审批
        3. HR备案
        
        详见[考勤管理制度]第5条。
        """
        
        result = ContentAnalyzer.analyze_content_source(content)
        
        assert result["has_reference"] is True
        # 检查是否提取到了引用（可能包含方括号）
        assert any("员工手册" in c for c in result["citations"])
        assert result["confidence"] > 0.9


class TestResponseBuilderIntegration:
    """测试 ResponseBuilder 与 ContentAnalyzer 的集成"""
    
    def test_done_chunk_with_document_reference(self):
        """测试有文档引用时的 done_chunk"""
        from app.services.response_builder import ResponseBuilder
        
        content = "根据[员工手册]规定，员工享有年假。"
        sources = [{"id": "1", "filename": "员工手册.pdf"}]
        
        chunk = ResponseBuilder.done_chunk(sources, content)
        
        import json
        data = json.loads(chunk[6:].strip())
        assert data["type"] == "done"
        assert "sources" in data
        assert len(data["sources"]) > 0
    
    def test_done_chunk_without_document_reference(self):
        """测试无文档引用时的 done_chunk"""
        from app.services.response_builder import ResponseBuilder
        
        content = "抱歉，我在知识库中没有找到相关信息。"
        sources = [{"id": "1", "filename": "员工手册.pdf"}]
        
        chunk = ResponseBuilder.done_chunk(sources, content)
        
        import json
        data = json.loads(chunk[6:].strip())
        assert data["type"] == "done"
        assert "sources" not in data  # sources 字段应该被省略
    
    def test_done_chunk_no_content(self):
        """测试没有提供 content 时的 done_chunk"""
        from app.services.response_builder import ResponseBuilder
        
        sources = [{"id": "1", "filename": "员工手册.pdf"}]
        
        chunk = ResponseBuilder.done_chunk(sources)  # 不提供 content
        
        import json
        data = json.loads(chunk[6:].strip())
        assert data["type"] == "done"
        assert "sources" in data  # 保守策略：包含 sources
    
    def test_done_chunk_empty_sources(self):
        """测试空 sources 时的 done_chunk"""
        from app.services.response_builder import ResponseBuilder
        
        content = "根据[员工手册]规定..."
        
        chunk = ResponseBuilder.done_chunk([], content)
        
        import json
        data = json.loads(chunk[6:].strip())
        assert data["type"] == "done"
        assert "sources" not in data  # 空 sources 应该被省略


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
