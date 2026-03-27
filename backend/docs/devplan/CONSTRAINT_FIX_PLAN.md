# 约束系统修复计划

## 执行摘要

本计划旨在修复约束配置未完全应用到项目中的问题，确保禁止主题和关键词约束能够正常工作。

**问题**: 约束配置中的禁止主题和关键词未在生成回答时应用，导致 LLM 不知道哪些主题是禁止的。

**影响**: 用户可以查询禁止主题并获得回答，违反了系统约束。

**优先级**: 🔴 高（影响核心功能和安全性）

## 修复任务清单

### 阶段 1: 紧急修复（必须完成）⭐

#### 任务 1.1: 修改 QA Agent 的 Prompt 构建
- **文件**: `backend/app/services/qa_agent.py`
- **优先级**: 🔴 P0 - 最高
- **预计时间**: 30 分钟
- **风险**: 低
- **依赖**: 无

**详细步骤**:

1. 在文件顶部添加导入
   ```python
   from app.prompts.strict_qa import StrictQAPrompt, ConstraintPromptBuilder
   ```

2. 定位到 `_execute_rag_flow` 方法（约第 513 行）

3. 找到以下代码：
   ```python
   # 2. 构建提示
   messages = StrictQAPrompt.build_messages(rag_context.context_text, query, history)
   ```

4. 替换为：
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

5. 保存文件

**验证步骤**:
```bash
# 运行检查脚本
python backend/tests/constraints/check_constraint_usage.py

# 应该看到 "Prompt 构建: ✅ 通过"
```

**回滚方案**:
如果出现问题，恢复原代码：
```python
messages = StrictQAPrompt.build_messages(rag_context.context_text, query, history)
```

---

#### 任务 1.2: 添加禁止主题预检查
- **文件**: `backend/app/services/qa_agent.py`
- **优先级**: 🔴 P0 - 最高
- **预计时间**: 45 分钟
- **风险**: 低
- **依赖**: 无

**详细步骤**:

1. 在 `QAAgent` 类中添加辅助方法（在 `_retrieve` 方法之后）：
   ```python
   def _check_forbidden_topics(
       self,
       query: str,
       config
   ) -> tuple:
       """
       检查查询是否包含禁止主题
       
       Args:
           query: 用户查询
           config: 约束配置
       
       Returns:
           (is_forbidden, matched_topic): 是否禁止，匹配的主题
       """
       forbidden_topics = config.generation.get('forbidden_topics', [])
       
       for topic in forbidden_topics:
           if topic in query:
               return True, topic
       
       return False, None
   ```

2. 在 `process` 方法开始处添加预检查（在 `start_time = time.time()` 之后）：
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
       
       # 继续原有逻辑...
       # 0. 基于知识库优化查询
       kb_optimizer = await get_kb_optimizer()
       ...
   ```

3. 保存文件

**验证步骤**:
```bash
# 运行测试
pytest backend/tests/constraints/test_forbidden_topics_e2e.py -v

