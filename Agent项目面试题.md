# 企业级 AI 问答系统 — 项目面试题

> 覆盖范围：Agent 架构、RAG、LLM、MCP、记忆系统、认证安全、前端转型
> 难度分级：⭐ 基础 / ⭐⭐ 中级 / ⭐⭐⭐ 高级

---

## 一、项目整体理解

**Q1 ⭐ 这个项目解决了什么问题？为什么要用 Agent 而不是简单的 RAG？**

A：项目解决企业员工查询公司制度、流程规范效率低的问题。
选择 Agent 而非简单 RAG 的原因：
1. 用户意图多样（查知识/查流程/查记忆/查余额），需要路由分发
2. 部分问题需要多步推理（ReAct 工具调用）
3. 流程指引需要多轮对话状态管理
4. 假期余额查询需要权限验证和数据库查询，不是纯检索问题

---

**Q2 ⭐ 项目整体架构是怎样的？各层职责是什么？**

A：五层架构：
- 前端展示层：Vue3 + TypeScript，SSE 流式接收，Pinia 状态管理
- API 网关层：FastAPI，JWT 鉴权，X-Trace-ID 请求追踪，全局异常处理
- Agent 核心层：OrchestratorAgent 路由 → QAAgent/GuideAgent/MemoryAgent 执行
- MCP 协议层：标准化工具/资源/提示词对外暴露，含完整安全机制
- 基础设施层：ChromaDB（向量）+ MongoDB（文档/会话/流程）

---

**Q3 ⭐⭐ 项目用了哪些 AI 相关技术？各自解决什么问题？**

A：
- 通义千问 qwen-plus：LLM 推理、意图识别、回答生成、流程提取
- text-embedding-v3：文本向量化，支持语义检索
- ChromaDB HNSW：向量存储与 cosine 相似度检索
- RAG：检索增强生成，让 LLM 基于知识库回答而非凭空生成
- ReAct：多步工具调用推理循环
- jieba：中文分词，构建倒排索引

---

## 二、Agent 架构设计

**Q4 ⭐ 项目有几个 Agent？各自职责是什么？**

A：五个 Agent：
- OrchestratorAgent：意图识别 + 路由分发（qa/guide/memory/hybrid/leave_balance）
- QAAgent：RAG 检索 + ReAct 多轮工具调用，回答知识库问题
- GuideAgent：数据驱动的流程指引，支持多轮对话 session 锁定
- MemoryAgent：跨会话历史记忆检索
- DocumentAgent：文档上传处理流水线

---

**Q5 ⭐⭐ Agent 系统是如何设计的？BaseAgent 和 AgentEngine 的作用？**

A：采用注册表模式：
- `BaseAgent` 是抽象基类，强制子类实现 `agent_id`、`name`、`run()` 三个接口
- `AgentEngine` 是全局单例注册表，`register()` 注册、`execute()` 调用
- 启动时按固定顺序注册：DocumentAgent → QAAgent → MemoryAgent → OrchestratorAgent → GuideAgent，**Tool 必须在 Agent 之前注册**，否则 ToolRegistry 为空
- 好处：解耦、可扩展、统一调度入口

```python
class AgentEngine:
    def register(self, agent): self._agents[agent.agent_id] = agent
    async def execute(self, agent_id, input_data):
        return await self._agents[agent_id].run(input_data)
```

**注意：** 实际处理聊天的核心是 `services/qa_agent.py` 的 Service 层 QAAgent（完整 ReAct），由 chat 路由直接调用，不经过 AgentEngine。

---

**Q6 ⭐⭐ OrchestratorAgent 的意图识别是怎么实现的？有什么容错机制？**

A：双保险机制：
1. 主路径：调用 LLM（`intent_detection` prompt），返回 5 种意图之一
2. 上下文感知：检查上一轮 assistant 消息，若含流程相关词汇则添加 context_hint
3. 回退路径：LLM 失败或返回无效意图时，降级为关键词匹配（`_MEMORY_KW`/`_HYBRID_KW`）
4. 配置开关：`agent_config.get_intent_detection_method()` 可切换 llm/keyword 模式

---

**Q7 ⭐⭐⭐ GuideAgent 的多轮对话是怎么保持连续性的？**

A：Session 锁定机制：
1. 用户发起新流程 → 关键词匹配 triggers → 命中后调用 `save_process_context(session_id, {guide_id})`
2. 用户继续对话（如回答"好的"）→ 当前 query 未命中任何流程 → 读取 `get_process_context(session_id)` → 沿用锁定的流程
3. 用户切换话题（意图变为 qa/memory/hybrid）→ OrchestratorAgent 调用 `clear_process_context(session_id)` 解锁
4. 存储：MongoDB `process_contexts` 集合，key 为 session_id

