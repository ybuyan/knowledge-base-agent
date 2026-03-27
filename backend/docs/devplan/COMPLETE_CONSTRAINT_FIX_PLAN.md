# 约束配置完整修复计划

## 执行摘要

通过全面检查发现，`constraints.json` 中的 22 个配置项中，只有 11 个（50%）被应用到代码中。

**关键发现**:
- ✅ 已应用: 11/22 (50%)
- ❌ 未应用: 11/22 (50%)
- 🔴 高优先级未应用: 5 项（generation 类别）
- 🟡 中优先级未应用: 4 项
- 🟢 低优先级未应用: 2 项

## 配置应用情况总览

### 按类别统计

| 类别 | 已应用 | 未应用 | 应用率 |
|------|--------|--------|--------|
| retrieval | 3/5 | 2/5 | 60% |
| generation | 0/6 | 6/6 | 0% ⚠️ |
| validation | 4/4 | 0/4 | 100% ✅ |
| fallback | 2/4 | 2/4 | 50% |
| suggest_questions | 2/3 | 1/3 | 67% |

**最严重问题**: generation 类别的所有配置项（6个）都未应用！

---

## 未应用配置项详细分析

### 🔴 高优先级（必须修复）

#### 1. generation.forbidden_topics - 禁止主题
**配置值**: `['薪资', '工资']`

**问题**:
- 虽然在 `strict_qa.py` 中有 `ConstraintPromptBuilder` 可以处理
- 但 `qa_agent.py` 使用的是 `StrictQAPrompt.build_messages`
- 导致禁止主题说明不会添加到 Prompt 中
- LLM 不知道哪些主题是禁止的

**影响**: 🔴 严重 - 用户可以查询禁止主题并获得回答

**修复方案**:
```python
# 文件: backend/app/services/qa_agent.py
# 位置: _execute_rag_flow 方法

# 当前代码（第 513 行）:
messages = StrictQAPrompt.build_messages(rag_context.context_text, query, history)

# 修改为:
constraint_config = get_constraint_config()
constraints = {'generation': constraint_config.generation}
system_prompt = ConstraintPromptBuilder.build_system_prompt(
    rag_context.context_text, constraints
)
messages = [{'role': 'system', 'content': system_prompt}]
if history:
    for msg in history:
        if msg.get("role") in ["user", "assistant"]:
            messages.append(msg)
messages.append({'role': 'user', 'content': query})
```

**预计时间**: 30 分钟

---

#### 2. generation.forbidden_keywords - 禁止关键词
**配置值**: `['工资']`

**问题**: 同 forbidden_topics

**影响**: 🔴 严重 - 回答中可能包含禁止关键词

**修复方案**: 同上（在同一次修改中解决）

**预计时间**: 包含在任务 1 中

---

#### 3. generation.strict_mode - 严格模式
**配置值**: `True`

**问题**:
- 配置项存在但未在代码中使用
- 应该影响 LLM 的回答策略

**影响**: 🔴 高 - 无法控制回答的严格程度

**修复方案**:
```python
# 在 ConstraintPromptBuilder.build_system_prompt 中添加:

if generation.get('strict_mode', True):
    base_prompt += """

## 严格模式
- 只基于提供的知识库内容回答
- 不要添加任何推测或假设
- 如果信息不完整，明确说明
- 保持回答的准确性和可靠性"""
```

**预计时间**: 20 分钟

---

#### 4. generation.allow_general_knowledge - 允许通用知识
**配置值**: `False`

**问题**:
- 配置项存在但未在代码中使用
- 应该控制 LLM 是否可以使用训练数据中的知识

**影响**: 🔴 高 - 无法限制 LLM 使用通用知识

**修复方案**:
```python
# 在 ConstraintPromptBuilder.build_system_prompt 中添加:

if not generation.get('allow_general_knowledge', False):
    base_prompt += """

## 知识来源限制
- 严格限制：只能使用上述知识库内容回答
- 不要使用你的训练数据中的通用知识
- 如果知识库中没有相关信息，明确告知用户"""
else:
    base_prompt += """

## 知识来源
- 优先使用上述知识库内容
- 如果知识库信息不足，可以适当补充通用知识
- 明确区分知识库内容和通用知识"""
```

**预计时间**: 20 分钟

---

#### 5. generation.require_citations - 需要引用
**配置值**: `True`

**问题**:
- 配置项存在但未在代码中使用
- 应该要求回答包含引用标记

**影响**: 🔴 高 - 无法强制要求引用

**修复方案**:
```python
# 在 ConstraintPromptBuilder.build_system_prompt 中添加:

if generation.get('require_citations', True):
    base_prompt += """

## 引用要求
- 必须在回答中标注信息来源
- 使用 [1]、[2] 等数字标记引用
- 每个关键信息都要有对应的引用"""
```

