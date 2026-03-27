# 公司制度问答系统 - UI设计规范

## 文档信息
- **项目名称**: 公司制度问答与流程指引助手
- **文档类型**: UI设计规范
- **版本**: v1.0
- **更新日期**: 2026年3月22日

---

## 目录

1. [设计原则](#一设计原则)
2. [色彩系统](#二色彩系统)
3. [排版规范](#三排版规范)
4. [间距系统](#四间距系统)
5. [圆角与阴影](#五圆角与阴影)
6. [组件规范](#六组件规范)
7. [交互模式](#七交互模式)
8. [实现指南](#八实现指南)

---

## 一、设计原则

### 1.1 设计理念

**简洁、专业、可信**

- **简洁**: 减少视觉噪音，聚焦核心内容
- **专业**: 体现企业级产品的严谨性
- **可信**: 通过一致的视觉语言建立用户信任

### 1.2 设计目标

1. **提升可读性**: 清晰的信息层级，舒适的阅读体验
2. **增强可操作性**: 明确的交互反馈，直观的操作引导
3. **保持一致性**: 统一的视觉语言，连贯的用户体验
4. **建立品牌感**: 体现企业专业形象，增强品牌认知

---

## 二、色彩系统

### 2.1 主色调

```
Primary Color (品牌主色)
├── 主色: #2563EB (蓝色)
├── 浅色: #3B82F6
├── 深色: #1D4ED8
└── 最浅: #EFF6FF (背景用)

Semantic Colors (语义色)
├── Success: #10B981 (绿色)
├── Warning: #F59E0B (橙色)
├── Error:   #EF4444 (红色)
└── Info:    #3B82F6 (蓝色)
```

### 2.2 中性色阶

```
Gray Scale (灰度色阶)
├── Gray-50:  #F9FAFB  (最浅背景)
├── Gray-100: #F3F4F6  (浅背景)
├── Gray-200: #E5E7EB  (边框、分割线)
├── Gray-300: #D1D5DB  (禁用状态)
├── Gray-400: #9CA3AF  (次要文字)
├── Gray-500: #6B7280  (辅助文字)
├── Gray-600: #4B5563  (正文)
├── Gray-700: #374151  (标题)
├── Gray-800: #1F2937  (深标题)
└── Gray-900: #111827  (最深)
```

### 2.3 功能色应用

| 用途 | 颜色 | 应用场景 |
|------|------|---------|
| 主按钮 | #2563EB | 主要操作按钮 |
| 次按钮 | #6B7280 | 次要操作按钮 |
| 危险操作 | #EF4444 | 删除、中止等 |
| 成功状态 | #10B981 | 完成、成功提示 |
| 警告状态 | #F59E0B | 警告、注意提示 |
| 链接文字 | #2563EB | 可点击链接 |
| 边框 | #E5E7EB | 组件边框 |
| 背景 | #F9FAFB | 页面背景 |
| 卡片背景 | #FFFFFF | 内容卡片 |

### 2.4 色彩使用规范

**背景色使用**
```css
--bg-primary: #FFFFFF;      /* 主背景 - 白色 */
--bg-secondary: #F9FAFB;    /* 次级背景 - 浅灰 */
--bg-tertiary: #F3F4F6;     /* 三级背景 - 更浅灰 */
--bg-hover: #F3F4F6;        /* 悬停背景 */
--bg-active: #EFF6FF;       /* 激活背景 - 蓝色浅 */
```

**文字色使用**
```css
--text-primary: #111827;    /* 主文字 - 深黑 */
--text-secondary: #4B5563;  /* 次级文字 */
--text-tertiary: #6B7280;   /* 辅助文字 */
--text-disabled: #9CA3AF;   /* 禁用文字 */
--text-link: #2563EB;       /* 链接文字 */
```

**边框色使用**
```css
--border-light: #E5E7EB;    /* 浅色边框 */
--border-medium: #D1D5DB;   /* 中等边框 */
--border-focus: #2563EB;    /* 聚焦边框 */
```

---

## 三、排版规范

### 3.1 字体系统

```
Font Family
├── 主字体: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial
├── 中文: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei"
└── 等宽: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono"

Font Size Scale
├── 2xs: 10px  (标签、徽章)
├── xs:  12px  (辅助文字、时间戳)
├── sm:  14px  (正文、按钮)
├── base: 16px (默认正文)
├── lg:  18px  (小标题)
├── xl:  20px  (标题)
├── 2xl: 24px  (大标题)
└── 3xl: 30px  (页面标题)
```

### 3.2 字重规范

```css
--font-weight-normal: 400;   /* 正文 */
--font-weight-medium: 500;   /* 强调 */
--font-weight-semibold: 600; /* 标题 */
--font-weight-bold: 700;     /* 重要标题 */
```

### 3.3 行高规范

```css
--line-height-tight: 1.25;   /* 紧凑 - 标题 */
--line-height-normal: 1.5;   /* 正常 - 正文 */
--line-height-relaxed: 1.75; /* 宽松 - 长文本 */
```

### 3.4 排版组合

| 元素 | 字号 | 字重 | 行高 | 颜色 |
|------|------|------|------|------|
| 页面标题 | 24px | 600 | 1.25 | Gray-900 |
| 卡片标题 | 18px | 600 | 1.25 | Gray-800 |
| 正文 | 16px | 400 | 1.5 | Gray-700 |
| 辅助文字 | 14px | 400 | 1.5 | Gray-500 |
| 标签文字 | 12px | 500 | 1.25 | Gray-500 |
| 时间戳 | 12px | 400 | 1.25 | Gray-400 |

---

## 四、间距系统

### 4.1 间距规范

```
Spacing Scale (4px base)
├── space-1: 4px   (极小间距)
├── space-2: 8px   (小间距)
├── space-3: 12px  (中间距)
├── space-4: 16px  (标准间距)
├── space-5: 20px  (大间距)
├── space-6: 24px  (较大间距)
├── space-8: 32px  (大间距)
└── space-10: 40px (超大间距)
```

### 4.2 间距应用

**组件内间距**
- 按钮内边距: 8px 16px (sm) / 10px 20px (md)
- 卡片内边距: 16px ~ 24px
- 输入框内边距: 12px 16px
- 列表项间距: 8px ~ 12px

**组件间间距**
- 相关元素: 8px
- 相邻组件: 16px
- 区块间距: 24px ~ 32px
- 页面边距: 24px ~ 40px

---

## 五、圆角与阴影

### 5.1 圆角规范

```css
--radius-sm: 4px;    /* 小圆角 - 标签、徽章 */
--radius-md: 8px;    /* 中圆角 - 按钮、输入框 */
--radius-lg: 12px;   /* 大圆角 - 卡片 */
--radius-xl: 16px;   /* 超大圆角 - 大卡片 */
--radius-full: 9999px; /* 完全圆角 - 胶囊、头像 */
```

### 5.2 阴影规范

```css
--shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
--shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
```

### 5.3 阴影使用场景

| 场景 | 阴影 | 说明 |
|------|------|------|
| 默认卡片 | 无 | 平面化设计 |
| 悬停卡片 | shadow-sm | 轻微提升感 |
| 下拉菜单 | shadow-md | 明显层级 |
| 模态框 | shadow-lg | 最高层级 |
| 浮动按钮 | shadow-md | 悬浮感 |

---

## 六、组件规范

### 6.1 按钮 (Button)

**主按钮 (Primary)**
```
样式:
- 背景: #2563EB
- 文字: #FFFFFF
- 边框: none
- 圆角: 8px
- 内边距: 10px 20px
- 字号: 14px
- 字重: 500

状态:
- Default: 背景 #2563EB
- Hover: 背景 #1D4ED8
- Active: 背景 #1E40AF
- Disabled: 背景 #93C5FD, 文字 #FFFFFF
```

**次按钮 (Secondary)**
```
样式:
- 背景: #FFFFFF
- 文字: #374151
- 边框: 1px solid #E5E7EB
- 圆角: 8px
- 内边距: 10px 20px

状态:
- Default: 背景 #FFFFFF, 边框 #E5E7EB
- Hover: 背景 #F9FAFB, 边框 #D1D5DB
- Active: 背景 #F3F4F6
- Disabled: 背景 #F9FAFB, 文字 #9CA3AF
```

**文字按钮 (Text)**
```
样式:
- 背景: transparent
- 文字: #2563EB
- 边框: none
- 内边距: 8px 12px

状态:
- Default: 文字 #2563EB
- Hover: 背景 #EFF6FF
- Active: 背景 #DBEAFE
```

**危险按钮 (Danger)**
```
样式:
- 背景: #EF4444
- 文字: #FFFFFF
- 边框: none
- 圆角: 50% (圆形)
- 尺寸: 40px x 40px

状态:
- Default: 背景 #EF4444
- Hover: 背景 #DC2626
- Active: 背景 #B91C1C
```

### 6.2 卡片 (Card)

**标准卡片**
```
样式:
- 背景: #FFFFFF
- 边框: 1px solid #E5E7EB
- 圆角: 12px
- 内边距: 16px
- 阴影: none (默认)

悬停状态:
- 阴影: 0 1px 2px 0 rgba(0, 0, 0, 0.05)
- 边框: #D1D5DB
```

**信息卡片 (Info Card)**
```
样式:
- 背景: #F9FAFB
- 边框: 1px solid #E5E7EB
- 圆角: 12px
- 内边距: 16px

变体:
- Info: 左边框 4px #3B82F6
- Success: 左边框 4px #10B981
- Warning: 左边框 4px #F59E0B
- Error: 左边框 4px #EF4444
```

### 6.3 输入框 (Input)

**标准输入框**
```
样式:
- 背景: #FFFFFF
- 边框: 1px solid #E5E7EB
- 圆角: 8px
- 内边距: 12px 16px
- 字号: 16px
- 颜色: #374151

状态:
- Default: 边框 #E5E7EB
- Hover: 边框 #D1D5DB
- Focus: 边框 #2563EB, 阴影 0 0 0 3px rgba(37, 99, 235, 0.1)
- Disabled: 背景 #F9FAFB, 文字 #9CA3AF
- Error: 边框 #EF4444
```

### 6.4 标签/徽章 (Tag/Badge)

**标准标签**
```
样式:
- 背景: #F3F4F6
- 文字: #4B5563
- 圆角: 4px
- 内边距: 4px 8px
- 字号: 12px
- 字重: 500

变体:
- Primary: 背景 #EFF6FF, 文字 #2563EB
- Success: 背景 #ECFDF5, 文字 #059669
- Warning: 背景 #FFFBEB, 文字 #D97706
- Error: 背景 #FEF2F2, 文字 #DC2626
```

### 6.5 链接按钮 (Link Button)

**相关链接**
```
样式:
- 背景: #FFFFFF
- 文字: #2563EB
- 边框: 1px solid #E5E7EB
- 圆角: 8px
- 内边距: 8px 12px
- 字号: 14px

状态:
- Default: 背景 #FFFFFF, 文字 #2563EB
- Hover: 背景 #2563EB, 文字 #FFFFFF, 边框 #2563EB
- Active: 背景 #1D4ED8, 边框 #1D4ED8
```

### 6.6 快捷提问按钮 (Suggestion Chip)

**标准样式**
```
样式:
- 背景: #FFFFFF
- 文字: #4B5563
- 边框: 1px solid #E5E7EB
- 圆角: 8px
- 内边距: 10px 16px
- 字号: 14px
- 最大宽度: 280px
- 溢出: 省略号

状态:
- Default: 背景 #FFFFFF, 边框 #E5E7EB
- Hover: 背景 #F9FAFB, 边框 #2563EB, 文字 #2563EB
- Active: 背景 #EFF6FF
```

---

## 七、交互模式

### 7.1 状态定义

**默认状态 (Default)**
- 组件的初始显示状态
- 使用标准样式

**悬停状态 (Hover)**
- 鼠标悬停时的视觉反馈
- 背景色变化或添加阴影
- 过渡时间: 150ms

**聚焦状态 (Focus)**
- 键盘或鼠标聚焦时的状态
- 显示聚焦环 (outline)
- 颜色: #2563EB

**激活状态 (Active)**
- 鼠标按下时的状态
- 背景色加深
- 过渡时间: 100ms

**禁用状态 (Disabled)**
- 不可交互时的状态
- 透明度: 0.5
- 光标: not-allowed
- 无悬停效果

**加载状态 (Loading)**
- 操作进行中的状态
- 显示加载动画
- 禁用交互

### 7.2 过渡动画

**标准过渡**
```css
transition: all 150ms cubic-bezier(0.4, 0, 0.2, 1);
```

**快速过渡**
```css
transition: all 100ms cubic-bezier(0.4, 0, 0.2, 1);
```

**慢速过渡**
```css
transition: all 300ms cubic-bezier(0.4, 0, 0.2, 1);
```

### 7.3 微交互

**按钮点击**
```css
.btn:active {
  transform: scale(0.96);
}
```

**卡片悬停**
```css
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}
```

**输入框聚焦**
```css
.input:focus {
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
```

---

## 八、实现指南

### 8.1 CSS变量定义

```css
:root {
  /* Colors */
  --color-primary: #2563EB;
  --color-primary-light: #3B82F6;
  --color-primary-dark: #1D4ED8;
  --color-primary-lightest: #EFF6FF;
  
  --color-success: #10B981;
  --color-warning: #F59E0B;
  --color-error: #EF4444;
  
  /* Backgrounds */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F9FAFB;
  --bg-tertiary: #F3F4F6;
  --bg-hover: #F3F4F6;
  --bg-active: #EFF6FF;
  
  /* Text */
  --text-primary: #111827;
  --text-secondary: #4B5563;
  --text-tertiary: #6B7280;
  --text-disabled: #9CA3AF;
  --text-link: #2563EB;
  
  /* Border */
  --border-light: #E5E7EB;
  --border-medium: #D1D5DB;
  --border-focus: #2563EB;
  
  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  
  /* Border Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
  
  /* Typography */
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
  
  /* Transitions */
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
}
```

### 8.2 组件样式示例

**相关链接按钮 (重构后)**
```vue
<template>
  <a 
    :href="link.url" 
    target="_blank"
    class="link-button"
  >
    <span class="link-icon">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
        <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
      </svg>
    </span>
    <span class="link-title">{{ link.title }}</span>
    <span v-if="link.description" class="link-desc">{{ link.description }}</span>
  </a>
</template>

<style scoped>
.link-button {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  text-decoration: none;
  transition: all var(--duration-fast) var(--ease-default);
}

.link-button:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--bg-primary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.link-button:active {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
  transform: translateY(0);
}

.link-icon {
  display: flex;
  align-items: center;
  opacity: 0.8;
}

.link-title {
  font-weight: var(--font-weight-medium);
}

.link-desc {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
}

.link-button:hover .link-desc {
  color: rgba(255, 255, 255, 0.8);
}
</style>
```

**快捷提问按钮 (重构后)**
```vue
<template>
  <button 
    class="suggestion-chip"
    @click="$emit('click', question)"
  >
    {{ question }}
  </button>
</template>

<style scoped>
.suggestion-chip {
  padding: var(--space-2) var(--space-4);
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
  text-align: left;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.suggestion-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--bg-secondary);
}

.suggestion-chip:active {
  background: var(--bg-active);
  transform: scale(0.98);
}
</style>
```

**相关链接容器 (重构后)**
```vue
<template>
  <div class="related-links-container">
    <div class="links-label">相关链接</div>
    <div class="links-list">
      <slot></slot>
    </div>
  </div>
</template>

<style scoped>
.related-links-container {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.links-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-3);
}

.links-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
```

**快捷提问容器 (重构后)**
```vue
<template>
  <div class="suggested-questions-container">
    <div class="questions-label">快捷提问</div>
    <div class="questions-list">
      <slot></slot>
    </div>
  </div>
</template>

<style scoped>
.suggested-questions-container {
  margin-top: var(--space-4);
  padding: var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.questions-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-3);
}

.questions-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
```

### 8.3 设计检查清单

**色彩一致性检查**
- [ ] 所有按钮使用标准色板
- [ ] 背景色使用规范变量
- [ ] 文字颜色符合对比度要求
- [ ] 边框颜色统一

**间距一致性检查**
- [ ] 组件内边距符合规范
- [ ] 组件间距符合规范
- [ ] 页面边距符合规范

**圆角一致性检查**
- [ ] 按钮圆角统一
- [ ] 卡片圆角统一
- [ ] 输入框圆角统一

**交互一致性检查**
- [ ] 悬停效果统一
- [ ] 点击效果统一
- [ ] 过渡动画统一

---

## 附录：设计对比

### 重构前后对比

| 组件 | 重构前 | 重构后 | 改进点 |
|------|--------|--------|--------|
| 相关链接按钮 | 渐变色背景、emoji图标 | 白色背景、SVG图标 | 更简洁专业 |
| 快捷提问按钮 | 无边框、灰色背景 | 白色背景、细边框 | 更清晰可点击 |
| 相关链接容器 | 蓝色渐变背景 | 浅灰背景 | 更低调不抢眼 |
| 快捷提问容器 | 无边框、灰色背景 | 带边框、统一背景 | 视觉层次更清晰 |
| 链接描述文字 | 灰色 | 悬停变白 | 提升可读性 |

---

**文档结束**

*本文档提供完整的UI设计规范，用于指导开发团队实现一致的视觉体验。*
