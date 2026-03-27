"""
知识库 MCP 服务器
提供知识检索相关的 MCP 工具和资源
"""
from typing import Dict, Any
from app.mcp.base import MCPServer, MCPTool, MCPResource, MCPPrompt, MCPPromptArgument, MCPServerRegistry
from app.mcp.protocol import GetPromptResult, PromptMessage, ContentItem


class KnowledgeMCPServer(MCPServer):
    def __init__(self):
        super().__init__(name="knowledge_server", version="1.0.0")

        # 8.1 Register tools
        self.register_tool(MCPTool(
            name="query_knowledge",
            description="查询知识库获取答案",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "用户问题"},
                    "context_limit": {"type": "integer", "default": 5}
                },
                "required": ["question"]
            }
        ))

        self.register_tool(MCPTool(
            name="get_related_questions",
            description="获取相关问题建议",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "用户问题"}
                },
                "required": ["question"]
            }
        ))

        # 8.1 Register prompts
        self.register_prompt(MCPPrompt(
            name="query_knowledge_prompt",
            description="引导用户提问知识库的 prompt 模板",
            arguments=[
                MCPPromptArgument(name="topic", description="查询主题", required=True),
                MCPPromptArgument(name="detail_level", description="详细程度，如 brief/detailed", required=False),
            ]
        ))

        # 8.1 Register resource for knowledge base index
        self.register_resource(MCPResource(
            uri="knowledge://index",
            name="知识库索引",
            description="知识库内容索引"
        ))

    async def _execute_tool_impl(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "query_knowledge":
            return await self._query_knowledge(
                arguments.get("question"),
                arguments.get("context_limit", 5)
            )
        elif name == "get_related_questions":
            return await self._get_related_questions(arguments.get("question"))
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _query_knowledge(self, question: str, context_limit: int) -> Dict[str, Any]:
        from app.agents import agent_engine

        result = await agent_engine.execute("qa_agent", {
            "question": question,
            "session_id": "mcp_session"
        })

        return {
            "answer": result.get("answer", ""),
            "sources": result.get("sources", []),
            "confidence": 0.85
        }

    async def _get_related_questions(self, question: str) -> Dict[str, Any]:
        return {
            "questions": [
                f"关于{question}的具体规定是什么？",
                f"{question}的适用范围有哪些？",
                f"如何申请{question}相关的流程？"
            ]
        }

    # 8.2 Override read_resource to handle dynamic knowledge:// URIs
    async def read_resource(self, uri: str) -> str:
        if not uri.startswith("knowledge://"):
            raise ValueError(f"Resource not found: {uri}")
        if uri == "knowledge://index":
            return "知识库资源索引"
        topic = uri[len("knowledge://"):]
        return f"知识库主题「{topic}」的相关内容描述"

    # 8.3 Implement get_prompt
    async def get_prompt(self, name: str, arguments: Dict[str, Any]) -> Dict:
        if name == "query_knowledge_prompt":
            topic = arguments.get("topic", "通用")
            detail_level = arguments.get("detail_level", "detailed")
            result = GetPromptResult(
                description="引导用户提问知识库的 prompt 模板",
                messages=[
                    PromptMessage(
                        role="user",
                        content=ContentItem(
                            type="text",
                            text=f"请{'详细' if detail_level == 'detailed' else '简要'}介绍关于「{topic}」的相关知识。"
                        )
                    )
                ]
            )
            return result.model_dump()
        raise ValueError(f"Prompt not found: {name}")


MCPServerRegistry.register(KnowledgeMCPServer())
