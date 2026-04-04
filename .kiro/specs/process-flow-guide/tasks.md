# 实施计划 - 文档解析流程指引功能

## 任务列表

- [x] 1. 后端数据模型与数据库
  - [x] 1.1 创建 StepEntryLink、FlowStep、FlowGuide、FlowGuideCreate Pydantic 模型（`backend/app/models/flow_guide.py`）
  - [x] 1.2 在 MongoDB 创建 flow_guides 集合，添加 name+category 联合索引、status 索引
  - [x] 1.3 创建 FlowGuideRepository 封装数据库操作（CRUD + 按分类分组查询 + entry_link 解析）

- [x] 2. 流程提取服务
  - [x] 2.1 创建 FlowExtractor 服务（`backend/app/services/flow_extractor.py`），实现 LLM 提取 Prompt 和响应解析
  - [x] 2.2 实现重复检测逻辑：提取后与数据库中同名流程对比，生成 pending_duplicates 记录
  - [x] 2.3 在文档上传路由（`documents.py`）的索引完成后，异步触发 FlowExtractor

- [x] 3. 流程指引 CRUD API
  - [x] 3.1 创建 `backend/app/api/routes/flow_guides.py`，实现列表、分组、创建、更新、删除、状态切换接口
  - [x] 3.2 实现 entry_link 解析中间件：GET 详情时自动将 external_link_id 解析为 label+url
  - [x] 3.3 实现重复确认接口（GET pending-duplicates、POST resolve-duplicate）
  - [x] 3.4 实现 GET /api/flow-guides/external-links 接口，返回 external_links 中 enabled=true 的条目供前端选择
  - [x] 3.5 在 `backend/app/main.py` 注册新路由

- [x] 4. 前端 API 封装
  - [x] 4.1 在 `frontend/src/api/index.ts` 添加 flowGuideApi（getGrouped、list、create、update、delete、toggleStatus、getPendingDuplicates、resolveDuplicate、getExternalLinks）

- [x] 5. GuideModal 弹窗组件
  - [x] 5.1 创建 `frontend/src/components/GuideModal/index.vue`，展示流程名称、分类、来源文档、步骤列表
  - [x] 5.2 实现步骤卡片：序号圆圈用主色 `#e0301e`，卡片背景用 `var(--bg-secondary)`，边框用 `var(--border-light)`
  - [x] 5.3 实现入口链接按钮：复用 `.link-btn` 样式（主色文字，hover 变主色背景），无 entry_link 时不渲染
  - [x] 5.4 弹窗标题区域添加左侧主色装饰线，与系统 `.links-label` 风格一致

- [x] 6. QuickPromptButton 扩展
  - [x] 6.1 启用 API 调用，改为 `flowGuideApi.getGrouped()`
  - [x] 6.2 修改点击处理：从 emit promptClick 改为打开 GuideModal，传入 flow_guide_id
  - [x] 6.3 集成 GuideModal 组件

- [x] 7. DuplicateConfirmDialog 组件
  - [x] 7.1 创建 `frontend/src/components/DuplicateConfirmDialog/index.vue`，展示新旧流程对比，提供"覆盖更新"/"保留原有"/"另存为新流程"三个选项
  - [x] 7.2 在文档上传成功后，调用 getPendingDuplicates 检查，若有则展示此对话框

- [x] 8. FlowManager 管理页面
  - [x] 8.1 创建 `frontend/src/views/FlowManager/index.vue`，实现流程列表（表格）、搜索筛选、启用/禁用；表格 hover 行背景用 `var(--bg-active)`
  - [x] 8.2 实现新增/编辑表单：名称、分类、描述、步骤列表（支持增删、上下移动）
  - [x] 8.3 实现步骤入口配置区域：支持"从系统链接选择"（下拉 external_links）和"手动输入"两种模式切换
  - [x] 8.4 实现删除确认对话框
  - [x] 8.5 在前端路由和导航菜单中添加"流程管理"入口（仅管理员可见）
