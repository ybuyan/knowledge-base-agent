# 前端转型 Agent 开发答辩 PPT 大纲

> 项目：企业级 AI 问答系统（公司制度问答与流程指引助手）
> 定位：突出 Agent 架构设计 + 核心技术实现 + 前端转型价值

---

## Slide 1 — 封面

**企业级 AI 问答系统**
公司制度问答与流程指引助手

- 姓名 / 部门
- 答辩日期
- 副标题：从前端开发到 Agent 全栈工程师的转型实践

---

## Slide 2 — 项目背景与痛点

**为什么要做这个系统？**

- 员工查制度靠翻文件、问 HR，效率低
- 流程指引分散，新员工上手成本高
- 传统搜索无法理解语义，关键词匹配不准

**解决方案：**
> 用自然语言对话，替代人工查询 + 流程咨询

---

## Slide 3 — 系统整体架构

```
前端 Vue3 + TypeScript
        ↓ HTTP / SSE
    FastAPI 网关层
        ↓
  OrchestratorAgent（意图路由）
    ↙        ↓        ↘
QAAgent  GuideAgent  MemoryAgent
  ↓           ↓
RAG检索   流程指引DB
  ↓
ChromaDB + MongoDB
```

**技术栈一句话：**
FastAPI + LangChain + ChromaDB + MongoDB + Vue3 + 通义千问

---

## Slide 4 — Agent 系统设计：四大 Agent

| Agent | 职责 |
|-------|------|
| OrchestratorAgent | 意图识别 → 路由分发 |
| QAAgent | RAG 检索 + ReAct 多轮工具调用 |
| GuideAgent | 数据驱动的流程指引 |
| MemoryAgent | 跨会话记忆检索 |

**设计亮点：注册表模式 + 统一调度**

```python
# 核心基类 + 引擎（伪代码）
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, input_data: dict) -> dict: ...

class AgentEngine:
    def register(self, agent: BaseAgent): 
        self._agents[agent.agent_id] = agent
    
    async def execute(self, agent_id: str, input_data: dict):
        return await self._agents[agent_id].run(input_data)

# 全局单例，启动时注册
agent_engine.register(QAAgent())
agent_engine.register(GuideAgent())
```

---

## Slide 5 — 核心 1：意图识别与路由（OrchestratorAgent）

**问题：** 用户一句话，系统怎么知道该干什么？

**方案：LLM 意图分类 + 关键词快速路径**

```python
# 意图类型：qa / guide / memory / hybrid / leave_balance
async def detect_intent_with_llm(query, history) -> str:
    # 1. 分析上下文：上一轮是否是流程指引对话？
    if last_assistant_msg 包含 ["申请", "流程", "步骤"]:
        context_hint = "当前可能是多轮对话的延续"
    
    # 2. 调用 LLM 分类
    system_prompt = prompt_manager.get_system_prompt("intent_detection")
    result = await call_llm(query + context_hint, system_prompt)
    
    # 3. 验证 + 回退
    if result not in valid_intents:
        return await detect_intent_with_keywords(query)  # 降级
    return result

# 路由分发
async def run(self, input_data):
    intent = await detect_intent(query, history)
    if intent == "guide":
        return await agent_engine.execute("guide_agent", ...)
    elif intent == "hybrid":
        # 并行执行 QA + Memory
        qa_result, memory_result = await asyncio.gather(
            agent_engine.execute("qa_agent", ...),
            agent_engine.execute("memory_agent", ...)
        )
```

**效果：** 5 种意图精准分类，多轮对话上下文感知

---

## Slide 6 — 核心 2：RAG 检索增强生成（QAAgent）

**RAG 流程：**

```
用户问题
  → KBQueryOptimizer（LLM 改写查询，提取关键词）
  → 向量检索（ChromaDB cosine 相似度）+ 关键词检索（MongoDB 倒排索引）
  → Reranker 重排序
  → AnswerValidator 过滤（相似度阈值 0.7）
  → LLM 流式生成回答（SSE）
```

**混合检索核心代码（伪代码）：**

```python
# 向量检索
async def retrieve_documents(self, query):
    query_embedding = await embeddings.aembed_query(query)
    results = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k * 3  # 先多取，再重排
    )
    if reranker.is_available():
        return reranker.rerank(query, results, top_k)
    return results[:top_k]

# 关键词检索（倒排索引）
async def keyword_search(query):
    terms = jieba.cut(query)          # 中文分词
    docs = mongo.keyword_index.find(  # 词频交集打分
        {"terms": {"$in": terms}}
    )
    return sorted(docs, by=term_freq_score)
```

**性能数据：** 向量检索 ~80ms，端到端 ~2.1s

---

## Slide 7 — 核心 3：ReAct 多轮工具调用

