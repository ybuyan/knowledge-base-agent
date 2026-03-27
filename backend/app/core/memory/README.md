# 增强记忆系统

## 概述

这是一个完整的多层次记忆管理系统，解决了原有记忆系统的不足，提供了可控、分类、带时效性的记忆管理能力。

## 核心特性

### ✅ 已实现的功能

1. **多层次记忆架构**
   - 工作记忆（Working Memory）：当前对话上下文
   - 临时记忆（Temporary Memory）：用户标记的重要信息
   - 短期记忆（Short-Term Memory）：最近的对话历史
   - 长期记忆（Long-Term Memory）：压缩的历史摘要
   - 永久记忆（Permanent Memory）：用户保存的知识

2. **智能权重系统**
   - 基础权重（根据记忆类型）
   - 时间衰减（指数衰减，不同类型衰减速度不同）
   - 访问频率加成
   - 重要性评分

3. **记忆可控性**
   - 用户可标记/取消标记
   - 用户可编辑/删除
   - 用户可设置过期时间
   - 防止重复记忆

4. **时效性管理**
   - 自动时间衰减
   - 临时记忆自动过期
   - 旧记忆自动归档
   - 低权重记忆自动清理

5. **记忆分类**
   - 按类型分类（5种类型）
   - 按标签分类（用户自定义）
   - 按来源分类（用户标记/自动生成/导入）
   - 按重要性分类

6. **高级检索**
   - 向量语义检索
   - 多条件过滤
   - 权重排序
   - 跨会话检索

## 文件结构

```
backend/app/core/memory/
├── __init__.py                      # 模块导出
├── types.py                         # 类型定义（Memory, MemoryType等）
├── enhanced_manager.py              # 增强记忆管理器
├── short_term.py                    # 原有短期记忆（保留兼容）
├── manager.py                       # 原有会话管理器（保留兼容）
├── enhanced_memory_design.md        # 设计文档
├── INTEGRATION_GUIDE.md             # 集成指南
├── usage_example.py                 # 使用示例
└── README.md                        # 本文件

backend/app/api/routes/
└── memory.py                        # 记忆管理 API
```

## 快速开始

### 1. 基础使用

```python
from app.core.memory import get_enhanced_memory_manager, MemoryType

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
from app.core.memory import MemoryQuery

query = MemoryQuery(
    query_text="查询内容",
    user_id="user_123",
    top_k=10
)
memories = await manager.retrieve_memories(query)
```

### 2. API 使用

```bash
# 创建记忆
POST /api/memory/create
{
  "session_id": "session_123",
  "content": "重要信息",
  "memory_type": "temporary",
  "expires_in_days": 7
}

# 搜索记忆
POST /api/memory/search
{
  "query": "查询内容",
  "top_k": 10
}

# 标记为临时记忆
POST /api/memory/mark-temporary/{memory_id}
{
  "expires_in_days": 30,
  "importance": 0.9
}

# 保存为永久记忆
POST /api/memory/save-permanent/{memory_id}
{
  "title": "重要知识",
  "tags": ["知识库"]
}
```

## 记忆类型对比

| 类型 | 基础权重 | 时间衰减 | 过期 | 用途 |
|------|---------|---------|------|------|
| 工作记忆 | 1.0 | 否 | 会话结束 | 当前对话 |
| 临时记忆 | 0.85 | 7天半衰期 | 可设置 | 短期重要信息 |
| 短期记忆 | 0.6 | 30天半衰期 | 90天后归档 | 最近对话 |
| 长期记忆 | 0.2 | 90天半衰期 | 1年后删除 | 历史摘要 |
| 永久记忆 | 0.5 | 否 | 否 | 用户保存的知识 |

## 权重计算示例

```python
# 工作记忆（最高优先级）
weight = 1.0 × importance = 1.0 × 0.5 = 0.5

# 临时记忆（3天后）
weight = 0.85 × exp(-3/7) × 0.5 + 0.01 × access_count
      = 0.85 × 0.65 × 0.5 + 0.01 × 5
      = 0.276 + 0.05 = 0.326

# 短期记忆（15天后）
weight = 0.6 × exp(-15/30) × 0.5 + 0.01 × access_count
      = 0.6 × 0.61 × 0.5 + 0.01 × 3
      = 0.183 + 0.03 = 0.213

# 永久记忆（不衰减）
weight = 0.5 × importance = 0.5 × 0.8 = 0.4
```

