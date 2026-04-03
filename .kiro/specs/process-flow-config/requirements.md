# 需求文档

## 简介

本功能为 HR 提供一个可视化的流程节点配置界面，使 HR 无需编写 YAML 代码即可对流程节点进行增删改排序操作。

当前架构中，流程节点定义在各 `SKILL.md` 的 YAML frontmatter `nodes` 字段中，修改需要手写 YAML，容易出错且不直观。本功能将节点配置迁移至独立的 `nodes.json` 文件，并通过 REST API 暴露给前端，由前端提供可视化编辑界面。

系统已有基础：
- `ProcessExecutor` 按 `node_type` 执行节点
- `SkillLoader` 支持热重载
- `ToolRegistry` 管理所有可用 tool，已有 `get_definitions()` 方法
- `require_hr` 依赖项已实现 HR 角色鉴权

---

## 词汇表

- **Flow_Config_API**：后端提供的流程节点配置 REST API
- **Flow_Config_UI**：前端可视化流程节点配置界面
- **Node**：流程中的单个步骤，包含 id、title、type、tool、content、params 等字段
- **nodes.json**：存储某个 Skill 节点列表的独立 JSON 文件，路径为 `skills/definitions/{skill_id}/nodes.json`
- **ToolRegistry**：后端 Tool 注册表，管理所有可用 tool 及其 schema
- **SkillLoader**：后端 Skill 加载器，支持热重载
- **ProcessExecutor**：按节点类型执行流程步骤的处理器
- **HR**：具有 `role == "hr"` 的系统用户，拥有流程配置权限
- **Process_Context**：正在进行中的流程会话状态，存储当前步骤和已收集数据

---

## 需求

### 需求 1：节点存储迁移

**用户故事：** 作为系统维护者，我希望流程节点配置存储在独立的 JSON 文件中，而不是嵌入 SKILL.md 的 YAML frontmatter，以便降低格式错误风险并支持 API 读写。

#### 验收标准

1. THE SkillLoader SHALL 优先从 `skills/definitions/{skill_id}/nodes.json` 加载节点列表；若该文件不存在，则回退读取 `SKILL.md` frontmatter 中的 `nodes` 字段。
2. WHEN `nodes.json` 文件不存在且 `SKILL.md` 中存在 `nodes` 字段时，THE SkillLoader SHALL 自动将节点数据迁移写入 `nodes.json`。
3. THE SkillLoader SHALL 在加载 `nodes.json` 失败时记录错误日志并回退到 `SKILL.md` 中的节点数据。
4. THE Flow_Config_API SHALL 对 `nodes.json` 执行所有节点的读写操作，不修改 `SKILL.md` 文件内容。

---

### 需求 2：Tool Schema API

**用户故事：** 作为前端开发者，我希望通过 API 获取所有可用 tool 的 schema 定义，以便在配置界面中动态渲染节点类型选项和参数表单。

#### 验收标准

1. THE Flow_Config_API SHALL 提供 `GET /api/flow-config/tools` 接口，返回所有已注册 tool 的 id、name、description、category 和 parameters schema。
2. WHEN 请求 `GET /api/flow-config/tools` 时，THE Flow_Config_API SHALL 仅返回 `category == "process"` 的 tool 列表。
3. THE Flow_Config_API SHALL 在返回的每个 tool 定义中包含 `parameters.properties` 中每个字段的类型、描述和是否必填信息。
4. IF 请求方未携带有效 JWT Token，THEN THE Flow_Config_API SHALL 返回 HTTP 401 状态码。

---

### 需求 3：节点列表读取 API

**用户故事：** 作为 HR，我希望通过 API 获取某个流程的完整节点列表，以便在配置界面中查看当前配置。

#### 验收标准

1. THE Flow_Config_API SHALL 提供 `GET /api/flow-config/skills/{skill_id}/nodes` 接口，返回该 Skill 的节点列表。
2. WHEN 请求的 `skill_id` 不存在时，THE Flow_Config_API SHALL 返回 HTTP 404 状态码及描述性错误信息。
3. IF 请求方的 `role` 不为 `"hr"`，THEN THE Flow_Config_API SHALL 返回 HTTP 403 状态码。
4. THE Flow_Config_API SHALL 在响应中包含每个节点的 id、title、type、tool、content 和 params 字段。