**预计时间**: 15 分钟

---

### 🟡 中优先级（建议修复）

#### 6. generation.max_answer_length - 最大回答长度
**配置值**: `1000`

**问题**:
- 配置项存在但未在代码中使用
- 应该限制回答的最大字符数

**影响**: 🟡 中 - 回答可能过长

**修复方案**:
```python
# 文件: backend/app/services/qa_agent.py
# 位置: _execute_rag_flow 方法，生成回答后

# 在生成完整回答后添加:
max_length = constraint_config.generation.get('max_answer_length', 1000)
if len(full_answer) > max_length:
    logger.warning(f"回答长度 {len(full_answer)} 超过限制 {max_length}，进行截断")
    full_answer = full_answer[:max_length] + "..."
```

**预计时间**: 15 分钟

---

#### 7. retrieval.min_relevant_docs - 最小相关文档数
**配置值**: `1`

**问题**:
- 配置项存在但未在代码中使用
- 应该检查检索到的文档数量是否满足最小要求

**影响**: 🟡 中 - 无法保证检索质量

**修复方案**:
```python
# 文件: backend/app/services/qa_agent.py
# 位置: _retrieve 方法，检索后

# 在检索验证后添加:
min_docs = retrieval_config.get('min_relevant_docs', 1)
if len(filtered_docs) < min_docs:
    logger.warning(
        f"检索到的文档数 {len(filtered_docs)} 少于最小要求 {min_docs}"
    )
    # 可选：返回兜底消息
```

**预计时间**: 15 分钟

---

#### 8. retrieval.content_coverage_threshold - 内容覆盖阈值
**配置值**: `0.5`

**问题**:
- 配置项存在但未在代码中使用
- 应该检查检索内容是否充分覆盖查询

**影响**: 🟡 中 - 无法评估检索质量

**修复方案**:
```python
# 文件: backend/app/services/answer_validator.py
# 添加新方法:

def check_content_coverage(
    self,
    query: str,
    documents: List[str],
    threshold: float = 0.5
) -> float:
    """
    检查文档内容对查询的覆盖度
    
    Returns:
        coverage_score: 覆盖度分数 (0-1)
    """
    query_words = set(query.split())
    doc_words = set(" ".join(documents).split())
    
    overlap = len(query_words & doc_words)
    coverage = overlap / len(query_words) if query_words else 0
    
    return coverage
```

**预计时间**: 30 分钟

---

#### 9. validation.* 在 qa_agent 中调用
**问题**:
- `answer_validator.validate_answer` 方法已实现
- 但在 `qa_agent.py` 中未调用
- 导致答案验证功能未生效

**影响**: 🟡 中 - 无法检测低质量回答

**修复方案**:
```python
# 文件: backend/app/services/qa_agent.py
# 位置: _execute_rag_flow 方法，生成回答后

# 在生成完整回答后添加:
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
    
    # 如果置信度太低，追加警告
    if validation_result.confidence_score < 0.3:
        warning_msg = "\n\n注意：此回答的可信度较低，建议谨慎参考。"
        yield ResponseBuilder.text_chunk(warning_msg)
        full_answer += warning_msg
```

**预计时间**: 20 分钟

---

### 🟢 低优先级（可选）

#### 10. fallback.suggest_similar - 建议相似问题
**配置值**: `True`

**问题**:
- 配置项存在但未在代码中使用
- 应该控制是否在无结果时建议相似问题

**影响**: 🟢 低 - 用户体验优化

**修复方案**:
```python
# 文件: backend/app/prompts/strict_qa.py
# 修改 get_fallback_message 方法:

@staticmethod
def get_fallback_message(
    contact_info: str = "",
    similar_questions: str = "",
    config = None
) -> str:
    """获取兜底提示消息"""
    result = prompt_manager.render("fallback", {
        "contact_info": contact_info,
        "similar_questions": similar_questions
    })
    
    message = result.get("content", "抱歉，我在知识库中没有找到相关信息。")
    
    # 根据配置决定是否添加相似问题建议
    if config:
        fallback_config = config.fallback
        if fallback_config.get('suggest_similar') and similar_questions:
            message += f"\n\n您可能想问：\n{similar_questions}"
        
        if fallback_config.get('suggest_contact') and contact_info:
            message += f"\n\n{contact_info}"
    
    return message
```

**预计时间**: 25 分钟

---

#### 11. fallback.suggest_contact - 建议联系方式
**配置值**: `True`

**问题**: 同 suggest_similar

**影响**: 🟢 低 - 用户体验优化

**修复方案**: 包含在任务 10 中

**预计时间**: 包含在任务 10 中

---

#### 12. suggest_questions.types - 建议问题类型
**配置值**: `['相关追问', '深入探索', '对比分析']`

