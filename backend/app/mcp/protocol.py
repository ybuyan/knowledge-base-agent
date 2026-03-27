from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict


# 3.1 Error code constants
class MCPErrorCode:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    RESOURCE_NOT_FOUND = -32002
    TOOL_NOT_FOUND = -32003
    PROMPT_NOT_FOUND = -32004


# 3.2 JSON-RPC 2.0 message models
class JSONRPCError(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    jsonrpc: Literal["2.0"]
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


# 3.3 Business data models
class ClientInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    version: str


class InitializeParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    protocolVersion: str
    capabilities: Dict[str, Any] = {}
    clientInfo: ClientInfo


class ServerInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    version: str


class InitializeResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    protocolVersion: str = "2024-11-05"
    capabilities: Any
    serverInfo: ServerInfo


class ContentItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["text", "image", "resource"]
    text: Optional[str] = None
    data: Optional[str] = None
    mimeType: Optional[str] = None


class CallToolParams(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    arguments: Optional[Dict[str, Any]] = None


class CallToolResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: List[ContentItem]
    isError: bool = False


class ResourceContent(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    uri: str
    mimeType: str
    text: Optional[str] = None
    blob: Optional[str] = None


class ReadResourceResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    contents: List[ResourceContent]


class PromptMessage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    role: Literal["user", "assistant"]
    content: ContentItem


class GetPromptResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    description: Optional[str] = None
    messages: List[PromptMessage]
