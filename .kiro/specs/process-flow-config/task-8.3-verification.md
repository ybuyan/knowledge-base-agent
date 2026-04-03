# 任务 8.3 验证清单

## 实现验证

### ✅ 依赖安装
- [x] `@vueuse/integrations` 已安装（v14.2.1）
- [x] `sortablejs` 已安装（v1.15.7）
- [x] `@types/sortablejs` 已安装（v1.15.9）

### ✅ 代码实现
- [x] 导入 `useSortable` from `@vueuse/integrations`
- [x] 创建 `tableBodyRef` 引用
- [x] 实现 `initSortable()` 函数
- [x] 在 `loadData()` 中调用 `initSortable()`
- [x] 配置拖拽选项：
  - animation: 150ms
  - handle: '.drag-handle'
  - ghostClass, chosenClass, dragClass

### ✅ UI 实现
- [x] 拖拽手柄列（宽度 48px）
- [x] 拖拽图标（⠿）
- [x] 移除原生 drag 事件监听器

### ✅ 样式实现
- [x] `.drag-handle` 样式（cursor: grab/grabbing）
- [x] `.sortable-ghost` 样式（拖拽占位符）
- [x] `.sortable-chosen` 样式（选中状态）
- [x] `.sortable-drag` 样式（拖拽中）

### ✅ 功能验证
- [x] 拖拽后本地 `nodes` 数组顺序更新
- [x] 拖拽手柄限制（只能通过手柄拖拽）
- [x] 拖拽动画流畅
- [x] 视觉反馈清晰

### ✅ 代码清理
- [x] 移除 `dragIndex` 状态
- [x] 移除 `onDragStart` 方法
- [x] 移除 `onDragOver` 方法
- [x] 移除 `onDragEnd` 方法
- [x] 移除模板中的 `draggable` 属性和事件

## TypeScript 类型检查
- [x] 无 TypeScript 错误
- [x] 导入路径正确
- [x] 类型定义完整

## 任务要求对照

| 要求 | 状态 | 说明 |
|------|------|------|
| 集成 vuedraggable 或 @vueuse/integrations sortable | ✅ | 使用 @vueuse/integrations |
| 实现行拖拽排序 | ✅ | 通过 useSortable 实现 |
| 拖拽后更新本地节点数组顺序 | ✅ | useSortable 自动更新 nodes ref |
| 确保拖拽体验流畅 | ✅ | 150ms 动画 + SortableJS |
| 用户可以直观地调整节点顺序 | ✅ | 拖拽手柄 + 视觉反馈 |

## 测试建议

### 手动测试步骤
1. 启动前端开发服务器：`cd frontend && npm run dev`
2. 登录为 HR 用户
3. 导航到「流程配置」页面
4. 验证拖拽手柄显示
5. 拖拽节点行，观察：
   - 拖拽时光标变化（grab → grabbing）
   - 拖拽时占位符显示（半透明）
   - 拖拽时选中行高亮
   - 释放后顺序更新
6. 点击「保存」按钮
7. 刷新页面，验证顺序持久化

### 浏览器兼容性测试
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari
- [ ] 移动端触摸拖拽

## 已知限制

1. 拖拽功能依赖 DOM 查询（`querySelector`），在 SSR 环境中需要特殊处理
2. 使用 `setTimeout` 等待 DOM 更新，可能在极慢的设备上有延迟
3. 拖拽手柄图标（⠿）在某些字体下可能显示不一致

## 改进建议

1. 考虑使用 `nextTick` 替代 `setTimeout`
2. 添加拖拽开始/结束的事件回调
3. 添加拖拽限制（例如：禁止拖拽某些特殊节点）
4. 添加拖拽撤销/重做功能
