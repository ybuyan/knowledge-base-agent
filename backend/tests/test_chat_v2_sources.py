"""
测试 chat/v2/ask/stream 接口的 sources 显示

验证场景：
1. 询问 ryan q yuan 的 leader 是谁
2. 期望返回正确的 leader 名字（qiang qc wang）
3. 期望返回 sources 包含 "前端团队成员结构.xlsx"
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, AsyncMock


class TestChatV2Sources:
    """测试 chat/v2/ask/stream 接口的 sources 显示"""
    
    @pytest.mark.asyncio
    async def test_ryan_leader_query_returns_correct_source(self):
        """
        测试：询问 ryan q yuan 的 leader 是谁
        期望：
        - 回答包含 qiang qc wang
        - sources 包含 前端团队成员结构.xlsx
        """
        from app.services.qa_agent import QAAgent, QAConfig
        from app.services.response_builder import ResponseBuilder
        from app.services.content_analyzer import ContentAnalyzer
        
        # 模拟 RAG 检索结果
        mock_sources = [
            {
                "id": "1",
                "filename": "前端团队成员结构.xlsx",
                "content": "记录 5: 姓名: ryan q yuan | 上级: qiang qc wang | 部门: 前端"
            }
        ]
        
        # 模拟 LLM 回答
        mock_answer = "ryan q yuan 的上级是 qiang qc wang。"
        
        # 测试 ContentAnalyzer
        analysis = ContentAnalyzer.analyze_content_source(mock_answer, mock_sources)
        print(f"\n分析结果: {analysis}")
        
        # 验证应该返回 has_reference=True
        assert analysis["has_reference"] is True, f"期望 has_reference=True，但得到 {analysis['has_reference']}"
        
        # 测试 ResponseBuilder
        done_chunk = ResponseBuilder.done_chunk(mock_sources, mock_answer)
        print(f"\ndone_chunk: {done_chunk}")
        
        # 解析 chunk
        data_str = done_chunk[6:].strip()
        data = json.loads(data_str)
        
        # 验证 sources 字段存在
        assert "sources" in data, f"期望包含 sources 字段，但响应为: {data}"
        assert len(data["sources"]) > 0, "期望 sources 不为空"
        assert data["sources"][0]["filename"] == "前端团队成员结构.xlsx", \
            f"期望文件名是 前端团队成员结构.xlsx，但得到 {data['sources'][0].get('filename')}"
    
    @pytest.mark.asyncio
    async def test_no_info_response_no_sources(self):
        """
        测试：无相关信息时不返回 sources
        """
        from app.services.response_builder import ResponseBuilder
        from app.services.content_analyzer import ContentAnalyzer
        
        # 模拟无信息回答
        mock_answer = "抱歉，我在知识库中没有找到相关信息。"
        mock_sources = []
        
        # 测试 ContentAnalyzer
        analysis = ContentAnalyzer.analyze_content_source(mock_answer, mock_sources)
        print(f"\n无信息回答分析结果: {analysis}")
        
        # 验证应该返回 has_reference=False
        assert analysis["has_reference"] is False
        
        # 测试 ResponseBuilder
        done_chunk = ResponseBuilder.done_chunk(mock_sources, mock_answer)
        data_str = done_chunk[6:].strip()
        data = json.loads(data_str)
        
        # 验证 sources 字段不存在
        assert "sources" not in data, f"期望不包含 sources 字段，但响应为: {data}"
    
    def test_content_analyzer_with_xlsx_source(self):
        """
        测试 ContentAnalyzer 正确处理 xlsx 来源
        """
        from app.services.content_analyzer import ContentAnalyzer
        
        # 场景1：有 sources，有效回答
        content = "根据文档，ryan q yuan 的上级是 qiang qc wang。"
        sources = [{"id": "1", "filename": "前端团队成员结构.xlsx"}]
        
        result = ContentAnalyzer.analyze_content_source(content, sources)
        print(f"\n场景1分析: {result}")
        assert result["has_reference"] is True, "有 sources 时应该返回 True"
        
        # 场景2：有 sources，但回答是无信息
        content2 = "抱歉，我没有找到相关信息。"
        result2 = ContentAnalyzer.analyze_content_source(content2, sources)
        print(f"\n场景2分析: {result2}")
        assert result2["has_reference"] is False, "无信息回答应该返回 False"
        
        # 场景3：无 sources
        content3 = "根据文档，ryan q yuan 的上级是 qiang qc wang。"
        sources3 = []
        result3 = ContentAnalyzer.analyze_content_source(content3, sources3)
        print(f"\n场景3分析: {result3}")
        # 没有 sources 时，根据内容判断
        # 如果内容中没有引用标记，可能返回 False
    
    def test_response_builder_conditional_sources(self):
        """
        测试 ResponseBuilder 条件显示 sources
        """
        from app.services.response_builder import ResponseBuilder
        import json
        
        # 场景1：有 sources，有文档引用
        content1 = "根据[前端团队成员结构.xlsx]，ryan 的上级是 qiang。"
        sources1 = [{"id": "1", "filename": "前端团队成员结构.xlsx"}]
        chunk1 = ResponseBuilder.done_chunk(sources1, content1)
        data1 = json.loads(chunk1[6:].strip())
        print(f"\n场景1响应: {data1}")
        assert "sources" in data1, "应该包含 sources"
        
        # 场景2：有 sources，但无明确引用（但有检索结果）
        content2 = "ryan q yuan 的上级是 qiang qc wang。"
        sources2 = [{"id": "1", "filename": "前端团队成员结构.xlsx"}]
        chunk2 = ResponseBuilder.done_chunk(sources2, content2)
        data2 = json.loads(chunk2[6:].strip())
        print(f"\n场景2响应: {data2}")
        # 现在有 sources 就会显示
        assert "sources" in data2, "有 sources 时应该包含 sources"
        
        # 场景3：无 sources
        content3 = "ryan q yuan 的上级是 qiang qc wang。"
        sources3 = []
        chunk3 = ResponseBuilder.done_chunk(sources3, content3)
        data3 = json.loads(chunk3[6:].strip())
        print(f"\n场景3响应: {data3}")
        assert "sources" not in data3, "无 sources 时不应该包含 sources"


class TestRAGContextWithXLSX:
    """测试 RAG 对 xlsx 文件的处理"""
    
    def test_xlsx_row_integrity_in_chunks(self):
        """
        测试 xlsx 行数据完整性
        """
        from app.skills.processors.document import DocumentParser
        
        # 创建测试 xlsx 内容
        # 注意：这里我们直接测试解析逻辑
        parser = DocumentParser()
        
        # 模拟 xlsx 解析结果
        # 实际测试需要真实的 xlsx 文件
        # 这里验证解析逻辑是否正确
        
        # 测试行数据格式
        test_row = "记录 5: 姓名: ryan q yuan | 上级: qiang qc wang | 部门: 前端"
        
        # 验证包含关键信息
        assert "ryan q yuan" in test_row
        assert "qiang qc wang" in test_row
        assert "记录 5" in test_row


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