**什么是 ReAct？** Reason（推理）→ Act（行动）→ Observe（观察）循环

```
用户查询
  ↓
LLM 决策：需要调用工具吗？（temperature=0.1 低温稳定）
  ↓ 是
并行执行工具（ToolExecutor.execute_batch）
  ↓
将工具结果追加到消息链，继续推理
  ↓ 直到 LLM 不再调用工具（最多 5 轮）
流式生成最终回答
```

**退出机制（关键）：**

```python
# 伪代码：ReAct 循环
for i in range(MAX_ITERATIONS=5):
    decision = await llm.chat_with_tools(messages, temperature=0.1)
    
    if not decision.tool_calls:  # LLM 不再调用工具 → 退出
        break
    
    # 并行执行所有工具
    tool_results = await asyncio.gather(*[
        tool_executor.execute(call) for call in decision.tool_calls
    ])
    messages.append(tool_results)  # 追加观察结果

# 最终流式输出
async for chunk in llm.stream_chat(messages):
    yield chunk
```

**温度参数影响：** 0.1 时平均 1.8 轮收敛，0.9 时需 4.2 轮

---

## Slide 8 — 核心 4：数据驱动的流程指引（GuideAgent）

**设计亮点：** 流程定义存 MongoDB，无需为每个流程写代码

```
用户："我要申请婚假"
  ↓
GuideAgent._match_flow_guide()
  ↓
从 DB 加载所有 active 流程 → 关键词匹配 triggers 字段
  ↓ 命中"婚假申请流程"
锁定 session（多轮对话连续性）
  ↓
动态构建 Prompt（注入流程步骤）
  ↓
LLM 流式生成指引
```

**多轮对话锁定机制（伪代码）：**

```python
async def _match_flow_guide(self, query, session_id):
    # 1. 当前 query 匹配新流程（优先）
    for guide in all_guides:
        if any(trigger in query for trigger in guide.triggers):
            await save_process_context(session_id, {"guide_id": guide.id})
            return guide
    
    # 2. 没命中 → 沿用 session 锁定的流程（多轮连续性）
    ctx = await get_process_context(session_id)
    if ctx.get("guide_id"):
        return await repo.get_by_id(ctx["guide_id"])
    
    return None  # 未匹配

# 流程步骤动态注入 Prompt
steps_text = "\n".join(
    f"{s.sequence}. {s.title}：{s.description}"
    for s in matched_guide.steps
)
```

---

## Slide 9 — 核心 5：三层记忆架构

```
短期记忆（内存）          长期记忆（向量DB）         持久化（MongoDB）
ShortTermMemory          ChromaDB                  sessions / messages
当前会话上下文            跨会话语义检索              完整历史 + 分页
max_tokens=3000          conversations 集合         支持搜索 / 归档
Token 滑动窗口            QA对向量化存储
```

**核心实现（伪代码）：**

```python
# 对话向量化存储（实现跨会话记忆）
async def _store_to_vector_db(self, session_id, answer):
    last_question = memory.get_last_user_message()
    conv_text = f"Q: {last_question}\nA: {answer}"
    
    embedding = await embeddings.aembed_query(conv_text)
    conversations_collection.add(
        ids=[uuid4()],
        embeddings=[embedding],
        documents=[conv_text],
        metadatas=[{"session_id": session_id}]
    )

# 检索时：并行拉取文档 + 历史对话
docs, convs = await asyncio.gather(
    retriever.retrieve_documents(query),
    retriever.retrieve_conversations(query, exclude_session=current_session)
)
```

**Token 优化效果：** 平均从 8000 tokens 压缩到 3000 tokens，节省约 60% 成本

---

## Slide 10 — 核心 6：MCP 标准协议层

**什么是 MCP？** Model Context Protocol — AI 工具调用的标准化协议（JSON-RPC 2.0）

**为什么要做 MCP？**
> 让知识库能力标准化对外暴露，任意 MCP 客户端都能接入

```
/mcp POST          → JSON-RPC 单次请求
/mcp/sse GET       → SSE 持久连接（15s keepalive）

支持方法：
  initialize       握手，返回 capabilities
  tools/call       调用工具（query_knowledge / search_documents）
  resources/read   读取资源（knowledge:// / document://）
  prompts/get      获取提示词模板
```

**分发器核心逻辑（伪代码）：**

```python
async def dispatch(self, request: JSONRPCRequest):
    # 速率限制 → 权限检查 → 路由
    await rate_limiter.check(auth_context)
    
    if request.method == "tools/call":
        # 遍历注册的 MCPServer，找到拥有该工具的 Server
        for server in MCPServerRegistry.list_servers():
            if request.params["name"] in server.tools:
                return await server.execute_tool(...)
    
    elif request.method == "resources/read":
        if not access_control.check_access(uri, auth_context):
            raise PermissionError("Access denied")
        return await server.read_resource(uri)
```

