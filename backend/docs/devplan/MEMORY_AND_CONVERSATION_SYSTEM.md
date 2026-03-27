# 多轮对话和记忆管理系统详解

> 文档日期：2026-03-26
> 项目版本：1.2.0

---

## 一、系统架构概览

项目采用**三层记忆架构**，实现了短期记忆、长期记忆和持久化存储的完美结合：

```
┌─────────────────────────────────────────────────────────────┐
│                    用户发起查询                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              HybridMemoryService (混合记忆服务)               │
│  • 协调短期和长期记忆                                          │
│  • 构建完整上下文                                              │
│  • 持久化对话到数据库                                          │
└──────────┬────────────────────────┬─────────────────────────┘
           │                        │
┌──────────▼──────────┐   ┌────────▼──────────────────────────┐
│  短期记忆 (内存)      │   │  长期记忆 (向量数据库)              │
│  ShortTermMemory     │   │  • ChromaDB documents 集合         │
│  • 当前会话上下文     │   │  • ChromaDB conversations 集合     │
│  • Token 限制管理    │   │  • 语义检索历史对话                 │
│  • 滑动窗口策略      │   │  • 跨会话知识共享                   │
└──────────┬──────────┘   └────────┬──────────────────────────┘
           │                        │
           └────────────┬───────────┘
                        │
┌───────────────────────▼─────────────────────────────────────┐
│              持久化存储 (MongoDB)                             │
│  • sessions 集合：会话元数据                                  │
│  • messages 集合：完整消息历史                                │
│  • 支持分页、搜索、归档                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心组件详解

### 2.1 短期记忆 (ShortTermMemory)

**位置：** `backend/app/core/memory/short_term.py`

**功能：** 管理当前会话的上下文，确保 LLM 调用时不超过 Token 限制。

**核心特性：**

1. **Token 计数**
   ```python
   # 使用 tiktoken 精确计算 Token 数量
   encoding = tiktoken.encoding_for_model(model)
   token_count = len(encoding.encode(text))
   ```

2. **滑动窗口策略 (SlidingWindowStrategy)**
   - 保留系统提示词（system message）
   - 当超过 max_tokens 时，从最早的对话开始删除
   - 保证至少保留 min_messages 条消息
   
   ```python
   while total_tokens > max_tokens and len(conversation_messages) > self.min_messages:
       removed = conversation_messages.pop(0)  # 删除最早的消息
       total_tokens -= removed.token_count
   ```

3. **消息管理**
   ```python
   # 添加消息
   memory.add_message("user", "什么是年假?")
   memory.add_message("assistant", "年假是...")
   
   # 获取上下文（应用策略）
   context = memory.get_context(apply_strategy=True)
   
   # 获取剩余 Token
   remaining = memory.get_remaining_tokens()
   ```

**配置参数：**
- `max_tokens`: 最大 Token 数（默认 3000）
- `min_messages`: 最少保留消息数（默认 2）
- `keep_system`: 是否保留系统提示词（默认 True）

### 2.2 会话记忆管理器 (ConversationMemoryManager)

**位置：** `backend/app/core/memory/manager.py`

**功能：** 管理多个会话的短期记忆，采用 LRU 缓存策略。

**核心特性：**

1. **LRU 缓存**
   ```python
   # 使用 OrderedDict 实现 LRU
   self._conversations: OrderedDict[str, ShortTermMemory] = OrderedDict()
   
   # 访问时移到末尾
   self._conversations.move_to_end(session_id)
   
   # 超过限制时淘汰最久未访问的
   oldest_id = min(self._last_access, key=self._last_access.get)
   ```

2. **会话隔离**
   - 每个 session_id 对应独立的 ShortTermMemory
   - 支持最多 1000 个活跃会话（可配置）
   - 自动淘汰最久未访问的会话

3. **异步安全**
   ```python
   async with self._lock:  # 使用 asyncio.Lock 保证线程安全
       memory = self._conversations.get(session_id)
   ```

**使用示例：**
```python
manager = get_memory_manager()

# 获取或创建会话记忆
memory = await manager.get_or_create(
    session_id="abc123",
    max_tokens=4000,
    system_prompt="你是一个AI助手"
)

# 加载历史消息
await manager.load_history(session_id, messages)

