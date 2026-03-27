"""
Assistant Tools - 助手相关工具
"""

from app.tools.base import BaseTool, ToolRegistry, ToolDefinition
from typing import Dict, Any


@ToolRegistry.register("introduce_assistant")
class IntroduceAssistantTool(BaseTool):
    """助手自我介绍工具"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="introduce_assistant",
            name="introduce_assistant",
            description="介绍助手的能力和功能。当用户询问你是谁、你能做什么、你有什么功能、介绍一下你自己等问题时使用此工具。",
            enabled=True,
            category="assistant",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            implementation="IntroduceAssistantTool"
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """返回助手介绍"""
        introduction = {
            "name": "智能知识库助手",
            "description": "我是一个基于知识库的智能问答助手，可以帮助您查询和解答公司相关的问题。",
            "capabilities": [
                {
                    "name": "知识库问答",
                    "description": "可以回答关于公司制度、规范、流程等方面的问题"
                },
                {
                    "name": "文档检索",
                    "description": "可以从知识库中检索相关文档和信息"
                },
                {
                    "name": "文档列表",
                    "description": "可以列出知识库中的所有文档"
                },
                {
                    "name": "文档详情",
                    "description": "可以查询特定文档的详细信息"
                }
            ],
            "examples": [
                "知识库有哪些文件？",
                "员工手册的内容是什么？",
                "请假制度是怎样的？",
                "差旅报销有什么规定？"
            ],
            "tips": "我会根据知识库中的内容回答您的问题，如果知识库中没有相关信息，我会如实告知。"
        }
        
        return {
            "success": True,
            "introduction": introduction,
            "message": self._format_introduction(introduction)
        }
    
    def _format_introduction(self, intro: Dict) -> str:
        """格式化介绍文本"""
        lines = [
            f"👋 你好！我是{intro['name']}",
            "",
            intro['description'],
            "",
            "🎯 我的能力："
        ]
        
        for cap in intro['capabilities']:
            lines.append(f"  • {cap['name']}：{cap['description']}")
        
        lines.append("")
        lines.append("💡 你可以这样问我：")
        for example in intro['examples']:
            lines.append(f'  "{example}"')
        
        lines.append("")
        lines.append(f"📌 {intro['tips']}")
        
        return "\n".join(lines)


@ToolRegistry.register("get_assistant_status")
class GetAssistantStatusTool(BaseTool):
    """获取助手状态工具"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="get_assistant_status",
            name="get_assistant_status",
            description="获取助手的当前状态和统计信息。当用户询问系统状态、运行情况等问题时使用。",
            enabled=True,
            category="assistant",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            implementation="GetAssistantStatusTool"
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """返回助手状态"""
        from app.models.document import DocumentDB
        from app.core.chroma import get_documents_collection
        
        # 获取文档数量
        docs, doc_count = await DocumentDB.list(page=1, page_size=1)
        
        # 获取向量数量
        collection = get_documents_collection()
        vector_count = collection.count()
        
        return {
            "success": True,
            "status": "running",
            "statistics": {
                "document_count": doc_count,
                "vector_count": vector_count,
                "status": "正常"
            },
            "message": f"助手状态：正常\n知识库文档：{doc_count} 个\n向量数量：{vector_count} 条"
        }
