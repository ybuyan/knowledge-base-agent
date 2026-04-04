# 公司制度问答与流程指引助手

<div align="center">

!\[Version]\(https\://img.shields.io/badge/version-1.0.0-blue.svg null)
!\[Python]\(https\://img.shields.io/badge/python-3.10+-green.svg null)
!\[FastAPI]\(https\://img.shields.io/badge/FastAPI-0.104+-orange.svg null)
!\[Vue]\(https\://img.shields.io/badge/Vue-3.3+-brightgreen.svg null)
!\[License]\(https\://img.shields.io/badge/license-MIT-red.svg null)

**基于AI Agent架构的企业级知识库问答系统**

[功能特性](#功能特性) • [快速开始](#快速开始) • [架构设计](#架构设计) • [API文档](#api文档) • [部署指南](#部署指南)

</div>

***

## 📋 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [架构设计](#架构设计)
- [技术栈](#技术栈)
- [快速开始](#快速开始)
- [使用指南](#使用指南)
- [API文档](#api文档)
- [开发指南](#开发指南)
- [部署指南](#部署指南)
- [性能优化](#性能优化)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

***

## 项目简介

本项目是一个基于**AI Agent架构**的企业级知识库问答系统，旨在为公司员工提供智能化的制度咨询和流程指引服务。系统采用先进的AI Agent技术，实现了**自主决策**、**工具调用**、**多智能体协作**等核心能力。

### 核心亮点

- 🤖 **智能Agent架构**: 基于LLM的自主决策机制，智能路由工具调用和知识检索
- 🔍 **混合检索系统**: 结合向量检索和BM25算法，提供高精度的知识检索
- 💬 **流式响应**: 支持SSE流式输出，提升用户体验
- ⏹️ **中止回答**: 用户可随时中止回答生成，红色脉冲动画按钮
- 🛠️ **可扩展工具系统**: 插件化的工具注册机制，轻松扩展系统能力
- 📚 **知识库管理**: 自动文档解析、向量化、索引构建
- 🔐 **严格约束**: 防止LLM幻觉，确保回答基于知识库内容
- ⚙️ **约束配置**: 可视化配置检索、生成、验证约束

***

## 功能特性

### 1. 智能问答

- ✅ **自然语言理解**: 支持自然语言查询，无需关键词匹配
- ✅ **多轮对话**: 支持上下文记忆，理解对话历史
- ✅ **来源追溯**: 每个回答都标注引用来源，可追溯验证
- ✅ **智能路由**: 自动判断使用工具调用还是知识检索

### 2. 知识库管理

- ✅ **多格式支持**: 支持PDF、DOCX、DOC等常见文档格式
- ✅ **自动解析**: 自动提取文档内容和元数据
- ✅ **向量索引**: 自动构建向量索引，支持语义检索
- ✅ **增量更新**: 支持文档增量添加和更新

### 3. Agent能力

- ✅ **自主决策**: LLM智能判断是否需要调用工具
- ✅ **工具调用**: 支持多工具并行调用
- ✅ **任务规划**: Skill引擎支持流水线式任务编排
- ✅ **多Agent协作**: 中间件机制实现Agent间协作

### 4. 性能优化

- ✅ **多级缓存**: Tool结果缓存、查询优化缓存
- ✅ **并行执行**: 异步IO，支持并发处理
- ✅ **流式输出**: 降低首字节响应时间
- ✅ **性能监控**: 完整的性能指标统计

### 5. 约束配置系统

- ✅ **检索约束**: 最小相似度、文档数量限制
- ✅ **生成约束**: 严格模式、禁止主题/关键词
- ✅ **验证约束**: 来源检查、置信度、幻觉检测
- ✅ **兜底策略**: 自定义无结果提示、联系信息

### 6. 用户体验增强

- ✅ **中止回答**: 随时中止生成中的回答
- ✅ **数据持久化**: 对话自动保存，刷新不丢失
- ✅ **来源追溯**: 回答标注引用来源
- ✅ **快捷提问**: 智能生成追问建议
- ✅ **相关链接**: 自动匹配相关外部链接
- ✅ **查询优化**: 一键优化查询，支持撤回

***

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端展示层 (Vue 3)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   ChatView   │  │ DocumentsView│  │  Constraints │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API网关层 (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Chat Routes │  │Document Routes│  │ Health Routes│          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent核心层                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    QAAgent (协调Agent)                    │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │
│  │  │ Tool Router │  │ RAG Engine  │  │ LLM Client  │     │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Tool Execution Layer                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │ToolExecutor │  │ Middleware  │  │ ToolCache   │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     基础设施层                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  ChromaDB   │  │   MongoDB   │  │  Embeddings │             │
│  │  (向量存储)  │  │  (会话存储)  │  │  (文本向量化)│             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ Memory Mgr  │  │ Query Cache │  │ Performance │             │
│  │  (记忆管理)  │  │  (查询缓存)  │  │  Monitor    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. QAAgent (问答协调Agent)

QAAgent是系统的核心协调器，负责整个问答流程的编排：

```python
用户查询 → 查询优化 → Tool决策 → [Tool路径 | RAG路径] → 流式输出
```

**核心能力**:

- 查询优化: 基于知识库内容优化用户查询
- 自主决策: 智能判断是否需要调用工具
- 结果整合: 统一处理不同路径的返回结果

#### 2. Tool系统

可扩展的工具调用框架：

- **ToolRegistry**: 工具注册表，支持装饰器注册
- **ToolExecutor**: 工具执行器，支持缓存和中间件
- **ToolMiddleware**: 中间件机制，支持日志、重试等

#### 3. RAG系统

检索增强生成系统：

- **HybridRetriever**: 混合检索器（向量+BM25）
- **KBQueryOptimizer**: 知识库查询优化器
- **StrictQAPrompt**: 严格约束提示工程

***

## 技术栈

### 后端技术

| 技术        | 版本     | 用途      |
| --------- | ------ | ------- |
| Python    | 3.10+  | 核心开发语言  |
| FastAPI   | 0.109+ | Web框架   |
| LangChain | 0.1+   | LLM应用框架 |
| ChromaDB  | 0.4+   | 向量数据库   |
| MongoDB   | 5.0+   | 文档数据库   |
| Pydantic  | 2.5+   | 数据验证    |
| asyncio   | -      | 异步IO    |
| Motor     | 3.3+   | 异步MongoDB驱动 |
| watchdog  | 3.0+   | 文件监控    |
| jieba     | 0.42+  | 中文分词    |
| reportlab | 4.0+   | PDF生成   |

### 前端技术

| 技术         | 版本   | 用途   |
| ---------- | ---- | ---- |
| Vue        | 3.5+ | 前端框架 |
| TypeScript | 5.9+ | 类型安全 |
| Vite       | 8.0+ | 构建工具 |
| Pinia      | 3.0+ | 状态管理 |
| Vue Router | 5.0+ | 路由管理 |
| Element Plus | 2.13+ | UI组件库 |
| markdown-it | 14.1+ | Markdown渲染 |

### AI/ML技术

| 技术              | 用途     |
| --------------- | ------ |
| 通义千问 (Qwen)     | 大语言模型  |
| Text Embeddings | 文本向量化  |
| BM25            | 关键词检索  |
| RAG             | 检索增强生成 |
| CrossEncoder    | 重排序模型  |
| MCP Protocol    | 工具协议标准 |

***

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MongoDB 5.0+
- 至少4GB可用内存

### 安装步骤

#### 1. 克隆项目

```bash
git clone <repository-url>
cd AI-assistent
```

#### 2. 后端配置

```bash
# 进入后端目录
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，填入必要的配置
```

#### 3. 前端配置

```bash
# 进入前端目录
cd ../frontend

# 安装依赖
npm install

# 配置环境变量（可选）
# 创建.env.local文件配置API地址
```

#### 4. 启动服务

本项目提供多种启动方式，可根据实际需求选择。

##### 方式一：使用启动脚本（推荐）

**Windows PowerShell脚本**：

```powershell
# 在项目根目录执行
.\start-services.ps1
```

**Windows BAT脚本**：

```bash
# 在项目根目录执行
.\start-services.bat
```

启动脚本会自动启动：

- ✅ 后端服务（端口8001）
- ✅ 前端服务（端口5173）
- ✅ 文件监听服务（自动扫描docs目录）

##### 方式二：手动启动各个服务

**步骤1：启动MongoDB（如果未运行）**

```bash
# Windows
mongod --dbpath C:\data\db

# Linux/Mac
mongod --dbpath /data/db
```

**步骤2：启动后端服务**

```bash
cd backend

# 方式A：使用Python主文件
python main.py

# 方式B：使用uvicorn命令
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload

# 方式C：指定配置启动
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload --workers 4
```

**步骤3：启动前端服务**

```bash
cd frontend

# 开发模式
npm run dev

# 生产模式构建
npm run build
npm run preview
```

**步骤4：启动文件监听服务（可选）**

文件监听服务会自动监控`docs`目录，当检测到文件变化时自动更新知识库。

```bash
cd backend

# 默认启动（使用默认配置）
python scripts/file_watcher.py

# 指定配置文件
python scripts/file_watcher.py --config scripts/config/watch.json

# 后台运行（Linux/Mac）
nohup python scripts/file_watcher.py > logs/watcher.log 2>&1 &

# Windows后台运行
start /B python scripts/file_watcher.py
```

##### 方式三：使用进程管理工具（生产环境推荐）

**使用PM2管理进程**：

```bash
# 安装PM2
npm install -g pm2

# 启动后端服务
pm2 start "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8001" --name qa-backend

# 启动文件监听服务
pm2 start "cd backend && python scripts/file_watcher.py" --name file-watcher

# 查看服务状态
pm2 status

# 查看日志
pm2 logs

# 停止所有服务
pm2 stop all
```

**使用Supervisor（Linux）**：

```bash
# 安装Supervisor
sudo apt-get install supervisor

# 创建配置文件
sudo nano /etc/supervisor/conf.d/qa-assistant.conf

# 配置内容
[program:qa-backend]
directory=/path/to/AI-assistent/backend
command=uvicorn app.main:app --host 0.0.0.0 --port 8001
autostart=true
autorestart=true
stderr_logfile=/var/log/qa-backend.err.log
stdout_logfile=/var/log/qa-backend.out.log

[program:file-watcher]
directory=/path/to/AI-assistent/backend
command=python scripts/file_watcher.py
autostart=true
autorestart=true
stderr_logfile=/var/log/file-watcher.err.log
stdout_logfile=/var/log/file-watcher.out.log

# 重新加载配置
sudo supervisorctl reread
sudo supervisorctl update

# 查看状态
sudo supervisorctl status
```

#### 5. 服务端口说明

| 服务      | 端口    | 说明        |
| ------- | ----- | --------- |
| 前端服务    | 5173  | Vue开发服务器  |
| 后端API   | 8001  | FastAPI服务 |
| MongoDB | 27017 | 数据库服务     |

#### 6. 访问应用

启动成功后，可以通过以下地址访问：

- 🌐 **前端地址**: <http://localhost:5173>
- 📚 **API文档**: <http://localhost:8001/docs>
- 📖 **API文档（ReDoc）**: <http://localhost:8001/redoc>
- ❤️ **健康检查**: <http://localhost:8001/health>

#### 7. 验证服务状态

**检查后端服务**：

```bash
# 健康检查
curl http://localhost:8001/health

# 或使用浏览器访问
# http://localhost:8001/health
```

**检查前端服务**：

```bash
# 访问前端页面
curl http://localhost:5173

# 或直接在浏览器打开
# http://localhost:5173
```

**检查文件监听服务**：

```bash
# 查看日志
tail -f backend/data/logs/watcher_*.log

# Windows查看日志
type backend\data\logs\watcher_*.log
```

***

## 使用指南

### 1. 上传文档

1. 访问"文档管理"页面
2. 点击"上传文档"按钮
3. 选择PDF、DOCX或DOC文件
4. 系统自动解析并建立索引

### 2. 开始问答

1. 访问"问答助手"页面
2. 在输入框中输入问题
3. 系统自动检索知识库并生成回答
4. 查看引用来源，验证答案准确性

### 3. 管理会话

- 创建新会话: 点击"新建会话"
- 切换会话: 点击会话列表中的会话
- 删除会话: 点击会话的删除按钮
- 归档会话: 点击归档按钮

### 4. 约束配置

在"设置"页面可以配置：

- 禁止回答的主题
- 禁止使用的关键词
- Fallback消息模板
- 联系方式信息

***

## API文档

### 核心接口

#### 1. 问答接口

**POST** `/api/chat/v2/ask/stream`

流式问答接口，返回SSE格式数据。

**请求体**:

```json
{
  "question": "什么是年假？",
  "session_id": "session-uuid"
}
```

**响应格式**:

```
data: {"type": "text", "content": "年假是..."}
data: {"type": "suggested_questions", "questions": ["年假有多少天？", "如何申请年假？"]}
data: {"type": "related_links", "links": [{"title": "请假制度", "url": "..."}]}
data: {"type": "done", "sources": [...]}
data: {"type": "warning", "message": "消息保存失败..."}
data: [DONE]
```

**支持中止**: 通过 `AbortController` 可随时中止请求

**响应字段说明**:
- `text`: 流式文本内容
- `suggested_questions`: 快捷提问建议（可选）
- `related_links`: 相关链接列表（可选）
- `done`: 完成信号，包含来源信息
- `warning`: 警告信息（可选）

#### 2. 约束配置接口

**GET** `/api/constraints` - 获取约束配置

**PUT** `/api/constraints` - 更新约束配置

**POST** `/api/constraints/reset` - 重置为默认配置

**GET** `/api/constraints/stats` - 获取约束统计

**响应示例**:

```json
{
  "constraints": {
    "retrieval": {
      "enabled": true,
      "min_similarity_score": 0.7,
      "max_relevant_docs": 5
    },
    "generation": {
      "strict_mode": true,
      "forbidden_topics": [],
      "forbidden_keywords": []
    },
    "validation": {
      "enabled": true,
      "hallucination_detection": true
    },
    "fallback": {
      "no_result_message": "抱歉，我在知识库中没有找到相关信息。"
    }
  }
}
```

#### 3. 文档上传

**POST** `/api/documents/upload`

上传文档并建立索引。

**请求**: multipart/form-data

- file: 文档文件

**响应**:

```json
{
  "success": true,
  "document_id": "doc-uuid",
  "filename": "员工手册.pdf"
}
```

#### 4. 文档列表

**GET** `/api/documents/list`

获取文档列表。

**查询参数**:

- skip: 跳过数量
- limit: 返回数量

**响应**:

```json
{
  "documents": [
    {
      "id": "doc-uuid",
      "filename": "员工手册.pdf",
      "status": "indexed",
      "created_at": "2024-01-01T00:00:00"
    }
  ],
  "total": 10
}
```

#### 5. 会话管理

**GET** `/api/chat/sessions` - 获取会话列表

**POST** `/api/chat/sessions` - 创建新会话

**GET** `/api/chat/sessions/{session_id}/messages` - 获取会话消息（支持分页）

**DELETE** `/api/chat/sessions/{session_id}` - 删除会话

**消息响应格式**:

```json
{
  "messages": [
    {
      "id": "msg-uuid",
      "role": "user",
      "content": "什么是年假？",
      "timestamp": "2026-03-18T10:00:00"
    },
    {
      "id": "msg-uuid",
      "role": "assistant",
      "content": "根据公司《请假制度》...",
      "sources": [
        {
          "id": "1",
          "filename": "请假制度.docx",
          "content": "年假是指..."
        }
      ],
      "suggested_questions": ["年假有多少天？", "如何申请年假？"],
      "related_links": [
        {"title": "请假系统", "url": "https://...", "description": "在线请假"}
      ],
      "timestamp": "2026-03-18T10:00:05"
    }
  ],
  "has_more": false,
  "next_cursor": null
}
```

#### 6. 查询优化接口

**POST** `/api/chat/optimize`

优化用户查询，提升检索效果。

**请求体**:

```json
{
  "query": "年假怎么请"
}
```

**响应**:

```json
{
  "original_query": "年假怎么请",
  "optimized_query": "年假申请流程和条件",
  "keywords": ["年假", "申请", "流程"]
}
```

#### 7. 链接管理接口

**GET** `/api/links` - 获取所有链接

**POST** `/api/links` - 创建新链接

**PUT** `/api/links/{link_id}` - 更新链接

**DELETE** `/api/links/{link_id}` - 删除链接

**链接数据结构**:

```json
{
  "id": "link-uuid",
  "title": "请假系统",
  "url": "https://leave.company.com",
  "description": "在线请假申请系统",
  "keywords": ["请假", "休假", "年假"],
  "enabled": true
}
```

### 完整API文档

访问 <http://localhost:8000/docs> 查看完整的交互式API文档。

***

## 开发指南

### 项目结构

```
AI-assistent/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── agents/         # Agent实现
│   │   │   ├── base.py     # Agent基类
│   │   │   └── implementations/
│   │   │       ├── qa_agent.py
│   │   │       └── document_agent.py
│   │   ├── api/            # API路由
│   │   │   └── routes/
│   │   │       ├── chat.py
│   │   │       ├── documents.py
│   │   │       ├── constraints.py
│   │   │       └── links.py
│   │   ├── core/           # 核心组件
│   │   │   ├── llm.py
│   │   │   ├── embeddings.py
│   │   │   ├── chroma.py
│   │   │   ├── mongodb.py
│   │   │   └── memory/     # 记忆管理
│   │   ├── services/       # 业务服务
│   │   │   ├── qa_agent.py
│   │   │   ├── tool_executor.py
│   │   │   ├── llm_client.py
│   │   │   ├── suggestion_generator.py  # 快捷提问
│   │   │   ├── link_matcher.py          # 链接匹配
│   │   │   ├── answer_validator.py      # 回答验证
│   │   │   └── kb_query_optimizer.py    # 查询优化
│   │   ├── tools/          # 工具实现
│   │   │   ├── base.py
│   │   │   └── implementations/
│   │   │       ├── search.py
│   │   │       ├── documents.py
│   │   │       └── assistant.py
│   │   ├── rag/            # RAG组件
│   │   │   ├── hybrid_retriever.py
│   │   │   ├── query_enhancer.py
│   │   │   └── indexer.py
│   │   ├── prompts/        # 提示模板
│   │   │   ├── manager.py
│   │   │   └── strict_qa.py
│   │   ├── skills/         # Skill引擎
│   │   │   ├── engine.py
│   │   │   ├── registry.py
│   │   │   └── processors/
│   │   └── mcp/            # MCP服务器
│   │       ├── document_server.py
│   │       └── knowledge_server.py
│   ├── scripts/            # 脚本
│   │   ├── file_watcher.py
│   │   └── batch_processor.py
│   ├── tests/              # 测试代码
│   ├── requirements.txt    # Python依赖
│   └── main.py            # 入口文件
│
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   │   ├── Chat/
│   │   │   │   └── ChatView.vue
│   │   │   ├── Documents/
│   │   │   │   └── DocumentsView.vue
│   │   │   └── Settings/
│   │   │       └── Constraints.vue
│   │   ├── components/    # 通用组件
│   │   │   └── Layout/
│   │   ├── api/          # API调用
│   │   │   └── index.ts
│   │   ├── stores/       # 状态管理
│   │   │   ├── chat.ts
│   │   │   └── document.ts
│   │   ├── utils/        # 工具函数
│   │   │   ├── markdown.ts
│   │   │   └── fileColors.ts
│   │   └── main.ts       # 入口文件
│   ├── package.json      # Node依赖
│   └── vite.config.ts    # Vite配置
│
├── docs/                  # 文档目录
├── .trae/                # Trae配置
└── README.md             # 项目文档
```

### 添加新工具

1. 在 `backend/app/tools/implementations/` 创建新工具类：

```python
from app.tools.base import BaseTool, ToolRegistry, ToolDefinition

@ToolRegistry.register("my_tool")
class MyTool(BaseTool):
    
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            id="my_tool",
            name="my_tool",
            description="工具描述",
            enabled=True,
            category="custom",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "参数说明"
                    }
                },
                "required": ["param1"]
            },
            implementation="MyTool"
        )
    
    async def execute(self, param1: str) -> Dict[str, Any]:
        # 实现工具逻辑
        return {"result": "success"}
```

1. 工具会自动注册到ToolRegistry，LLM可以自动发现和调用。

### 添加新Skill

1. 在 `backend/app/skills/processors/` 创建处理器：

```python
from app.skills.base import BaseProcessor, ProcessorRegistry

@ProcessorRegistry.register("my_processor")
class MyProcessor(BaseProcessor):
    
    @property
    def name(self) -> str:
        return "my_processor"
    
    async def process(self, context: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        # 实现处理逻辑
        return {"result": "data"}
```

1. 在配置文件中定义Skill流水线。

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_qa_agent.py

# 生成覆盖率报告
pytest --cov=app tests/
```

***

## 部署指南

### Docker部署

#### 1. 构建镜像

```bash
# 构建后端镜像
docker build -t qa-backend ./backend

# 构建前端镜像
docker build -t qa-frontend ./frontend
```

#### 2. 使用Docker Compose

```bash
docker-compose up -d
```

### 生产环境部署

#### 1. 后端部署

```bash
# 使用Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### 2. 前端部署

```bash
# 构建
npm run build

# 使用Nginx服务
# 配置nginx.conf指向dist目录
```

#### 3. 环境变量配置

创建 `.env` 文件：

```env
# LLM配置
LLM_API_KEY=your-api-key
LLM_MODEL=qwen-plus
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# MongoDB配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=qa_assistant

# ChromaDB配置
CHROMA_PERSIST_DIR=./data/chroma

# 应用配置
APP_ENV=production
APP_DEBUG=false
```

***

## 性能优化

### 性能指标

| 指标       | 平均值   | 优化建议    |
| -------- | ----- | ------- |
| Tool决策时间 | 0.35s | 添加决策缓存  |
| 向量检索时间   | 0.08s | 使用GPU加速 |
| RAG生成时间  | 1.5s  | 优化上下文长度 |
| 端到端响应    | 2.1s  | 使用流式输出  |

### 优化建议

1. **缓存优化**
   - 启用Tool结果缓存
   - 使用查询优化缓存
   - 配置合理的TTL
2. **并发优化**
   - 增加Worker数量
   - 使用异步IO
   - 启用连接池
3. **检索优化**
   - 调整向量权重
   - 优化分块大小
   - 使用混合检索

***

## 常见问题

### Q1: 如何更换LLM模型？

A: 修改 `.env` 文件中的 `LLM_MODEL` 和 `LLM_BASE_URL` 配置。

### Q2: 如何提高检索精度？

A:

- 调整 `max_rag_docs` 参数
- 使用混合检索（向量+BM25）
- 优化文档分块策略

### Q3: 如何处理大量文档？

A:

- 使用批量上传接口
- 配置异步索引
- 增加ChromaDB存储空间

### Q4: 如何防止LLM幻觉？

A:

- 使用StrictQAPrompt严格约束
- 配置禁止主题和关键词
- 启用来源验证

### Q5: 刷新页面后对话丢失怎么办？

A: 系统已实现数据持久化，对话会自动保存到 MongoDB。如果刷新后丢失，请检查：
- MongoDB 服务是否正常运行
- 后端日志是否有保存失败记录
- 浏览器控制台是否有加载错误

### Q6: 如何中止正在生成的回答？

A: 在回答生成过程中，发送按钮会变为红色中止按钮，点击即可中止。中止后已生成的内容会保留并标注"回答已中止"。

### Q7: Sources 显示 "Unknown" 怎么办？

A: 这通常是因为文档元数据缺失。确保：
- 上传文档时正确解析了文件名
- 向量数据库中的 metadata 包含 `document_name` 字段
- 后端服务已重启加载最新代码

### Q8: 如何配置约束设置？

A: 访问"设置"页面的"约束设置"标签，可以配置：
- 检索约束：最小相似度、文档数量
- 生成约束：严格模式、禁止主题
- 验证约束：来源检查、幻觉检测
- 兜底策略：无结果提示语

### Q9: 快捷提问是如何生成的？

A: 系统基于用户问题和回答内容，使用LLM智能生成相关的追问建议：
- 生成数量可在约束配置中设置（默认3个）
- 如果回答包含"没有找到"等关键词，会返回默认建议
- 前端点击即可快速发起追问

### Q10: 相关链接是如何匹配的？

A: 系统通过关键词匹配自动推荐相关链接：
- 管理员可在后台配置链接和对应关键词
- 当用户查询包含关键词时，自动展示相关链接
- 链接以卡片形式展示，支持点击跳转

***

## 贡献指南

我们欢迎所有形式的贡献！

### 贡献流程

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

### 代码规范

- 遵循PEP 8编码规范
- 添加必要的注释和文档
- 编写单元测试
- 更新相关文档

***

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

***

## 联系方式

- 项目主页: \[GitHub Repository]
- 问题反馈: \[GitHub Issues]
- 邮箱: <support@example.com>

***

<div align="center">

**⭐ 如果这个项目对您有帮助，请给一个Star支持一下！⭐**

Made with ❤️ by AI Assistant Team

</div>
