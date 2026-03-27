# 提示词整理报告

## 概述

本次整理将项目中分散在各个文件中的提示词统一迁移到 `backend/app/prompts/config.json` 配置文件中，实现统一管理。

## 整理日期

2026年3月26日

## 新增提示词

以下是本次整理新增到配置文件中的提示词：

### 1. 内容验证类 (validation)

#### forbidden_topic_check - 禁止主题检查
- **用途**: 检查用户查询是否涉及禁止主题
- **来源**: `backend/app/services/qa_agent.py`
- **变量**: `forbidden_topics`, `topics_list`, `query`

### 2. 快捷提问建议类 (suggestion)

#### suggestion_related - 相关追问建议
- **用途**: 生成与当前话题相关的追问
- **来源**: `backend/app/services/suggestion_generator.py`
- **变量**: `question`, `answer`

#### suggestion_deep - 深入探索建议
- **用途**: 生成深入探讨细节的问题
- **来源**: `backend/app/services/suggestion_generator.py`
- **变量**: `question`, `answer`

#### suggestion_compare - 对比分析建议
- **用途**: 生成对比分析类的问题
- **来源**: `backend/app/services/suggestion_generator.py`
- **变量**: `question`, `answer`

#### suggestion_practical - 实际应用建议
- **用途**: 生成关于实际应用的问题
- **来源**: `backend/app/services/suggestion_generator.py`
- **变量**: `question`, `answer`

#### suggestion_background - 背景原因建议
- **用途**: 生成关于背景或原因的问题
- **来源**: `backend/app/services/suggestion_generator.py`
- **变量**: `question`, `answer`

#### suggestion_default - 默认快捷提问
- **用途**: 生成通用的快捷提问建议
- **来源**: `backend/app/services/suggestion_generator.py`
- **变量**: `question`, `answer`, `count`

### 3. MCP服务器类 (mcp)

#### mcp_knowledge_query - MCP知识库查询提示
- **用途**: MCP服务器的知识库查询提示词模板
- **来源**: `backend/app/mcp/knowledge_server.py`
- **变量**: `topic`, `detail_level`

#### mcp_document_search - MCP文档搜索提示
- **用途**: MCP服务器的文档搜索提示词模板
- **来源**: `backend/app/mcp/document_server.py`
- **变量**: `query`, `file_type_hint`

## 已有提示词（保持不变）

以下提示词在之前已经整理到配置文件中：

1. **qa_rag** - RAG问答提示词
2. **strict_qa** - 严格知识库问答
3. **fallback** - 无结果兜底提示
4. **tool_router** - 工具路由决策
5. **tool_flow** - 工具流程回答
6. **query_optimize** - 查询优化
7. **query_enhance** - 查询增强
8. **query_optimizer_enhance** - 查询优化增强
9. **document_summary** - 文档摘要
10. **clarify_question** - 问题澄清
11. **conversation_summary** - 对话摘要
12. **default_assistant** - 默认助手

## 新增分类

本次整理新增了以下提示词分类：

- **validation** - 内容验证
- **suggestion** - 快捷提问建议
- **mcp** - MCP服务器

## 配置文件结构

```json
{
  "version": "2.1",
  "description": "统一提示词配置文件 - 整理所有项目中使用的提示词",
  "prompts": {
    // 各个提示词配置
  },
  "categories": {
    // 分类定义
  }
}
```

## 使用方式

### 1. 获取提示词

```python
from app.prompts.manager import prompt_manager

# 获取提示词配置
prompt_config = prompt_manager.get("forbidden_topic_check")

# 渲染提示词
result = prompt_manager.render("forbidden_topic_check", {
    "forbidden_topics": "薪资、工资",
    "topics_list": "1. 薪资\n2. 工资",
    "query": "我的工资是多少"
})
```

### 2. 获取系统提示词

```python
system_prompt = prompt_manager.get_system_prompt("strict_qa")
```

### 3. 按分类列出提示词

```python
suggestions = prompt_manager.list_by_category("suggestion")
```

## 代码迁移建议

### 已完成的迁移

以下文件已经完成提示词迁移，使用 `prompt_manager` 替代硬编码：

1. **backend/app/services/qa_agent.py** ✅
   - ✅ 已迁移 `forbidden_topic_check` 提示词
   - ✅ 使用 `prompt_manager.render("forbidden_topic_check", {...})`
   - ✅ 保留了合理的回退默认值

2. **backend/app/services/suggestion_generator.py** ✅
   - ✅ 已迁移所有类型的快捷提问提示词
   - ✅ 使用类型到提示词ID的映射 `TYPE_TO_PROMPT_ID`
   - ✅ 所有 `_generate_by_type` 和 `_generate_default` 方法已更新

### 迁移示例

#### 迁移前（硬编码）
```python
check_prompt = f"""你是一个内容审核助手。请判断用户的查询是否涉及以下禁止主题：{topics_str}

禁止主题包括：
- 直接提及这些词汇
...

用户查询：{query}
"""
```

#### 迁移后（使用配置）
```python
from app.prompts.manager import prompt_manager

prompt_result = prompt_manager.render("forbidden_topic_check", {
    "forbidden_topics": topics_str,
    "query": query
})

messages = [
    {'role': 'system', 'content': prompt_result.get('system', '')},
    {'role': 'user', 'content': prompt_result.get('user', '')}
]
```

### 需要更新的文件（可选）

以下文件已经在使用 `prompt_manager`，但有硬编码的回退默认值（这是合理的设计）：

1. **backend/app/api/routes/chat.py**
   - 已使用 `prompt_manager.get_system_prompt("query_optimize")`
   - 有回退默认值（合理）

2. **backend/app/services/hybrid_memory.py**
   - 已使用 `prompt_manager.get_system_prompt("default_assistant")`
   - 有回退默认值（合理）

## 优势

1. **统一管理**: 所有提示词集中在一个配置文件中
2. **易于维护**: 修改提示词无需改动代码
3. **版本控制**: 配置文件有版本号，便于追踪变更
4. **分类清晰**: 按功能分类，便于查找和管理
5. **可扩展**: 支持动态添加新的提示词和分类
6. **热重载**: 支持运行时重新加载配置

## 统计信息

- **总提示词数量**: 22个
- **新增提示词**: 9个
- **提示词分类**: 9个
- **配置文件版本**: 2.1

## 下一步工作

1. 更新相关代码文件，使用 `prompt_manager` 替代硬编码提示词
2. 添加单元测试验证提示词配置的正确性
3. 编写提示词使用文档和最佳实践指南
4. 考虑添加提示词版本管理和A/B测试功能