## 记忆生命周期

```
创建 → 活跃使用 → 时间衰减 → 压缩/归档 → 删除/永久保存
  ↓        ↓          ↓           ↓              ↓
工作记忆  临时记忆   短期记忆    长期记忆      永久记忆/删除
```

### 自动转换规则

1. **工作记忆 → 短期记忆**：会话结束时自动转换
2. **短期记忆 → 长期记忆**：30天后且访问次数<5次
3. **任意记忆 → 永久记忆**：用户手动标记
4. **临时记忆 → 删除**：过期后自动删除
5. **长期记忆 → 删除**：1年后且权重<0.1

## 与原有系统的对比

| 特性 | 原有系统 | 增强系统 |
|------|---------|---------|
| 记忆层次 | 2层（短期/长期） | 5层（工作/临时/短期/长期/永久） |
| 权重计算 | 无 | 智能权重系统 |
| 时间衰减 | 无 | 指数衰减 |
| 用户控制 | 有限 | 完全可控 |
| 记忆分类 | 无 | 标签+类型 |
| 过期管理 | 无 | 自动过期 |
| 防重复 | 无 | 自动去重 |
| 检索策略 | 简单 | 多条件智能检索 |

## 性能特点

- **工作记忆**：内存存储，毫秒级访问
- **其他记忆**：MongoDB + ChromaDB，秒级检索
- **向量检索**：支持语义搜索，准确率高
- **批量操作**：支持异步批量处理
- **自动维护**：定时任务自动清理和归档

## 使用场景

### 1. 智能客服

```python
# 记住用户偏好
await manager.save_as_permanent(
    memory_id=preference_id,
    title="用户偏好：喜欢简洁回答",
    tags=["用户偏好"]
)

# 记住临时上下文
await manager.mark_as_temporary(
    memory_id=context_id,
    expires_in_days=1  # 1天后过期
)
```

### 2. 项目管理助手

```python
# 记住项目截止日期
await manager.create_memory(
    content="项目A截止日期：2024-12-31",
    memory_type=MemoryType.TEMPORARY,
    metadata=MemoryMetadata(
        tags=["项目", "截止日期"],
        importance=0.9
    ),
    expires_in_days=90
)
```

### 3. 知识库助手

```python
# 保存重要知识
await manager.create_memory(
    content="公司政策：年假10天",
    memory_type=MemoryType.PERMANENT,
    metadata=MemoryMetadata(
        title="年假政策",
        tags=["公司政策", "人事"],
        importance=1.0
    )
)
```

## 最佳实践

1. **合理使用记忆类型**：根据信息的重要性和时效性选择合适的类型
2. **设置合理的过期时间**：临时记忆建议7-30天
3. **使用标签分类**：建立统一的标签体系
4. **定期维护**：运行清理和归档任务
5. **监控权重分布**：确保重要信息权重足够高

## 扩展性

系统设计支持以下扩展：

1. **自定义记忆类型**：可添加新的记忆类型
2. **自定义权重算法**：可修改权重计算逻辑
3. **自定义衰减策略**：可调整时间衰减参数
4. **自定义检索策略**：可实现复杂的检索逻辑
5. **集成外部存储**：可接入其他数据库或向量库

## 文档

- [设计文档](./enhanced_memory_design.md) - 详细的架构设计
- [集成指南](./INTEGRATION_GUIDE.md) - 如何集成到现有系统
- [使用示例](./usage_example.py) - 完整的代码示例

## 兼容性

增强记忆系统与原有系统完全兼容：

- 原有的 `ShortTermMemory` 和 `ConversationMemoryManager` 保持不变
- 可以逐步迁移到新系统
- 两套系统可以并存使用

## 下一步计划

- [ ] 实现记忆冲突检测
- [ ] 添加记忆版本控制
- [ ] 实现记忆关联图谱
- [ ] 支持记忆导入/导出
- [ ] 添加记忆分析和可视化
- [ ] 实现多用户记忆共享

## 贡献

欢迎提出改进建议和问题反馈！

## 许可

MIT License
