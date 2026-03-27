# 内容保护功能

## 功能概述

为了保护公司制度文档的版权和安全性，系统实现了以下内容保护功能：

## 已实现的保护措施

### 1. 禁用复制功能

#### 移除复制按钮
- 移除了助手回复消息下方的"复制"按钮
- 位置：`frontend/src/views/Chat/ChatContent.vue`

#### 禁用文本选择
- 通过 CSS 禁用助手回复内容的文本选择
- 使用 `user-select: none` 属性
- 仅针对助手回复，用户消息仍可选择

```css
.message.assistant .message-text {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}
```

#### 禁用键盘复制快捷键
- 拦截 `Ctrl+C` / `Cmd+C` 快捷键
- 检测选中内容是否在助手消息中
- 如果是，则阻止复制操作

### 2. 禁用右键菜单

- 在助手回复内容上禁用右键菜单
- 防止通过右键菜单复制内容
- 实现方式：`@contextmenu` 事件处理

### 3. 禁用代码块复制

- 移除了代码块中的"复制"按钮
- 位置：`frontend/src/utils/markdown.ts`
- 代码块内容同样受文本选择禁用保护

### 4. 禁用链接下载

- 自定义链接渲染规则
- 移除 `download` 属性
- 添加 `onclick="return false;"` 阻止默认行为
- 链接仅用于显示，不可点击下载

## 技术实现

### 前端保护层级

1. **UI 层**：移除复制/下载按钮
2. **CSS 层**：禁用文本选择
3. **事件层**：拦截右键菜单和键盘快捷键
4. **渲染层**：自定义 Markdown 渲染规则

### 代码位置

- `frontend/src/views/Chat/ChatContent.vue` - 聊天界面保护
- `frontend/src/utils/markdown.ts` - Markdown 渲染保护

## 用户体验

### 保护的内容
- ✓ 助手的回复内容
- ✓ 代码块内容
- ✓ 链接和下载

### 不受影响的功能
- ✓ 用户自己的消息可以复制
- ✓ 正常的阅读和浏览
- ✓ 界面交互和操作

## 安全说明

### 前端保护的局限性

前端保护措施可以防止普通用户的复制和下载行为，但无法完全防止技术用户：

1. 浏览器开发者工具可以查看 DOM 内容
2. 网络请求可以被拦截
3. 截图和屏幕录制无法阻止

### 建议的额外措施

如需更强的保护，建议：

1. **后端保护**
   - 添加水印（包含用户 ID 和时间戳）
   - 限制查询频率
   - 记录所有查询日志

2. **访问控制**
   - 用户身份验证
   - 权限分级管理
   - 敏感内容脱敏

3. **审计追踪**
   - 记录所有查询和回复
   - 异常行为检测
   - 定期审计报告

## 测试验证

### 测试场景

1. **复制测试**
   - [ ] 无法通过鼠标选择助手回复内容
   - [ ] 无法通过 Ctrl+C 复制助手回复
   - [ ] 无法通过右键菜单复制
   - [ ] 代码块无复制按钮

2. **下载测试**
   - [ ] 链接无法点击下载
   - [ ] 无 download 属性

3. **用户体验测试**
   - [ ] 用户消息仍可正常复制
   - [ ] 界面操作流畅
   - [ ] 无明显性能影响

## 维护说明

### 如需临时启用复制功能

1. 注释掉 CSS 中的 `user-select: none`
2. 移除 `handleContextMenu` 和 `handleKeyDown` 事件处理
3. 恢复复制按钮

### 如需调整保护级别

可以通过配置文件控制保护功能的开关：

```typescript
// config/security.ts
export const contentProtection = {
  disableCopy: true,
  disableContextMenu: true,
  disableKeyboardShortcuts: true,
  disableDownload: true
}
```

## 更新日志

- 2024-01-XX: 初始实现内容保护功能
  - 禁用复制
  - 禁用右键菜单
  - 禁用下载
  - 禁用代码块复制
