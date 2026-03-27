# Tool系统架构改进任务清单

## 阶段一：基础设施

### 1.1 Tool Executor
- [ ] 创建 `services/tool_executor.py`
- [ ] 实现 `ToolCall` 数据类
- [ ] 实现 `ToolResult` 数据类
- [ ] 实现 `ToolExecutor.execute()` 方法
- [ ] 实现 `ToolExecutor.execute_batch()` 方法
- [ ] 实现 `ToolCache` 缓存类
- [ ] 添加单元测试 `tests/test_tool_executor.py`

### 1.2 Response Builder
- [ ] 创建 `services/response_builder.py`
- [ ] 实现 `ResponseBuilder.text_chunk()` 方法
- [ ] 实现 `ResponseBuilder.done_chunk()` 方法
- [ ] 实现 `ResponseBuilder.error_chunk()` 方法
- [ ] 实现 `ResponseBuilder.tool_chunk()` 方法
- [ ] 添加单元测试 `tests/test_response_builder.py`

### 1.3 LLM Client
- [ ] 创建 `services/llm_client.py`
- [ ] 实现 `LLMConfig` 配置类
- [ ] 实现 `LLMClient.chat()` 方法
- [ ] 实现 `LLMClient.chat_with_tools()` 方法
- [ ] 实现 `LLMClient.stream_chat()` 方法
- [ ] 添加单元测试 `tests/test_llm_client.py`

### 1.4 Tool Middleware
- [ ] 创建 `services/tool_middleware.py`
- [ ] 实现 `ToolMiddleware` 基类
- [ ] 实现 `LoggingMiddleware` 日志中间件
- [ ] 实现 `CacheMiddleware` 缓存中间件
- [ ] 实现 `RetryMiddleware` 重试中间件

## 阶段二：Agent重构

### 2.1 QA Agent
- [ ] 创建 `agents/qa_agent.py`
- [ ] 实现 `QAAgent.process()` 方法
- [ ] 实现 `QAAgent._should_use_tool()` 方法
- [ ] 实现 `QAAgent._execute_tool_flow()` 方法
- [ ] 实现 `QAAgent._execute_rag_flow()` 方法
- [ ] 添加集成测试 `tests/test_qa_agent.py`

### 2.2 RAG Engine
- [ ] 创建 `services/rag_engine.py`
- [ ] 实现 `RAGEngine.search()` 方法
- [ ] 实现 `RAGEngine.build_context()` 方法
- [ ] 添加单元测试 `tests/test_rag_engine.py`

## 阶段三：API简化

### 3.1 Chat API重构
- [ ] 修改 `api/routes/chat.py` 使用新Agent
- [ ] 删除重复的Tool调用逻辑
- [ ] 删除重复的响应构建逻辑
- [ ] 添加回归测试

### 3.2 配置化
- [ ] 创建 `config/llm.yaml` 配置文件
- [ ] 创建 `config/tools.yaml` 配置文件
- [ ] 实现配置加载逻辑

### 3.3 文档和清理
- [ ] 更新API文档
- [ ] 删除废弃代码
- [ ] 更新README

## 验收标准

### 功能验收
- [ ] 所有现有功能正常工作
- [ ] Tool调用正确执行
- [ ] RAG检索正确执行
- [ ] 流式输出正常

### 性能验收
- [ ] Tool调用响应时间 < 500ms
- [ ] 缓存命中响应时间 < 50ms
- [ ] 支持多Tool并行调用

### 质量验收
- [ ] 单元测试覆盖率 > 80%
- [ ] 无P0/P1级别bug
- [ ] 代码通过lint检查
