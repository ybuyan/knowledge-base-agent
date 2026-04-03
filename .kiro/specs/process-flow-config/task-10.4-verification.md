# 任务 10.4 验证文档

## 功能说明
若保存响应中的 `warnings` 非空，用 `el-alert` 展示依赖警告，列出缺失字段名称。

## 实现位置
- **文件**: `frontend/src/views/FlowConfig/FlowConfigView.vue`
- **行数**: 179-187 (template 部分)

## 实现细节

### 1. 数据结构
```typescript
const warnings = ref<string[]>([])
```

### 2. 保存逻辑
```typescript
async function saveNodes() {
  saving.value = true
  warnings.value = []  // 清空之前的警告
  nodeErrors.value = {}
  try {
    const res = await flowConfigApi.saveNodes(SKILL_ID, nodes.value)
    if (res.warnings?.length) warnings.value = res.warnings  // 接收后端警告
    ElMessage.success('保存成功')
    // ...
  }
}
```

### 3. UI 展示
```vue
<!-- 依赖警告 -->
<el-alert
  v-if="warnings.length"
  type="warning"
  :closable="false"
  style="margin-bottom: 16px"
>
  <div v-for="w in warnings" :key="w" style="font-size: 13px">⚠ {{ w }}</div>
</el-alert>
```

## 警告信息格式
后端返回的警告格式（来自 `backend/app/api/routes/flow_config.py`）：
```
节点「{node.title}」({node.type}) 依赖字段 {missing}，但前置节点未提供
```

示例：
```
节点「校验假期余额」(balance_check) 依赖字段 ['leave_type', 'start_date', 'end_date']，但前置节点未提供
```

## 手动测试步骤

### 测试场景 1：正常配置（无警告）
1. 启动前后端服务
2. 以 HR 角色登录
3. 进入「流程配置」页面
4. 保持当前节点顺序不变（正确的依赖顺序）
5. 点击「保存」
6. **预期结果**: 显示"保存成功"，不显示警告

### 测试场景 2：触发依赖警告
1. 进入「流程配置」页面
2. 将「校验假期余额」节点拖拽到「获取用户信息」节点之后（第2位）
3. 此时「校验假期余额」前面没有提供 `leave_type`、`start_date`、`end_date` 字段的节点
4. 点击「保存」
5. **预期结果**: 
   - 显示"保存成功"（警告不阻止保存）
   - 在页面顶部显示黄色警告框
   - 警告内容包含：节点标题、类型、缺失的字段列表

### 测试场景 3：多个警告
1. 删除所有 `info_collect` 类型的节点
2. 保留「校验假期余额」和「提交申请」节点
3. 点击「保存」
4. **预期结果**: 
   - 显示多条警告（如果多个节点缺少依赖）
   - 每条警告单独一行显示

## 验收标准检查

✅ **任务要求 1**: 若 `warnings` 非空，用 `el-alert` 展示依赖警告
- 实现：使用 `v-if="warnings.length"` 条件渲染 `el-alert`

✅ **任务要求 2**: 列出缺失字段名称，让用户知道哪些节点的依赖关系有问题
- 实现：警告信息包含节点标题、类型和缺失字段列表

✅ **任务要求 3**: 警告不阻止保存，但需要提醒用户注意
- 实现：后端在校验通过后才检查依赖，警告不影响保存成功
- UI 使用醒目的黄色警告样式（`type="warning"`）

## 相关代码文件
- 前端：`frontend/src/views/FlowConfig/FlowConfigView.vue`
- 后端：`backend/app/api/routes/flow_config.py` (第 40-56 行：`_check_dependencies` 函数)
- API：`frontend/src/api/index.ts` (`flowConfigApi.saveNodes`)

## 依赖检查逻辑
后端检查的节点类型及其依赖字段（`_NODE_REQUIRED_FIELDS`）：
```python
{
    "balance_check": ["username", "leave_type", "start_date", "end_date"],
    "process_submit": [],
    "fetch_user_info": [],
    "info_collect": [],
    "text_info": [],
}
```

字段提供来源：
- `info_collect` 节点：提供 `params.fields` 中定义的所有字段
- `fetch_user_info` 节点：提供 `params.fields` 中列出的字段（默认：username, display_name, department, email, role）
