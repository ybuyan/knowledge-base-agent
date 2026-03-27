# 禁止主题功能分析与改进建议

## 当前实现方式

### 工作原理

当前系统通过以下方式处理禁止主题：

1. **配置存储**
   - 禁止主题存储在 `config/constraints.json` 中
   - 配置项：`generation.forbidden_topics` 和 `generation.forbidden_keywords`
   - 示例：`["薪资", "工资"]`

2. **Prompt 注入**
   - 通过 `ConstraintPromptBuilder.build_system_prompt()` 构建系统提示词
   - 将禁止主题和关键词添加到 prompt 中
   - 示例 prompt：
     ```
     ## 禁止回答的主题
     请不要回答与以下主题相关的问题：薪资、工资
     
     ## 禁止使用的关键词
     回答中请不要使用以下关键词：工资
     ```

3. **LLM 自主判断**
   - 依赖 LLM 根据 prompt 中的指示自行判断
   - LLM 决定是否回答以及如何回答

### 当前配置

```json
{
  "generation": {
    "forbidden_topics": ["薪资", "工资"],
    "forbidden_keywords": ["工资"]
  }
}
```

### 测试验证

✅ **已验证的功能**：
1. 查询包含禁止主题的检测
2. Prompt 中包含禁止主题说明
3. Prompt 中包含禁止关键词说明
4. 配置的动态更新
5. 完整工作流程

## 存在的问题

### 1. 依赖 LLM 自觉性 ⚠️

**问题**：
- LLM 可能不完全遵守 prompt 中的指示
- 不同的 LLM 模型遵守程度不同
- 无法 100% 保证拒绝回答

**示例场景**：
```
用户：公司的工资标准是什么？
当前行为：发送给 LLM，依赖 LLM 拒绝
可能结果：
  - LLM 正确拒绝 ✅
  - LLM 部分回答 ⚠️
  - LLM 完全回答 ❌
```

### 2. 成本浪费 💰

**问题**：
- 即使查询包含禁止主题，仍然调用 LLM
- 每次调用都产生 API 费用
- 响应时间较长

**成本对比**：
```
当前方式：
  查询 → LLM 调用 → LLM 拒绝 → 返回
  成本：1 次 LLM 调用
  时间：1-3 秒

建议方式：
  查询 → 预检查 → 直接拒绝 → 返回
  成本：0 次 LLM 调用
  时间：< 0.1 秒
```

### 3. 行为不一致 🔄

**问题**：
- LLM 的拒绝消息可能每次不同
- 难以提供统一的用户体验
- 无法精确控制拒绝消息格式

**示例**：
```
查询 1：公司的工资标准是什么？
回答 1：抱歉，我无法回答关于薪资的问题。

查询 2：员工工资如何计算？
回答 2：很抱歉，这个问题不在我的回答范围内。

查询 3：工资发放时间？
回答 3：关于薪资相关的问题，请联系HR部门。
```

### 4. 缺少审计日志 📝

**问题**：
- 无法追踪用户尝试查询禁止主题的行为
- 难以分析哪些禁止主题被频繁查询
- 无法优化禁止主题列表

## 改进建议

### 方案 1：预检查 + 直接拒绝（推荐）⭐

**实现方式**：

```python
def check_forbidden_topics(query: str, config) -> tuple:
    """
    在调用 LLM 前检查禁止主题
    
    Returns:
        (is_forbidden, matched_topic, rejection_message)
    """
    forbidden_topics = config.generation.get('forbidden_topics', [])
    
    for topic in forbidden_topics:
        if topic in query:
            # 直接返回拒绝消息，不调用 LLM
            rejection_message = config.fallback.get('no_result_message', '未找到相关信息')
            contact_info = config.fallback.get('contact_info', '')
            
            full_message = f"{rejection_message}\n\n{contact_info}"
            
            return True, topic, full_message
    
    return False, None, None


# 在 QA Agent 或 Chat API 中使用
async def process_query(query: str, config):
    # 预检查
    is_forbidden, topic, rejection = check_forbidden_topics(query, config)
    
    if is_forbidden:
        # 记录日志
        logger.warning(f"拒绝禁止主题查询: topic='{topic}', query='{query[:50]}'")
        
        # 直接返回拒绝消息
        return rejection
    
    # 正常处理
    return await call_llm(query)
```

**优点**：
- ✅ 100% 确保拒绝
- ✅ 节省 LLM 调用成本
- ✅ 响应速度快
- ✅ 行为一致
- ✅ 易于审计

**缺点**：
- ⚠️ 简单的字符串匹配可能误判
- ⚠️ 需要维护禁止主题列表

### 方案 2：双重检查（平衡方案）

**实现方式**：

```python
async def process_query_with_double_check(query: str, config):
    # 第一层：预检查（快速过滤明显的禁止主题）
    is_forbidden, topic, _ = check_forbidden_topics(query, config)
    
    if is_forbidden:
        # 明确包含禁止主题，直接拒绝
        return get_rejection_message(topic, config)
    
    # 第二层：调用 LLM（处理模糊情况）
    # 在 prompt 中仍然包含禁止主题说明
    response = await call_llm_with_constraints(query, config)
    
    # 第三层：后验证（检查 LLM 回答是否包含禁止关键词）
    if contains_forbidden_keywords(response, config):
        logger.warning(f"LLM 回答包含禁止关键词: query='{query[:50]}'")
        return get_rejection_message("相关主题", config)
    
    return response
```