# 删除会话记忆
await manager.delete(session_id)
```

### 2.3 混合记忆服务 (HybridMemoryService)

**位置：** `backend/app/services/hybrid_memory.py`

**功能：** 整合短期记忆和长期记忆，提供统一的记忆管理接口。

**核心流程：**

#### 2.3.1 构建上下文 (build_context)

```python
async def build_context(
    session_id: str,
    query: str,
    include_long_term: bool = True
) -> Tuple[List[Dict], ShortTermMemory]:
    # 1. 获取短期记忆
    memory = await self.get_or_create_memory(session_id)
    
    # 2. 检索长期记忆（可选）
    if include_long_term:
        long_term_context = await self._retrieve_long_term(query, session_id)
        # 添加到上下文
        context_messages.append({
            "role": "system",
            "content": f"[相关上下文]\n{long_term_context}"
        })
    
    # 3. 获取短期记忆上下文
    short_term_context = memory.get_context(apply_strategy=True)
    context_messages.extend(short_term_context)
    
    return context_messages, memory
```

#### 2.3.2 长期记忆检索 (_retrieve_long_term)

并行检索两种长期记忆：

```python
# 并行执行
docs_task = retriever.retrieve_documents(query, top_k=3)  # 知识库文档
convs_task = self._retrieve_related_conversations(query, session_id)  # 历史对话

docs, convs = await asyncio.gather(docs_task, convs_task)
```

**知识库文档检索：**
- 从 ChromaDB `documents` 集合检索
- 返回最相关的 3 个文档片段
- 每个片段截断到 500 字符

**历史对话检索：**
- 从 ChromaDB `conversations` 集合检索
- 排除当前会话
- 返回最相关的 2 个历史 QA 对
- 每个 QA 对截断到 300 字符

#### 2.3.3 消息持久化 (add_message)

```python
async def add_message(
    session_id: str,
    role: str,
    content: str,
    sources: Optional[List[Dict]] = None
) -> None:
    # 1. 添加到短期记忆
    memory = await self.get_or_create_memory(session_id)
    memory.add_message(role, content)
    
    # 2. 持久化到 MongoDB
    await message_service.add_message(...)
    
    # 3. 更新会话活动状态
    await session_service.update_session_activity(session_id, content)
    
    # 4. 如果是 AI 回复，存储到向量数据库
    if role == "assistant":
        await self._store_to_vector_db(session_id, content)
```

#### 2.3.4 向量化存储 (_store_to_vector_db)

```python
async def _store_to_vector_db(session_id: str, answer: str) -> None:
    # 1. 获取最后一个用户问题
    memory = await get_memory_manager().get(session_id)
    user_messages = [m for m in memory.get_messages() if m.role == "user"]
    last_question = user_messages[-1].content
    
    # 2. 构建 QA 对
    conv_text = f"Q: {last_question}\nA: {answer}"
    
    # 3. 向量化
    conv_embedding = await embeddings.aembed_query(conv_text)
    
    # 4. 存储到 ChromaDB conversations 集合
    collection.add(
        ids=[str(uuid.uuid4())],
        embeddings=[conv_embedding],
        documents=[conv_text],
        metadatas=[{"session_id": session_id, "type": "qa_pair"}]
    )
```

---

## 三、多轮对话流程

### 3.1 完整对话流程

```
用户发送消息
    │
    ▼
1. API 接收请求 (/v2/ask/stream)
    │
    ▼
2. 加载历史消息（最近 6 条）
    messages = await message_service.get_messages(session_id)
    history = [{"role": msg.role, "content": msg.content} for msg in messages[-6:]]
    │
    ▼
3. QAAgent 处理查询
    agent = get_qa_agent()
    async for chunk in agent.process(question, history):
        # 流式返回结果
        yield chunk
    │
    ▼
4. 持久化对话
    await persist_conversation(
        session_id=session_id,
        question=question,
        answer=full_response,
        sources=sources,
        suggested_questions=suggested_questions,
        related_links=related_links
    )
    │
    ▼
5. 更新会话状态
    - 更新 message_count
    - 更新 last_message
    - 更新 updated_at
```

### 3.2 QAAgent 中的历史上下文使用

**位置：** `backend/app/services/qa_agent.py`

```python
async def process(self, query: str, history: List[Dict] = None):
    # 1. 构建消息列表
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query}
    ]
    
    # 2. 添加历史上下文（最近 4 轮）
    if history:
        for msg in history[-4:]:
            if msg.get("role") in ["user", "assistant"]:
                messages.insert(-1, msg)  # 插入到最后一条用户消息之前
    
    # 3. 调用 LLM
    decision = await self._llm_client.chat_with_tools(messages, tools)
