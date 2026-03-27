from app.tools.base import BaseTool, ToolRegistry, ToolDefinition
from typing import Dict, Any


@ToolRegistry.register("list_documents")
class ListDocumentsTool(BaseTool):
    """列出知识库中所有文档的Tool"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="list_documents",
            name="list_documents",
            description="列出知识库中的所有文档文件。当用户询问知识库有哪些文件、文档列表、有什么内容时使用此工具。",
            enabled=True,
            category="retrieval",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            implementation="ListDocumentsTool"
        )
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        from app.models.document import DocumentDB
        
        docs, total = await DocumentDB.list(page=1, page_size=1000)
        
        documents = []
        for doc in docs:
            documents.append({
                "id": doc.id,
                "filename": doc.filename,
                "status": doc.status,
                "size": doc.size,
                "chunk_count": doc.chunk_count
            })
        
        return {
            "success": True,
            "documents": documents,
            "total": total,
            "message": f"知识库中共有 {total} 个文档"
        }


@ToolRegistry.register("get_document_info")
class GetDocumentInfoTool(BaseTool):
    """获取单个文档详细信息的Tool"""
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="get_document_info",
            name="get_document_info",
            description="获取指定文档的详细信息，包括文件名、大小、状态、分块数量等。",
            enabled=True,
            category="retrieval",
            parameters={
                "type": "object",
                "properties": {
                    "document_name": {
                        "type": "string",
                        "description": "文档名称或文件名"
                    }
                },
                "required": ["document_name"]
            },
            implementation="GetDocumentInfoTool"
        )
    
    async def execute(self, document_name: str) -> Dict[str, Any]:
        from app.models.document import DocumentDB
        
        docs, _ = await DocumentDB.list(page=1, page_size=1000)
        
        for doc in docs:
            if document_name.lower() in doc.filename.lower():
                return {
                    "success": True,
                    "document": {
                        "id": doc.id,
                        "filename": doc.filename,
                        "status": doc.status,
                        "size": doc.size,
                        "chunk_count": doc.chunk_count,
                        "upload_time": doc.uploadTime
                    }
                }
        
        return {
            "success": False,
            "message": f"未找到文档: {document_name}"
        }
