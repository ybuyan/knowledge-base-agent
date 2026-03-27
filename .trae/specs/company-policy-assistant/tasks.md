# 开发任务清单 - 公司制度问答与流程指引助手

## 执行顺序说明

```
┌─────────────────────────────────────────────────────────────┐
│  第一阶段：前端开发 (立即执行)                                  │
│  ├── Task 1: 初始化前端项目                                    │
│  ├── Task 2: 开发文档管理页面                                  │
│  └── Task 3: 开发问答聊天界面                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    等待用户确认前端完成
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  第二阶段：后端开发 (确认后执行)                                │
│  ├── Task 4: 初始化后端项目 + ChromaDB配置                     │
│  ├── Task 5: 实现文档上传Agent                                 │
│  ├── Task 6: 实现问答Agent (含多轮对话向量检索)                 │
│  └── Task 7: 前后端集成测试                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 第一阶段：前端开发 (立即执行)

### Task 1: 初始化前端项目

#### Task 1.1: 创建 Vue 3 项目
- [x] 使用 Vite 初始化 Vue 3 + TypeScript 项目
- [x] 配置项目结构 (src/components, src/views, src/stores, src/api)
- [x] 安装 Element Plus UI 组件库
- [x] 安装 Pinia 状态管理
- [x] 安装 Vue Router 4
- [x] 安装 Axios
- [x] 安装 markdown-it 和 highlight.js

#### Task 1.2: 配置主题色 #e0301e
- [x] 创建 Element Plus 主题配置文件
- [x] 设置主色 #e0301e
- [x] 设置浅色 #ff4d3a
- [x] 设置深色 #b52616
- [x] 应用到按钮、链接、标签等组件

#### Task 1.3: 基础布局和路由
- [x] 创建主布局组件 (左侧导航 + 右侧内容)
- [x] 配置路由：/chat (问答页), /documents (文档管理页)
- [x] 创建导航菜单组件
- [x] 设置路由守卫

---

### Task 2: 文档管理页面 (参考"文档上传.png")

#### Task 2.1: 文档上传组件
- [x] 创建拖拽上传区域组件
- [x] 实现文件选择功能
- [x] 显示支持格式提示 (PDF, DOCX, TXT)
- [x] 显示上传进度条
- [x] 应用主题色到上传按钮

#### Task 2.2: 文档列表组件
- [x] 创建文档列表表格
- [x] 显示文件名、状态、上传日期、大小
- [x] 实现状态标签 (READY-绿色, INDEXING-蓝色, QUEUED-黄色, ERROR-红色)
- [x] 实现删除按钮
- [x] 实现分页组件

#### Task 2.3: 文档管理页面整合
- [x] 整合上传组件和列表组件
- [x] 添加页面标题 "知识库文档管理"
- [x] 添加"重新索引全部"按钮 (主题色)
- [x] 响应式布局适配

---

### Task 3: 问答聊天界面 (参考"问答界面.png")

#### Task 3.1: 三栏布局结构
- [x] 创建左侧导航栏
  - 用户信息卡片
  - "New Session" 按钮 (主题色)
  - 历史会话列表
  - 导航菜单 (Chat, Documents)
- [x] 创建中间聊天区域
- [x] 创建右侧信息面板

#### Task 3.2: 聊天消息组件
- [x] 创建用户消息气泡 (右侧，浅色背景)
- [x] 创建助手消息气泡 (左侧，白色背景)
- [x] 集成 Markdown 渲染
- [x] 代码块语法高亮
- [x] 引用标记 [1][2] 样式

#### Task 3.3: 流式响应展示
- [x] 实现 SSE 客户端连接
- [x] 实现打字机效果 (逐字显示)
- [x] 添加加载动画
- [x] 支持中断响应

#### Task 3.4: 输入和发送组件
- [x] 创建消息输入框
- [x] 发送按钮 (主题色)
- [x] 回车键发送
- [x] 文件上传按钮 (UI)
- [x] 语音输入按钮 (UI)

#### Task 3.5: 来源展示组件
- [x] 创建"Sources Verified" 区域
- [x] 显示来源文档卡片
- [x] 显示文档名称、页码、段落

#### Task 3.6: 右侧面板
- [x] "Suggested Questions" 列表
- [x] "Topic Clusters" 标签云
- [x] "System Status" 面板
- [x] 知识库统计信息

---

## 第二阶段：后端开发 (确认后执行)

### Task 4: 初始化后端项目 + ChromaDB配置

#### Task 4.1: FastAPI 项目搭建
- [x] 创建 backend 目录结构
- [x] 创建 requirements.txt
  - fastapi, uvicorn
  - langchain, langchain-community
  - chromadb
  - PyPDF2, python-docx
  - sqlalchemy
- [x] 创建 main.py 入口
- [x] 配置 CORS

#### Task 4.2: ChromaDB 双集合配置
- [x] 初始化 ChromaDB 客户端
- [x] 创建 `documents` 集合 (文档知识库)
- [x] 创建 `conversations` 集合 (对话历史)
- [x] 配置 Embedding 函数
- [x] 创建向量存储服务封装

#### Task 4.3: 数据库模型
- [x] 创建 Document 模型 (id, filename, status, upload_time, size)
- [x] 创建 ChatSession 模型 (id, title, created_at)
- [x] 配置 SQLite 数据库

---

### Task 5: 实现文档上传Agent

#### Task 5.1: 文档上传Agent核心
- [ ] 创建 DocumentUploadAgent 类
- [ ] 实现文档解析方法 (PDF/DOCX/TXT)
- [ ] 实现文本切分策略
- [ ] 实现向量化方法
- [ ] 实现 ChromaDB 存储方法

#### Task 5.2: 文档管理 API
- [ ] POST /api/documents/upload - 文件上传
- [ ] GET /api/documents - 文档列表
- [ ] DELETE /api/documents/{id} - 删除文档
- [ ] POST /api/documents/{id}/reindex - 重新索引

#### Task 5.3: 文档处理服务
- [ ] PDF 文本提取 (PyPDF2)
- [ ] Word 文档解析 (python-docx)
- [ ] TXT 文件读取
- [ ] 文本切分 (按段落/长度)
- [ ] 元数据提取和存储

---

### Task 6: 实现问答Agent (含多轮对话向量检索)

#### Task 6.1: 问答Agent核心
- [ ] 创建 QAAgent 类
- [ ] 实现问题向量化方法
- [ ] 实现文档知识库检索方法
- [ ] 实现对话历史检索方法
- [ ] 实现上下文组装方法
- [ ] 实现对话历史存储方法

#### Task 6.2: LLM 集成
- [ ] 配置 LLM 客户端
- [ ] 设计 Prompt 模板
- [ ] 实现答案生成方法
- [ ] 实现引用标注逻辑
- [ ] 实现流式生成 (SSE)

#### Task 6.3: 问答 API
- [ ] POST /api/chat/ask - 普通问答
- [ ] POST /api/chat/ask/stream - 流式问答 (SSE)
- [ ] GET /api/chat/sessions - 会话列表
- [ ] POST /api/chat/sessions - 创建会话
- [ ] GET /api/chat/sessions/{id}/messages - 获取消息历史

---

### Task 7: 前后端集成测试

#### Task 7.1: 前后端联调
- [ ] 配置前端代理到后端
- [ ] 测试文档上传流程
- [ ] 测试问答流程
- [ ] 测试流式响应
- [ ] 测试多轮对话

#### Task 7.2: 功能测试
- [ ] 测试各种格式文档上传
- [ ] 测试问答准确性
- [ ] 测试引用溯源
- [ ] 测试界面交互
- [ ] 测试对话历史检索

#### Task 7.3: 优化
- [ ] 优化首屏加载
- [ ] 优化大文件上传
- [ ] 优化向量检索性能
- [ ] 错误处理完善
- [ ] 添加加载状态

---

## 任务依赖关系

### 第一阶段依赖 (前端)
```
Task 1.1 (Vue项目) ── Task 1.2 (主题色) ── Task 1.3 (布局路由)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ↓                         ↓                         ↓
              Task 2.1 (上传组件)      Task 2.2 (列表组件)      Task 3.1 (三栏布局)
                    │                         │                         │
                    └──────────┬──────────────┘                         │
                               ↓                                        │
                        Task 2.3 (文档页面)                              │
                                                                        │
                               ←─────────────────────────────────────────┘
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
                    ↓                         ↓                         ↓
              Task 3.2 (消息组件)      Task 3.4 (输入组件)      Task 3.5 (来源展示)
                    │                         │                         │
                    └──────────┬──────────────┴─────────────────────────┘
                               ↓
                        Task 3.3 (流式响应)
                               │
                               ↓
                        Task 3.6 (右侧面板)