---

## 三、RAG 技术

**Q8 ⭐ 什么是 RAG？项目中 RAG 的完整流程是什么？**

A：RAG（Retrieval-Augmented Generation）= 检索增强生成，先从知识库检索相关内容，再让 LLM 基于检索结果生成回答，避免幻觉。

项目流程：
```
用户问题 → KBQueryOptimizer（LLM 改写查询）
→ 向量检索（ChromaDB）+ 关键词检索（MongoDB 倒排索引）
→ Reranker 重排序（sentence-transformers，不可用时跳过）
→ AnswerValidator 过滤（相似度 < 0.7 的文档丢弃）
→ 构建 Prompt（StrictQAPrompt）
→ LLM 流式生成回答
→ SuggestionGenerator 生成 3 个追问
→ LinkMatcher 匹配相关外部链接
```

---

**Q9 ⭐⭐ 为什么要做混合检索（向量 + 关键词）？各自的优缺点？**

A：
- 向量检索：语义理解强，能处理同义词和模糊查询，但对精确词汇匹配弱
- 关键词检索（倒排索引）：精确词汇匹配强，速度快，但无法理解语义
- 混合检索互补：用户搜"年假"时关键词检索精准命中，搜"带薪休假"时向量检索能找到"年假"相关内容

项目实现：jieba 分词 → MongoDB keyword_index 集合（`{doc_id, terms[], term_freq{}}`）→ `$in` 查询 → 词频交集打分

---

**Q10 ⭐⭐ 向量数据库 ChromaDB 是怎么用的？文档是如何存储和检索的？**

A：
- 两个集合：`documents`（知识库文档块）和 `conversations`（历史对话 QA 对）
- 文档存储：上传 → 文本切分（chunk_size=500, overlap=50）→ 批量向量化（batch_size=100）→ 存入 ChromaDB，ID 格式 `{doc_id}_chunk_{i}`
- 检索：`aembed_query(query)` → `collection.query(query_embeddings, n_results)` → 返回 distances（cosine）
- 删除：按 ID 前缀匹配删除（比 metadata 过滤更可靠）

---

**Q11 ⭐⭐⭐ 查询优化（KBQueryOptimizer）是怎么工作的？为什么需要它？**

A：用户的原始问题往往口语化，不适合直接做向量检索。KBQueryOptimizer 用 LLM 将口语化问题改写为更适合检索的专业表达，同时提取关键词。

流程：
1. 调用 LLM 改写查询，返回 `{optimized_query, keywords, confidence}`
2. `confidence > 0.6` → 使用优化查询；否则使用原始查询
3. 关键词用于增强向量检索（`query + keywords[:3]` 拼接）
4. 结果缓存（LRU，避免重复调用 LLM）

---

## 四、ReAct 与工具调用

**Q12 ⭐⭐ 什么是 ReAct？项目中是怎么实现的？**

A：ReAct = Reason（推理）+ Act（行动）+ Observe（观察），是一种让 LLM 通过多步工具调用解决复杂问题的模式。

项目实现在 `services/qa_agent.py` 的 `_execute_tool_flow()` 中（注意不是 `agents/implementations/qa_agent.py`，那个是 Agent 层，走 SkillEngine）：
```python
for i in range(MAX_ITERATIONS=5):
    decision = await llm_client.chat_with_tools(messages, temperature=0.1)
    if not decision.tool_calls:  # LLM 不再调用工具 → 退出
        break
    # 并行执行所有工具（ToolExecutor.execute_batch，支持缓存+中间件）
    results = await tool_executor.execute_batch(decision.tool_calls)
    messages.append(tool_results)  # 追加观察结果，继续推理
# 最终流式生成回答
```

---

**Q13 ⭐⭐ ReAct 循环怎么防止无限循环？temperature 参数有什么影响？**

A：两重保障：
1. 硬限制：最大迭代 5 轮，超出强制退出
2. 低温度（0.1）：LLM 决策稳定，不会重复调用相同工具，快速收敛

温度影响数据：
- temperature=0.1：平均 1.8 轮，重复调用率 2%
- temperature=0.9：平均 4.2 轮，重复调用率 75%

退出条件：OpenAI 响应中没有 `tool_calls` 字段 → `should_use_tool=False` → 退出循环

---

**Q14 ⭐⭐ 假期余额查询是怎么集成到 Agent 系统的？**

