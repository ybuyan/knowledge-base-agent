"""
文档 MCP 服务器
提供文档相关的 MCP 工具和资源
"""
from typing import Dict, Any
from app.mcp.base import MCPServer, MCPTool, MCPResource, MCPPrompt, MCPPromptArgument, MCPServerRegistry
from app.mcp.protocol import GetPromptResult, PromptMessage, ContentItem
from app.tools.implementations import SearchKnowledgeTool


class DocumentMCPServer(MCPServer):
    def __init__(self):
        super().__init__(name="document_server", version="1.0.0")

        self.register_tool(MCPTool(
            name="search_documents",
            description="在知识库中搜索相关文档",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "top_k": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        ))

        self.register_tool(MCPTool(
            name="get_document",
            description="获取指定文档内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "文档ID"}
                },
                "required": ["document_id"]
            }
        ))

        # 9.1 Register prompts
        self.register_prompt(MCPPrompt(
            name="search_document_prompt",
            description="引导用户搜索文档的 prompt 模板",
            arguments=[
                MCPPromptArgument(name="query", description="搜索关键词", required=True),
                MCPPromptArgument(name="file_type", description="文件类型，如 pdf/word/excel", required=False),
            ]
        ))

        # 注册资源（按访问级别分类）
        # 公开资源 - 任何人可访问
        self.register_resource(MCPResource(
            uri="document://public/manual",
            name="用户手册",
            description="公开的用户手册和操作指南"
        ))
        
        self.register_resource(MCPResource(
            uri="document://public/tutorial",
            name="教程文档",
            description="公开的教程和培训文档"
        ))
        
        # 内部资源 - 需要员工角色
        self.register_resource(MCPResource(
            uri="document://internal/handbook",
            name="员工手册",
            description="内部员工手册"
        ))
        
        self.register_resource(MCPResource(
            uri="document://internal/report",
            name="内部报告",
            description="内部报告和分析文档"
        ))
        
        # 机密资源 - 需要特殊权限
        self.register_resource(MCPResource(
            uri="document://confidential/contract",
            name="合同文档",
            description="机密的合同和协议文档"
        ))
        
        self.register_resource(MCPResource(
            uri="document://confidential/strategy",
            name="战略文档",
            description="机密的战略规划文档"
        ))
        
        # 保留旧的索引资源（默认为 internal 级别）
        self.register_resource(MCPResource(
            uri="document://index",
            name="文档索引",
            description="文档库内容索引"
        ))

    async def _execute_tool_impl(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "search_documents":
            tool = SearchKnowledgeTool()
            return await tool.execute(
                query=arguments.get("query"),
                top_k=arguments.get("top_k", 5)
            )
        elif name == "get_document":
            return await self._get_document(arguments.get("document_id"))
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _get_document(self, document_id: str) -> Dict[str, Any]:
        from app.core.chroma import get_documents_collection

        collection = get_documents_collection()
        results = collection.get(ids=[document_id])

        if results["documents"]:
            return {
                "content": results["documents"][0],
                "metadata": results["metadatas"][0] if results["metadatas"] else {}
            }
        return {"content": "", "metadata": {}}

    # 9.2 Override read_resource to handle dynamic document:// URIs
    async def read_resource(self, uri: str) -> str:
        """
        读取文档资源
        
        支持的 URI 格式：
        - document://public/* - 公开资源
        - document://internal/* - 内部资源
        - document://confidential/* - 机密资源
        - document://index - 索引（默认 internal）
        """
        if not uri.startswith("document://"):
            raise ValueError(f"Resource not found: {uri}")
        
        # 处理特定资源
        if uri == "document://index":
            return "文档库资源索引\n\n包含公开、内部和机密文档的完整索引。"
        
        # 处理公开资源
        if uri == "document://public/manual":
            return "用户手册\n\n本手册提供系统使用的详细说明和操作指南。"
        
        if uri == "document://public/tutorial":
            return "教程文档\n\n包含各类教程和培训材料，帮助用户快速上手。"
        
        # 处理内部资源
        if uri == "document://internal/handbook":
            return "员工手册\n\n包含公司规章制度、行为准则等内部文档。"
        
        if uri == "document://internal/report":
            return "内部报告\n\n包含各类内部报告、分析和总结文档。"
        
        # 处理机密资源
        if uri == "document://confidential/contract":
            return "合同文档\n\n包含公司重要合同和协议的机密文档。"
        
        if uri == "document://confidential/strategy":
            return "战略文档\n\n包含公司战略规划和机密决策文档。"
        
        # 动态资源处理
        doc_id = uri[len("document://"):]
        return f"文档「{doc_id}」的内容描述"

    async def _read_resource_impl(self, uri: str) -> str:
        return ""

    # 9.3 Implement get_prompt
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict:
        if name == "search_document_prompt":
            query = arguments.get("query", "文档")
            file_type = arguments.get("file_type", "")
            type_hint = f"（文件类型：{file_type}）" if file_type else ""
            result = GetPromptResult(
                description="引导用户搜索文档的 prompt 模板",
                messages=[
                    PromptMessage(
                        role="user",
                        content=ContentItem(
                            type="text",
                            text=f"请帮我搜索关于「{query}」的相关文档{type_hint}。"
                        )
                    )
                ]
            )
            return result.model_dump()
        raise ValueError(f"Prompt not found: {name}")


MCPServerRegistry.register(DocumentMCPServer())
