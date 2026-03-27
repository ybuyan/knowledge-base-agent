# Tool系统架构改进规范

## 1. 项目概述

### 1.1 背景
当前Tool系统存在代码重复、缺乏复用、可扩展性差等问题，需要进行架构重构。

### 1.2 目标
- 提高代码复用性，减少重复代码
- 增强可扩展性，支持多Tool链式调用
- 统一LLM调用接口
- 添加缓存和错误处理机制

### 1.3 范围
- Tool执行器抽象
- QA Agent重构
- LLM客户端统一封装
- 响应流式输出公共方法

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Chat API Layer                        │
│                  (chat.py - 只负责路由)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         QA Agent                             │
│           (agents/qa_agent.py - 核心协调逻辑)                 │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Tool Router  │  │ RAG Engine  │  │ LLM Client  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Tool Executor                           │
│         (services/tool_executor.py - 执行层)                 │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Middleware  │  │   Cache     │  │  Registry   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块职责

| 模块 | 职责 | 文件 |
|------|------|------|
| Chat API | 路由、参数验证、响应 | `api/routes/chat.py` |
| QA Agent | 协调Tool和RAG | `agents/qa_agent.py` |
| Tool Executor | 执行Tool、缓存、错误处理 | `services/tool_executor.py` |
| LLM Client | 统一LLM调用接口 | `services/llm_client.py` |
| Response Builder | 构建流式响应 | `services/response_builder.py` |

## 3. 详细设计

### 3.1 Tool Executor

```python
class ToolExecutor:
    """Tool执行器 - 统一管理Tool执行"""
    
    def __init__(self):
        self._cache = ToolCache()
        self._middlewares: List[ToolMiddleware] = []
    
    async def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行单个Tool调用"""
        # 1. 检查缓存
        # 2. 执行前置中间件
        # 3. 执行Tool
        # 4. 执行后置中间件
        # 5. 缓存结果
        pass
    
    async def execute_batch(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """批量执行Tool调用（并行）"""
        pass
    
    def add_middleware(self, middleware: ToolMiddleware):
        """添加中间件"""
        pass
```

### 3.2 QA Agent

```python
class QAAgent:
    """问答Agent - 协调Tool和RAG"""
    
    def __init__(self):
        self._tool_executor = ToolExecutor()
        self._llm_client = LLMClient()
        self._rag_engine = RAGEngine()
    
    async def process(self, query: str) -> AsyncGenerator[ResponseChunk, None]:
        """处理用户查询"""
        # 1. 判断是否需要Tool
        # 2. 执行Tool或RAG
        # 3. 生成回答
        pass
    
    async def _should_use_tool(self, query: str) -> Optional[ToolCall]:
        """判断是否需要使用Tool"""
        pass
    
    async def _execute_tool_flow(self, query: str, tool_call: ToolCall) -> AsyncGenerator:
        """执行Tool流程"""
        pass
    
    async def _execute_rag_flow(self, query: str) -> AsyncGenerator:
        """执行RAG流程"""
        pass
```

### 3.3 LLM Client

```python
class LLMClient:
    """统一LLM调用客户端"""
    
    def __init__(self, config: LLMConfig):
        self._config = config
        self._client = None
    
    async def chat(self, messages: List[Dict], tools: List[Dict] = None, **kwargs) -> ChatResponse:
        """聊天补全"""
        pass
    
    async def chat_with_tools(self, messages: List[Dict], tools: List[Dict]) -> ToolDecision:
        """带Tool的聊天"""
        pass
    
    async def stream_chat(self, messages: List[Dict], **kwargs) -> AsyncGenerator:
        """流式聊天"""
        pass
```

### 3.4 Response Builder

```python
class ResponseBuilder:
    """响应构建器 - 统一流式输出"""
    
    @staticmethod
    def text_chunk(content: str) -> str:
        """构建文本块"""
        pass
    
    @staticmethod
    def done_chunk(sources: List[Dict]) -> str:
        """构建完成块"""
        pass
    
    @staticmethod
    def error_chunk(error: str) -> str:
        """构建错误块"""
        pass
    
    @staticmethod
    def tool_chunk(tool_name: str, tool_args: Dict) -> str:
        """构建Tool调用块"""
        pass
```

### 3.5 Tool Middleware

```python
class ToolMiddleware(ABC):
    """Tool中间件基类"""
    
    @abstractmethod
    async def before_execute(self, tool_name: str, args: Dict) -> Dict:
        """执行前钩子"""
        pass
    
    @abstractmethod
    async def after_execute(self, tool_name: str, result: Dict) -> Dict:
        """执行后钩子"""
        pass
    
    @abstractmethod
    async def on_error(self, tool_name: str, error: Exception) -> Dict:
        """错误处理钩子"""
        pass


class LoggingMiddleware(ToolMiddleware):
    """日志中间件"""
    pass


class CacheMiddleware(ToolMiddleware):
    """缓存中间件"""
    pass


class RetryMiddleware(ToolMiddleware):
    """重试中间件"""
    pass
```

## 4. 配置设计

### 4.1 LLM配置

```yaml
# config/llm.yaml
default_model: "qwen-plus"
models:
  qwen-plus:
    temperature: 0.3
    max_tokens: 2000
  qwen-turbo:
    temperature: 0.1
    max_tokens: 1000

tool_decision:
  model: "qwen-turbo"
  temperature: 0.1
  max_retries: 3
```

### 4.2 Tool配置

```yaml
# config/tools.yaml
executor:
  cache_enabled: true
  cache_ttl: 300
  max_parallel: 5
  timeout: 30

middlewares:
  - logging
  - cache
  - retry
```

## 5. 数据结构

### 5.1 ToolCall

```python
@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]
```

### 5.2 ToolResult

```python
@dataclass
class ToolResult:
    success: bool
    data: Dict[str, Any]
    error: Optional[str] = None
    cached: bool = False
    execution_time: float = 0.0
```

### 5.3 ResponseChunk

```python
@dataclass
class ResponseChunk:
    type: str  # "text", "tool_call", "done", "error"
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict] = None
    sources: Optional[List[Dict]] = None
```

## 6. 接口设计

### 6.1 chat.py 简化后

```python
@router.post("/ask/stream")
async def ask_stream(request: ChatStreamRequest):
    """流式问答接口"""
    agent = QAAgent()
    
    async def generate():
        async for chunk in agent.process(request.question):
            yield ResponseBuilder.text_chunk(chunk.content)
        yield ResponseBuilder.done_chunk(chunk.sources)
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

## 7. 迁移策略

### 7.1 阶段一：基础设施
1. 创建ToolExecutor
2. 创建ResponseBuilder
3. 创建LLMClient

### 7.2 阶段二：Agent重构
1. 创建QAAgent
2. 迁移Tool调用逻辑
3. 迁移RAG逻辑

### 7.3 阶段三：chat.py简化
1. 使用QAAgent替换原有逻辑
2. 删除重复代码

## 8. 测试策略

### 8.1 单元测试
- ToolExecutor测试
- LLMClient测试
- ResponseBuilder测试

### 8.2 集成测试
- QA Agent端到端测试
- Tool调用流程测试
- RAG流程测试

## 9. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 重构期间功能中断 | 高 | 分阶段迁移，保持向后兼容 |
| 性能下降 | 中 | 添加性能测试，监控关键指标 |
| 缓存一致性问题 | 中 | 设计合理的缓存失效策略 |

## 10. 成功指标

- 代码重复率降低 > 50%
- 单元测试覆盖率 > 80%
- Tool调用响应时间 < 100ms（缓存命中）
- 支持多Tool并行调用
