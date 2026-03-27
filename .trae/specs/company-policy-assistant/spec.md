# 公司制度问答与流程指引助手 - 需求规格说明书

## Why

企业需要为员工提供准确、及时的公司制度咨询服务。通过构建基于RAG技术的智能问答助手，员工可以随时随地获取关于员工手册、请假制度、考勤规范、报销流程等信息的准确回答，系统能够标注答案来源，确保信息的可追溯性。

## What Changes

- **新增** 文档上传Agent：负责文档解析、切分、向量化和存储
- **新增** 问答Agent：负责知识检索、多轮对话管理和答案生成
- **新增** ChromaDB向量存储：存储文档知识库和对话历史
- **新增** 现代化前端界面：Vue 3 + TypeScript构建，主题色 #e0301e

## Impact

- **受影响系统**: 后端API服务、前端Web应用、向量数据库
- **关键文件**: 
  - 后端: `backend/app/` 目录
  - 前端: `frontend/src/` 目录

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Vue 3)                              │
│  ┌──────────────────┐    ┌──────────────────────────────────┐   │
│  │  文档管理页面     │    │        问答聊天界面               │   │
│  │  (文档上传.png)   │    │        (问答界面.png)             │   │
│  └────────┬─────────┘    └────────────────┬─────────────────┘   │
└───────────┼───────────────────────────────┼─────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                        后端 API (FastAPI)                          │
│  ┌──────────────────┐    ┌──────────────────────────────────┐    │
│  │  文档上传 API     │    │         问答 API                  │    │
│  └────────┬─────────┘    └────────────────┬─────────────────┘    │
└───────────┼───────────────────────────────┼──────────────────────┘
            │                               │
            ▼                               ▼
┌───────────────────────────┐    ┌─────────────────────────────────┐
│    文档上传 Agent          │    │        问答 Agent                │
│  ┌─────────────────────┐  │    │  ┌───────────────────────────┐  │
│  │ 1. 文档解析          │  │    │  │ 1. 问题向量化             │  │
│  │ 2. 文本切分          │  │    │  │ 2. 知识库检索             │  │
│  │ 3. 向量化           │  │    │  │ 3. 对话历史检索           │  │
│  │ 4. 存储到ChromaDB   │  │    │  │ 4. 上下文组装             │  │
│  └─────────────────────┘  │    │  │ 5. LLM生成回答            │  │
│                           │    │  │ 6. 对话历史存储           │  │
└─────────────┬─────────────┘    │  └───────────────────────────┘  │
              │                  └───────────────┬─────────────────┘
              │                                  │
              └──────────────┬───────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ChromaDB 向量存储                              │
│  ┌─────────────────────┐    ┌─────────────────────────────┐     │
│  │   文档知识库         │    │      对话历史存储            │     │
│  │  - 文档向量          │    │  - 问题向量                  │     │
│  │  - 文本块            │    │  - 回答向量                  │     │
│  │  - 元数据            │    │  - 会话ID                    │     │
│  └─────────────────────┘    └─────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## ADDED Requirements

### Requirement 1: 文档上传Agent

文档上传Agent负责接收、解析、切分、向量化和存储制度文档。

#### Scenario 1.1: 文档上传与解析
- **GIVEN** 用户上传PDF/DOCX/TXT文件
- **WHEN** 文档上传Agent接收文件
- **THEN** 提取文档文本内容
- **AND** 识别文档结构（标题、段落、列表）

#### Scenario 1.2: 文本切分
- **GIVEN** 文档文本已提取
- **WHEN** Agent执行切分
- **THEN** 按语义段落切分为适当大小的文本块
- **AND** 保留上下文关联信息
- **AND** 添加文档元数据（文件名、页码、章节）

#### Scenario 1.3: 向量化与存储
- **GIVEN** 文本块已生成
- **WHEN** Agent执行向量化
- **THEN** 使用Embedding模型生成向量
- **AND** 存储到ChromaDB文档知识库集合
- **AND** 返回处理状态和文档ID

### Requirement 2: 问答Agent

问答Agent负责检索知识库、管理多轮对话、生成有依据的回答。

#### Scenario 2.1: 问题理解与向量化
- **GIVEN** 用户输入问题
- **WHEN** 问答Agent接收问题
- **THEN** 理解问题意图
- **AND** 将问题转换为向量表示

#### Scenario 2.2: 知识库检索
- **GIVEN** 问题向量已生成
- **WHEN** Agent执行检索
- **THEN** 从ChromaDB文档知识库检索相关文档片段
- **AND** 返回Top-K相关结果
- **AND** 计算相似度分数

#### Scenario 2.3: 对话历史检索
- **GIVEN** 用户进行多轮对话
- **WHEN** Agent需要上下文
- **THEN** 从ChromaDB对话历史集合检索相关历史对话
- **AND** 组装上下文信息
- **AND** 保持对话连贯性

#### Scenario 2.4: 答案生成
- **GIVEN** 检索结果和对话历史
- **WHEN** Agent调用LLM
- **THEN** 基于检索内容生成回答
- **AND** 标注引用来源[1][2]
- **AND** 在知识不足时明确说明

#### Scenario 2.5: 对话历史存储
- **GIVEN** 一轮对话完成
- **WHEN** Agent存储对话
- **THEN** 将问题和回答向量化
- **AND** 存储到ChromaDB对话历史集合
- **AND** 关联会话ID

### Requirement 3: ChromaDB向量存储