A：完整链路：
1. OrchestratorAgent 识别 `leave_balance` 意图（LLM 分类）
2. `_extract_leave_type()` 从 query 中提取假期类型关键词
3. 调用 `ToolExecutor.execute_tool("check_leave_balance", {leave_type}, auth_context)`
4. `LeaveBalanceTool.execute()` 验证权限（role != "guest"）→ 查询 MongoDB → 格式化输出
5. 余额不足（< 20%）显示 ⚠️ 警告
6. 记录审计日志

---

## 五、记忆系统

**Q15 ⭐⭐ 项目的三层记忆架构是怎么设计的？**

A：
- 短期记忆（ShortTermMemory）：内存存储，当前会话上下文，max_tokens=3000，滑动窗口截断
- 长期记忆（ChromaDB conversations 集合）：历史 QA 对向量化存储，支持跨会话语义检索
- 持久化存储（MongoDB messages 集合）：完整消息历史，支持分页、搜索、归档

**协作流程：**
1. 首次访问 session → 从 MongoDB 加载历史消息到短期记忆
2. 检索时并行：短期记忆（当前上下文）+ 长期记忆（相关历史 QA 对）
3. 回答后：更新短期记忆 → 持久化到 MongoDB → 向量化 QA 对存入 ChromaDB

---

**Q16 ⭐⭐ Token 管理是怎么做的？为什么能节省 60% 成本？**

A：
- 短期记忆上限 3000 tokens，超出时滑动窗口删除最早对话
- 系统 prompt 受保护不被删除
- 长期记忆按需加载，不占用短期记忆空间
- 历史消息只加载最近 6 条（API 层），QAAgent 只使用最近 4 轮

原始对话平均 8000 tokens → 优化后 3000 tokens，节省约 60%

---

## 六、MCP 协议

**Q17 ⭐ 什么是 MCP？项目为什么要实现 MCP？**

A：MCP（Model Context Protocol）是 AI 工具调用的标准化协议，基于 JSON-RPC 2.0，让任意 MCP 客户端都能以统一方式调用工具、读取资源、获取提示词。

项目实现 MCP 的原因：
1. 将知识库查询、文档搜索能力标准化对外暴露
2. 兼容任意 MCP 客户端（如 Claude Desktop、Cursor 等）
3. 支持 SSE 持久连接，适合流式场景

---

**Q18 ⭐⭐ MCP 的安全机制是怎么实现的？**

A：四层安全：
1. 认证（MCPAuthMiddleware）：`X-API-Key` 头验证，无效 key 返回 401，无 key 降级为 guest
2. 授权（ResourceAccessControl）：资源 URI 三级分类（public/internal/confidential），按角色过滤
3. 速率限制（RateLimiter）：滑动窗口算法，超限返回 429，guest 用户 30次/分钟
4. 审计（AuditLogger）：所有操作记录到 MongoDB audit_logs，含响应时间、用户信息、操作结果

---

**Q19 ⭐⭐⭐ MCP Dispatcher 的分发逻辑是怎样的？**

A：
```python
async def dispatch(self, request, auth_context):
    # 1. 速率限制
    await rate_limiter.check_rate_limit(auth_context.user_id, auth_context.rate_limit)
    # 2. 方法路由
    if method == "tools/call":
        # 遍历所有注册的 MCPServer，找到拥有该工具的 Server
        for server in MCPServerRegistry.list_servers():
            if tool_name in server.tools:
                return await server.execute_tool(tool_name, arguments)
    elif method == "resources/read":
        if not access_control.check_access(uri, auth_context):
            raise PermissionError("Access denied")
        return await server.read_resource(uri)
    # 3. 审计日志（成功/失败均记录）
    await audit_logger.log_access(...)
```

---

## 七、流程指引与自动提取

**Q20 ⭐⭐ 流程指引是怎么做到"数据驱动"的？有什么好处？**

A：流程定义完全存储在 MongoDB flow_guides 集合中，GuideAgent 运行时动态加载，无需为每个流程写代码。

好处：
1. HR 可以通过前端页面增删改流程，无需改代码重启服务
2. 新增流程只需在数据库插入一条记录
3. triggers 字段配置关键词，灵活控制匹配规则
4. 文档上传后 LLM 自动提取流程，大幅降低人工录入成本

---

**Q21 ⭐⭐ FlowExtractor 是怎么从文档中提取流程的？如何处理重复？**