**问题**:
- 配置项存在但未在代码中使用
- 应该根据类型生成不同风格的建议问题

**影响**: 🟢 低 - 建议问题质量优化

**修复方案**:
```python
# 文件: backend/app/services/suggestion_generator.py
# 修改 generate 方法:

async def generate(
    self,
    question: str,
    answer: str,
    count: int = 3
) -> List[str]:
    """生成建议问题"""
    config = get_constraint_config()
    types = config.suggest_questions.get('types', [])
    
    if not types:
        types = ['相关追问', '深入探索', '对比分析']
    
    # 根据类型生成不同风格的问题
    type_prompts = {
        '相关追问': '基于当前回答，生成相关的追问',
        '深入探索': '生成更深入探索该主题的问题',
        '对比分析': '生成对比分析相关概念的问题'
    }
    
    # 为每种类型生成问题...
```

**预计时间**: 40 分钟

---

## 修复优先级和时间估算

### 阶段 1: 紧急修复（必须完成）🔴

| 任务 | 配置项 | 预计时间 |
|------|--------|----------|
| 1 | forbidden_topics + forbidden_keywords | 30 分钟 |
| 2 | strict_mode | 20 分钟 |
| 3 | allow_general_knowledge | 20 分钟 |
| 4 | require_citations | 15 分钟 |
| **小计** | | **1.42 小时** |

### 阶段 2: 质量改进（建议完成）🟡

| 任务 | 配置项 | 预计时间 |
|------|--------|----------|
| 5 | max_answer_length | 15 分钟 |
| 6 | min_relevant_docs | 15 分钟 |
| 7 | content_coverage_threshold | 30 分钟 |
| 8 | validation 调用 | 20 分钟 |
| **小计** | | **1.33 小时** |

### 阶段 3: 用户体验优化（可选）🟢

| 任务 | 配置项 | 预计时间 |
|------|--------|----------|
| 9 | suggest_similar + suggest_contact | 25 分钟 |
| 10 | suggest_questions.types | 40 分钟 |
| **小计** | | **1.08 小时** |

### 总计

- **最小实施（阶段 1）**: 1.42 小时
- **推荐实施（阶段 1+2）**: 2.75 小时
- **完整实施（全部）**: 3.83 小时

---

## 实施步骤

### 步骤 1: 修改 ConstraintPromptBuilder（阶段 1）

**文件**: `backend/app/prompts/strict_qa.py`

**修改内容**:
```python
@staticmethod
def build_system_prompt(
    context: str,
    constraints: Dict[str, Any] = None
) -> str:
    """构建带约束的系统提示词"""
    constraints = constraints or {}
    generation = constraints.get("generation", {})
    
    # 基础提示词
    base_prompt = prompt_manager.get_system_prompt("strict_qa") or ""
    
    # 1. 严格模式
    if generation.get('strict_mode', True):
        base_prompt += """

## 严格模式
- 只基于提供的知识库内容回答
- 不要添加任何推测或假设
- 如果信息不完整，明确说明
- 保持回答的准确性和可靠性"""
    
    # 2. 通用知识限制
    if not generation.get('allow_general_knowledge', False):
        base_prompt += """

## 知识来源限制
- 严格限制：只能使用上述知识库内容回答
- 不要使用你的训练数据中的通用知识
- 如果知识库中没有相关信息，明确告知用户"""
    
    # 3. 引用要求
    if generation.get('require_citations', True):
        base_prompt += """

## 引用要求
- 必须在回答中标注信息来源
- 使用 [1]、[2] 等数字标记引用
- 每个关键信息都要有对应的引用"""
    
    # 4. 禁止主题
    forbidden_topics = generation.get("forbidden_topics", [])
    if forbidden_topics:
        topics_str = "、".join(forbidden_topics)
        base_prompt += f"\n\n## 禁止回答的主题\n请不要回答与以下主题相关的问题：{topics_str}"
    
    # 5. 禁止关键词
    forbidden_keywords = generation.get("forbidden_keywords", [])
    if forbidden_keywords:
        keywords_str = "、".join(forbidden_keywords)
        base_prompt += f"\n\n## 禁止使用的关键词\n回答中请不要使用以下关键词：{keywords_str}"
    
    return base_prompt.format(context=context, forbidden_topics="无")
```

---

### 步骤 2: 修改 QA Agent（阶段 1+2）

**文件**: `backend/app/services/qa_agent.py`

**修改 1: 导入**
```python
from app.prompts.strict_qa import StrictQAPrompt, ConstraintPromptBuilder
```