系统使用ChromaDB作为统一的向量存储，分别管理文档知识库和对话历史。

#### Scenario 3.1: 文档知识库集合
- **GIVEN** 文档上传Agent处理文档
- **WHEN** 存储文档向量
- **THEN** 存储到`documents`集合
- **AND** 包含字段：id, embedding, document, metadata
- **AND** metadata包含：filename, page, chunk_index, upload_time

#### Scenario 3.2: 对话历史集合
- **GIVEN** 问答Agent完成对话
- **WHEN** 存储对话历史
- **THEN** 存储到`conversations`集合
- **AND** 包含字段：id, embedding, document, metadata
- **AND** metadata包含：session_id, role, timestamp

#### Scenario 3.3: 混合检索
- **GIVEN** 用户提问
- **WHEN** 执行检索
- **THEN** 同时检索文档知识库和对话历史
- **AND** 合并检索结果
- **AND** 按相关性排序

### Requirement 4: 前端界面

#### 4.1 文档管理页面 (参考"文档上传.png")
- **主题色**: #e0301e
- **功能**: 拖拽上传、文档列表、状态管理

#### 4.2 问答聊天界面 (参考"问答界面.png")
- **主题色**: #e0301e
- **布局**: 三栏布局
- **功能**: 流式响应、引用展示、会话管理

---

## Technical Requirements

### Backend
- **Framework**: Python 3.11+ + FastAPI
- **AI/ML**: LangChain for Agent orchestration
- **Vector DB**: ChromaDB (双集合: documents, conversations)
- **Embedding**: BGE / text-embedding-3
- **LLM**: OpenAI API compatible
- **Database**: SQLite (元数据) + ChromaDB (向量)

### Frontend
- **Framework**: Vue 3 + Composition API
- **Language**: TypeScript
- **Build**: Vite
- **UI Library**: Element Plus
- **State**: Pinia
- **Router**: Vue Router 4
- **HTTP**: Axios + SSE
- **Markdown**: markdown-it

### 主题色配置
```css
--primary-color: #e0301e;
--primary-light: #ff4d3a;
--primary-dark: #b52616;
```

---

## Agent 设计详情

### 文档上传Agent

```python
class DocumentUploadAgent:
    """文档上传Agent - 负责文档处理和向量化存储"""
    
    def __init__(self, chroma_client, embedding_model):
        self.chroma = chroma_client
        self.embedding = embedding_model
        self.collection = chroma.get_collection("documents")
    
    async def process_document(self, file) -> DocumentResult:
        # 1. 解析文档
        text = await self.parse_document(file)
        # 2. 切分文本
        chunks = self.split_text(text)
        # 3. 向量化并存储
        for chunk in chunks:
            embedding = self.embedding.embed(chunk.text)
            self.collection.add(
                ids=[chunk.id],
                embeddings=[embedding],
                documents=[chunk.text],
                metadatas=[chunk.metadata]
            )
        return DocumentResult(status="success", chunks=len(chunks))
```

### 问答Agent

```python
class QAAgent:
    """问答Agent - 负责检索和答案生成"""
    
    def __init__(self, chroma_client, embedding_model, llm):
        self.chroma = chroma_client
        self.embedding = embedding_model
        self.llm = llm
        self.doc_collection = chroma.get_collection("documents")
        self.conv_collection = chroma.get_collection("conversations")
    
    async def answer(self, question: str, session_id: str) -> Answer:
        # 1. 问题向量化
        question_embedding = self.embedding.embed(question)
        
        # 2. 检索文档知识库
        doc_results = self.doc_collection.query(
            query_embeddings=[question_embedding],
            n_results=5
        )
        
        # 3. 检索对话历史
        conv_results = self.conv_collection.query(
            query_embeddings=[question_embedding],
            where={"session_id": session_id},
            n_results=3
        )
        
        # 4. 组装上下文
        context = self.build_context(doc_results, conv_results)
        
        # 5. LLM生成回答
        answer = await self.llm.generate(question, context)
        
        # 6. 存储对话历史
        self.store_conversation(session_id, question, answer)
        
        return answer
```

---

## User Stories

- 作为员工，我希望快速查询公司制度，获得准确答案和依据
- 作为HR，我希望上传管理制度文档，维护知识库内容
- 作为用户，我希望系统能记住我们的对话上下文

---

## Development Milestones

### Week 1: 基础架构
- 后端项目搭建 (FastAPI)
- ChromaDB配置 (双集合)
- 前端项目搭建 (Vue 3 + Element Plus + 主题色)

### Week 2: 文档上传Agent
- 文档解析和切分
- 向量化服务
- ChromaDB文档集合存储

### Week 3: 问答Agent
- 知识库检索
- 对话历史检索
- LLM集成和答案生成
- 对话历史存储

### Week 4: 前端界面
- 文档管理页面
- 聊天界面 (三栏布局)
- 流式响应展示

### Week 5: 集成测试
- 端到端测试
- 性能优化
- Bug修复

---

## Success Criteria

- [ ] 支持PDF、DOCX、TXT上传解析
- [ ] ChromaDB双集合正常工作
- [ ] 文档上传Agent独立运行
- [ ] 问答Agent独立运行
- [ ] 多轮对话上下文检索准确
- [ ] 问答准确率 > 80%
- [ ] 界面使用主题色 #e0301e
- [ ] 响应时间 < 3秒
- [ ] 支持流式打字机效果
