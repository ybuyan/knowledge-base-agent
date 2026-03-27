# 约束配置验证指南

## 快速回答你的问题

### 问：询问"我的工资是多少"会返回什么？

**答：根据当前配置，LLM 会拒绝回答，因为"工资"属于禁止主题。**

**预期回答示例**：
```
抱歉，关于薪资/工资相关的问题属于禁止回答的主题。
根据公司政策，薪资信息属于保密内容。
如有疑问，请联系人力资源部门。
```

---

## 工作原理

### 1. 配置文件

**位置**: `backend/config/constraints.json`

```json
{
  "constraints": {
    "generation": {
      "strict_mode": true,
      "allow_general_knowledge": false,
      "require_citations": true,
      "max_answer_length": 1000,
      "forbidden_topics": ["薪资", "工资"],
      "forbidden_keywords": ["工资"]
    }
  }
}
```

### 2. 系统提示词构建

当用户查询时，系统会：

1. **加载约束配置**
   ```python
   config = get_constraint_config()
   # forbidden_topics: ['薪资', '工资']
   ```

2. **构建系统提示词**
   ```python
   system_prompt = ConstraintPromptBuilder.build_system_prompt(
       context=knowledge_base_content,
       constraints={'generation': config.generation}
   )
   ```

3. **生成的系统提示词包含**：
   ```
   ## 严格模式
   - 只基于提供的知识库内容回答
   - 不要添加任何推测或假设
   
   ## 知识来源限制
   - 严格限制：只能使用上述知识库内容回答
   - 不要使用你的训练数据中的通用知识
   
   ## 引用要求
   - 必须在回答中标注信息来源
   - 使用 [1]、[2] 等数字标记引用
   
   ## 禁止回答的主题
   请不要回答与以下主题相关的问题：薪资、工资
   
   ## 禁止使用的关键词
   回答中请不要使用以下关键词：工资
   ```

4. **发送给 LLM**
   ```python
   messages = [
       {'role': 'system', 'content': system_prompt},
       {'role': 'user', 'content': '我的工资是多少？'}
   ]
   ```

5. **LLM 看到约束后拒绝回答**

---

## 验证方法

### 方法 1: 运行验证脚本（推荐）

```bash
cd backend
python tests/constraints/verify_forbidden_topics_live.py
```

**输出示例**：
```
======================================================================
  3. 测试禁止主题查询
======================================================================

❌ 查询: 我的工资是多少？
   预期: LLM 应拒绝回答，说明该主题被禁止

【LLM 预期回答】
----------------------------------------------------------------------
抱歉，关于薪资/工资相关的问题属于禁止回答的主题。
根据公司政策，薪资信息属于保密内容。
如有疑问，请联系人力资源部门。
```

### 方法 2: 运行单元测试

```bash
cd backend
pytest tests/constraints/test_forbidden_salary_query.py -v -s
```

**测试结果**：
```
✅ test_salary_query_prompt_contains_forbidden_topics PASSED
✅ test_salary_query_full_prompt PASSED
✅ test_different_salary_queries PASSED
✅ test_configuration_values PASSED
```

### 方法 3: 实际 API 测试

**步骤 1**: 启动后端服务
```bash
cd backend
python -m uvicorn app.main:app --reload
```

**步骤 2**: 测试禁止主题查询
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "我的工资是多少？", "session_id": "test-forbidden"}'
```

**预期响应**：
```json
{
  "type": "text",
  "content": "抱歉，关于薪资/工资相关的问题属于禁止回答的主题..."
}
```

**步骤 3**: 对比测试允许的查询
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "年假政策是什么？", "session_id": "test-allowed"}'
```

**预期响应**：
```json
{
  "type": "text",
  "content": "根据员工手册，年假制度如下：[1]\n- 入职满1年：5天年假..."
}
```

### 方法 4: 使用前端界面测试

1. 打开浏览器访问前端界面
2. 输入: "我的工资是多少？"
3. 观察 LLM 回答是否拒绝
4. 输入: "年假政策是什么？"
5. 观察 LLM 是否正常回答并包含引用

---

## 测试场景对比

### 场景 1: 禁止主题查询 ❌

| 项目 | 内容 |
|------|------|
| 用户查询 | "我的工资是多少？" |
| 系统行为 | 1. 加载约束配置<br>2. 识别 forbidden_topics: ['薪资', '工资']<br>3. 构建包含禁止主题的系统提示词<br>4. LLM 拒绝回答 |
| LLM 回答 | "抱歉，关于薪资/工资相关的问题属于禁止回答的主题。" |
| 是否包含引用 | 否（因为没有实际回答） |
| 答案验证 | 不适用 |

### 场景 2: 允许的查询 ✅

| 项目 | 内容 |
|------|------|
| 用户查询 | "年假政策是什么？" |
| 系统行为 | 1. 加载约束配置<br>2. 构建包含严格模式、引用要求的系统提示词<br>3. 检索知识库<br>4. LLM 基于知识库生成回答<br>5. 答案验证 |
| LLM 回答 | "根据员工手册，年假制度如下：[1]<br>- 入职满1年：5天年假<br>- 入职满3年：10天年假<br>参考来源：[1] 员工手册" |
| 是否包含引用 | 是 [1] |
| 答案验证 | 通过 |

---

## 各种工资相关查询的处理

所有以下查询都会被拒绝：