**修改 2: _execute_rag_flow 方法**
```python
async def _execute_rag_flow(
    self,
    query: str,
    history: List[Dict] = None,
    optimized_keywords: List[str] = None
) -> AsyncGenerator[str, None]:
    """执行RAG流程"""
    
    # 获取约束配置
    constraint_config = get_constraint_config()
    
    # 1. 向量检索
    rag_context = await self._retrieve(query, optimized_keywords)
    
    if not rag_context.documents:
        # 无检索结果，返回fallback消息
        fallback_msg = StrictQAPrompt.get_fallback_message()
        yield ResponseBuilder.text_chunk(fallback_msg)
        yield ResponseBuilder.done_chunk([], content=fallback_msg)
        return
    
    # 2. 构建提示（应用约束配置）
    constraints = {
        'generation': constraint_config.generation,
        'validation': constraint_config.validation
    }
    
    system_prompt = ConstraintPromptBuilder.build_system_prompt(
        rag_context.context_text,
        constraints
    )
    
    messages = [{'role': 'system', 'content': system_prompt}]
    
    if history:
        for msg in history:
            if msg.get("role") in ["user", "assistant"]:
                messages.append(msg)
    
    messages.append({'role': 'user', 'content': query})
    
    # 3. 流式生成回答
    full_answer = ""
    async for chunk in self._llm_client.stream_chat(messages):
        full_answer += chunk
        yield ResponseBuilder.text_chunk(chunk)
    
    # 4. 答案验证
    validator = get_answer_validator()
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
        
        if validation_result.confidence_score < 0.3:
            warning_msg = "\n\n注意：此回答的可信度较低，建议谨慎参考。"
            yield ResponseBuilder.text_chunk(warning_msg)
            full_answer += warning_msg
    
    # 5. 长度限制
    max_length = constraint_config.generation.get('max_answer_length', 1000)
    if len(full_answer) > max_length:
        logger.warning(f"回答长度 {len(full_answer)} 超过限制 {max_length}")
        full_answer = full_answer[:max_length] + "..."
    
    # 6. 生成快捷提问
    suggested_questions = []
    suggest_config = constraint_config.suggest_questions
    if suggest_config.get("enabled", True):
        try:
            suggestion_generator = get_suggestion_generator()
            suggested_questions = await suggestion_generator.generate(
                question=query,
                answer=full_answer,
                count=suggest_config.get("count", 3)
            )
        except Exception as e:
            logger.warning(f"生成快捷提问失败: {e}")
    
    # 7. 匹配相关链接
    related_links = []
    if full_answer and len(full_answer.strip()) > 0:
        try:
            link_matcher = get_link_matcher()
            related_links = await link_matcher.match_links(query)
        except Exception as e:
            logger.warning(f"匹配链接失败: {e}")
    
    # 8. 返回结果
    yield ResponseBuilder.done_chunk(
        rag_context.sources,
        content=full_answer,
        suggested_questions=suggested_questions,
        related_links=related_links
    )
```

---

## 验证计划

### 验证步骤

1. **运行全面检查脚本**
   ```bash
   python backend/tests/constraints/check_all_constraints.py
   ```
   预期结果: 应用率从 50% 提升到 100%

2. **运行所有测试**
   ```bash
   pytest backend/tests/constraints/ -v
   ```
   预期结果: 所有测试通过

3. **手动测试各项配置**
   - 禁止主题: 查询 "工资标准" 应被拒绝
   - 严格模式: 回答应只基于知识库
   - 引用要求: 回答应包含 [1]、[2] 等标记
   - 最大长度: 过长回答应被截断
   - 答案验证: 低质量回答应有警告

---

## 成功标准

- ✅ 所有 22 个配置项都应用到代码中
- ✅ 检查脚本显示 100% 应用率
- ✅ 所有测试通过
- ✅ 手动测试验证功能正常
- ✅ 代码审查通过
- ✅ 文档更新完整

---

## 风险和缓解

### 风险 1: Prompt 变化影响回答质量
- **概率**: 中
- **影响**: 中
- **缓解**: 在测试环境充分测试，对比修改前后的回答质量

### 风险 2: 性能影响
- **概率**: 低
- **影响**: 低
- **缓解**: 添加的检查都是轻量级操作，性能影响可忽略

### 风险 3: 配置冲突
- **概率**: 低
- **影响**: 中
- **缓解**: 明确配置优先级，添加配置验证

---

## 相关文档

- [约束配置使用报告](../tests/constraints/CONSTRAINT_USAGE_REPORT.md)
- [禁止主题功能分析](../tests/constraints/FORBIDDEN_TOPICS_ANALYSIS.md)
- [修复执行清单](CONSTRAINT_FIX_CHECKLIST.md)
- [全面检查脚本](../tests/constraints/check_all_constraints.py)

---

**文档版本**: 1.0
**创建日期**: 2024-03-25
**状态**: 待审批
**预计完成时间**: 2.75 - 3.83 小时
