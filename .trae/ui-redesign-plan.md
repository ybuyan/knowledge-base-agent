# AI助手项目UI重设计计划

## 设计目标

保持主题色 `#e0301e`（红色）不变，打造**简约且高级**的视觉体验。

### 设计理念
- **极简主义**：减少视觉噪音，突出内容
- **精致细节**：微交互、过渡动画、阴影层次
- **一致性**：统一的设计语言和组件规范
- **高级感**：留白、 typography、材质感

---

## 一、设计系统重构

### 1.1 色彩系统优化

#### 主色调（保持不变）
```css
--primary-color: #e0301e;
--primary-light: #ff4d3a;
--primary-dark: #b52616;
--primary-bg-light: #fef0ef;
```

#### 中性色（高级灰）
```css
/* 背景色 */
--bg-primary: #ffffff;           /* 主背景 */
--bg-secondary: #fafafa;         /* 次级背景 */
--bg-tertiary: #f5f5f5;          /* 三级背景 */
--bg-elevated: #ffffff;          /* 悬浮卡片 */

/* 文字色 */
--text-primary: #1a1a1a;         /* 主文字 - 近黑 */
--text-secondary: #666666;       /* 次级文字 */
--text-tertiary: #999999;        /* 辅助文字 */
--text-disabled: #c4c4c4;        /* 禁用文字 */
--text-inverse: #ffffff;         /* 反色文字 */

/* 边框色 */
--border-light: #f0f0f0;         /* 浅色边框 */
--border-default: #e8e8e8;       /* 默认边框 */
--border-strong: #d9d9d9;        /* 强调边框 */
```

#### 功能色（更柔和）
```css
--success-color: #52c41a;
--success-bg: #f6ffed;
--warning-color: #faad14;
--warning-bg: #fffbe6;
--error-color: #ff4d4f;
--error-bg: #fff2f0;
--info-color: #1890ff;
--info-bg: #e6f7ff;
```

### 1.2 字体系统（新增）

```css
/* 字体族 */
--font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;

/* 字号层级 */
--font-size-xs: 12px;      /* 辅助文字 */
--font-size-sm: 13px;      /* 小字 */
--font-size-base: 14px;    /* 正文 */
--font-size-md: 16px;      /* 中等 */
--font-size-lg: 18px;      /* 大标题 */
--font-size-xl: 20px;      /* 页面标题 */
--font-size-2xl: 24px;     /* 大标题 */

/* 字重 */
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

/* 行高 */
--line-height-tight: 1.25;
--line-height-normal: 1.5;
--line-height-relaxed: 1.75;
```

### 1.3 间距系统（8px基准）

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
```

### 1.4 阴影系统（更细腻）

```css
--shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.04);
--shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.06);
--shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
--shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.10);
--shadow-xl: 0 16px 48px rgba(0, 0, 0, 0.12);

