# AI助手项目UI重设计计划 V2

## 参考风格分析

基于PwC DC HR Hub的设计风格：
- **整体风格**：极简、干净、专业
- **配色**：白色主背景 + 浅灰背景 + 品牌色点缀
- **布局**：左侧图标导航 + 顶部筛选栏 + 内容区域
- **圆角**：大圆角设计（12-16px）
- **阴影**：极淡或无边框阴影
- **字体**：干净的无衬线字体，层次分明

---

## 一、色彩系统（基于参考风格）

### 1.1 主色调（保持红色主题）
```css
--primary-color: #e0301e;
--primary-light: #ff4d3a;
--primary-dark: #b52616;
--primary-bg: #fef0ef;
```

### 1.2 中性色（参考风格）
```css
/* 背景色 */
--bg-primary: #ffffff;           /* 纯白主背景 */
--bg-secondary: #f8f9fa;         /* 浅灰次级背景 */
--bg-tertiary: #f0f2f5;          /* 更浅灰 */
--bg-sidebar: #ffffff;           /* 侧边栏纯白 */

/* 文字色 */
--text-primary: #1a1a2e;         /* 深蓝黑 - 标题 */
--text-secondary: #4a4a68;       /* 中灰蓝 - 正文 */
--text-tertiary: #8b8ba7;        /* 浅灰 - 辅助 */
--text-muted: #a0a0b8;           /* 更浅 - 禁用 */

/* 边框色 */
--border-light: #f0f0f5;         /* 极浅边框 */
--border-default: #e8e8ed;       /* 默认边框 */
--border-strong: #d0d0d8;        /* 强调边框 */
```

### 1.3 功能色
```css
--success-color: #10b981;
--success-bg: #ecfdf5;
--warning-color: #f59e0b;
--warning-bg: #fffbeb;
--error-color: #ef4444;
--error-bg: #fef2f2;
--info-color: #3b82f6;
--info-bg: #eff6ff;
```

---

## 二、布局系统（参考风格）

### 2.1 整体结构
```
┌─────────────────────────────────────────────────────────────┐
│  Header (固定顶部)                                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Logo/Title          [Stats]              User Avatar  │  │
│  └───────────────────────────────────────────────────────┘  │
├───────┬─────────────────────────────────────────────────────┤
│       │  Filter Bar (筛选栏)                                │
│ Side  │  ┌─────────────────────────────────────────────┐    │
│ Nav   │  │ [Tab1] [Tab2] | [Filter1] [Filter2] [Btn]   │    │
│ (60px)│  └─────────────────────────────────────────────┘    │
│       │                                                     │
│  🔍   │  Content Area (内容区域)                            │
│  📁   │  ┌─────────────────────────────────────────────┐    │
│  📊   │  │                                             │    │
│       │  │              Main Content                   │    │
│       │  │                                             │    │
│       │  └─────────────────────────────────────────────┘    │
│       │                                                     │
└───────┴─────────────────────────────────────────────────────┘
```

### 2.2 尺寸规范
```css
/* 侧边栏 */
--sidebar-width: 60px;           /* 窄侧边栏 */
--sidebar-icon-size: 24px;       /* 图标大小 */

/* 顶部栏 */
--header-height: 64px;           /* 顶部高度 */
--filter-bar-height: 56px;       /* 筛选栏高度 */

/* 内容区 */
--content-max-width: 1400px;     /* 最大宽度 */
--content-padding: 24px;         /* 内边距 */

/* 卡片 */
--card-border-radius: 12px;      /* 大圆角 */
--card-padding: 20px;            /* 卡片内边距 */
```

---

## 三、组件设计

### 3.1 侧边栏导航
- 宽度：60px（极简图标导航）
- 背景：纯白色
- 图标：24px，灰色默认，红色选中
- 选中状态：左侧3px红色竖线 + 背景微红
- 无文字标签（hover显示tooltip）

### 3.2 顶部栏
- 高度：64px
- 背景：白色
- 底部边框：1px solid #f0f0f5
- 左侧：Logo/标题
- 右侧：用户头像（圆形）

### 3.3 筛选栏（Filter Bar）
- 高度：56px
- 背景：透明或#f8f9fa
- Tab切换：文字 + 下划线
- 筛选器：圆角输入框/下拉框
- 按钮：圆角矩形，主色背景

### 3.4 按钮样式
```css
/* 主按钮 */
.btn-primary {
  background: var(--primary-color);
  color: white;
  border-radius: 8px;
  padding: 8px 20px;
  font-weight: 500;
  border: none;
  transition: all 0.2s;
}
.btn-primary:hover {
  background: var(--primary-light);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(224, 48, 30, 0.2);
}

/* 次级按钮 */
.btn-secondary {
  background: white;
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 8px 16px;
}
.btn-secondary:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
}

/* 图标按钮 */
.btn-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  background: transparent;
}
.btn-icon:hover {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}
```