# 手动测试
# 启动服务器，查询 "公司的工资标准是什么？"
# 应该立即返回拒绝消息，不调用 LLM
```

**性能影响**:
- 预检查耗时: < 1ms
- 节省 LLM 调用: 每次约 1-3 秒
- 成本节省: 每次约 $0.002

---

### 阶段 2: 质量改进（推荐完成）⭐

#### 任务 2.1: 添加答案后验证
- **文件**: `backend/app/services/qa_agent.py`
- **优先级**: 🟡 P1 - 高
- **预计时间**: 30 分钟
- **风险**: 低
- **依赖**: 任务 1.1

**详细步骤**:

1. 在 `_execute_rag_flow` 方法中，找到生成回答的代码（约第 516 行）：
   ```python
   # 3. 流式生成回答
   full_answer = ""
   async for chunk in self._llm_client.stream_chat(messages):
       full_answer += chunk
       yield ResponseBuilder.text_chunk(chunk)
   ```

2. 在生成回答后添加验证：
   ```python
   # 3. 流式生成回答
   full_answer = ""
   async for chunk in self._llm_client.stream_chat(messages):
       full_answer += chunk
       yield ResponseBuilder.text_chunk(chunk)
   
   # 验证答案质量
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
       
       # 如果置信度太低，追加警告信息
       if validation_result.confidence_score < 0.3:
           warning_msg = "\n\n注意：此回答的可信度较低，建议谨慎参考。"
           yield ResponseBuilder.text_chunk(warning_msg)
           full_answer += warning_msg
   ```

3. 保存文件

**验证步骤**:
```bash
# 运行测试
pytest backend/tests/constraints/test_answer_validator.py -v
```

---

#### 任务 2.2: 改进禁止关键词检查
- **文件**: `backend/app/services/qa_agent.py`
- **优先级**: 🟡 P1 - 高
- **预计时间**: 20 分钟
- **风险**: 低
- **依赖**: 任务 2.1

**详细步骤**:

1. 在 `_check_forbidden_topics` 方法中添加关键词检查：
   ```python
   def _check_forbidden_topics(
       self,
       query: str,
       config
   ) -> tuple:
       """
       检查查询是否包含禁止主题或关键词
       
       Args:
           query: 用户查询
           config: 约束配置
       
       Returns:
           (is_forbidden, matched_item): 是否禁止，匹配的主题/关键词
       """
       # 检查禁止主题
       forbidden_topics = config.generation.get('forbidden_topics', [])
       for topic in forbidden_topics:
           if topic in query:
               return True, f"主题:{topic}"
       
       # 检查禁止关键词
       forbidden_keywords = config.generation.get('forbidden_keywords', [])
       for keyword in forbidden_keywords:
           if keyword in query:
               return True, f"关键词:{keyword}"
       
       return False, None
   ```

2. 保存文件

**验证步骤**:
```bash
# 测试禁止关键词
# 查询包含 "工资" 应该被拒绝
```

---

### 阶段 3: 监控和优化（可选）

#### 任务 3.1: 添加审计日志
- **文件**: `backend/app/services/qa_agent.py`
- **优先级**: 🟢 P2 - 中
- **预计时间**: 30 分钟
- **风险**: 低
- **依赖**: 任务 1.2

**详细步骤**:

1. 创建日志记录函数：
   ```python
   def _log_forbidden_attempt(
       self,
       query: str,
       topic: str,
       user_id: str = None
   ):
       """
       记录禁止主题查询尝试
       
       Args:
           query: 用户查询
           topic: 匹配的禁止主题
           user_id: 用户ID（可选）
       """
       import os
       from datetime import datetime
       
       log_dir = "data/logs"
       os.makedirs(log_dir, exist_ok=True)
       
       log_entry = {
           "timestamp": datetime.now().isoformat(),
           "query": query[:100],
           "matched_topic": topic,
           "user_id": user_id or "unknown"
       }
       
       log_file = os.path.join(log_dir, "forbidden_attempts.log")
       with open(log_file, 'a', encoding='utf-8') as f:
           f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
   ```

2. 在预检查中调用：
   ```python
   if is_forbidden:
       # 记录日志
       logger.warning(f"拒绝禁止主题查询: topic='{topic}', query='{query[:50]}...'")
       self._log_forbidden_attempt(query, topic)
       ...
   ```

3. 保存文件

**验证步骤**:
```bash
# 查询禁止主题后，检查日志文件
cat data/logs/forbidden_attempts.log
```

---

#### 任务 3.2: 添加统计分析
- **文件**: 新建 `backend/app/services/constraint_stats.py`
- **优先级**: 🟢 P2 - 中
- **预计时间**: 1 小时
- **风险**: 低
- **依赖**: 任务 3.1

**详细步骤**:

1. 创建统计服务：
   ```python
   """
   约束统计服务
   
   提供约束相关的统计分析功能
   """
   
   import json
   from datetime import datetime, timedelta
   from pathlib import Path
   from typing import Dict, List
   
   
   class ConstraintStats:
       """约束统计"""
       
       def __init__(self):
           self.log_file = Path("data/logs/forbidden_attempts.log")
       
       def get_stats(self, days: int = 7) -> Dict:
           """
           获取统计数据
           
           Args:
               days: 统计最近几天的数据
           
           Returns:
               统计结果字典
           """
           if not self.log_file.exists():
               return {
                   "total_attempts": 0,
                   "top_topics": [],
                   "daily_counts": []
               }
           
           cutoff_date = datetime.now() - timedelta(days=days)
           attempts = []
           
           with open(self.log_file, 'r', encoding='utf-8') as f:
               for line in f:
                   try:
                       entry = json.loads(line)
                       entry_date = datetime.fromisoformat(entry['timestamp'])
                       if entry_date >= cutoff_date:
                           attempts.append(entry)
                   except:
                       continue
           
           # 统计
           topic_counts = {}
           for attempt in attempts:
               topic = attempt.get('matched_topic', 'unknown')
               topic_counts[topic] = topic_counts.get(topic, 0) + 1
           
           top_topics = sorted(
               topic_counts.items(),
               key=lambda x: x[1],
               reverse=True
           )[:10]
           
           return {
               "total_attempts": len(attempts),
               "top_topics": [{"topic": t, "count": c} for t, c in top_topics],
               "period_days": days
           }
   
   
   def get_constraint_stats() -> ConstraintStats:
       """获取统计实例"""
       return ConstraintStats()
   ```

2. 在约束 API 中添加统计端点（`backend/app/api/routes/constraints.py`）：
   ```python
   from app.services.constraint_stats import get_constraint_stats
   
   @router.get("/stats/forbidden")
   async def get_forbidden_stats(days: int = 7):
       """获取禁止主题统计"""
       stats_service = get_constraint_stats()
       return stats_service.get_stats(days)
   ```

3. 保存文件

**验证步骤**:
```bash
# 访问统计 API
curl http://localhost:8000/api/constraints/stats/forbidden?days=7
```

---

## 测试计划

### 单元测试

```bash
# 运行所有约束测试
pytest backend/tests/constraints/ -v

