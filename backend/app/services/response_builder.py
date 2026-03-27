"""
Response Builder - 统一响应构建器
"""

import json
from typing import Dict, Any, List


class ResponseBuilder:
    """统一流式响应构建器"""
    
    @staticmethod
    def text_chunk(content: str) -> str:
        """构建文本块"""
        data = json.dumps({
            "type": "text",
            "content": content
        }, ensure_ascii=False)
        return f"data: {data}\n\n"
    
    @staticmethod
    def done_chunk(
        sources: List[Dict] = None, 
        content: str = None,
        suggested_questions: List[str] = None,
        related_links: List[Dict] = None
    ) -> str:
        """
        构建完成块
        
        参数:
            sources (List[Dict], optional): 来源列表
            content (str, optional): LLM 生成的完整响应内容
            suggested_questions (List[str], optional): 快捷提问列表
            related_links (List[Dict], optional): 相关链接列表
        
        返回:
            str: SSE 格式的完成块
        """
        data: Dict[str, Any] = {
            "type": "done"
        }
        
        # 智能判断是否包含 sources 字段
        if sources:
            if content:
                from app.services.content_analyzer import ContentAnalyzer
                analysis = ContentAnalyzer.analyze_content_source(content, sources)
                
                if analysis["has_reference"]:
                    data["sources"] = sources
            else:
                data["sources"] = sources
        
        # 添加快捷提问
        if suggested_questions:
            data["suggested_questions"] = suggested_questions
        
        # 添加相关链接
        if related_links:
            data["related_links"] = related_links
        
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    @staticmethod
    def error_chunk(error: str) -> str:
        """构建错误块"""
        data = json.dumps({
            "type": "error",
            "content": error
        }, ensure_ascii=False)
        return f"data: {data}\n\n"
    
    @staticmethod
    def tool_call_chunk(tool_name: str, tool_args: Dict) -> str:
        """构建Tool调用块"""
        data = json.dumps({
            "type": "tool_call",
            "tool_name": tool_name,
            "tool_args": tool_args
        }, ensure_ascii=False)
        return f"data: {data}\n\n"
    
    MAX_SOURCES = 5

    @staticmethod
    def build_sources_from_documents(documents: List[Dict]) -> List[Dict]:
        """
        从文档列表构建sources
        
        支持两种格式：
        1. {"content": "...", "metadata": {"document_name": "..."}} - Tool 返回格式
        2. {"filename": "...", "content": "..."} - 直接格式
        """
        sources = []
        for i, doc in enumerate(documents[:ResponseBuilder.MAX_SOURCES]):
            # 处理 Tool 返回的格式
            if "metadata" in doc:
                metadata = doc.get("metadata", {})
                filename = metadata.get("document_name", metadata.get("filename", "Unknown"))
                content = doc.get("content", "")
            else:
                # 处理直接格式
                filename = doc.get("filename", doc.get("document_name", "Unknown"))
                content = doc.get("content", doc.get("text", ""))
            
            # 截断内容
            if len(content) > 200:
                content = content[:200] + "..."
            
            sources.append({
                "id": str(i + 1),
                "filename": filename,
                "content": content
            })
        return sources