---

## Slide 11 — Skill 引擎：流水线设计

**设计思路：** 将 Agent 的执行步骤抽象为可配置的流水线

```yaml
# SKILL.md 配置（数据驱动，无需改代码）
skill_id: qa_rag
pipeline:
  - step: embed_query
    processor: EmbeddingProcessor
  - step: retrieve
    processor: VectorRetriever
    params: {top_k: 5}
  - step: build_context
    processor: ContextBuilder
    params: {max_tokens: 4000}
  - step: generate
    processor: LLMGenerator
    params: {stream: false}
```

```python
# 引擎执行（伪代码）
async def execute(self, skill_id, input_data):
    skill = self.skill_loader.get(skill_id)
    context = input_data.copy()
    
    for step in skill["pipeline"]:
        processor = ProcessorRegistry.get(step["processor"])
        result = await processor.process(context, step["params"])
        context.update(result)  # 每步结果传递给下一步
    
    return extract_output(context, skill["output"])
```

---

## Slide 12 — 流式响应：SSE 实现

**前端（Vue3）：** 原生 fetch + ReadableStream，支持 AbortController 中止

```typescript
// 伪代码：SSE 流式接收
const response = await fetch('/api/chat/v2/ask/stream', {
    method: 'POST',
    signal: abortController.signal,
    body: JSON.stringify({ query, session_id })
})

const reader = response.body.getReader()
const decoder = new TextDecoder()

while (true) {
    const { done, value } = await reader.read()
    if (done) break
    
    const chunk = decoder.decode(value)
    // 解析 SSE 格式：data: {"type":"text","content":"..."}
    if (chunk.type === 'text') appendToMessage(chunk.content)
    if (chunk.type === 'done') showSources(chunk.sources)
}
```

**后端（FastAPI）：** StreamingResponse + async generator

```python
async def stream_answer(query, session_id):
    async for chunk in guide_agent.run_stream(input_data):
        yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"
```

---

## Slide 13 — 前端转型亮点

**从前端视角带来的价值：**

| 前端经验 | 在 Agent 开发中的应用 |
|---------|---------------------|
| 组件化思维 | Agent 模块化设计，每个 Agent 单一职责 |
| 状态管理（Pinia） | 会话状态、消息流、分页游标统一管理 |
| 异步编程（Promise/async） | Python asyncio 并行 Agent 调用 |
| 用户体验意识 | SSE 流式输出、快捷提问、相关链接 |
| API 设计经验 | RESTful + SSE 接口规范设计 |

**技术跨越：**
> Vue3 Composition API → Python async/await
> 前端状态机 → Agent 状态机（idle/processing/completed/error）
> 组件 props/emit → Agent input_data/output dict

---

## Slide 14 — 系统难点与解决方案

| 难点 | 解决方案 |
|------|---------|
| 多轮对话上下文丢失 | session 锁定 + 三层记忆架构 |
| 意图识别不准 | LLM 分类 + 关键词快速路径双保险 |
| ReAct 无限循环 | 最大 5 轮限制 + 低温度（0.1）稳定决策 |
| 向量删除不可靠 | ID 前缀匹配替代 metadata 过滤 |
| 禁止主题绕过 | 预检查机制，在 RAG 检索前拦截 |
| Token 超限 | 滑动窗口 + 3000 token 上限，节省 60% |

---

## Slide 15 — 项目成果与数据

**功能完成度：**
- 知识库问答（RAG + ReAct）✅
- 流程指引（数据驱动，支持动态配置）✅
- 多轮对话（三层记忆）✅
- MCP 标准协议（v1.1.0）✅
- 约束配置系统（应用率 90.9%）✅

**性能指标：**
- 向量检索：~80ms
- 端到端响应：~2.1s
- Token 成本节省：~60%
- ReAct 平均收敛：1.8 轮

---

## Slide 16 — 未来规划

**短期：**
- 记忆压缩（SummaryBuffer，旧对话摘要化）
- 相似问题推荐

**中期：**
- 多用户权限隔离
- Redis 分布式短期记忆

**长期：**
- 知识图谱 + 推理查询
- 多模态支持（图片/语音）

---

## Slide 17 — 总结

**一句话：**
> 用 Agent 架构 + RAG 技术，把企业知识库变成会对话的智能助手

**核心技术收获：**
- Agent 设计模式（注册表 + 状态机 + 路由）
- RAG 全链路（向量化 → 检索 → 重排 → 生成）
- ReAct 推理循环
- MCP 标准协议
- 三层记忆架构

**转型价值：**
前端工程师的用户体验思维 + 全栈 Agent 开发能力 = 更懂产品的 AI 工程师

---

> 备注：代码示例均为项目实际代码的精简伪代码版本，完整实现见项目仓库