# 运行特定测试
pytest backend/tests/constraints/test_forbidden_topics_e2e.py -v
pytest backend/tests/constraints/test_answer_validator.py -v
```

### 集成测试

```bash
# 运行检查脚本
python backend/tests/constraints/check_constraint_usage.py

# 预期结果: 5/5 通过
```

### 手动测试

1. **测试禁止主题拒绝**
   ```
   查询: "公司的工资标准是什么？"
   预期: 立即返回拒绝消息，不调用 LLM
   ```

2. **测试允许主题正常回答**
   ```
   查询: "公司的年假政策是什么？"
   预期: 正常检索并回答
   ```

3. **测试 Prompt 包含约束**
   ```python
   # 在测试环境中打印 Prompt
   config = get_constraint_config()
   constraints = {'generation': config.generation}
   prompt = ConstraintPromptBuilder.build_system_prompt("context", constraints)
   print(prompt)
   # 应该包含 "禁止回答的主题：薪资、工资"
   ```

4. **测试答案验证**
   ```
   查询: 任意问题
   检查日志: 应该看到答案验证的日志
   ```

---

## 部署计划

### 开发环境

1. 创建功能分支
   ```bash
   git checkout -b fix/constraint-application
   ```

2. 按顺序完成任务 1.1 和 1.2

3. 运行测试验证
   ```bash
   pytest backend/tests/constraints/ -v
   python backend/tests/constraints/check_constraint_usage.py
   ```

4. 提交代码
   ```bash
   git add .
   git commit -m "fix: 应用约束配置到 QA Agent

   - 修改 Prompt 构建使用 ConstraintPromptBuilder
   - 添加禁止主题预检查
   - 确保禁止主题和关键词约束生效
   
   Fixes #XXX"
   ```

### 测试环境

1. 合并到测试分支
   ```bash
   git checkout test
   git merge fix/constraint-application
   ```

2. 部署到测试环境

3. 执行完整测试套件

4. 进行手动测试验证

### 生产环境

1. 代码审查

2. 合并到主分支
   ```bash
   git checkout main
   git merge fix/constraint-application
   ```

3. 创建发布标签
   ```bash
   git tag -a v1.1.0 -m "修复约束配置应用问题"
   git push origin v1.1.0
   ```

4. 部署到生产环境

5. 监控日志和性能指标

---

## 回滚计划

如果部署后发现问题：

### 快速回滚

1. 回滚到上一个版本
   ```bash
   git revert HEAD
   git push
   ```

2. 重新部署

### 问题排查

如果需要保留修改但修复问题：

1. 检查日志
   ```bash
   tail -f data/logs/app.log
   ```

2. 运行诊断脚本
   ```bash
   python backend/tests/constraints/check_constraint_usage.py
   ```

3. 根据错误信息修复

---

## 风险评估

### 高风险项

无

### 中风险项

1. **Prompt 格式变化**
   - 风险: 新的 Prompt 格式可能影响 LLM 回答质量
   - 缓解: 在测试环境充分测试
   - 回滚: 恢复原 Prompt 构建方法

2. **预检查误判**
   - 风险: 简单字符串匹配可能误判
   - 缓解: 仔细设计禁止主题列表
   - 回滚: 禁用预检查，仅依赖 Prompt

### 低风险项

1. **性能影响**
   - 风险: 预检查增加处理时间
   - 影响: < 1ms，可忽略
   - 缓解: 无需特殊处理

2. **日志文件增长**
   - 风险: 审计日志文件可能变大
   - 缓解: 添加日志轮转
   - 回滚: 删除日志文件

---

## 成功标准

### 功能标准

- ✅ 禁止主题查询被正确拒绝
- ✅ 允许主题查询正常处理
- ✅ Prompt 包含约束说明
- ✅ 所有测试通过
- ✅ 检查脚本 5/5 通过

### 性能标准

- ✅ 预检查耗时 < 1ms
- ✅ 禁止主题查询响应时间 < 100ms
- ✅ 正常查询响应时间无明显增加

### 质量标准

- ✅ 代码审查通过
- ✅ 测试覆盖率 > 90%
- ✅ 无新增 bug
- ✅ 文档完整

---

## 时间估算

### 阶段 1: 紧急修复
- 任务 1.1: 30 分钟
- 任务 1.2: 45 分钟
- 测试验证: 30 分钟
- **小计: 1.75 小时**

### 阶段 2: 质量改进
- 任务 2.1: 30 分钟
- 任务 2.2: 20 分钟
- 测试验证: 20 分钟
- **小计: 1.17 小时**

### 阶段 3: 监控和优化
- 任务 3.1: 30 分钟
- 任务 3.2: 1 小时
- 测试验证: 30 分钟
- **小计: 2 小时**

### 总计
- **最小实施（阶段 1）**: 1.75 小时
- **推荐实施（阶段 1+2）**: 2.92 小时
- **完整实施（全部）**: 4.92 小时

---

## 资源需求

### 人力资源
- 后端开发: 1 人
- 测试工程师: 0.5 人（兼职）
- 代码审查: 1 人

### 技术资源
- 开发环境: 已有
- 测试环境: 已有
- 监控工具: 已有

### 时间资源
- 开发时间: 3-5 小时
- 测试时间: 1-2 小时
- 部署时间: 0.5 小时
- **总计: 4.5-7.5 小时**

---

## 后续优化

完成本计划后，可以考虑以下优化：

1. **语义匹配**
   - 使用 embedding 进行语义相似度检查
   - 处理同义词和变体
   - 预计时间: 4-6 小时

2. **智能重定向**
   - 不是简单拒绝，而是引导到相关的允许主题
   - 提供替代问题建议
   - 预计时间: 6-8 小时

3. **动态学习**
   - 根据用户查询自动发现新的禁止主题
   - 管理员审核和批准
   - 预计时间: 8-12 小时

4. **A/B 测试**
   - 对比不同约束策略的效果
   - 优化拒绝消息
   - 预计时间: 4-6 小时

---

## 联系人

- **项目负责人**: [姓名]
- **技术负责人**: [姓名]
- **测试负责人**: [姓名]

---

## 附录

### A. 相关文档

- [约束配置使用报告](../tests/constraints/CONSTRAINT_USAGE_REPORT.md)
- [禁止主题功能分析](../tests/constraints/FORBIDDEN_TOPICS_ANALYSIS.md)
- [测试使用指南](../tests/constraints/USAGE_GUIDE.md)

### B. 检查工具

- [约束使用检查脚本](../tests/constraints/check_constraint_usage.py)
- [快速测试脚本](../tests/constraints/quick_test.py)

### C. 测试用例

- [禁止主题端到端测试](../tests/constraints/test_forbidden_topics_e2e.py)
- [约束配置测试](../tests/constraints/test_constraint_config.py)
- [答案验证器测试](../tests/constraints/test_answer_validator.py)

---

**文档版本**: 1.0
**创建日期**: 2024-03-25
**最后更新**: 2024-03-25
**状态**: 待审批