### 3.5 输入框
```css
.input-field {
  background: white;
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  transition: all 0.2s;
}
.input-field:focus {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(224, 48, 30, 0.08);
  outline: none;
}
```

### 3.6 卡片/面板
```css
.card {
  background: white;
  border-radius: 12px;
  border: 1px solid var(--border-light);
  padding: 20px;
}
.card-hover:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border-color: var(--border-default);
}
```

### 3.7 表格
```css
.table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}
.table th {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 500;
  font-size: 13px;
  padding: 12px 16px;
  text-align: left;
}
.table td {
  padding: 16px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-primary);
}
.table tr:hover td {
  background: var(--bg-secondary);
}
```

### 3.8 Tab切换
```css
.tabs {
  display: flex;
  gap: 24px;
  border-bottom: 1px solid var(--border-light);
}
.tab {
  padding: 12px 4px;
  color: var(--text-tertiary);
  font-weight: 500;
  cursor: pointer;
  position: relative;
  transition: color 0.2s;
}
.tab:hover {
  color: var(--text-secondary);
}
.tab.active {
  color: var(--primary-color);
}
.tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--primary-color);
  border-radius: 2px 2px 0 0;
}
```

---

## 四、页面重设计

### 4.1 聊天页面布局
```
┌─────────────────────────────────────────────────────────────┐
│  Header                                                     │
│  AI助手                              [统计信息]    [用户]   │
├───────┬─────────────────────────────────────────────────────┤
│       │  Chat Tabs                                          │
│  💬   │  [对话] [历史记录] | [搜索框]          [新建对话]   │
│       │                                                     │
│  📁   │  ┌─────────────────────────────────────────────┐    │
│       │  │                                             │    │
│       │  │              Chat Messages                  │    │
│       │  │                                             │    │
│       │  │                                             │    │
│       │  └─────────────────────────────────────────────┘    │
│       │  ┌─────────────────────────────────────────────┐    │
│       │  │ [输入框...]                        [发送]   │    │
│       │  └─────────────────────────────────────────────┘    │
└───────┴─────────────────────────────────────────────────────┘
```

### 4.2 文档管理页面布局
```
┌─────────────────────────────────────────────────────────────┐
│  Header                                                     │
├───────┬─────────────────────────────────────────────────────┤
│       │  Doc Tabs                                           │
│  💬   │  [全部文档] [处理中] [已完成] | [搜索]   [上传]     │
│       │                                                     │
│  📁   │  ┌─────────────────────────────────────────────┐    │
│       │  │  Drag & Drop Upload Area                      │    │
│       │  └─────────────────────────────────────────────┘    │
│       │                                                     │
│       │  ┌─────────────────────────────────────────────┐    │
│       │  │  Documents Table                              │    │
│       │  │  文件名 | 状态 | 大小 | 时间 | 操作           │    │
│       │  └─────────────────────────────────────────────┘    │
└───────┴─────────────────────────────────────────────────────┘
```

---

## 五、动画规范

### 5.1 过渡时间
```css
--duration-fast: 150ms;
--duration-normal: 200ms;
--duration-slow: 300ms;
```

### 5.2 缓动函数
```css
--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-in: cubic-bezier(0.4, 0, 1, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### 5.3 交互动画
- 按钮hover：背景色变化 + 轻微上浮（2px）
- 卡片hover：阴影出现
- Tab切换：下划线滑动
- 侧边栏选中：左侧竖线 + 背景色
- 页面切换：淡入淡出

---

## 六、实施计划

### 阶段一：全局样式重构（2天）
1. 更新CSS变量系统
2. 创建新的工具类
3. 配置Element Plus主题

### 阶段二：布局组件（2天）
1. 新侧边栏（60px图标导航）
2. 顶部Header
3. 筛选栏组件
4. Tab组件

### 阶段三：页面重构（4天）
1. 聊天页面重设计
2. 文档管理页面重设计
3. 空状态和加载状态

### 阶段四：细节优化（2天）
1. 动画效果
2. 响应式适配
3. 细节调整

---

## 七、设计原则

1. **极简**：去除不必要的装饰，留白充足
2. **一致性**：所有组件遵循统一的设计语言
3. **层次清晰**：通过颜色、字号、间距建立视觉层级
4. **反馈明确**：hover、active状态清晰可见
5. **专业感**：圆角、阴影、过渡都保持克制
