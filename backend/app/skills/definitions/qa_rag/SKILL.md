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

## 适用场景

- 企业内部知识库问答
- 文档检索与摘要
- 政策制度咨询
