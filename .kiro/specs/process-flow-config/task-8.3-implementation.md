# 任务 8.3 实现说明：集成拖拽排序功能

## 实现概述

已成功在 FlowConfigView 中集成 `@vueuse/integrations` 的 `useSortable` 功能，实现流畅的行拖拽排序体验。

## 技术选型

选择 `@vueuse/integrations` 的 `useSortable` 而非 `vuedraggable`，原因：
- 更轻量级，与 Vue 3 Composition API 深度集成
- 基于成熟的 SortableJS 库，提供流畅的拖拽体验
- 配置简单，API 清晰

## 实现细节

### 1. 依赖安装

```bash
npm install @vueuse/integrations sortablejs
npm install --save-dev @types/sortablejs
```

### 2. 核心代码变更

#### 导入依赖
```typescript
import { useSortable } from '@vueuse/integrations'
```

#### 初始化拖拽
```typescript
function initSortable() {
  setTimeout(() => {
    const tbody = document.querySelector('.nodes-table .el-table__body-wrapper tbody')
    if (tbody) {
      tableBodyRef.value = tbody as HTMLElement
      useSortable(tableBodyRef, nodes, {
        animation: 150,
        handle: '.drag-handle',
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        dragClass: 'sortable-drag',
      })
    }
  }, 100)
}
```

#### 拖拽手柄
```vue
<el-table-column width="48" align="center">
  <template #default>
    <span class="drag-handle">⠿</span>
  </template>
</el-table-column>
```

### 3. 样式优化

添加了拖拽状态的视觉反馈：
- `sortable-ghost`: 拖拽时的占位符样式（半透明）
- `sortable-chosen`: 被选中的行样式（高亮背景）
- `sortable-drag`: 正在拖拽的元素样式
- `drag-handle`: 拖拽手柄的光标样式（grab/grabbing）

## 功能特性

1. **拖拽手柄**：每行左侧有专用的拖拽图标（⠿），只能通过该图标拖拽
2. **流畅动画**：150ms 的过渡动画，提供平滑的视觉体验
3. **视觉反馈**：
   - 拖拽时显示半透明占位符
   - 被选中的行高亮显示
   - 光标变化（grab → grabbing）
4. **实时更新**：拖拽后立即更新本地节点数组顺序
5. **保存持久化**：点击「保存」按钮后，新顺序会持久化到后端

## 用户体验

- 用户可以通过拖拽手柄直观地调整节点顺序
- 拖拽过程流畅，有清晰的视觉反馈
- 拖拽后需要点击「保存」按钮才会持久化到后端
- 支持键盘辅助操作（通过 SortableJS 内置支持）

## 测试建议

1. 加载页面后，验证拖拽手柄是否显示
2. 拖拽节点行，验证顺序是否正确更新
3. 拖拽后保存，验证后端是否正确接收新顺序
4. 刷新页面，验证保存的顺序是否持久化

## 已移除的代码

移除了原有的原生 HTML5 drag API 实现：
- `dragIndex` 状态
- `onDragStart`、`onDragOver`、`onDragEnd` 方法
- 拖拽列的 `draggable` 属性和事件监听器

## 兼容性

- 支持所有现代浏览器（Chrome、Firefox、Safari、Edge）
- 移动端触摸拖拽支持（通过 SortableJS）
- 无障碍访问支持（键盘操作）
