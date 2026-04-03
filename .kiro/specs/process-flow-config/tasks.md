# 任务列表：process-flow-config

## 后端任务

### 1. SkillLoader 支持 nodes.json 优先加载与自动迁移

- [x] 1.1 修改 `SkillDefinition.__init__`，新增 `nodes` 属性，从构造参数接收节点列表（不再直接从 frontmatter 读取）
- [x] 1.2 在 `SkillLoader._load_one` 中，加载 SKILL.md 后检查同目录是否存在 `nodes.json`：若存在则读取并解析为节点列表；若不存在且 frontmatter 有 `nodes` 字段，则将其写入 `nodes.json` 并记录 info 日志
- [x] 1.3 在 `SkillLoader._load_one` 中，若读取 `nodes.json` 失败（JSON 解析错误等），记录 error 日志并回退使用 frontmatter 中的 `nodes` 字段
- [x] 1.4 确认 `SkillDefinition.to_dict()` 返回的 `nodes` 字段来自上述加载逻辑（而非直接 `frontmatter.get("nodes")`）

### 2. Flow Config API 路由文件

- [x] 2.1 新建 `backend/app/api/routes/flow_config.py`，创建 `router = APIRouter()`，所有路由统一使用 `Depends(require_hr)` 鉴权
- [x] 2.2 在 `backend/app/main.py` 中 import 并注册：`app.include_router(flow_config.router, prefix="/api/flow-config", tags=["flow-config"])`，同时在 startup 中确保 process tools 已注册（`base_nodes.py` 等已 import）

### 3. GET /api/flow-config/tools

- [x] 3.1 实现接口：调用 `ToolRegistry.get_definitions()`，过滤 `category == "process"` 的条目，返回列表（字段：`id`、`name`、`description`、`category`、`parameters`）
- [x] 3.2 未携带有效 JWT 时由 `require_hr` 依赖自动返回 401/403，无需额外处理

### 4. GET /api/flow-config/skills/{skill_id}/nodes

- [x] 4.1 实现接口：从 `SkillEngine`（或直接 `SkillLoader`）获取 skill，若不存在返回 404
- [x] 4.2 返回节点列表，每个节点包含 `id`、`title`、`type`、`tool`、`content`、`params` 字段

### 5. PUT /api/flow-config/skills/{skill_id}/nodes

- [x] 5.1 定义请求体 Pydantic 模型 `NodeItem`（字段：`id: str`、`title: str`、`type: str`、`tool: str`、`content: str`、`params: dict`）和 `SaveNodesRequest(nodes: List[NodeItem])`
- [x] 5.2 校验节点列表：`id` 不能为空、不能重复，否则返回 422 及字段错误详情
- [x] 5.3 校验每个节点的 `tool` 字段在 `ToolRegistry` 中存在，否则返回 422 及节点错误信息
- [x] 5.4 依赖检查（需求 7.2）：遍历节点，检查每个节点所需上游字段是否由前置节点提供，收集警告列表（不阻止保存）
- [x] 5.5 写入前将原 `nodes.json` 备份为 `nodes.json.bak`（若原文件存在）
- [x] 5.6 将节点列表序列化写入 `skills/definitions/{skill_id}/nodes.json`
- [x] 5.7 调用 `skill_engine.reload(skill_id)` 使新配置立即生效
- [x] 5.8 检查 MongoDB `process_contexts` 集合中 `flow_id == skill_id` 的活跃记录；若其 `current_step >= 新节点数量`，则将 `current_step` 重置为 0 并清空 `collected_data`
- [x] 5.9 返回响应：`{ "success": true, "affected_sessions": <数量>, "warnings": [<依赖警告>] }`

---

## 前端任务

### 6. API 封装

- [x] 6.1 在 `frontend/src/api/index.ts` 中新增 `flowConfigApi` 对象，包含：
  - `getTools()` → `GET /api/flow-config/tools`
  - `getNodes(skillId)` → `GET /api/flow-config/skills/{skillId}/nodes`
  - `saveNodes(skillId, nodes)` → `PUT /api/flow-config/skills/{skillId}/nodes`

### 7. 路由与侧边栏入口

- [x] 7.1 在 `frontend/src/router/index.ts` 中新增路由：`{ path: 'flow-config', name: 'FlowConfig', component: () => import('@/views/FlowConfig/FlowConfigView.vue'), meta: { title: 'Flow Config', requiresHR: true } }`
- [x] 7.2 在 `AppSidebar.vue` 的 HR 专属导航区（`v-if="authStore.isHR"` 块内）新增菜单项，图标使用 `Setting`，文字「流程配置」，点击跳转 `/flow-config`

### 8. FlowConfigView 主视图

- [x] 8.1 新建 `frontend/src/views/FlowConfig/FlowConfigView.vue`，页面挂载时调用 `flowConfigApi.getNodes('leave_apply')` 加载节点列表（skill_id 先硬编码，后续可扩展为下拉选择）
- [x] 8.2 使用 Element Plus `el-table` 展示节点列表，列：序号、title、type、tool，每行有「编辑」「删除」操作按钮
- [x] 8.3 集成 `vuedraggable`（或 `@vueuse/integrations` sortable）实现行拖拽排序，拖拽后更新本地节点数组顺序
- [x] 8.4 页面顶部放置「新增节点」按钮和「保存」按钮

### 9. 节点编辑表单（NodeEditDialog）

- [x] 9.1 新建 `frontend/src/views/FlowConfig/NodeEditDialog.vue`，接收 `modelValue`（节点对象或 null）和 `tools`（tool 列表）props，emit `update:modelValue` 和 `confirm`
- [x] 9.2 表单字段：`id`（文本输入）、`title`（文本输入）、`type/tool`（`el-select`，选项从 `tools` prop 动态渲染，选中后同时设置 `type` 和 `tool` 为该 tool 的 `id`）、`content`（文本域）
- [x] 9.3 选择 tool 后，根据该 tool 的 `parameters.properties` 动态渲染 `params` 表单：`string` 类型渲染 `el-input`，`array` 类型渲染 `el-input`（JSON 文本），`boolean` 渲染 `el-switch`
- [x] 9.4 表单提交时对 `id` 和 `title` 做非空校验，通过后 emit `confirm` 事件传出节点对象

### 10. 保存与错误处理

- [x] 10.1 在 `FlowConfigView` 的「保存」按钮点击处理中，调用 `flowConfigApi.saveNodes(skillId, nodes)`
- [x] 10.2 若响应为 422，解析 `detail` 字段，将错误信息标注到对应节点行（可用行内红色文字或 tooltip）
- [x] 10.3 若保存成功，显示 `ElMessage.success('保存成功')`；若 `affected_sessions > 0`，额外弹出提示「已重置 N 个进行中的流程会话」
- [x] 10.4 若 `warnings` 非空，用 `el-alert` 展示依赖警告，列出缺失字段名称
