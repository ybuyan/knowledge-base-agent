# 约束配置使用情况报告

## 执行摘要

通过全面检查，发现约束配置**部分应用**到项目中，但存在关键问题导致禁止主题和关键词约束**未生效**。

### 检查结果

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 配置加载 | ✅ 通过 | 配置文件正确加载 |
| Prompt 构建 | ❌ 失败 | 未使用包含约束的 Prompt 构建方法 |
| QA Agent 使用 | ❌ 失败 | 关键位置未应用约束 |
| 答案验证器使用 | ✅ 通过 | 检索验证已应用 |
| Chat API 使用 | ✅ 通过 | 已导入配置 |

**总体评分**: 3/5 通过

## 详细发现

### ✅ 已正确应用的部分

#### 1. 配置加载
- 配置文件 `config/constraints.json` 正确加载
- 当前配置值：
  - 禁止主题: `['薪资', '工资']`
  - 禁止关键词: `['工资']`
  - 严格模式: `True`
  - 最小相似度: `0.3`

#### 2. 检索验证
在 `qa_agent.py` 的 `_retrieve` 方法中：
```python
# 使用验证器过滤检索结果
if retrieval_config.get("enabled", True):
    filtered_docs, _ = validator.validate_retrieval(docs, metadatas, distances)
```

这部分**正常工作**，会根据约束配置过滤低相似度文档。

#### 3. 建议问题生成
```python
suggest_config = get_constraint_config().suggest_questions
if suggest_config.get("enabled", True):
    # 生成建议问题
```

这部分**正常工作**。

### ❌ 未正确应用的部分

#### 1. 禁止主题和关键词（关键问题）⚠️

**问题位置**: `qa_agent.py` 的 `_execute_rag_flow` 方法

**当前代码**:
```python
# 2. 构建提示
messages = StrictQAPrompt.build_messages(rag_context.context_text, query, history)
```

**问题分析**:
- `StrictQAPrompt.build_messages` 方法**不会**自动读取约束配置
- 生成的 Prompt **不包含**禁止主题和关键词的说明
- 导致 LLM **不知道**哪些主题是禁止的

**验证结果**:
```
方法 1 (当前使用): StrictQAPrompt.build_messages
  系统提示词长度: 530 字符
  ❌ 不包含禁止主题说明

方法 2 (应该使用): ConstraintPromptBuilder.build_system_prompt
  系统提示词长度: 594 字符
  ✅ 包含禁止主题说明
  差异: 64 字符（禁止主题说明）
```

**影响**:
- 用户查询"公司的工资标准是什么？"时
- LLM **不会**拒绝回答
- 约束配置中的禁止主题**完全无效**

#### 2. 缺少预检查

**问题**: 没有在调用 LLM 前检查禁止主题

**当前行为**:
```
用户查询 → 直接调用 LLM → 依赖 LLM 判断（但 LLM 不知道约束）
```

**应该的行为**:
```
用户查询 → 预检查禁止主题 → 直接拒绝 OR 调用 LLM
```

**影响**:
- 无法 100% 保证拒绝禁止主题
- 浪费 LLM 调用成本
- 响应时间较长

#### 3. 缺少答案后验证

**问题**: 生成回答后没有验证答案质量

**当前代码**:
```python
# 3. 流式生成回答
full_answer = ""
async for chunk in self._llm_client.stream_chat(messages):
    full_answer += chunk
    yield ResponseBuilder.text_chunk(chunk)

# 直接返回，没有验证
yield ResponseBuilder.done_chunk(rag_context.sources, ...)
```

**应该添加**:
```python
# 验证答案
validation_result = validator.validate_answer(
    full_answer,
    rag_context.sources,
    rag_context.context_text
)

if not validation_result.is_valid:
    logger.warning(f'答案验证失败: {validation_result.warnings}')
```

## 修复方案

### 方案 1: 修改 Prompt 构建（必须）⭐

**文件**: `backend/app/services/qa_agent.py`

**位置**: `_execute_rag_flow` 方法，第 513 行附近

**当前代码**:
```python
# 2. 构建提示
messages = StrictQAPrompt.build_messages(rag_context.context_text, query, history)
```

**修改为**:
```python
# 2. 构建提示（应用约束配置）
constraint_config = get_constraint_config()
constraints = {
    'generation': constraint_config.generation,
    'validation': constraint_config.validation
}

# 构建包含约束的系统提示词
system_prompt = ConstraintPromptBuilder.build_system_prompt(
    rag_context.context_text,
    constraints
)

# 构建消息列表
messages = [{'role': 'system', 'content': system_prompt}]

# 添加历史消息
if history:
    for msg in history:
        if msg.get("role") in ["user", "assistant"]:
            messages.append(msg)

# 添加当前问题
messages.append({'role': 'user', 'content': query})
```

**需要导入**:
```python
from app.prompts.strict_qa import ConstraintPromptBuilder
```

### 方案 2: 添加预检查（推荐）⭐

**文件**: `backend/app/services/qa_agent.py`

**位置**: `process` 方法开始处

