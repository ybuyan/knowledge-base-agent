---
name: qa_rag
display_name: RAG 问答
description: 基于知识库检索增强生成，回答用户问题
version: "1.0"
enabled: true
triggers:
  - user_question
pipeline:
  - step: embed_query
    processor: EmbeddingProcessor
    params: {}
  - step: retrieve_knowledge
    processor: VectorRetriever
    params:
      collection: documents
      top_k: 5
      score_threshold: 0.0
  - step: retrieve_history
    processor: VectorRetriever
    params:
      collection: conversations
      top_k: 3
  - step: build_context
    processor: ContextBuilder
    params:
      max_tokens: 4000
      include_sources: true
  - step: generate_answer
    processor: LLMGenerator
    params:
      prompt_template: qa_rag
      stream: false
  - step: store_conversation
    processor: VectorStore
    params:
      collection: conversations
output:
  return:
    - answer
    - sources
    - conversation_id
---

# RAG 问答 Skill

本 Skill 实现检索增强生成（Retrieval-Augmented Generation）问答流程。
Agent 在收到用户问题时，先从知识库中检索相关内容，再结合上下文生成准确答案。

## 工作流程

1. **向量化查询** — 将用户问题转换为向量表示，用于语义相似度检索
2. **检索知识库** — 从文档知识库中找出最相关的 5 个文本块
3. **检索对话历史** — 从历史对话中找出最相关的 3 条记录，保持上下文连贯
4. **构建上下文** — 整合检索结果，构建不超过 4000 tokens 的上下文，附带来源信息
5. **生成回答** — 调用 LLM，基于上下文生成答案
6. **存储对话** — 将本次问答存入对话历史，供后续检索

## 输出规范

- `answer` — 生成的回答文本
- `sources` — 引用来源列表，每项包含 `id`、`filename`、`content` 预览
- `conversation_id` — 本次对话的唯一标识

## 行为规则

- 只基于检索到的知识库内容回答，不编造信息
- 若知识库中无相关内容，明确告知用户
- 回答末尾标注引用来源，格式为 `[来源1][来源2]`
- 回答简洁、准确、专业

## 特殊场景处理

### 请假相关问题

当用户询问"我想请假"、"怎么请假"、"请假流程"等问题时，提供以下操作指引：

**假期类型**：
- 年假、病假、事假、婚假、产假、陪产假、高温假（仅限 6-9 月）

**申请流程**：
1. 发起请假申请
2. 直属上级审批
3. HR 备案

**申请入口**：
https://oa.company.com/leave

**申请模板**：
```
【年假申请】
申请人：xxx
时间：xxxx 年 xx 月 xx 日 - xxxx 年 xx 月 xx 日，共 X 天
事由：个人事务
```

**注意事项**：
- 请提前 3 天申请
- 审批时间：1-3 个工作日
- 紧急情况请先电话联系直属上级
- 高温假仅限 6-9 月申请

**回答格式**：
- 先询问用户需要申请什么类型的假期、多少天、什么时间
- 然后提供完整的操作指引（包含流程、入口、模板、注意事项）
- 不要直接帮用户提交申请，只提供指引让用户自己操作

## 适用场景

- 企业内部知识库问答
- 文档检索与摘要
- 政策制度咨询
