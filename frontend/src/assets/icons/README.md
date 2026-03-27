# 图标设计规范

## 概述

本文档定义了"优化"和"撤回优化"两个功能图标的设计规范，确保与Trae品牌视觉语言保持一致。

## 图标清单

### 1. 优化图标 (Optimize)

**文件名**: `optimize.svg`

**设计理念**:
- 以五角星魔法棒为主体，象征智能优化和提升
- 右侧添加闪光效果，表示AI增强和魔法般的效果
- 整体传达"让查询更智能"的含义

**视觉元素**:
- 五角星形状，5个尖角
- 3个闪光圆点，大小递减
- 使用currentColor，支持主题色切换

**使用场景**:
- 输入框右侧的优化按钮
- 优化过程中的加载状态
- 已优化的状态指示

### 2. 撤回图标 (Revert)

**文件名**: `revert.svg`

**设计理念**:
- 弯曲的返回箭头，明确表示撤销操作
- 简洁的线条设计，易于识别
- 传达"恢复原状"的含义

**视觉元素**:
- 左侧箭头指向左下方
- 右侧横线表示原始状态
- 1.5px线条粗细，圆角端点

**使用场景**:
- 优化后的撤回按钮
- 撤销操作的入口

## 尺寸规范

| 尺寸 | 用途 | 文件 |
|------|------|------|
| 16x16px | 按钮图标、内联图标 | `optimize.svg`, `revert.svg` |
| 24x24px | 大按钮、工具栏 | `optimize-24.svg`, `revert-24.svg` |

## 交互状态

### 默认状态
- 颜色: 主题色 (`var(--primary-color)`)
- 透明度: 100%
- 大小: 16x16px

### 悬停状态
- 背景: 主题色填充
- 图标: 白色
- 缩放: 1.05倍
- 阴影: 微光效果

### 点击状态
- 缩放: 0.95倍
- 过渡: 150ms ease

### 禁用状态
- 透明度: 50%
- 光标: not-allowed

## 技术规范

### SVG属性
```xml
<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- 使用currentColor实现主题色切换 -->
  <path fill="currentColor"/>
</svg>
```

### 使用方式
```vue
<!-- Vue组件中使用 -->
<template>
  <OptimizeIcon class="custom-icon" />
  <RevertIcon class="custom-icon" />
</template>

<script setup>
import OptimizeIcon from '@/assets/icons/optimize.svg'
import RevertIcon from '@/assets/icons/revert.svg'
</script>

<style>
.custom-icon {
  width: 16px;
  height: 16px;
}
</style>
```

## 设计原则

### 1. 一致性
- 与Element Plus图标风格统一
- 使用相同的线条粗细和圆角
- 保持视觉重量平衡

### 2. 可识别性
- 16px尺寸下依然清晰可辨
- 独特的形状特征
- 避免与其他图标混淆

### 3. 表意清晰
- 优化图标: 魔法+星星 = 智能提升
- 撤回图标: 返回箭头 = 撤销恢复

### 4. 无障碍
- 支持高对比度模式
- 提供文字标签备选
- 支持屏幕阅读器

## 版本记录

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-03-15 | 初始版本，创建优化和撤回图标 |
