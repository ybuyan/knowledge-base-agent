# 实施计划：企业级系统：公司制度问答与流程指引助手

本项目旨在开发一个智能问答助手，提供准确的解答和流程指引。对标企业级 Agent 框架的标准，本架构在后端基于大语言模型和检索增强生成 (RAG) 外，补充了企业必需的治理与可观测性模块，并规划了表现层 (Vue 3 前端系统)。

## 1. 后端：核心架构与补全的企业级特性

- **框架**: Python + FastAPI + LangChain + MCP
- **企业级补充模块**:
  - **Auth/RBAC 权限层**: 增强身份认证与鉴权(如 JWT/OAuth2)，控制不同级别员工对涉密制度（如高管薪酬）的访问，以及细粒度的技能调用权限。
  - **审计与追踪 (Audit & Traceability)**: 记录所有用户提问与系统返回（特别是被引用的具体制度溯源信息），并在出现幻觉风险时保留排查日志 (Langfuse 或 langsmith 集成)。
  - **多租户/环境隔离 (Multi-Tenancy/Namespaces)**: 支持同一个后端为子公司/不同部门划分独立的知识库检索空间。

### 后端目录结构更新 (Backend Structure)

```text
assistant-agent/backend/     # 【更新：将后端包裹进 backend 目录】
├── app/                     
│   ├── main.py              
│   ├── api/                 
│   ├── core/                
│   │   ├── security.py      # 【新增】企业级 Auth 认证、JWT 密钥处理与 RBAC 权限系统
│   │   ├── telemetry.py     # 【新增】Opentelemetry / Langfuse 监控埋点与链路追踪配置
│   ├── services/            
│   ├── agent/               
│   ├── skills/              # JSON 技能声明体系
│   ├── tools/               # Python 底层工具实现
│   ├── mcp/                 
│   ├── prompts/             
│   ├── rag/                 
│   ├── models/              # 【新增】数据库 ORM 模型设计 (SQLAlchemy/SQLModel) 用于存储用户与日志
│   ├── utils/               
├── data/                    
├── tests/                   
├── requirements.txt         
├── README.md                
```

## 2. 前端：Vue 3 现代化终端交互界面

系统将采用前后端分离架构，前端选用 **Vue 3** 生态构建，注重响应式交互及企业级后台的设计审美。

- **核心栈**: Vue 3 (Composition API, `<script setup>`), TypeScript, Vite
- **UI 组件库**: Element Plus / Ant Design Vue (或更现代的 Naive UI)
- **状态管理与路由**: Pinia, Vue Router 4
- **通信与 API 处理**: Axios (SSE / WebSocket 长连接支持，用于流式打字机效果输出)
- **工程化限制**: ESLint, Prettier, Husky

### 前端目录结构设计 (Frontend Structure)

```text
assistant-agent/frontend/    # 【新增：独立的前端工程目录】
├── public/                  # 静态资源 (Logo, favicon等)
├── src/
│   ├── api/                 # 基于 Axios 封装的后端接口请求集合 (对应后端的 api 层)
│   ├── assets/              # 样式、图片、图标资源
│   ├── components/          # 核心可复用组件 (通用业务)
│   │   ├── ChatBot/         # 独立抽离的流式对话主窗体组件
│   │   ├── DocumentList/    # 制度大纲或上传管理组件
│   │   ├── MarkdownViewer/  # 处理服务端返回富文本及代码高亮的渲染组件
│   ├── layouts/             # 全局页面布局容器 (如后台的侧边栏+Header+主内容区)
│   ├── router/              # 前端路由表配置
│   ├── stores/              # Pinia 状态管理 (包含User Store, Chat History Store)
│   ├── views/               # 各个路由级页面组件
│   │   ├── Chat/            # 面向员工的 C 端问答交互界面
│   │   ├── Admin/           # 【管理端】知识库维护、提示词热更新、使用统计图表
│   ├── App.vue              # 根组件
│   ├── main.ts              # 入口文件
├── index.html               # 宿主页面
├── vite.config.ts           # Vite 脚手架及代理(Proxy)策略配置
├── package.json             # 前端依赖与脚本指令
├── tsconfig.json            # TypeScript 编译约束
```

### Manual Verification
- 进行端到端的协同测试：启动 Vite dev server 和 FastAPI 后台。用户在 Vue 界面提问 -> Axios 流式请求 -> 后端 JWT 解析、RAG 检索、Agent 调用 Skill -> 触发 Tool -> 包装打字机数据流回写 -> 前端 Markdown 实时解析高亮展示。
