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

        # 注册资源（按访问级别分类）
        # 公开资源 - 任何人可访问
        self.register_resource(MCPResource(
            uri="knowledge://public/faq",
            name="常见问题",
            description="公开的常见问题解答"
        ))
        
        self.register_resource(MCPResource(
            uri="knowledge://public/guide",
            name="使用指南",
            description="公开的使用指南和帮助文档"
        ))
        
        # 内部资源 - 需要员工角色
        self.register_resource(MCPResource(
            uri="knowledge://internal/policy",
            name="内部政策",
            description="公司内部政策文档"
        ))
        
        self.register_resource(MCPResource(
            uri="knowledge://internal/procedure",
            name="内部流程",
            description="公司内部流程文档"
        ))
        
        # 机密资源 - 需要特殊权限
        self.register_resource(MCPResource(
            uri="knowledge://confidential/salary",
            name="薪酬政策",
            description="机密的薪酬政策文档"
        ))
        
        self.register_resource(MCPResource(
            uri="knowledge://confidential/financial",
            name="财务信息",
            description="机密的财务信息"
        ))
        
        # 保留旧的索引资源（默认为 internal 级别）
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
        """使用 LLM 生成相关问题"""
        try:
            from app.prompts.manager import prompt_manager
            from app.core.llm import call_llm
            
            result = prompt_manager.render("mcp_related_questions", {"question": question})
            prompt = result.get("user")
            if not prompt:
                logger.warning("未找到 mcp_related_questions prompt 模板，使用默认问题")
                return {
                    "questions": [
                        f"关于{question}的具体规定是什么？",
                        f"{question}的适用范围有哪些？",
                        f"如何申请{question}相关的流程？"
                    ]
                }
            
            response = await call_llm(prompt)
            questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
            return {"questions": questions[:3]}
        except Exception as e:
            logger.warning(f"生成相关问题失败: {e}，使用默认问题")
            return {
                "questions": [
                    f"关于{question}的具体规定是什么？",
                    f"{question}的适用范围有哪些？",
                    f"如何申请{question}相关的流程？"
                ]
            }

    # 8.2 Override read_resource to handle dynamic knowledge:// URIs
    async def read_resource(self, uri: str) -> str:
        """
        读取知识库资源
        
        支持的 URI 格式：
        - knowledge://public/* - 公开资源
        - knowledge://internal/* - 内部资源
        - knowledge://confidential/* - 机密资源
        - knowledge://index - 索引（默认 internal）
        """
        if not uri.startswith("knowledge://"):
            raise ValueError(f"Resource not found: {uri}")
        
        # 处理特定资源
        if uri == "knowledge://index":
            return "知识库资源索引\n\n包含公开、内部和机密资源的完整索引。"
        
        # 处理公开资源
        if uri == "knowledge://public/faq":
            return "常见问题解答\n\n1. 如何使用知识库？\n2. 如何搜索信息？\n3. 如何联系支持？"
        
        if uri == "knowledge://public/guide":
            return "使用指南\n\n欢迎使用知识库系统。本指南将帮助您快速上手。"
        
        # 处理内部资源
        if uri == "knowledge://internal/policy":
            return "内部政策文档\n\n包含公司各项内部政策和规定。"
        
        if uri == "knowledge://internal/procedure":
            return "内部流程文档\n\n包含公司各项内部流程和操作指南。"
        
        # 处理机密资源
        if uri == "knowledge://confidential/salary":
            return "薪酬政策文档\n\n包含公司薪酬体系和相关机密信息。"
        
        if uri == "knowledge://confidential/financial":
            return "财务信息文档\n\n包含公司财务数据和相关机密信息。"
        
        # 动态资源处理
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
