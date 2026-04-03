---
name: document_upload
display_name: 文档上传处理
description: 解析上传的文档，切分文本，向量化后存入知识库
version: "1.0"
enabled: true
triggers:
  - document_upload
pipeline:
  - step: parse_document
    processor: DocumentParser
    params:
      supported_formats:
        - pdf
        - docx
        - txt
        - xlsx
        - pptx
        - png
        - jpg
        - jpeg
        - gif
        - bmp
        - webp
  - step: split_text
    processor: TextSplitter
    params:
      chunk_size: 500
      chunk_overlap: 50
      split_by: paragraph
  - step: embed_chunks
    processor: EmbeddingProcessor
    params: {}
  - step: store_vectors
    processor: VectorStore
    params:
      collection: documents
      batch_size: 100
  - step: build_keyword_index
    processor: KeywordIndexBuilder
    params: {}
output:
  return:
    - document_id
    - chunk_count
    - status
---

# 文档上传处理 Skill

本 Skill 负责将用户上传的文档解析、切分、向量化，并存入知识库，
使文档内容可被 `qa_rag` Skill 检索和引用。

## 工作流程

1. **解析文档** — 从文件中提取纯文本内容，支持多种格式
2. **切分文本** — 将长文本切分为 500 字符的块，块间重叠 50 字符以保持上下文连贯
3. **向量化** — 将每个文本块转换为向量表示
4. **存储向量** — 批量写入向量数据库的 `documents` 集合，每批 100 条
5. **构建关键词索引** — 建立倒排索引，支持混合检索（向量 + 关键词）

## 支持的文件格式

| 格式 | 说明 |
|------|------|
| PDF | 逐页提取文本 |
| DOCX | Word 文档 |
| TXT | 纯文本 |
| XLSX | Excel，保留行结构 |
| PPTX | PowerPoint，逐页提取 |
| 图片 (PNG/JPG/GIF/BMP/WEBP) | OCR 提取文字（需安装 pytesseract） |

## 输出规范

- `document_id` — 文档唯一标识
- `chunk_count` — 切分后的文本块数量
- `status` — 处理状态（success / error）

## 行为规则

- 不支持的格式直接返回错误，不做静默处理
- 图片格式在 pytesseract 未安装时降级为空文本并记录警告
- 向量存储失败时回滚，不写入部分数据
