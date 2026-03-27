# AI助手项目UI重设计计划 V3
## 参考主流知识库问答系统风格

---

## 一、参考分析

### 1.1 ChatGPT / Claude 风格
- 简洁对话流，无侧边栏干扰
- 深色/浅色主题切换
- 消息气泡清晰区分
- 底部固定输入框
- 极简顶部导航

### 1.2 Notion 风格
- 侧边栏可折叠
- 面包屑导航
- 页面即文档的概念
- 丰富的内容块支持

### 1.3 Slack / Discord 风格
- 左侧频道/会话列表
- 中间消息区域
- 右侧成员/信息面板（可选）
- 紧凑高效的信息密度

### 1.4 综合最佳实践
结合以上优点，打造适合企业知识库问答的UI：
- **清晰的三栏布局**：导航 + 内容 + 辅助信息
- **对话为核心**：消息流为主视觉
- **文档管理便捷**：侧边栏快速访问
- **专业但不失温度**：企业级设计 + 友好交互

---

## 二、整体布局设计

### 2.1 布局结构
```
┌─────────────────────────────────────────────────────────────────────┐
│  Top Bar (固定顶部，极简)                                             │
│  [Logo]  AI知识助手                           [Theme] [Settings] [👤]│
├──────────┬──────────────────────────────────────────┬───────────────┤
│          │                                          │               │
│ Sidebar  │         Main Content Area                │ Right Panel   │
│ (240px)  │         (自适应，最大1200px)              │ (280px,可选)  │
│          │                                          │               │
│  🔍 搜索  │  ┌────────────────────────────────────┐  │  📚 知识库    │
│          │  │                                    │  │  📄 相关文档  │
│ 📁 文档   │  │     Chat / Document Content        │  │  💡 推荐问题  │
│          │  │                                    │  │               │
│ 💬 对话   │  │                                    │  │               │
│          │  │                                    │  │               │
│ [+ 新建]  │  └────────────────────────────────────┘  │               │
│          │                                          │               │
│ ──────── │  ┌────────────────────────────────────┐  │               │
│          │  │      Input Area (固定底部)          │  │               │
│ 👤 用户   │  │  [输入框...]              [发送]   │  │               │
│          │  └────────────────────────────────────┘  │               │
└──────────┴──────────────────────────────────────────┴───────────────┘
```

### 2.2 尺寸规范
```css
/* 顶部栏 */
--topbar-height: 56px;

/* 侧边栏 */
--sidebar-width: 240px;
--sidebar-collapsed: 60px;

/* 右侧面板 */
--right-panel-width: 280px;

/* 内容区 */
--content-max-width: 1200px;
--content-padding: 32px;

/* 输入区 */
--input-area-height: auto; /* 自适应 */
```

---

## 三、色彩系统

### 3.1 主色调（保持红色）
```css
--primary-color: #e0301e;
--primary-light: #ff4d3a;
--primary-dark: #b52616;
--primary-bg: rgba(224, 48, 30, 0.08);
```

### 3.2 浅色主题（默认）
```css
/* 背景 */
--bg-primary: #ffffff;
--bg-secondary: #f7f7f8;
--bg-tertiary: #f0f0f1;
--bg-sidebar: #f9f9f9;
--bg-hover: rgba(0, 0, 0, 0.04);
--bg-active: rgba(224, 48, 30, 0.08);

/* 文字 */
--text-primary: #1f1f1f;
--text-secondary: #5f5f5f;
--text-tertiary: #8e8e8e;
--text-disabled: #b4b4b4;

/* 边框 */
--border-light: #e5e5e5;
--border-default: #d1d1d1;
--border-strong: #b4b4b4;

/* 阴影 */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
--shadow-lg: 0 12px 36px rgba(0, 0, 0, 0.12);
```

### 3.3 深色主题（可选）
```css
--bg-primary: #1f1f1f;
--bg-secondary: #2d2d2d;
--bg-tertiary: #3d3d3d;
--text-primary: #ffffff;
--text-secondary: #b4b4b4;
```