---

### 需求 4：节点列表保存 API

**用户故事：** 作为 HR，我希望通过 API 保存修改后的节点列表，以便将可视化配置的结果持久化。

#### 验收标准

1. THE Flow_Config_API SHALL 提供 `PUT /api/flow-config/skills/{skill_id}/nodes` 接口，接受完整节点列表并写入 `nodes.json`。
2. WHEN 节点列表保存成功后，THE Flow_Config_API SHALL 调用 `SkillLoader.reload(skill_id)` 使新配置立即生效。
3. IF 请求方的 `role` 不为 `"hr"`，THEN THE Flow_Config_API SHALL 返回 HTTP 403 状态码。
4. IF 提交的节点列表中存在 `id` 字段为空或重复的节点，THEN THE Flow_Config_API SHALL 返回 HTTP 422 状态码及具体的字段错误信息。
5. IF 提交的节点列表中某个节点的 `tool` 字段引用了 ToolRegistry 中不存在的 tool_id，THEN THE Flow_Config_API SHALL 返回 HTTP 422 状态码及该节点的错误信息。
6. THE Flow_Config_API SHALL 在写入 `nodes.json` 前先将原文件备份为 `nodes.json.bak`。

---

### 需求 5：进行中流程的上下文保护

**用户故事：** 作为系统，我希望在节点配置被修改后，正在进行中的流程会话能够得到妥善处理，以避免因节点索引失效导致的运行时错误。

#### 验收标准

1. WHEN 节点列表保存成功后，THE Flow_Config_API SHALL 检查是否存在 `flow_id == skill_id` 的活跃 Process_Context。
2. WHEN 存在活跃 Process_Context 且其 `current_step` 超出新节点列表长度时，THE ProcessExecutor SHALL 将该会话的 `current_step` 重置为 0 并清空 `collected_data`。
3. THE Flow_Config_API SHALL 在保存响应中返回受影响的活跃会话数量。

---

### 需求 6：可视化配置界面

**用户故事：** 作为 HR，我希望通过可视化界面查看、新增、编辑、删除和排序流程节点，而不需要手写 YAML 或 JSON。

#### 验收标准

1. THE Flow_Config_UI SHALL 展示当前 Skill 的所有节点，每个节点显示序号、title、type 和 tool 信息。
2. THE Flow_Config_UI SHALL 支持通过拖拽方式对节点进行排序。
3. WHEN HR 点击「新增节点」时，THE Flow_Config_UI SHALL 展示节点编辑表单，表单中的「节点类型」选项从 `GET /api/flow-config/tools` 动态加载。
4. WHEN HR 选择节点类型后，THE Flow_Config_UI SHALL 根据该 tool 的 `parameters` schema 动态渲染对应的参数配置表单。
5. WHEN HR 点击「保存」时，THE Flow_Config_UI SHALL 调用 `PUT /api/flow-config/skills/{skill_id}/nodes` 提交完整节点列表。
6. WHEN 保存请求返回 HTTP 422 时，THE Flow_Config_UI SHALL 在对应节点或字段旁展示具体的错误提示信息。
7. WHEN 保存成功时，THE Flow_Config_UI SHALL 展示成功提示，并显示受影响的活跃会话数量（若大于 0）。
8. IF HR 未登录或 Token 已过期，THEN THE Flow_Config_UI SHALL 跳转至登录页面。
9. THE Flow_Config_UI SHALL 仅对 `role == "hr"` 的用户展示入口菜单项。

---

### 需求 7：节点字段依赖说明

**用户故事：** 作为 HR，我希望在配置节点时能看到节点间的字段依赖提示，以避免配置出缺少前置数据的节点顺序。

#### 验收标准

1. THE Flow_Config_UI SHALL 在节点编辑表单中展示该节点类型所依赖的上游字段列表（如 `balance_check` 依赖 `leave_type`、`start_date`、`end_date`）。
2. WHEN HR 保存节点列表时，THE Flow_Config_API SHALL 检查每个节点所需的依赖字段是否由其前置节点提供，若存在缺失则在响应中返回警告信息（不阻止保存）。
3. THE Flow_Config_UI SHALL 将后端返回的依赖警告以醒目样式展示给 HR，并说明具体缺失的字段名称。
