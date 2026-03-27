"""
MCP (Model Context Protocol) 模块
用于与外部工具和服务进行标准化交互
"""
from .base import MCPTool, MCPResource, MCPServer, MCPServerRegistry

try:
    from .base import MCPPrompt
except ImportError:
    MCPPrompt = None  # type: ignore[assignment,misc]

from .document_server import DocumentMCPServer
from .knowledge_server import KnowledgeMCPServer

__all__ = [
    "MCPTool",
    "MCPResource",
    "MCPPrompt",
    "MCPServer",
    "MCPServerRegistry",
    "DocumentMCPServer",
    "KnowledgeMCPServer",
]