---

## 四、组件设计

### 4.1 顶部栏 (Top Bar)
- 高度：56px
- 背景：白色/透明
- 底部边框：1px solid var(--border-light)
- 左侧：Logo + 产品名
- 右侧：主题切换、设置、用户头像
- 风格：极简，无多余元素

### 4.2 侧边栏 (Sidebar)

#### 整体风格
- 宽度：240px（可折叠到60px）
- 背景：#f9f9f9
- 右边框：1px solid var(--border-light)

#### 搜索框
```css
.search-box {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  padding: 10px 14px;
  margin: 12px;
}
```

#### 导航项
```css
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  margin: 2px 8px;
  border-radius: 8px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}
.nav-item.active {
  background: var(--bg-active);
  color: var(--primary-color);
}
```

#### 会话列表
- 分组标题：小字、灰色、大写
- 会话项：紧凑、hover显示操作
- 时间：灰色小字
- 选中：左侧竖线标记

#### 新建按钮
- 位置：侧边栏底部或顶部
- 样式：主色填充，圆角8px
- 全宽或自适应

### 4.3 对话区域 (Chat Area)

#### 消息气泡
```css
/* 用户消息 */
.message.user {
  align-self: flex-end;
  background: var(--primary-color);
  color: white;
  border-radius: 18px 18px 4px 18px;
  max-width: 80%;
}

/* AI消息 */
.message.assistant {
  align-self: flex-start;
  background: var(--bg-secondary);
  color: var(--text-primary);
  border-radius: 18px 18px 18px 4px;
  max-width: 80%;
  border: 1px solid var(--border-light);
}
```

#### 消息内容
- 字体：16px，行高1.6
- Markdown渲染
- 代码块：深色背景，语法高亮
- 引用来源：卡片式，左侧彩色边框

#### 头像
- 用户：圆形头像或首字母
- AI：品牌Logo或机器人图标
- 尺寸：32px

### 4.4 输入区域 (Input Area)

#### 样式
```css
.input-wrapper {
  background: white;
  border: 1px solid var(--border-default);
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.2s;
}
.input-wrapper:focus-within {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--bg-active);
}
```

#### 功能
- 多行输入（自动增高）
- 发送按钮（圆形主色）
- 附件按钮（可选）
- 快捷键提示（Enter发送，Shift+Enter换行）

### 4.5 右侧面板 (Right Panel)

#### 知识库
- 文档列表
- 搜索知识库
- 快捷引用

#### 推荐问题
- 基于上下文的建议
- 点击快速提问

#### 系统状态
- 模型信息
- 响应时间
- Token消耗（可选）

### 4.6 按钮组件

#### 主按钮
```css
.btn-primary {
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-weight: 500;
  transition: all 0.15s;
}
.btn-primary:hover {
  background: var(--primary-light);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
```

#### 次级按钮
```css
.btn-secondary {
  background: white;
  color: var(--text-secondary);
  border: 1px solid var(--border-default);
  border-radius: 8px;
  padding: 10px 16px;
}
.btn-secondary:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background: var(--bg-active);
}
```

#### 图标按钮
```css
.btn-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-tertiary);
  background: transparent;
  border: none;
  cursor: pointer;
}
.btn-icon:hover {
  background: var(--bg-hover);
  color: var(--text-secondary);
}
```

### 4.7 文档卡片
```css
.doc-card {
  background: white;
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.2s;
}
.doc-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-default);
}
```

---

## 五、页面详细设计

### 5.1 对话页面

#### 空状态
- 居中大标题："有什么可以帮您的？"
- 副标题：简短介绍
- 快捷问题：3-4个推荐问题卡片
- 底部：输入框

#### 有消息状态
- 消息流：从上到下，新消息在底部
- 自动滚动到底部
- 滚动时显示"新消息"提示
- 支持加载历史消息

#### 引用展示
- 悬浮卡片
- 文件名 + 内容预览
- 点击跳转原文

### 5.2 文档管理页面

