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

        # 9.1 Register resource for document index
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
        if not uri.startswith("document://"):
            raise ValueError(f"Resource not found: {uri}")
        if uri == "document://index":
            return "文档库资源索引"
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
