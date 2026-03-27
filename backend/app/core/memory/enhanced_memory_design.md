# 增强记忆系统设计方案

## 需求分析

1. **短期/长期记忆分离**：明确的记忆层次
2. **记忆可控**：避免混乱，有清晰的管理机制
3. **时效性衰减**：时间越久权重越低
4. **记忆分类**：永久记忆、临时记忆、工作记忆
5. **权重系统**：临时记忆权重最高

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    增强记忆管理系统                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  工作记忆 (Working Memory)                            │  │
│  │  - 当前对话上下文 (最近 5-10 轮)                       │  │
│  │  - 最高优先级，权重 1.0                               │  │
│  │  - 实时更新，会话结束后清空                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  临时记忆 (Temporary Memory)                          │  │
│  │  - 用户显式标记的重要信息                              │  │
│  │  - 高权重 0.8-0.9，有过期时间                         │  │
│  │  - 可手动删除或自动过期                                │  │
│  │  - 存储：Redis (快速访问) + MongoDB (持久化)          │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  短期记忆 (Short-Term Memory)                         │  │
│  │  - 最近 N 天的对话历史                                 │  │
│  │  - 权重随时间衰减 (0.3-0.7)                           │  │
│  │  - 向量检索 + 时间过滤                                 │  │
│  │  - 存储：ChromaDB + MongoDB                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  长期记忆 (Long-Term Memory)                          │  │
│  │  - 历史对话的压缩摘要                                  │  │
│  │  - 低权重 0.1-0.3                                     │  │
│  │  - 定期压缩和归档                                      │  │
│  │  - 存储：MongoDB (摘要) + ChromaDB (向量)             │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  永久记忆 (Permanent Memory)                          │  │
│  │  - 用户显式保存的知识                                  │  │
│  │  - 固定权重 0.5，不衰减                               │  │
│  │  - 用户可编辑、删除                                    │  │
│  │  - 存储：MongoDB + ChromaDB                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 核心概念

### 1. 记忆类型 (MemoryType)

```python
class MemoryType(Enum):
    WORKING = "working"        # 工作记忆：当前对话
    TEMPORARY = "temporary"    # 临时记忆：用户标记的重要信息
    SHORT_TERM = "short_term"  # 短期记忆：最近的对话历史
    LONG_TERM = "long_term"    # 长期记忆：压缩的历史摘要
    PERMANENT = "permanent"    # 永久记忆：用户保存的知识
```

### 2. 记忆权重计算

```python
def calculate_weight(memory_type, created_at, access_count=0):
    base_weights = {
        MemoryType.WORKING: 1.0,      # 最高优先级
        MemoryType.TEMPORARY: 0.85,   # 临时记忆高权重
        MemoryType.SHORT_TERM: 0.6,   # 短期记忆中等权重
        MemoryType.LONG_TERM: 0.2,    # 长期记忆低权重
        MemoryType.PERMANENT: 0.5     # 永久记忆固定权重
    }
    
    base_weight = base_weights[memory_type]
    
    # 永久记忆和工作记忆不衰减
    if memory_type in [MemoryType.PERMANENT, MemoryType.WORKING]:
        return base_weight
    
    # 时间衰减（指数衰减）
    days_old = (datetime.now() - created_at).days
    time_decay = math.exp(-days_old / 30)  # 30天半衰期
    
    # 访问频率加成
    access_boost = min(0.1, access_count * 0.01)
    
    final_weight = base_weight * time_decay + access_boost
    return max(0.1, min(1.0, final_weight))
```

### 3. 记忆生命周期

```
创建 → 活跃使用 → 时间衰减 → 压缩/归档 → 删除/永久保存
  ↓        ↓          ↓           ↓              ↓
工作记忆  临时记忆   短期记忆    长期记忆      永久记忆/删除
```

### 4. 记忆检索策略

```python
def retrieve_memories(query, session_id, top_k=10):
    memories = []
    
    # 1. 工作记忆（当前会话）- 全部返回
    working = get_working_memory(session_id)
    memories.extend(working)
    
    # 2. 临时记忆 - 向量检索 + 未过期
    temporary = vector_search(query, MemoryType.TEMPORARY, top_k=3)
    temporary = [m for m in temporary if not is_expired(m)]
    memories.extend(temporary)
    
    # 3. 短期记忆 - 向量检索 + 时间过滤（最近30天）
    short_term = vector_search(query, MemoryType.SHORT_TERM, top_k=5)
    short_term = [m for m in short_term if days_old(m) <= 30]
    memories.extend(short_term)
    
    # 4. 永久记忆 - 向量检索
    permanent = vector_search(query, MemoryType.PERMANENT, top_k=2)
    memories.extend(permanent)
    
    # 5. 长期记忆 - 向量检索（低优先级）
    if len(memories) < top_k:
        long_term = vector_search(query, MemoryType.LONG_TERM, top_k=2)
        memories.extend(long_term)
    
    # 按权重排序
    memories.sort(key=lambda m: m.weight, reverse=True)
    return memories[:top_k]
```

## 数据模型

### Memory Document (MongoDB)

```python
{
    "_id": ObjectId,
    "user_id": str,
    "session_id": str,
    "memory_type": str,  # working/temporary/short_term/long_term/permanent
    "content": str,
    "metadata": {
        "title": str,  # 可选：记忆标题
        "tags": [str],  # 可选：分类标签
        "source": str,  # 来源：user_marked/auto_generated/imported
    },
    "created_at": datetime,
    "updated_at": datetime,
    "expires_at": datetime,  # 可选：过期时间（临时记忆）
    "access_count": int,  # 访问次数
    "last_accessed": datetime,
    "weight": float,  # 当前权重
    "is_active": bool,  # 是否激活
    "vector_id": str  # ChromaDB 中的向量 ID
}
```

## 实现要点

### 1. 记忆转换机制

- **工作记忆 → 短期记忆**：会话结束后自动转换
- **短期记忆 → 长期记忆**：30天后压缩为摘要
- **任意记忆 → 永久记忆**：用户手动标记

### 2. 记忆清理策略

- **工作记忆**：会话结束立即清空
- **临时记忆**：过期后自动删除
- **短期记忆**：90天后转为长期记忆或删除
- **长期记忆**：1年后删除低权重记忆
- **永久记忆**：用户手动删除

### 3. 防止记忆混乱

- **去重机制**：相似度 > 0.95 的记忆合并
- **冲突检测**：检测矛盾信息，提示用户
- **版本控制**：记忆更新时保留历史版本
- **来源追踪**：记录记忆的来源和创建方式

### 4. 用户控制接口

```python
# 标记为临时记忆
mark_as_temporary(message_id, expires_in_days=7)

# 保存为永久记忆
save_as_permanent(message_id, title="重要信息", tags=["项目", "需求"])

# 删除记忆
delete_memory(memory_id)

# 编辑记忆
update_memory(memory_id, content="更新后的内容")

# 查看记忆
list_memories(memory_type=MemoryType.TEMPORARY, limit=20)
```

## 优势

1. **清晰的层次结构**：每种记忆类型职责明确
2. **智能权重系统**：自动平衡新旧信息
3. **用户可控**：提供丰富的管理接口
4. **性能优化**：分层存储，按需加载
5. **可扩展性**：易于添加新的记忆类型

## 实施步骤

1. 实现核心数据模型和枚举
2. 实现权重计算和时间衰减逻辑
3. 实现各类记忆的存储和检索
4. 实现记忆转换和清理机制
5. 实现用户控制 API
6. 集成到现有的 Agent 系统
