from app.tools.base import BaseTool, ToolRegistry, ToolDefinition
from app.core.chroma import get_documents_collection, get_conversations_collection
from app.core.embeddings import get_embeddings
from typing import Dict, Any


@ToolRegistry.register("search_knowledge")
class SearchKnowledgeTool(BaseTool):
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="search_knowledge",
            name="search_knowledge",
            description="在知识库中搜索相关内容",
            enabled=True,
            category="retrieval",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "返回结果数量",
                        "default": 5
                    },
                    "collection": {
                        "type": "string",
                        "description": "集合名称",
                        "enum": ["documents", "conversations"],
                        "default": "documents"
                    }
                },
                "required": ["query"]
            },
            implementation="SearchKnowledgeTool"
        )
    
    async def execute(self, query: str, top_k: int = 5, collection: str = "documents") -> Dict[str, Any]:
        embeddings = get_embeddings()
        query_embedding = await embeddings.aembed_query(query)
        
        if collection == "conversations":
            coll = get_conversations_collection()
        else:
            coll = get_documents_collection()
        
        results = coll.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        documents = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                documents.append({
                    "content": doc,
                    "metadata": metadata
                })
        
        return {
            "success": True,
            "documents": documents,
            "count": len(documents),
            "collection": collection
        }


@ToolRegistry.register("get_system_status")
class SystemStatusTool(BaseTool):
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="get_system_status",
            name="get_system_status",
            description="获取系统运行状态",
            enabled=True,
            category="system",
            parameters={
                "type": "object",
                "properties": {}
            },
            implementation="SystemStatusTool"
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        from app.core.chroma import get_chroma_stats
        
        stats = get_chroma_stats()
        
        return {
            "success": True,
            "status": "running",
            "chroma": stats
        }