**添加代码**:
```python
async def process(
    self,
    query: str,
    history: List[Dict] = None
) -> AsyncGenerator[str, None]:
    """处理用户查询"""
    start_time = time.time()
    
    # 预检查禁止主题
    constraint_config = get_constraint_config()
    is_forbidden, topic = self._check_forbidden_topics(query, constraint_config)
    
    if is_forbidden:
        # 记录日志
        logger.warning(
            f"拒绝禁止主题查询: topic='{topic}', query='{query[:50]}...'"
        )
        
        # 返回拒绝消息
        fallback_msg = constraint_config.fallback.get(
            'no_result_message',
            '抱歉，这个问题不在我的回答范围内。'
        )
        contact_info = constraint_config.fallback.get('contact_info', '')
        
        full_message = f"{fallback_msg}\n\n{contact_info}"
        
        yield ResponseBuilder.text_chunk(full_message)
        yield ResponseBuilder.done_chunk([], content=full_message)
        return
    
    # 继续正常处理...
    # 0. 基于知识库优化查询
    ...

def _check_forbidden_topics(
    self,
    query: str,
    config
) -> tuple:
    """
    检查查询是否包含禁止主题
    
    Returns:
        (is_forbidden, matched_topic)
    """
    forbidden_topics = config.generation.get('forbidden_topics', [])
    
    for topic in forbidden_topics:
        if topic in query:
            return True, topic
    
    return False, None
```

### 方案 3: 添加答案后验证（可选）

**文件**: `backend/app/services/qa_agent.py`

**位置**: `_execute_rag_flow` 方法，生成回答后

**添加代码**:
```python
# 3. 流式生成回答
full_answer = ""
async for chunk in self._llm_client.stream_chat(messages):
    full_answer += chunk
    yield ResponseBuilder.text_chunk(chunk)

# 验证答案质量
validation_result = validator.validate_answer(
    full_answer,
    rag_context.sources,
    rag_context.context_text
)

if not validation_result.is_valid:
    logger.warning(
        f"答案验证失败: confidence={validation_result.confidence_score:.2f}, "
        f"warnings={validation_result.warnings}"
    )
    
    # 可选：如果置信度太低，返回兜底消息
    if validation_result.confidence_score < 0.3:
        fallback_msg = StrictQAPrompt.get_fallback_message()
        yield ResponseBuilder.text_chunk(f"\n\n{fallback_msg}")

# 继续返回结果...
```

## 实施优先级

### 高优先级（必须立即修复）

1. **修改 Prompt 构建** - 方案 1
   - 影响：禁止主题和关键词约束完全无效
   - 工作量：小（约 10 行代码）
   - 风险：低

2. **添加预检查** - 方案 2
   - 影响：无法保证拒绝禁止主题，浪费成本
   - 工作量：中（约 30 行代码）
   - 风险：低

### 中优先级（建议实施）

3. **添加答案后验证** - 方案 3
   - 影响：无法检测低质量回答
   - 工作量：小（约 15 行代码）
   - 风险：低

### 低优先级（可选）

4. 添加审计日志
5. 实现语义匹配
6. 添加智能重定向

## 测试验证

修复后，运行以下测试验证：

```bash
# 1. 运行检查脚本
python backend/tests/constraints/check_constraint_usage.py

# 2. 运行禁止主题测试
pytest backend/tests/constraints/test_forbidden_topics_e2e.py -v

# 3. 运行完整测试套件
pytest backend/tests/constraints/ -v
```

预期结果：
- 检查脚本应该 5/5 通过
- 所有测试应该通过
- Prompt 应该包含禁止主题说明

## 预期效果

修复后的效果：

### 修复前
```
用户: 公司的工资标准是什么？
系统: [调用 LLM，LLM 不知道约束]
LLM: 根据公司政策，工资标准如下...  ❌ 回答了禁止主题
```

### 修复后（方案 1）
```
用户: 公司的工资标准是什么？
系统: [调用 LLM，Prompt 包含禁止主题说明]
LLM: 抱歉，关于薪资的问题不在我的回答范围内。  ✅ 正确拒绝
```

### 修复后（方案 1 + 2）
```
用户: 公司的工资标准是什么？
系统: [预检查发现禁止主题，直接拒绝]
系统: 抱歉，这个问题不在我的回答范围内。  ✅ 更快、更省成本
```

## 成本收益分析

### 当前成本（未修复）
- 禁止主题查询仍然调用 LLM
- 假设 5% 的查询是禁止主题
- 每次调用成本：$0.002
- 每天 1000 次查询
- 浪费成本：1000 × 5% × $0.002 = $0.10/天 = $36.5/年

### 修复后收益
- 禁止主题查询不调用 LLM
- 节省成本：$36.5/年
- 响应速度提升：从 1-3 秒降至 < 0.1 秒
- 用户体验改善：一致的拒绝消息
- 安全性提升：100% 保证拒绝

### 实施成本
- 开发时间：2-4 小时
- 测试时间：1-2 小时
- 总计：3-6 小时

**ROI**: 非常高（一次性投入，长期收益）

## 总结

### 当前状态
- ✅ 配置系统完善
- ✅ 检索验证正常
- ❌ 禁止主题约束未生效
- ❌ 缺少预检查
- ❌ 缺少答案验证

### 关键问题
**QA Agent 在生成回答时使用的 Prompt 不包含约束配置中的禁止主题和关键词，导致这些约束完全无效。**

### 解决方案
1. 修改 Prompt 构建方法（必须）
2. 添加预检查机制（推荐）
3. 添加答案后验证（可选）

### 下一步行动
1. 立即修复 Prompt 构建（方案 1）
2. 添加预检查（方案 2）
3. 运行测试验证
4. 部署到生产环境
5. 监控效果

---

**报告生成时间**: 2024-03-25
**检查工具**: `check_constraint_usage.py`
**状态**: ⚠️ 需要修复
