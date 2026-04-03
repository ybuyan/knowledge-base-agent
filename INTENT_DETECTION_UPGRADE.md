# 意图识别优化 - 从关键词到 LLM

## 问题

原来的关键词匹配方式存在以下问题：
1. ❌ 太呆板 - 只能匹配预定义的关键词
2. ❌ 难维护 - 每次添加新场景都要更新关键词列表
3. ❌ 准确率低 - 测试显示只有 53.3% 的准确率
4. ❌ 无法理解语义 - "请假申请怎么写" 无法识别为 guide 意图

## 解决方案

使用 **LLM 进行意图识别**，实现智能化的意图判断。

### 优势

1. ✅ **智能理解** - 能理解各种表达方式
2. ✅ **高准确率** - 测试显示达到 100% 准确率
3. ✅ **易维护** - 只需更新 prompt，不需要维护关键词列表
4. ✅ **可扩展** - 添加新意图只需在 prompt 中描述

### 测试结果对比

```
测试用例: 15 个查询

LLM 方法:
- 准确率: 100.0% (15/15)
- guide 意图: 7/7 ✅
- qa 意图: 3/3 ✅
- memory 意图: 3/3 ✅
- hybrid 意图: 2/2 ✅

关键词方法:
- 准确率: 53.3% (8/15)
- guide 意图: 0/7 ❌ (全部失败)
- qa 意图: 3/3 ✅
- memory 意图: 3/3 ✅
- hybrid 意图: 2/2 ✅

提升: +46.7%
```

### 关键改进

**原来无法识别的查询现在都能正确识别**:
- "请假申请怎么写" → guide ✅
- "如何申请年假" → guide ✅
- "办理请假需要什么材料" → guide ✅
- "请假步骤" → guide ✅

## 实现方式

### 1. LLM 意图识别

使用专门的 prompt 让 LLM 判断意图类型：

```python
async def detect_intent_with_llm(query: str) -> str:
    """使用 LLM 进行意图识别"""
    # 使用精心设计的 prompt
    result = await call_llm(user_prompt, INTENT_DETECTION_PROMPT)
    return result.strip().lower()
```

### 2. 关键词作为回退方案

如果 LLM 调用失败，自动回退到关键词匹配：

```python
async def detect_intent_with_llm(query: str) -> str:
    try:
        # 尝试使用 LLM
        return await call_llm(...)
    except Exception as e:
        # 失败时回退到关键词
        return await detect_intent_with_keywords(query)
```

### 3. 配置化控制

通过配置文件控制使用哪种方法：

```json
{
  "orchestrator": {
    "intent_detection": {
      "method": "llm",  // 或 "keyword"
      "fallback_to_keyword": true
    }
  }
}
```

## 使用方法

### 默认使用 LLM（推荐）

```python
intent = await detect_intent(query)  # 默认使用 LLM
```

### 强制使用关键词

```python
intent = await detect_intent(query, use_llm=False)
```

### 修改配置

编辑 `backend/app/agents/config.json`:

```json
{
  "orchestrator": {
    "intent_detection": {
      "method": "keyword"  // 改为关键词方法
    }
  }
}
```

## 意图类型

### 1. guide - 流程指引
用户想了解如何办理某个流程、操作步骤

**示例**:
- "请假怎么办"
- "如何申请"
- "办理流程"
- "申请怎么写"
- "需要什么材料"

**特征**: 询问"怎么做"、"如何办理"、"流程"、"步骤"

### 2. qa - 知识查询
查询知识库中的信息

**示例**:
- "年假有多少天"
- "报销政策是什么"
- "公司地址在哪里"

**特征**: 询问具体信息、政策、规定

### 3. memory - 历史记忆
询问之前的对话内容

**示例**:
- "上次说的"
- "之前提到"
- "你刚才说"

**特征**: 时间词（上次、之前、刚才）

### 4. hybrid - 混合查询
需要对比历史信息和知识库