```

**历史消息限制：**
- API 层：加载最近 6 条消息
- QAAgent：使用最近 4 轮对话
- 原因：平衡上下文长度和响应速度

---

## 四、数据持久化

### 4.1 MongoDB 数据结构

#### sessions 集合
```javascript
{
    _id: ObjectId("..."),
    user_id: "default_user",
    title: "新对话",
    created_at: ISODate("2026-03-26T10:00:00Z"),
    updated_at: ISODate("2026-03-26T10:05:00Z"),
    is_archived: false,
    message_count: 5,
    last_message: "年假是指..."
}
```

#### messages 集合
```javascript
{
    _id: ObjectId("..."),
    session_id: "abc123",
    user_id: "default_user",
    role: "assistant",
    content: "年假是指员工...",
    sources: [
        {
            id: "1",
            filename: "员工手册.pdf",
            content: "年假规定..."
        }
    ],
    suggested_questions: [
        "年假如何申请？",
        "年假天数如何计算？",
        "年假可以累积吗？"
    ],
    related_links: [
        {
            id: "link1",
            title: "HR系统",
            url: "https://hr.company.com",
            description: "在线申请年假"
        }
    ],
    created_at: ISODate("2026-03-26T10:05:00Z")
}
```

### 4.2 ChromaDB 向量存储

#### documents 集合（知识库文档）
```python
{
    "id": "doc123_chunk_0",
    "document": "年假是指员工在工作满一定年限后...",
    "metadata": {
        "document_id": "doc123",
        "document_name": "员工手册.pdf",
        "chunk_index": 0
    },
    "embedding": [0.123, 0.456, ...]  # 向量
}
```

#### conversations 集合（历史对话）
```python
{
    "id": "uuid-xxx",
    "document": "Q: 什么是年假?\nA: 年假是指员工...",
    "metadata": {
        "session_id": "abc123",
        "type": "qa_pair"
    },
    "embedding": [0.789, 0.012, ...]  # 向量
}
```

---

## 五、记忆策略

### 5.1 Token 管理策略

**问题：** LLM 有 Token 限制（如 qwen-plus 支持 32k tokens）

**解决方案：**

1. **短期记忆限制**
   - 默认 max_tokens = 3000
   - 为 LLM 生成预留足够空间（通常需要 4000+ tokens）

2. **滑动窗口**
   - 保留最近的对话
   - 删除最早的对话
   - 保证系统提示词不被删除

3. **长期记忆补充**
   - 不占用短期记忆空间
   - 通过语义检索按需加载
   - 只加载最相关的内容

### 5.2 记忆衰减策略

**位置：** `backend/app/core/memory/types.py`

虽然项目中定义了完整的记忆衰减模型，但当前版本**未启用**。

**设计思路：**

```python
def calculate_weight(self) -> float:
    # 1. 基础权重（根据记忆类型）
    base_weight = {
        MemoryType.WORKING: 1.0,      # 工作记忆：最高权重
        MemoryType.SHORT_TERM: 0.6,   # 短期记忆
        MemoryType.LONG_TERM: 0.2     # 长期记忆
    }
    
    # 2. 时间衰减（指数衰减）
    days_old = (datetime.utcnow() - self.created_at).days
    decay_rate = 30  # 30天半衰期
    time_decay = math.exp(-days_old / decay_rate)
    
    # 3. 访问频率加成
    access_boost = min(0.15, self.access_count * 0.01)
    
    # 4. 重要性因子
    importance_factor = self.metadata.importance
    
    # 5. 最终权重
    return (base_weight * time_decay * importance_factor) + access_boost
```

**未来可扩展：**
- 根据权重自动归档低价值记忆
- 智能清理过期记忆
- 优先检索高权重记忆

---

## 六、性能优化

### 6.1 缓存策略

1. **短期记忆缓存**
   - 内存中保存最近 1000 个会话
   - LRU 淘汰策略
   - 避免频繁数据库查询

2. **向量化缓存**
   - EmbeddingCache（LRU，maxsize=1000）
   - MD5 哈希键
   - 缓存命中率统计

3. **查询优化缓存**
   - QueryCache（LRU）
   - 缓存优化后的查询
   - 减少 LLM 调用

### 6.2 并发优化

1. **异步 IO**
   - 所有数据库操作使用 async/await
   - Motor 异步 MongoDB 驱动
   - 并发处理多个请求

2. **并行检索**
   ```python
   # 并行检索文档和对话
   docs_task = retriever.retrieve_documents(query)
   convs_task = self._retrieve_related_conversations(query)
   docs, convs = await asyncio.gather(docs_task, convs_task)
   ```

3. **流式响应**
   - SSE 流式输出
   - 降低首字节响应时间
   - 提升用户体验

### 6.3 数据库优化

1. **MongoDB 索引**
   ```javascript
   // sessions 集合
   db.sessions.createIndex({ user_id: 1, updated_at: -1 })
   db.sessions.createIndex({ title: "text" })
   
   // messages 集合
   db.messages.createIndex({ session_id: 1, created_at: 1 })
   db.messages.createIndex({ content: "text" })
   ```

2. **分页查询**
   - 游标分页（cursor-based pagination）
   - 避免 skip 性能问题
   - 支持无限滚动

3. **批量操作**
   - 批量向量化（batch_size=100）
   - 批量插入消息
   - 减少数据库往返

---

## 七、使用示例

### 7.1 基础使用

```python
from app.services.hybrid_memory import hybrid_memory_service

