# 增强记忆系统集成指南

## 概述

增强记忆系统提供了完整的多层次记忆管理能力，包括工作记忆、临时记忆、短期记忆、长期记忆和永久记忆。

## 快速开始

### 1. 导入模块

```python
from app.core.memory import (
    get_enhanced_memory_manager,
    MemoryType,
    MemoryMetadata,
    MemorySource,
    MemoryQuery
)
```

### 2. 基础使用

```python
manager = get_enhanced_memory_manager()

# 创建记忆
memory = await manager.create_memory(
    user_id="user_123",
    session_id="session_456",
    content="重要信息",
    memory_type=MemoryType.TEMPORARY,
    expires_in_days=7
)

# 检索记忆
query = MemoryQuery(
    query_text="查询内容",
    user_id="user_123",
    top_k=10
)
memories = await manager.retrieve_memories(query)
```

## 集成到现有系统

### 1. 集成到 QA Agent

修改 `backend/app/services/qa_agent.py`:

```python
from app.core.memory import get_enhanced_memory_manager, MemoryType, MemoryQuery

class QAAgentService:
    def __init__(self):
        self.memory_manager = get_enhanced_memory_manager()
    
    async def process_query(self, question: str, session_id: str, user_id: str):
        # 1. 创建工作记忆（用户问题）
        await self.memory_manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content=f"Q: {question}",
            memory_type=MemoryType.WORKING
        )
        
        # 2. 检索相关记忆
        query = MemoryQuery(
            query_text=question,
            user_id=user_id,
            session_id=session_id,
            top_k=5
        )
        relevant_memories = await self.memory_manager.retrieve_memories(query)
        
        # 3. 构建上下文（包含记忆）
        context = self._build_context_with_memories(relevant_memories)
        
        # 4. 生成回答
        answer = await self._generate_answer(question, context)
        
        # 5. 保存回答为工作记忆
        await self.memory_manager.create_memory(
            user_id=user_id,
            session_id=session_id,
            content=f"A: {answer}",
            memory_type=MemoryType.WORKING
        )
        
        return answer
    
    def _build_context_with_memories(self, memories):
        context_parts = []
        
        # 按权重分组
        high_priority = [m for m in memories if m.weight > 0.7]
        medium_priority = [m for m in memories if 0.4 <= m.weight <= 0.7]
        
        if high_priority:
            context_parts.append("=== 重要记忆 ===")
            for mem in high_priority:
                context_parts.append(f"[{mem.memory_type.value}] {mem.content}")
        
        if medium_priority:
            context_parts.append("\n=== 相关记忆 ===")
            for mem in medium_priority:
                context_parts.append(f"[{mem.memory_type.value}] {mem.content}")
        
        return "\n".join(context_parts)
```

### 2. 集成到 Chat API

修改 `backend/app/api/routes/chat.py`:

```python
from app.core.memory import get_enhanced_memory_manager, MemoryType

@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    manager = get_enhanced_memory_manager()
    
    async def generate():
        # 处理对话...
        answer = await process_question(request.question)
        
        # 会话结束后，转换工作记忆为短期记忆
        if request.is_session_end:
            await manager.convert_working_to_short_term(
                request.session_id,
                request.user_id
            )
        
        yield answer
    
    return StreamingResponse(generate())

@router.post("/chat/mark-important/{message_id}")
async def mark_message_important(message_id: str):
    """用户标记重要消息"""
    manager = get_enhanced_memory_manager()
    
    # 将消息标记为临时记忆
    await manager.mark_as_temporary(
        memory_id=message_id,
        user_id=request.user_id,
        expires_in_days=30,
        importance=0.9
    )
    
    return {"success": True}

@router.post("/chat/save-permanent/{message_id}")
async def save_message_permanent(message_id: str, title: str, tags: List[str]):
    """用户保存为永久记忆"""
    manager = get_enhanced_memory_manager()
    
    await manager.save_as_permanent(
        memory_id=message_id,
        user_id=request.user_id,
        title=title,
        tags=tags
    )
    
    return {"success": True}
```

### 3. 添加定时任务

创建 `backend/app/tasks/memory_maintenance.py`:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.core.memory import get_enhanced_memory_manager

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2)  # 每天凌晨2点
async def daily_memory_maintenance():
    """每日记忆维护任务"""
    manager = get_enhanced_memory_manager()
    
    # 获取所有用户（实际应该从数据库获取）
    users = await get_all_users()
    
    for user_id in users:
        # 1. 清理过期记忆
        await manager.cleanup_expired_memories(user_id)
        
        # 2. 归档旧记忆
        await manager.archive_old_memories(user_id)
        
        print(f"完成用户 {user_id} 的记忆维护")

def start_scheduler():
    scheduler.start()
```

在 `backend/app/main.py` 中启动:

```python
from app.tasks.memory_maintenance import start_scheduler

@app.on_event("startup")
async def startup_event():
    start_scheduler()
