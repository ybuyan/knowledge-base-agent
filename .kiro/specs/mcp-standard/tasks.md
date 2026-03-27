# 实施计划：MCP 标准规范实现（mcp-standard）

## 概述

按照设计文档，将 `backend/app/mcp/` 模块重构为符合 MCP 官方规范的完整实现。分层推进：先建基础模型，再实现协议层，然后服务层，最后路由与集成。

## 任务

- [x] 1. 清理 `__init__.py` 重复定义
  - 删除 `__init__.py` 中所有重复的类定义，改为从 `base.py` / `protocol.py` re-export
  - 保留对外公开的符号：`MCPTool`, `MCPResource`, `MCPPrompt`, `MCPServer`, `MCPServerRegistry`
  - 确保现有 import 路径不受影响

- [x] 2. 重构 `base.py`，补全核心抽象类
  - [x] 2.1 新增 `MCPPromptArgument` 和 `MCPPrompt` 数据模型
    - `MCPPromptArgument`: `name`, `description`, `required: bool = False`
    - `MCPPrompt`: `name`, `description`, `arguments: List[MCPPromptArgument]`
  - [x] 2.2 新增 `MCPCapabilities` 数据模型
    - 字段：`tools`, `resources`, `prompts`（均为 `Optional[Dict]`）
  - [x] 2.3 将 `MCPTool.input_schema` 重命名为 `inputSchema`，`MCPResource.mime_type` 重命名为 `mimeType`
    - 使用 Pydantic `Field(alias=...)` 或直接改字段名，确保序列化输出为 camelCase
  - [x] 2.4 在 `MCPServer` 中添加 prompts 注册与列举方法
    - `register_prompt(prompt: MCPPrompt)`
    - `list_prompts() -> List[MCPPrompt]`
    - `get_capabilities() -> MCPCapabilities`（根据已注册内容动态生成）
    - `get_prompt(name, arguments)` 抽象方法（子类实现）
  - [ ]* 2.5 为 `MCPServer.get_capabilities()` 编写单元测试
    - 验证：注册 tool/resource/prompt 后，对应能力字段不为 None
    - 验证：未注册时对应字段为 None

- [x] 3. 新建 `protocol.py`，实现 JSON-RPC 2.0 消息模型
  - [x] 3.1 定义 `MCPErrorCode` 常量类
    - 标准码：`PARSE_ERROR=-32700`, `INVALID_REQUEST=-32600`, `METHOD_NOT_FOUND=-32601`, `INVALID_PARAMS=-32602`, `INTERNAL_ERROR=-32603`
    - MCP 扩展码：`RESOURCE_NOT_FOUND=-32002`, `TOOL_NOT_FOUND=-32003`, `PROMPT_NOT_FOUND=-32004`
  - [x] 3.2 定义 Pydantic 消息模型
    - `JSONRPCError`: `code`, `message`, `data: Optional[Any]`
    - `JSONRPCRequest`: `jsonrpc: Literal["2.0"]`, `id: Optional[Union[str,int]]`, `method`, `params`
    - `JSONRPCResponse`: `jsonrpc="2.0"`, `id`, `result`, `error`
  - [x] 3.3 定义业务数据模型
    - `InitializeParams`, `ClientInfo`, `InitializeResult`, `ServerInfo`
    - `CallToolParams`, `CallToolResult`, `ContentItem`
    - `ReadResourceResult`, `ResourceContent`
    - `GetPromptResult`, `PromptMessage`
  - [ ]* 3.4 为消息模型编写序列化/反序列化单元测试
    - 验证 `JSONRPCRequest` 解析合法请求和 notification（无 id）
    - 验证 `JSONRPCResponse` 序列化后字段名符合 camelCase 规范

- [x] 4. 新建 `dispatcher.py`，实现请求分发器
  - [x] 4.1 实现 `MCPDispatcher.__init__` 和 `dispatch` 主入口
    - 接收 `JSONRPCRequest`，根据 `method` 路由到对应处理方法
    - notification（`id` 为 None）处理后返回 `None`
    - 未知方法返回 `METHOD_NOT_FOUND` 错误响应
  - [x] 4.2 实现 `_handle_initialize` 和 `_handle_ping`
    - `initialize`：聚合所有注册 Server 的 capabilities，返回 `InitializeResult`
    - `ping`：返回空 `{}`
  - [x] 4.3 实现 `_handle_tools_list` 和 `_handle_tools_call`
    - `tools/list`：遍历 registry 中所有 Server，合并 tool 列表
    - `tools/call`：找到对应 Server，调用 `execute_tool`；工具不存在返回 `TOOL_NOT_FOUND`；执行异常返回 `isError: true` 的 `CallToolResult`（不抛 JSON-RPC 错误）
  - [x] 4.4 实现 `_handle_resources_list` 和 `_handle_resources_read`
    - `resources/list`：合并所有 Server 的 resource 列表
    - `resources/read`：按 URI 找到对应 Server，调用 `read_resource`；URI 不存在返回 `RESOURCE_NOT_FOUND`
  - [x] 4.5 实现 `_handle_prompts_list` 和 `_handle_prompts_get`
    - `prompts/list`：合并所有 Server 的 prompt 列表
    - `prompts/get`：按名称找到对应 Server，调用 `get_prompt`；不存在返回 `PROMPT_NOT_FOUND`
  - [ ]* 4.6 为 `MCPDispatcher` 编写单元测试（mock MCPServerRegistry）
    - 验证 `initialize` 返回正确的 `protocolVersion` 和 `capabilities`
    - 验证 `tools/call` 对不存在工具名返回 `-32003`
    - 验证 notification 返回 `None`
    - 验证未知方法返回 `-32601`
  - [ ]* 4.7 为 `dispatcher.dispatch()` 编写属性测试
    - **Property 1: 合法 JSON-RPC 请求必须返回合法响应或 None**
    - **Validates: 协议层正确性**
    - 使用 `hypothesis` 生成任意合法 method 字符串，验证返回值类型