**示例**:
- "和之前的有什么区别"
- "对比一下"

**特征**: 对比词（对比、区别、不同）

## Prompt 设计

意图识别的 prompt 包含：

1. **角色定义** - "你是一个意图识别助手"
2. **意图说明** - 每种意图的定义和特征
3. **示例** - 典型的查询示例
4. **输出格式** - 只返回意图类型，不解释

```python
INTENT_DETECTION_PROMPT = """你是一个意图识别助手。请判断用户查询属于以下哪种意图：

1. **guide** - 流程指引
   - 用户想了解如何办理某个流程、操作步骤
   - 例如：请假怎么办、如何申请、办理流程、申请怎么写
   - 关键特征：询问"怎么做"、"如何办理"、"流程"、"步骤"

...

请只返回意图类型，不要解释。格式：intent_type
"""
```

## 性能考虑

### LLM 调用开销

- 每次意图识别需要调用一次 LLM
- 平均响应时间: ~200-500ms
- 可以通过缓存优化（相同查询直接返回缓存结果）

### 优化建议

1. **缓存常见查询** - 对高频查询缓存意图结果
2. **批量处理** - 如果有多个查询，可以批量识别
3. **快速路径** - 对明显的关键词（如"上次"）直接返回，跳过 LLM

## 测试

### 运行测试

```bash
# 测试意图识别准确率
python backend/test_intent_detection.py

# 测试完整流程
python backend/test_guide_with_logs.py
```

### 添加测试用例

在 `test_intent_detection.py` 中添加：

```python
test_cases = [
    ("你的查询", "预期意图"),
    # ...
]
```

## 日志

意图识别会产生以下日志：

```log
# LLM 识别
INFO:...orchestrator_agent:🤔 [INTENT] 使用 LLM 进行意图识别 | query='请假申请怎么写'
INFO:...orchestrator_agent:✅ [INTENT] LLM 识别意图 | query='请假申请怎么写' -> guide

# 关键词识别（回退）
INFO:...orchestrator_agent:❌ [INTENT] LLM 意图识别失败: ..., 回退到关键词匹配

# 最终结果
INFO:...orchestrator_agent:OrchestratorAgent 意图: '请假申请怎么写' -> guide (method=llm)
```

## 故障排查

### 问题 1: LLM 返回无效意图

**日志**:
```log
WARNING:...orchestrator_agent:⚠️  [INTENT] LLM 返回无效意图: xxx，使用默认 qa
```

**原因**: LLM 返回了不在 [guide, qa, memory, hybrid] 中的值

**解决**: 
- 检查 prompt 是否清晰
- 查看 LLM 的实际返回内容
- 优化 prompt 的输出格式说明

### 问题 2: LLM 调用失败

**日志**:
```log
ERROR:...orchestrator_agent:❌ [INTENT] LLM 意图识别失败: ..., 回退到关键词匹配
```

**原因**: LLM API 调用失败

**解决**:
- 检查 API 配置
- 检查网络连接
- 系统会自动回退到关键词匹配

### 问题 3: 意图识别不准确

**解决**:
1. 运行测试查看准确率
2. 检查 prompt 是否需要优化
3. 添加更多示例到 prompt
4. 考虑使用更强大的 LLM 模型

## 未来优化

1. **意图缓存** - 缓存常见查询的意图结果
2. **混合策略** - 简单查询用关键词，复杂查询用 LLM
3. **意图置信度** - LLM 返回置信度分数
4. **多轮对话** - 意图不明确时主动询问用户
5. **意图历史** - 基于对话历史优化意图识别

## 总结

通过使用 LLM 进行意图识别，我们实现了：

✅ 准确率从 53.3% 提升到 100%
✅ 支持各种自然语言表达
✅ 易于维护和扩展
✅ 自动回退机制保证可靠性

现在 "请假申请怎么写" 这样的查询能够正确识别为 guide 意图，并路由到 GuideAgent 进行处理！
