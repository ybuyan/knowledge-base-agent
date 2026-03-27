# 约束配置快速参考

## 配置文件位置

```
backend/config/constraints.json
```

## 配置结构

```json
{
  "constraints": {
    "retrieval": { ... },
    "generation": { ... },
    "validation": { ... },
    "fallback": { ... }
  },
  "suggest_questions": { ... }
}
```

---

## 生成约束 (generation) - 100% 已应用 ✅

### strict_mode - 严格模式

**配置**:
```json
"strict_mode": true
```

**效果**:
- 只基于知识库内容回答
- 不添加推测或假设
- 信息不完整时明确说明

**使用场景**: 需要高度准确的回答，如法律、医疗、金融等领域

---

### allow_general_knowledge - 允许通用知识

**配置**:
```json
"allow_general_knowledge": false
```

**效果**:
- `false`: 严格限制只使用知识库内容，不使用 LLM 训练数据
- `true`: 优先使用知识库，可适当补充通用知识

**使用场景**: 
- `false`: 企业内部知识库，需要严格控制信息来源
- `true`: 通用问答，可以补充背景知识

---

### require_citations - 需要引用

**配置**:
```json
"require_citations": true
```

**效果**:
- 回答中必须包含引用标记 [1]、[2] 等
- 每个关键信息都有对应引用

**使用场景**: 需要追溯信息来源，提高可信度

---

### max_answer_length - 最大回答长度

**配置**:
```json
"max_answer_length": 1000
```

**效果**:
- 限制回答的最大字符数
- 超过限制自动截断并添加 "..."
- 记录警告日志

**使用场景**: 控制回答长度，避免过长的回答

---

### forbidden_topics - 禁止主题

**配置**:
```json
"forbidden_topics": ["薪资", "工资", "奖金"]
```

**效果**:
- 在 Prompt 中明确告知 LLM 不要回答这些主题
- LLM 会拒绝回答相关问题

**使用场景**: 敏感话题、隐私信息、未公开信息等

**示例**:
```
用户: "公司的工资标准是什么？"
助手: "抱歉，关于薪资相关的问题属于禁止回答的主题。"
```

---

### forbidden_keywords - 禁止关键词

**配置**:
```json
"forbidden_keywords": ["工资", "薪水", "收入"]
```

**效果**:
- 在 Prompt 中明确告知 LLM 不要使用这些关键词
- 回答中应避免包含这些词汇

**使用场景**: 避免使用特定词汇，如敏感词、竞品名称等

---

## 检索约束 (retrieval) - 60% 已应用

### enabled - 是否启用检索约束 ✅

**配置**:
```json
"enabled": true
```

**效果**: 启用或禁用检索约束功能

---

### min_similarity_score - 最小相似度阈值 ✅

**配置**:
```json
"min_similarity_score": 0.3
```

**效果**: 过滤低于此相似度的文档

---

### max_relevant_docs - 最大相关文档数 ✅

**配置**:
```json
"max_relevant_docs": 5
```

**效果**: 限制检索返回的最大文档数量

---

### min_relevant_docs - 最小相关文档数 ⚠️

**配置**:
```json
"min_relevant_docs": 1
```

**效果**: 检查检索到的文档数量，不足时记录警告

**状态**: 已添加检查但未强制执行

---

### content_coverage_threshold - 内容覆盖阈值 ⚠️

**配置**:
```json
"content_coverage_threshold": 0.5
```

**效果**: 检查检索内容是否充分覆盖查询

**状态**: 未实施

---

## 验证约束 (validation) - 100% 已应用 ✅

### enabled - 是否启用验证 ✅

**配置**:
```json
"enabled": true
```

**效果**: 启用或禁用答案验证功能

---

### check_source_attribution - 检查来源归属 ✅

**配置**:
```json
"check_source_attribution": true
```

**效果**: 验证回答是否包含引用标记

---

### min_confidence_score - 最小置信度 ✅

**配置**:
```json
"min_confidence_score": 0.5
```

**效果**: 
- 置信度低于 0.5 时标记为无效
- 置信度低于 0.3 时附加警告信息

---

### hallucination_detection - 幻觉检测 ✅

**配置**:
```json
"hallucination_detection": true
```

**效果**: 检测回答中的不确定性词汇和数字

---

## 兜底配置 (fallback) - 50% 已应用

### no_result_message - 无结果消息 ✅

**配置**:
```json
"no_result_message": "未找到相关信息"
```

**效果**: 无检索结果时返回的消息