A：
1. 截取文档前 8000 字符（避免超出 LLM 上下文）
2. 调用 LLM（flow_extract prompt），要求返回 JSON 数组格式的流程列表
3. 正则提取 JSON（`re.search(r"\[.*\]", text, re.DOTALL)`），容错 LLM 额外文字
4. 重复检测：`find_by_name()` 精确匹配流程名
   - 无重复 → 直接保存 flow_guides
   - 有重复 → 写入 pending_duplicates，等待 HR 在前端确认（overwrite/keep/save_as_new）

---

## 八、认证与安全

**Q22 ⭐⭐ 项目的认证系统是怎么设计的？前后端如何配合？**

A：
- 后端：`POST /api/auth/login` 验证用户名/密码（bcrypt hash），返回 JWT Token（含 sub/role）
- 受保护路由：`Depends(require_hr)` 依赖注入，解析 JWT 验证角色
- 前端：axios 请求拦截器自动附加 `Authorization: Bearer <token>`
- 前端：响应拦截器捕获 401，清除本地 token，跳转 `/login`
- auth_context 传递：JWT 解析后构建 dict，随 input_data 传入 Agent，最终到达 Tool 层做权限验证

---

**Q23 ⭐⭐ 假期余额查询为什么需要 auth_context？如果不传会怎样？**

A：假期余额是个人隐私数据，必须确保用户只能查自己的数据。

auth_context 包含 `user_id`，Tool 用它查询 `leave_balances` 集合中 `user_id` 匹配的记录，确保数据隔离。

不传 auth_context 或 role 为 guest 时，Tool 直接返回 `"请先登录后查询假期余额"`，不执行数据库查询。

---

## 九、前端技术

**Q24 ⭐ 前端为什么用 fetch 而不是 axios 来处理 SSE 流式响应？**

A：因为 `EventSource`（浏览器原生 SSE API）不支持 POST 请求和自定义 Header（无法附加 JWT Token），也不支持主动中止。

项目使用 `fetch` + `ReadableStream` + `TextDecoder`：
- 支持 POST 请求体（传 question 和 session_id）
- 支持 `Authorization` Header（JWT 认证）
- 支持 `AbortController` 主动中止（用户停止生成）

---

**Q25 ⭐⭐ 前端的 SSE 流式数据是怎么解析的？**

A：
```typescript
const reader = response.body.getReader()
const decoder = new TextDecoder()
let buffer = ''

while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''  // 保留不完整的行
    
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const parsed = JSON.parse(line.slice(6))
            if (parsed.type === 'text') appendContent(parsed.content)
            if (parsed.type === 'done') showSources(parsed.sources)
        }
    }
}
```

关键点：buffer 处理不完整的 SSE 行（网络分包问题）

---

**Q26 ⭐⭐ axios 的重试机制是怎么实现的？**

A：在响应拦截器中：
1. 记录重试次数 `config._retryCount`
2. 满足条件时（503/502/504/ECONNABORTED/ERR_NETWORK）且未超过 3 次
3. 指数退避等待（1s/2s/3s）后重新发起请求
4. 401 不重试，直接跳转登录

---

## 十、系统设计与工程实践

**Q27 ⭐⭐ 项目中有哪些值得一提的工程实践？**

A：
1. 请求追踪：每个请求生成 `X-Trace-ID`，贯穿整个调用链，便于排查问题
2. 降级策略：MongoDB 不可用时降级为纯短期记忆；Reranker 不可用时跳过重排；LLM 意图识别失败时降级关键词匹配
3. 配置驱动：Agent/Skill/Tool/Prompt 均通过 JSON 配置文件定义，运行时可热更新
4. 向量 ID 规范：`{doc_id}_chunk_{i}` 格式，删除时按前缀匹配，比 metadata 过滤更可靠
5. 单一"新对话"：前后端双重检查，避免重复创建空会话

---

**Q28 ⭐⭐⭐ 如果让你优化这个系统的性能，你会从哪些方面入手？**

A：
1. 向量检索缓存：相同 query 的向量化结果缓存（已有 EmbeddingCache LRU）
2. 查询优化缓存：KBQueryOptimizer 结果缓存（已实现）
3. 异步并行：hybrid 意图时 QA + Memory 并行执行（已实现 asyncio.gather）
4. 连接池：MongoDB Motor 连接池（已配置 2-10）
5. 流程指引缓存：GuideAgent 的 `get_all()` 结果可缓存（当前每次查 DB）
6. 长期：Redis 替代内存速率限制，支持多实例部署

---

**Q29 ⭐⭐⭐ 禁止主题功能最初有什么 Bug？是怎么修复的？**

