"""
测试 Sources 去重功能
"""

import pytest
from app.services.tool_types import ToolResult


class TestSourcesDeduplication:
    """测试sources去重功能"""
    
    def test_extract_sources_with_duplicates(self):
        """测试提取sources时去重"""
        from app.services.qa_agent import QAAgent
        
        # 模拟多个工具返回相同文档
        result1 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_1",
            data={
                "documents": [
                    {"metadata": {"document_name": "请假制度.docx"}, "content": "员工请假需要提前申请..."}
                ]
            }
        )
        
        result2 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_2",
            data={
                "documents": [
                    {"metadata": {"document_name": "请假制度.docx"}, "content": "请假流程包括..."}
                ]
            }
        )
        
        result3 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_3",
            data={
                "documents": [
                    {"metadata": {"document_name": "请假制度.docx"}, "content": "请假天数规定..."}
                ]
            }
        )
        
        agent = QAAgent()
        sources = agent._extract_sources_from_tool_results([result1, result2, result3])
        
        # 验证去重：3个相同文档应该只保留1个
        assert len(sources) == 1, f"期望1个source，实际{len(sources)}"
        assert sources[0]["filename"] == "请假制度.docx"
        assert sources[0]["id"] == "1"
    
    def test_extract_sources_with_different_files(self):
        """测试提取不同文件的sources"""
        from app.services.qa_agent import QAAgent
        
        result1 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_1",
            data={
                "documents": [
                    {"metadata": {"document_name": "请假制度.docx"}, "content": "内容1"}
                ]
            }
        )
        
        result2 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_2",
            data={
                "documents": [
                    {"metadata": {"document_name": "报销制度.docx"}, "content": "内容2"}
                ]
            }
        )
        
        result3 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_3",
            data={
                "documents": [
                    {"metadata": {"document_name": "考勤制度.docx"}, "content": "内容3"}
                ]
            }
        )
        
        agent = QAAgent()
        sources = agent._extract_sources_from_tool_results([result1, result2, result3])
        
        # 验证：3个不同文档应该都保留
        assert len(sources) == 3, f"期望3个sources，实际{len(sources)}"
        
        filenames = [s["filename"] for s in sources]
        assert "请假制度.docx" in filenames
        assert "报销制度.docx" in filenames
        assert "考勤制度.docx" in filenames
        
        # 验证ID连续
        assert sources[0]["id"] == "1"
        assert sources[1]["id"] == "2"
        assert sources[2]["id"] == "3"
    
    def test_extract_sources_mixed_duplicates(self):
        """测试混合重复和不重复的情况"""
        from app.services.qa_agent import QAAgent
        
        result1 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_1",
            data={
                "documents": [
                    {"metadata": {"document_name": "请假制度.docx"}, "content": "内容1"}
                ]
            }
        )
        
        result2 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_2",
            data={
                "documents": [
                    {"metadata": {"document_name": "报销制度.docx"}, "content": "内容2"}
                ]
            }
        )
        
        result3 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_3",
            data={
                "documents": [
                    {"metadata": {"document_name": "请假制度.docx"}, "content": "内容3（重复）"}
                ]
            }
        )
        
        result4 = ToolResult(
            success=True,
            tool_name="search_knowledge",
            tool_call_id="call_4",
            data={
                "documents": [
                    {"metadata": {"document_name": "考勤制度.docx"}, "content": "内容4"}
                ]
            }
        )
        
        agent = QAAgent()
        sources = agent._extract_sources_from_tool_results([result1, result2, result3, result4])
        
        # 验证：4个结果，1个重复，应该保留3个
        assert len(sources) == 3, f"期望3个sources，实际{len(sources)}"
        
        filenames = [s["filename"] for s in sources]
        assert "请假制度.docx" in filenames
        assert "报销制度.docx" in filenames
        assert "考勤制度.docx" in filenames
        
        # 验证每个文件名只出现一次
        assert filenames.count("请假制度.docx") == 1
        assert filenames.count("报销制度.docx") == 1
        assert filenames.count("考勤制度.docx") == 1
    
    def test_extract_sources_max_limit(self):
        """测试sources数量限制"""
        from app.services.qa_agent import QAAgent
        from app.services.response_builder import ResponseBuilder
        
        # 创建超过MAX_SOURCES数量的不同文档
        results = []
        for i in range(10):
            results.append(ToolResult(
                success=True,
                tool_name="search_knowledge",
                tool_call_id=f"call_{i}",
                data={
                    "documents": [
                        {"metadata": {"document_name": f"文档{i}.docx"}, "content": f"内容{i}"}
                    ]
                }
            ))
        
        agent = QAAgent()
        sources = agent._extract_sources_from_tool_results(results)
        
        # 验证：不超过MAX_SOURCES限制
        assert len(sources) <= ResponseBuilder.MAX_SOURCES, \
            f"sources数量{len(sources)}超过限制{ResponseBuilder.MAX_SOURCES}"
    
    def test_extract_sources_empty_results(self):
        """测试空结果"""
        from app.services.qa_agent import QAAgent
        
        agent = QAAgent()
        sources = agent._extract_sources_from_tool_results([])
        
        assert len(sources) == 0, "空结果应该返回空列表"
    
    def test_extract_sources_no_documents(self):
        """测试没有documents字段的结果"""
        from app.services.qa_agent import QAAgent
        
        result = ToolResult(
            success=True,
            tool_name="some_tool",
            tool_call_id="call_1",
            data={"answer": "这是一个回答"}
        )
        
        agent = QAAgent()
        sources = agent._extract_sources_from_tool_results([result])
        
        assert len(sources) == 0, "没有documents字段应该返回空列表"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