#### 布局
- 左侧：文档分类/文件夹
- 中间：文档列表（卡片或表格）
- 顶部：搜索 + 上传按钮

#### 上传区域
- 拖拽上传
- 进度显示
- 状态标签（处理中/已完成/失败）

#### 文档列表
- 图标 + 文件名 + 状态 + 时间 + 操作
- 批量操作
- 排序和筛选

---

## 六、动画与交互

### 6.1 过渡时间
```css
--duration-instant: 100ms;
--duration-fast: 150ms;
--duration-normal: 200ms;
--duration-slow: 300ms;
```

### 6.2 缓动函数
```css
--ease-default: cubic-bezier(0.4, 0, 0.2, 1);
--ease-out: cubic-bezier(0, 0, 0.2, 1);
--ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
```

### 6.3 关键动画
- 侧边栏展开/收起：宽度变化 + 内容淡入淡出
- 消息出现：从底部滑入 + 淡入
- 按钮hover：背景色 + 轻微上浮
- 输入框聚焦：边框色 + 外发光
- 页面切换：淡入淡出

---

## 七、响应式设计

### 7.1 断点
```css
--bp-mobile: 640px;
--bp-tablet: 768px;
--bp-desktop: 1024px;
--bp-wide: 1440px;
```

### 7.2 移动端适配
- 侧边栏：抽屉式，从左侧滑出
- 右侧面板：折叠到底部或隐藏
- 输入框：固定在底部
- 消息气泡：宽度90%

### 7.3 平板适配
- 侧边栏：可折叠
- 右侧面板：可隐藏
- 内容区：自适应

---

## 八、实施计划

### 阶段一：基础架构（2天）
1. 重构全局CSS变量
2. 搭建新布局框架
3. 配置主题系统

### 阶段二：核心组件（3天）
1. 顶部栏
2. 侧边栏（可折叠）
3. 消息气泡组件
4. 输入框组件

### 阶段三：页面实现（4天）
1. 对话页面
2. 文档管理页面
3. 空状态和加载状态
4. 错误页面

### 阶段四：高级功能（2天）
1. 主题切换（深色/浅色）
2. 响应式适配
3. 动画优化

### 阶段五：测试优化（2天）
1. 跨浏览器测试
2. 性能优化
3. 细节调整

---

## 九、设计原则

1. **内容优先**：减少装饰，突出对话内容
2. **高效导航**：侧边栏快速切换，搜索便捷
3. **清晰反馈**：操作有响应，状态明确
4. **一致性**：全站设计语言统一
5. **可访问性**：良好的对比度，支持键盘操作
6. **响应式**：多端体验一致

---

## 十、参考截图描述

### 对话界面
```
┌────────────────────────────────────────────────────────────┐
│  AI知识助手                                    [🌙] [⚙️] [👤]│
├────────┬───────────────────────────────────────┬───────────┤
│        │                                       │           │
│ 🔍     │  👤 你好，请问有什么可以帮助您的？      │  💡 推荐   │
│        │                                       │  ─────────  │
│ 📁     │  🤖 您好！我是AI助手，可以帮您：        │  • 如何... │
│ 文档   │                                       │  • 什么... │
│        │  1. 查询知识库文档                      │  • 怎么... │
│ 💬     │  2. 解答常见问题                        │           │
│ 对话   │  3. 协助处理任务                        │  📚 知识库 │
│        │                                       │  ─────────  │
│ [+]    │  有什么我可以帮您的吗？                 │  📄 文档1  │
│        │                                       │  📄 文档2  │
│ ─────  │                                       │           │
│        │                                       │           │
│ 👤 用户│                                       │           │
│        │                                       │           │
│        │  ┌─────────────────────────────────┐  │           │
│        │  │  请输入您的问题...      [⬆️]   │  │           │
│        │  └─────────────────────────────────┘  │           │
└────────┴───────────────────────────────────────┴───────────┘
```

这种设计融合了ChatGPT的对话体验、Slack的侧边栏导航、Notion的文档管理，打造专业且易用的企业知识库问答系统。