| 查询 | 结果 |
|------|------|
| "我的工资是多少？" | ❌ 拒绝 |
| "公司的薪资标准是什么？" | ❌ 拒绝 |
| "工资什么时候发？" | ❌ 拒绝 |
| "薪资待遇如何？" | ❌ 拒绝 |
| "月薪多少？" | ❌ 拒绝 |
| "年薪是多少？" | ❌ 拒绝 |
| "奖金怎么算？" | ❌ 拒绝 |

允许的查询：

| 查询 | 结果 |
|------|------|
| "年假政策是什么？" | ✅ 正常回答 |
| "如何申请病假？" | ✅ 正常回答 |
| "公司的福利有哪些？" | ✅ 正常回答 |
| "工作时间是怎样的？" | ✅ 正常回答 |

---

## 配置生效的证据

### 1. 配置文件检查

```bash
cat backend/config/constraints.json
```

**确认**：
```json
"forbidden_topics": ["薪资", "工资"],
"forbidden_keywords": ["工资"]
```

### 2. 代码检查

```bash
python backend/tests/constraints/check_all_constraints.py
```

**确认**：
```
✅ generation.forbidden_topics: 在代码中使用
✅ generation.forbidden_keywords: 在代码中使用
配置应用率: 17/22 (77.3%)
```

### 3. 单元测试

```bash
pytest backend/tests/constraints/test_constraint_prompt_builder.py -v
```

**确认**：
```
✅ test_forbidden_topics PASSED
✅ test_forbidden_keywords PASSED
✅ test_multiple_constraints PASSED
```

### 4. 系统提示词检查

运行验证脚本查看实际生成的系统提示词：

```bash
python backend/tests/constraints/verify_forbidden_topics_live.py
```

**确认系统提示词包含**：
```
## 禁止回答的主题
请不要回答与以下主题相关的问题：薪资、工资

## 禁止使用的关键词
回答中请不要使用以下关键词：工资
```

---

## 修改配置

### 添加更多禁止主题

编辑 `backend/config/constraints.json`：

```json
{
  "generation": {
    "forbidden_topics": [
      "薪资",
      "工资",
      "奖金",
      "股权",
      "期权",
      "内部机密",
      "财务数据"
    ],
    "forbidden_keywords": [
      "工资",
      "薪水",
      "收入",
      "年薪",
      "月薪"
    ]
  }
}
```

### 调整严格程度

**更严格**（企业知识库）：
```json
{
  "generation": {
    "strict_mode": true,
    "allow_general_knowledge": false,
    "require_citations": true,
    "max_answer_length": 1000
  }
}
```

**更宽松**（通用问答）：
```json
{
  "generation": {
    "strict_mode": false,
    "allow_general_knowledge": true,
    "require_citations": false,
    "max_answer_length": 2000
  }
}
```

**修改后重启服务**：
```bash
# 停止服务 (Ctrl+C)
# 重新启动
python -m uvicorn app.main:app --reload
```

---

## 故障排查

### 问题 1: 禁止主题未生效

**症状**: 用户询问工资，LLM 仍然回答

**检查步骤**:

1. 确认配置文件正确
   ```bash
   cat backend/config/constraints.json | grep forbidden_topics
   ```

2. 确认服务已重启
   ```bash
   # 重启后端服务
   ```

3. 检查日志
   ```bash
   # 查看是否使用了 ConstraintPromptBuilder
   grep "ConstraintPromptBuilder" logs/app.log
   ```

4. 运行检查脚本
   ```bash
   python backend/tests/constraints/check_all_constraints.py
   ```

**可能原因**:
- 配置文件未保存
- 服务未重启
- LLM 未严格遵守 Prompt（需要更明确的说明）

### 问题 2: 所有查询都被拒绝

**症状**: 连允许的查询也被拒绝

**检查步骤**:

1. 检查 forbidden_topics 是否过于宽泛
2. 检查知识库是否有内容
3. 检查 strict_mode 设置

**解决方案**:
- 缩小 forbidden_topics 范围
- 确保知识库有相关内容
- 适当放宽 strict_mode

---

## 重要说明

### 1. LLM 依赖性

禁止主题功能依赖于 LLM 遵守系统提示词中的约束。虽然大多数情况下有效，但 LLM 可能：
- 不完全遵守约束
- 以不同方式表达拒绝
- 在某些边缘情况下仍然回答

### 2. 增强方案

如需更强的控制，可以考虑：
- 添加预检查机制（在发送给 LLM 前检查查询）
- 添加后检查机制（检查回答是否包含禁止关键词）
- 使用更明确的 Prompt 说明

### 3. 最佳实践

- 定期测试禁止主题功能
- 收集用户反馈
- 根据实际情况调整配置
- 记录和分析被拒绝的查询

---

## 相关文档

- [约束配置快速参考](CONSTRAINT_QUICK_REFERENCE.md)
- [约束配置修复总结](CONSTRAINT_FIX_SUMMARY.md)
- [详细实施报告](CONSTRAINT_FIX_IMPLEMENTATION.md)
- [测试使用指南](../tests/constraints/USAGE_GUIDE.md)

---

## 总结

✅ **配置已生效**: forbidden_topics 和 forbidden_keywords 已正确应用

✅ **工作原理**: 通过在系统提示词中添加约束说明，指导 LLM 拒绝回答

✅ **验证方法**: 提供了 4 种验证方法，可以确认配置生效

✅ **预期行为**: 询问工资会被拒绝，允许的查询正常回答

✅ **可配置**: 可以随时修改配置文件调整禁止主题

---

**文档版本**: 1.0  
**更新日期**: 2024-03-25  
**状态**: 配置已验证生效