```

### 第二阶段依赖 (后端)
```
Task 4.1 (FastAPI) ── Task 4.2 (ChromaDB) ── Task 4.3 (数据库)
                            │
                            ↓
                     Task 5.1 (文档Agent核心) ── Task 5.2 (文档API) ── Task 5.3 (文档处理)
                                                        │
                            ┌───────────────────────────┤
                            │                           │
                            ↓                           ↓
                     Task 6.1 (问答Agent核心)     Task 6.2 (LLM集成)
                            │                           │
                            └───────────┬───────────────┘
                                        ↓
                                 Task 6.3 (问答API)
                                        │
                                        ↓
                                 Task 7.1 (联调)
                                        │
                                        ↓
                                 Task 7.2 (测试)
                                        │
                                        ↓
                                 Task 7.3 (优化)
```

---

## Agent 架构说明

### 文档上传Agent
```
输入: 文件 (PDF/DOCX/TXT)
处理流程:
  1. 文档解析 → 提取文本
  2. 文本切分 → 生成文本块
  3. 向量化 → Embedding模型
  4. 存储 → ChromaDB documents集合
输出: 文档ID, 切分数量, 状态
```

### 问答Agent
```
输入: 问题 + 会话ID
处理流程:
  1. 问题向量化 → Embedding模型
  2. 知识库检索 → ChromaDB documents集合
  3. 对话历史检索 → ChromaDB conversations集合
  4. 上下文组装 → 合并检索结果
  5. LLM生成 → 流式输出答案
  6. 对话存储 → ChromaDB conversations集合
输出: 答案 + 引用来源
```