```

## API 使用示例

### 前端集成

```typescript
// 创建记忆
async function createMemory(content: string, type: string) {
  const response = await fetch('/api/memory/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: currentSessionId,
      content: content,
      memory_type: type,
      tags: ['重要'],
      importance: 0.8
    })
  });
  return response.json();
}

// 搜索记忆
async function searchMemories(query: string) {
  const response = await fetch('/api/memory/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: query,
      session_id: currentSessionId,
      top_k: 10
    })
  });
  return response.json();
}

// 标记为重要
async function markImportant(memoryId: string) {
  const response = await fetch(`/api/memory/mark-temporary/${memoryId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      expires_in_days: 30,
      importance: 0.9
    })
  });
  return response.json();
}

// 保存为永久记忆
async function savePermanent(memoryId: string, title: string) {
  const response = await fetch(`/api/memory/save-permanent/${memoryId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: title,
      tags: ['知识库', '重要']
    })
  });
  return response.json();
}
```

## 最佳实践

### 1. 记忆类型选择

- **工作记忆**: 当前对话的临时上下文，会话结束后自动转换
- **临时记忆**: 用户标记的短期重要信息（如待办事项）
- **短期记忆**: 最近的对话历史，自动管理
- **长期记忆**: 历史对话的摘要，节省存储空间
- **永久记忆**: 用户明确保存的知识，不会删除

### 2. 权重优化

```python
# 高重要性记忆
metadata = MemoryMetadata(
    importance=0.9,  # 高重要性
    tags=['关键信息']
)

# 普通记忆
metadata = MemoryMetadata(
    importance=0.5,  # 默认重要性
    tags=['一般']
)
```

### 3. 标签管理

建议使用统一的标签体系：

```python
MEMORY_TAGS = {
    'category': ['工作', '生活', '学习', '项目'],
    'priority': ['紧急', '重要', '一般'],
    'status': ['待办', '进行中', '已完成'],
    'type': ['事实', '意见', '计划', '问题']
}
```

### 4. 检索优化

```python
# 精确检索（高权重记忆）
query = MemoryQuery(
    query_text="项目截止日期",
    min_weight=0.7,  # 只返回高权重记忆
    memory_types=[MemoryType.TEMPORARY, MemoryType.PERMANENT],
    top_k=5
)

# 广泛检索（包含历史）
query = MemoryQuery(
    query_text="项目相关",
    min_weight=0.3,  # 包含低权重记忆
    max_age_days=90,  # 最近90天
    top_k=20
)
```

### 5. 防止记忆混乱

```python
# 1. 使用明确的标题
metadata = MemoryMetadata(
    title="2024年Q1销售目标",  # 清晰的标题
    tags=['销售', '目标', '2024Q1']
)

# 2. 定期清理
await manager.cleanup_expired_memories(user_id)
await manager.archive_old_memories(user_id)

# 3. 检查重复（系统自动）
# 相似度 > 0.95 的记忆会被自动合并
```

## 性能优化

### 1. 批量操作

```python
# 批量创建记忆
memories = []
for content in contents:
    memory = await manager.create_memory(...)
    memories.append(memory)
```

### 2. 缓存策略

```python
# 工作记忆在内存中，访问快速
# 其他记忆从数据库加载，建议缓存热点数据
```

### 3. 异步处理

```python
# 记忆维护任务异步执行
import asyncio

async def background_maintenance():
    while True:
        await manager.cleanup_expired_memories(user_id)
        await asyncio.sleep(3600)  # 每小时执行一次

asyncio.create_task(background_maintenance())
```

## 监控和调试

### 1. 记忆统计

```python
# 获取统计信息
stats = await manager.get_memory_stats(user_id)
print(f"总记忆数: {stats['total_count']}")
print(f"各类型分布: {stats['by_type']}")
```

### 2. 日志记录

系统会自动记录关键操作：
- 记忆创建/更新/删除
- 权重计算
- 记忆转换
- 清理和归档

### 3. 问题排查

```python
# 查看特定记忆的详细信息
memory = await manager.get_memory(memory_id, user_id)
print(f"类型: {memory.memory_type}")
print(f"权重: {memory.weight}")
print(f"访问次数: {memory.access_count}")
print(f"创建时间: {memory.created_at}")
print(f"是否过期: {memory.is_expired()}")
```

## 常见问题

### Q1: 记忆权重如何计算？

A: 权重 = 基础权重 × 时间衰减 × 重要性 + 访问频率加成

### Q2: 什么时候应该使用永久记忆？

A: 用户明确表示要保存的知识、不会变化的事实信息、重要的参考资料。

### Q3: 如何避免记忆过多导致性能问题？

A: 系统会自动归档和清理，建议定期运行维护任务。

### Q4: 记忆检索的优先级是什么？

A: 工作记忆 > 临时记忆 > 永久记忆 > 短期记忆 > 长期记忆

### Q5: 如何处理记忆冲突？

A: 系统会检测相似记忆并提示，用户可以选择更新或保留多个版本。

## 下一步

1. 阅读 `usage_example.py` 了解更多使用场景
2. 查看 API 文档了解完整接口
3. 根据业务需求调整权重计算策略
4. 实现自定义的记忆分类和标签体系