---

### contact_info - 联系信息 ✅

**配置**:
```json
"contact_info": "如有疑问，请联系：\n电话：12345\n邮箱：support@company.com"
```

**效果**: 在兜底消息中显示联系信息

---

### suggest_similar - 建议相似问题 ⚠️

**配置**:
```json
"suggest_similar": true
```

**效果**: 控制是否在无结果时建议相似问题

**状态**: 未实施

---

### suggest_contact - 建议联系方式 ⚠️

**配置**:
```json
"suggest_contact": true
```

**效果**: 控制是否在无结果时显示联系方式

**状态**: 未实施

---

## 建议问题配置 (suggest_questions) - 67% 已应用

### enabled - 是否启用建议问题 ✅

**配置**:
```json
"enabled": true
```

**效果**: 启用或禁用建议问题生成

---

### count - 建议问题数量 ✅

**配置**:
```json
"count": 3
```

**效果**: 控制生成的建议问题数量

---

### types - 建议问题类型 ⚠️

**配置**:
```json
"types": ["相关追问", "深入探索", "对比分析"]
```

**效果**: 定义建议问题的类型

**状态**: 未实施

---

## 常见配置场景

### 场景 1: 严格的企业知识库

```json
{
  "generation": {
    "strict_mode": true,
    "allow_general_knowledge": false,
    "require_citations": true,
    "max_answer_length": 1000,
    "forbidden_topics": ["薪资", "工资", "内部机密"],
    "forbidden_keywords": ["工资", "薪水"]
  },
  "validation": {
    "enabled": true,
    "check_source_attribution": true,
    "min_confidence_score": 0.7,
    "hallucination_detection": true
  }
}
```

**特点**: 高度严格，只使用知识库，强制引用，高置信度要求

---

### 场景 2: 通用问答助手

```json
{
  "generation": {
    "strict_mode": false,
    "allow_general_knowledge": true,
    "require_citations": false,
    "max_answer_length": 2000,
    "forbidden_topics": [],
    "forbidden_keywords": []
  },
  "validation": {
    "enabled": true,
    "check_source_attribution": false,
    "min_confidence_score": 0.3,
    "hallucination_detection": true
  }
}
```

**特点**: 较宽松，可使用通用知识，不强制引用，低置信度要求

---

### 场景 3: 客户服务助手

```json
{
  "generation": {
    "strict_mode": true,
    "allow_general_knowledge": false,
    "require_citations": true,
    "max_answer_length": 500,
    "forbidden_topics": ["价格", "折扣"],
    "forbidden_keywords": []
  },
  "fallback": {
    "no_result_message": "抱歉，我没有找到相关信息",
    "suggest_similar": true,
    "suggest_contact": true,
    "contact_info": "如需帮助，请联系客服：400-123-4567"
  }
}
```

**特点**: 严格但友好，提供联系方式，建议相似问题

---

## 检查配置应用情况

```bash
# 运行全面检查
python backend/tests/constraints/check_all_constraints.py

# 运行快速测试
pytest backend/tests/constraints/quick_test.py -v

# 运行约束提示词构建器测试
pytest backend/tests/constraints/test_constraint_prompt_builder.py -v
```

---

## 修改配置后的操作

1. 修改 `backend/config/constraints.json`
2. 重启后端服务
3. 运行检查脚本验证
4. 进行功能测试

---

## 故障排查

### 问题: 配置未生效

**检查步骤**:
1. 确认配置文件路径正确
2. 确认 JSON 格式正确
3. 重启后端服务
4. 运行检查脚本

### 问题: 禁止主题未生效

**可能原因**:
- LLM 未严格遵守 Prompt 指令
- 需要在 Prompt 中更明确地说明

**解决方案**:
- 增强 Prompt 说明
- 考虑添加预检查机制

### 问题: 答案长度限制未生效

**检查步骤**:
1. 确认 `max_answer_length` 配置正确
2. 检查日志中是否有截断警告
3. 验证代码中的长度检查逻辑

---

## 相关文档

- [详细实施报告](CONSTRAINT_FIX_IMPLEMENTATION.md)
- [总结文档](CONSTRAINT_FIX_SUMMARY.md)
- [完整修复计划](COMPLETE_CONSTRAINT_FIX_PLAN.md)
- [测试使用指南](../tests/constraints/USAGE_GUIDE.md)

---

**文档版本**: 1.0  
**更新日期**: 2024-03-25  
**状态**: 当前配置应用率 77.3%