- [x] 5. 检查点 — 确保基础层测试全部通过
  - 确保所有测试通过，如有问题请向用户反馈。

- [x] 6. 新建 `transport.py`，实现传输层
  - [x] 6.1 实现 HTTP POST 处理函数 `handle_jsonrpc_request`
    - 解析请求体为 JSON，失败返回 `PARSE_ERROR`
    - 验证为合法 `JSONRPCRequest`，失败返回 `INVALID_REQUEST`
    - 调用 `dispatcher.dispatch()`，notification 返回 204，正常请求返回 200 JSON
  - [x] 6.2 实现 SSE 生成器 `sse_generator`
    - 建立连接时推送 `event: endpoint\ndata: {"uri":"/mcp"}` 事件
    - 使用 `asyncio.Queue` 管理消息队列
    - 客户端断开时静默清理队列，不记录为错误
  - [ ]* 6.3 为 HTTP 处理函数编写属性测试
    - **Property 2: 任意非法 JSON 输入必须返回 -32700，不能抛出 500**
    - **Validates: 传输层健壮性**

- [x] 7. 新建 `router.py`，挂载 FastAPI 路由
  - 创建 `APIRouter(prefix="/mcp", tags=["mcp"])`
  - 实现 `POST /mcp`：调用 `transport.handle_jsonrpc_request`
  - 实现 `GET /mcp/sse`：返回 SSE 流（`StreamingResponse` 或 `EventSourceResponse`）
  - 实现 `GET /mcp/capabilities`：返回所有 Server 能力声明（调试用）

- [x] 8. 重构 `knowledge_server.py`，补全 prompts 能力与 Resource 实现
  - [x] 8.1 在 `__init__` 中注册 prompts
    - 注册 `query_knowledge_prompt`：引导用户提问知识库的 prompt 模板
    - 参数：`topic: str`（required），`detail_level: str`（optional）
  - [x] 8.2 实现 `read_resource` 方法
    - 支持 URI 格式：`knowledge://{topic}`
    - 返回对应知识库内容，URI 不存在时抛出异常（由 dispatcher 转为 RESOURCE_NOT_FOUND）
  - [x] 8.3 实现 `get_prompt` 方法
    - 根据 prompt name 和 arguments 生成 `GetPromptResult`
    - prompt 不存在时抛出异常
  - [ ]* 8.4 为 `KnowledgeMCPServer` 编写单元测试
    - 验证 `list_tools()` 返回非空列表
    - 验证 `list_prompts()` 返回已注册的 prompt
    - 验证 `get_capabilities()` 包含 tools、resources、prompts 三项

- [x] 9. 重构 `document_server.py`，补全 prompts 能力与 Resource 实现
  - [x] 9.1 在 `__init__` 中注册 prompts
    - 注册 `search_document_prompt`：引导用户搜索文档的 prompt 模板
    - 参数：`query: str`（required），`file_type: str`（optional）
  - [x] 9.2 实现 `read_resource` 方法
    - 支持 URI 格式：`document://{doc_id}`
    - 返回对应文档内容
  - [x] 9.3 实现 `get_prompt` 方法
    - 根据 prompt name 和 arguments 生成 `GetPromptResult`
  - [ ]* 9.4 为 `DocumentMCPServer` 编写单元测试
    - 验证 `list_prompts()` 返回已注册的 prompt
    - 验证 `get_capabilities()` 包含 tools、resources、prompts 三项

- [x] 10. 在 `main.py` 注册 MCP 路由
  - 从 `app.mcp.router` import `router as mcp_router`
  - 调用 `app.include_router(mcp_router)`
  - 确保 `KnowledgeMCPServer` 和 `DocumentMCPServer` 在应用启动时注册到 `MCPServerRegistry`

- [ ] 11. 编写集成测试
  - [ ]* 11.1 编写握手流程集成测试
    - 使用 `httpx.AsyncClient` + FastAPI `TestClient`
    - 验证 `POST /mcp` initialize → 返回 `protocolVersion: "2024-11-05"` 和完整 capabilities
    - 验证 `notifications/initialized` notification → 返回 204
  - [ ]* 11.2 编写工具调用集成测试
    - 验证 `tools/list` 返回 KnowledgeMCPServer 和 DocumentMCPServer 的所有工具
    - 验证 `tools/call` 对不存在工具名返回 `-32003` 错误
  - [ ]* 11.3 编写 SSE 端点集成测试
    - 验证 `GET /mcp/sse` 返回 `text/event-stream` Content-Type
    - 验证首条事件为 `event: endpoint`

- [x] 12. 最终检查点 — 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户反馈。

## 备注

- 标有 `*` 的子任务为可选项，可跳过以加快 MVP 进度
- 每个任务均引用设计文档中对应的组件规范
- 属性测试使用 `hypothesis` 库
- 集成测试使用 `httpx.AsyncClient`
- 实现过程中不引入新的第三方依赖（`sse-starlette` 若未安装则用 `StreamingResponse` 替代）