/* 悬浮阴影 */
--shadow-hover: 0 8px 24px rgba(224, 48, 30, 0.12);
```

### 1.5 圆角系统

```css
--radius-sm: 6px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-full: 9999px;
```

---

## 二、组件重设计

### 2.1 按钮组件

#### 主按钮
- 背景：渐变 `linear-gradient(135deg, #e0301e, #ff4d3a)`
- 圆角：8px
- 阴影：`0 2px 8px rgba(224, 48, 30, 0.25)`
- Hover：上浮 + 阴影增强
- 过渡：0.2s ease

#### 次级按钮
- 背景：透明
- 边框：1px solid #e8e8e8
- Hover：背景 #fafafa

#### 图标按钮
- 尺寸：32x32px
- 圆角：8px
- Hover：背景 rgba(224, 48, 30, 0.08)

### 2.2 输入框

- 背景：#fafafa
- 边框：1px solid transparent（聚焦时显示主色）
- 圆角：10px
- 内边距：12px 16px
- 聚焦：外发光效果

### 2.3 卡片组件

- 背景：#ffffff
- 圆角：12px
- 阴影：--shadow-sm
- Hover：--shadow-md + 轻微上浮
- 边框：1px solid #f0f0f0（可选）

### 2.4 会话列表项

- 布局：图标 + 内容 + 操作
- 圆角：10px
- 内边距：12px 16px
- Hover：背景 #fafafa
- 选中：左边框 3px 主色 + 背景渐变

---

## 三、页面重设计

### 3.1 侧边栏重设计

#### 视觉风格
- 背景：纯白色 #ffffff
- 宽度：260px（更窄更精致）
- 分隔：右边框 1px solid #f0f0f0

#### 用户信息卡片
- 布局：头像 + 信息
- 头像：48px，圆角 12px
- 背景：渐变遮罩或纯色
- 悬停：轻微阴影

#### 新建按钮
- 全宽按钮
- 渐变背景
- 圆角 10px
- 图标 + 文字

#### 搜索框
- 背景：#f5f5f5
- 无边框
- 圆角 10px
- 占位符颜色：#999

#### 会话列表
- 分组标题：大写字母 + 字间距
- 列表项：更紧凑的间距
- 时间：灰色小字
- 操作按钮：悬浮显示

#### 底部导航
- 图标 + 文字
- 选中：主色 + 背景高亮
- 圆角：8px

### 3.2 聊天页面重设计

#### 整体布局
- 最大宽度：800px（居中）
- 背景：#fafafa
- 消息气泡：圆角 16px

#### 空状态
- 居中大图标
- 简洁文案
- 快捷操作按钮

#### 消息气泡
- 用户：主色渐变，白色文字
- AI：白色背景，细边框
- 圆角：16px（用户右下圆角小，AI左下圆角小）
- 阴影：轻微

#### 输入区域
- 悬浮卡片设计
- 圆角 16px
- 阴影：--shadow-md
- 发送按钮：圆形主色按钮

#### 引用来源
- 卡片式设计
- 左侧彩色边框
- 文件名 + 内容预览

### 3.3 文档管理页面重设计

#### 上传区域
- 虚线边框
- 拖拽高亮：主色边框
- 图标 + 文案
- 圆角 16px

#### 文档列表
- 卡片式或表格
- 状态标签：彩色圆点 + 文字
- 操作：图标按钮组
- 悬停：阴影 + 上浮

---

## 四、动画与交互

### 4.1 过渡动画

```css
/* 默认过渡 */
--transition-fast: 0.15s ease;
--transition-normal: 0.2s ease;
--transition-slow: 0.3s ease;

/* 弹性过渡 */
--transition-bounce: 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
```

### 4.2 页面过渡

- 淡入 + 轻微上移
- 时长：0.3s
- 缓动：ease-out

### 4.3 列表动画

- 新项目：滑入 + 淡入
- 删除：滑出 + 淡出
- 重排：平滑过渡

### 4.4 微交互

- 按钮点击：缩放 0.96
- 卡片悬停：上浮 2px + 阴影增强
- 输入聚焦：外发光
- 加载：骨架屏或优雅spinner

---

## 五、响应式设计

### 5.1 断点

```css
--breakpoint-sm: 640px;   /* 手机 */
--breakpoint-md: 768px;   /* 平板 */
--breakpoint-lg: 1024px;  /* 小桌面 */
--breakpoint-xl: 1280px;  /* 大桌面 */
```

### 5.2 移动端适配

- 侧边栏：抽屉式
- 聊天：全宽
- 底部导航：固定底部

---

## 六、实施计划

### 阶段一：设计系统（2天）
1. 重构全局CSS变量
2. 创建基础工具类
3. 定义字体和间距系统

### 阶段二：组件重构（3天）
1. 按钮组件
2. 输入框组件
3. 卡片组件
4. 列表项组件

### 阶段三：页面重构（4天）
1. 侧边栏
2. 聊天页面
3. 文档管理页面
4. 空状态和加载状态

### 阶段四：动画优化（2天）
1. 页面过渡
2. 列表动画
3. 微交互

### 阶段五：响应式（2天）
1. 移动端适配
2. 测试和优化

---

## 七、设计原则检查清单

- [ ] 保持主题色 #e0301e
- [ ] 足够的留白
- [ ] 一致的间距
- [ ] 清晰的视觉层级
- [ ] 流畅的动画
- [ ] 精致的细节
- [ ] 良好的对比度
- [ ] 响应式支持