**优点**：
- ✅ 多层保护
- ✅ 处理模糊情况
- ✅ 灵活性高

**缺点**：
- ⚠️ 实现复杂
- ⚠️ 仍有 LLM 调用成本

### 方案 3：语义匹配（高级方案）

**实现方式**：

```python
from app.core.embeddings import get_embeddings

async def semantic_check_forbidden_topics(query: str, config):
    """
    使用语义相似度检查禁止主题
    """
    forbidden_topics = config.generation.get('forbidden_topics', [])
    
    if not forbidden_topics:
        return False, None
    
    # 获取查询的 embedding
    embeddings = get_embeddings()
    query_embedding = embeddings.embed_query(query)
    
    # 获取禁止主题的 embeddings
    topic_embeddings = embeddings.embed_documents(forbidden_topics)
    
    # 计算相似度
    from numpy import dot
    from numpy.linalg import norm
    
    for i, topic in enumerate(forbidden_topics):
        similarity = dot(query_embedding, topic_embeddings[i]) / (
            norm(query_embedding) * norm(topic_embeddings[i])
        )
        
        # 相似度阈值（可配置）
        if similarity > 0.8:
            return True, topic
    
    return False, None
```

**优点**：
- ✅ 语义理解
- ✅ 减少误判
- ✅ 处理同义词

**缺点**：
- ⚠️ 需要 embedding 调用
- ⚠️ 实现复杂
- ⚠️ 有一定成本

## 推荐实现方案

### 短期改进（立即可实施）

1. **添加预检查函数**
   ```python
   # 在 app/services/forbidden_checker.py
   def check_forbidden_topics(query: str, config) -> tuple:
       # 实现方案 1 的逻辑
       pass
   ```

2. **在 Chat API 中集成**
   ```python
   # 在 app/api/routes/chat.py
   from app.services.forbidden_checker import check_forbidden_topics
   
   @router.post("/v2/ask/stream")
   async def ask_stream(request: ChatStreamRequest):
       # 预检查
       is_forbidden, topic, rejection = check_forbidden_topics(
           request.question, 
           get_constraint_config()
       )
       
       if is_forbidden:
           # 返回拒绝消息
           yield format_rejection_response(rejection)
           return
       
       # 正常处理
       ...
   ```

3. **添加审计日志**
   ```python
   def log_forbidden_attempt(query: str, topic: str, user_id: str = None):
       logger.warning(
           f"禁止主题查询: topic='{topic}', "
           f"query='{query[:50]}...', user_id='{user_id}'"
       )
       
       # 可选：写入数据库用于分析
       # await save_forbidden_attempt(query, topic, user_id)
   ```

### 中期改进（1-2 周）

1. **实现双重检查机制**
   - 预检查 + LLM 判断 + 后验证

2. **添加配置选项**
   ```json
   {
     "generation": {
       "forbidden_topics": ["薪资", "工资"],
       "forbidden_check_mode": "pre_check",  // "pre_check" | "llm_only" | "double_check"
       "forbidden_action": "reject",  // "reject" | "redirect" | "log_only"
     }
   }
   ```

3. **实现统计分析**
   - 禁止主题查询频率
   - 最常被查询的禁止主题
   - 用户行为分析

### 长期改进（1-2 月）

1. **语义匹配**
   - 使用 embedding 进行语义相似度检查
   - 处理同义词和变体

2. **智能重定向**
   - 不是简单拒绝，而是引导到相关的允许主题
   - 提供替代问题建议

3. **动态学习**
   - 根据用户查询自动发现新的禁止主题
   - 管理员审核和批准

## 测试用例

### 已实现的测试

✅ `test_forbidden_topics_e2e.py` - 13 个测试用例
- 禁止主题检测
- Prompt 构建
- 配置管理
- 工作流程验证

### 需要添加的测试

1. **预检查功能测试**
   ```python
   def test_pre_check_rejects_forbidden_topics():
       """测试预检查能够拒绝禁止主题"""
       pass
   ```

2. **性能测试**
   ```python
   def test_pre_check_performance():
       """测试预检查的性能"""
       pass
   ```

3. **审计日志测试**
   ```python
   def test_forbidden_attempts_are_logged():
       """测试禁止主题尝试被记录"""
       pass
   ```

## 总结

### 当前状态
- ✅ 配置系统完善
- ✅ Prompt 注入正常
- ⚠️ 依赖 LLM 自觉性
- ❌ 缺少预检查
- ❌ 缺少审计日志

### 建议优先级

1. **高优先级**（立即实施）
   - 添加预检查函数
   - 在 Chat API 中集成
   - 添加审计日志

2. **中优先级**（1-2 周）
   - 实现双重检查
   - 添加配置选项
   - 实现统计分析

3. **低优先级**（1-2 月）
   - 语义匹配
   - 智能重定向
   - 动态学习

### 预期效果

实施改进后：
- 🎯 100% 确保拒绝禁止主题
- 💰 节省 LLM 调用成本（预计 5-10%）
- ⚡ 提升响应速度（禁止主题查询 < 0.1 秒）
- 📊 提供完整的审计日志
- 👥 改善用户体验（一致的拒绝消息）

---

**文档版本**: 1.0
**最后更新**: 2024-03-25
**作者**: 开发团队