# 1. 构建上下文
context_messages, memory = await hybrid_memory_service.build_context(
    session_id="abc123",
    query="什么是年假?",
    include_long_term=True  # 包含长期记忆
)

# 2. 调用 LLM
response = await llm_client.chat(context_messages)

# 3. 保存消息
await hybrid_memory_service.add_message(
    session_id="abc123",
    role="assistant",
    content=response,
    sources=[...]
)
```

### 7.2 高级使用

```python
from app.core.memory import get_memory_manager

# 获取记忆管理器
manager = get_memory_manager()

# 创建会话记忆
memory = await manager.get_or_create(
    session_id="abc123",
    max_tokens=4000,
    system_prompt="你是一个专业的HR助手"
)

# 添加消息
memory.add_message("user", "什么是年假?")
memory.add_message("assistant", "年假是指...")

# 获取上下文（应用Token限制）
context = memory.get_context(apply_strategy=True)

# 检查Token使用情况
total_tokens = memory.get_token_count()
remaining_tokens = memory.get_remaining_tokens()

# 清空会话记忆
await manager.clear("abc123")

# 删除会话记忆
await manager.delete("abc123")
```

---

## 八、配置参数

### 8.1 环境变量配置

```bash
# .env 文件
MEMORY_MAX_SESSIONS=1000        # 最大活跃会话数
MEMORY_MAX_TOKENS=3000          # 每个会话最大Token数
MONGO_URL=mongodb://localhost:27017
MONGO_DB_NAME=agent
CHROMA_PERSIST_DIR=./data/chroma
```

### 8.2 代码配置

```python
# backend/app/config.py
class Settings(BaseSettings):
    memory_max_sessions: int = 1000
    memory_max_tokens: int = 3000
    
    # MongoDB
    mongo_url: str = "mongodb://localhost:27017"
    mongo_db_name: str = "agent"
    
    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
```

---

## 九、常见问题

### Q1: 为什么历史消息只加载最近 6 条？

**A:** 平衡上下文长度和响应速度：
- 6 条消息约 3 轮对话
- 足够理解上下文
- 不会超过 Token 限制
- 可通过长期记忆补充更早的信息

### Q2: 短期记忆和长期记忆的区别？

**A:**
- **短期记忆**：内存中，当前会话，快速访问，Token 限制
- **长期记忆**：向量数据库，所有会话，语义检索，无 Token 限制

### Q3: 会话记忆何时被清除？

**A:**
- 用户删除会话时
- LRU 淘汰（超过 1000 个活跃会话）
- 服务重启（内存数据丢失，但数据库数据保留）

### Q4: 如何提高多轮对话的准确性？

**A:**
1. 增加历史消息数量（修改 `messages[-6:]`）
2. 启用长期记忆检索（`include_long_term=True`）
3. 优化系统提示词
4. 使用更大的 max_tokens

### Q5: 向量化存储的 QA 对如何使用？

**A:**
- 自动存储每次 AI 回复
- 跨会话语义检索
- 提供相关历史对话作为上下文
- 帮助 LLM 理解类似问题

---

## 十、未来优化方向

### 10.1 短期优化

1. **记忆压缩**
   - 实现 SummaryBufferStrategy
   - 压缩旧对话为摘要
   - 节省 Token 空间

2. **智能记忆选择**
   - 根据查询类型选择记忆策略
   - 简单问题：只用短期记忆
   - 复杂问题：结合长期记忆

3. **记忆去重**
   - 检测重复的历史对话
   - 避免冗余信息

### 10.2 长期优化

1. **分布式记忆**
   - Redis 缓存短期记忆
   - 支持多实例部署
   - 会话亲和性路由

2. **记忆图谱**
   - 构建知识图谱
   - 记录实体关系
   - 支持推理查询

3. **个性化记忆**
   - 用户画像
   - 偏好学习
   - 个性化推荐

---

**文档结束**