A：
- Bug：用户问"我的工资是多少"，系统返回"知识库中没有相关信息"，而不是禁止主题拒绝消息
- 根因：原实现在构建 Prompt 时才检查禁止主题，但如果知识库无相关文档，系统在检索阶段就返回 fallback，根本不会执行到 LLM 生成阶段
- 修复：在 `process()` 方法最开始添加预检查，在任何检索之前就拦截禁止查询

```python
async def process(self, query, history=None):
    # 0. 预检查禁止主题（新增，在检索之前）
    forbidden_check = self._check_forbidden_topics(query, constraint_config)
    if forbidden_check:
        yield ResponseBuilder.text_chunk(forbidden_check)
        yield ResponseBuilder.done_chunk([], content=forbidden_check)
        return
    # 1. 后续正常流程...
```

---

**Q30 ⭐⭐ 作为前端转型 Agent 开发，你觉得前端经验对你有哪些帮助？**

A：
1. 异步编程思维：前端 Promise/async-await → Python asyncio，理解并发和事件循环
2. 组件化思维：前端组件单一职责 → Agent 模块化设计，每个 Agent 专注一个领域
3. 状态管理经验：Pinia store → Agent 状态机（idle/processing/completed/error）
4. 用户体验意识：主动设计了 SSE 流式输出、快捷提问、相关链接、余额不足警告等体验细节
5. API 设计经验：熟悉 RESTful 规范，设计了清晰的前后端接口契约
6. 调试能力：前端 DevTools 调试经验 → 后端日志追踪（X-Trace-ID）

---

## 附录：高频追问

---

**Q31 ⭐⭐⭐ 项目里有两个 QAAgent，有什么区别？**

A：这是一个容易混淆的设计点：

| | `agents/implementations/qa_agent.py` | `services/qa_agent.py` |
|--|--------------------------------------|------------------------|
| 层次 | Agent 层 | Service 层 |
| 注册 | 通过 AgentEngine 注册 | 不注册，直接实例化 |
| 调用方 | OrchestratorAgent（hybrid/qa 意图时） | `/api/chat/v2/ask/stream` 路由直接调用 |
| 实现 | 通过 SkillEngine 执行 `qa_rag` skill | 完整 ReAct 循环（禁止主题检查 + 查询优化 + Tool决策 + RAG） |
| 流式 | `run_stream()` 简单流式 | `process()` 完整 SSE 流式 |

实际用户聊天走的是 Service 层 QAAgent。Agent 层 QAAgent 是为了让 OrchestratorAgent 在 hybrid 意图时能通过 AgentEngine 统一调度。

---

**Q32 ⭐⭐ 提示词是怎么管理的？运行时能修改吗？**

A：三层机制：
1. 文件层：`prompts/config.json` 是初始数据源
2. 数据库层：启动时若 MongoDB 为空，自动从文件写入；之后以数据库为准
3. 内存缓存层：`config_loader` 内存缓存，每 5 分钟从数据库同步（APScheduler）

运行时修改：通过 `/api/prompt-config` 接口（需登录，修改需 admin 角色）更新数据库，下次同步（最多 5 分钟）后生效，无需重启服务。

`PromptManager` 是单例，加载优先级：数据库 > 文件。各 Agent 通过 `prompt_manager.get_system_prompt("intent_detection")` 等方法获取提示词。
A：ChromaDB 返回的是 distance（距离），越小越相似。项目中 `score_threshold=0.7` 是过滤阈值，distance > 0.7 的文档被丢弃（相关性不足）。

**Q：为什么选 ChromaDB 而不是 Milvus/Qdrant？**
A：ChromaDB 轻量，无需独立服务，支持持久化模式，适合中小规模项目快速落地。Milvus/Qdrant 适合大规模生产环境，是未来升级方向。

**Q：MongoDB 为什么不用事务？**
A：单机 MongoDB 不支持事务（需要副本集）。项目通过业务逻辑保证一致性（如会话删除时不检查 user_id，直接按 session_id 删除），避免事务依赖。

**Q：Skill 引擎和 Agent 有什么区别？**
A：Agent 是决策层，负责意图理解和路由；Skill 是执行层，是具体的流水线（pipeline），由多个 Processor 串联组成。Agent 调用 Skill，Skill 调用 Processor。

**Q：流式响应（SSE）和 WebSocket 有什么区别？为什么选 SSE？**
A：SSE 是单向推送（服务端 → 客户端），实现简单，浏览器原生支持，适合 AI 回答这种单向流场景。WebSocket 是双向通信，复杂度更高。项目选 SSE 因为只需要服务端推送，无需双向通信。
