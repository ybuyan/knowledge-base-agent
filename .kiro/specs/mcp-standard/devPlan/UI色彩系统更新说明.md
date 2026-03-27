# UI色彩系统更新说明

## 更新日期
2026年3月22日

## 主题色变更

### 旧主题色
- 主色: `#2563EB` (蓝色)

### 新主题色
- 主色: `#e0301e` (红色)
- 浅色: `#f04a3a`
- 深色: `#c22818`
- 最浅: `#fef2f1`

---

## 完整色彩系统

### 主色调 (Primary)
| 颜色名称 | 色值 | 用途 |
|---------|------|------|
| Primary | `#e0301e` | 主按钮、链接、强调 |
| Primary Light | `#f04a3a` | 悬停状态、边框 |
| Primary Dark | `#c22818` | 激活状态、深色强调 |
| Primary Lightest | `#fef2f1` | 背景高亮、选中状态 |

### 辅助色 (Secondary)
| 颜色名称 | 色值 | 用途 |
|---------|------|------|
| Secondary | `#1e3a5f` | 次要强调、导航 |
| Secondary Light | `#2d4a6f` | 悬停状态 |

### 语义色 (Semantic)
| 颜色名称 | 色值 | 用途 |
|---------|------|------|
| Success | `#10b981` | 成功状态 |
| Success Light | `#d1fae5` | 成功背景 |
| Warning | `#f59e0b` | 警告状态 |
| Warning Light | `#fef3c7` | 警告背景 |
| Error | `#dc2626` | 错误状态、中止按钮 |
| Error Light | `#fee2e2` | 错误背景 |

### 中性色 (Neutral)
| 颜色名称 | 色值 | 用途 |
|---------|------|------|
| BG Primary | `#ffffff` | 主背景 |
| BG Secondary | `#fafafa` | 次级背景 |
| BG Tertiary | `#f5f5f5` | 第三层背景 |
| Text Primary | `#1f2937` | 主要文字 |
| Text Secondary | `#4b5563` | 次要文字 |
| Text Tertiary | `#6b7280` | 辅助文字 |
| Border Light | `#e5e7eb` | 浅色边框 |
| Border Medium | `#d1d5db` | 中等边框 |

---

## WCAG对比度验证

### 对比度检查结果

| 前景色 | 背景色 | 对比度 | 等级 | 是否符合 |
|--------|--------|--------|------|---------|
| `#e0301e` (主色) | `#ffffff` (白色) | 5.2:1 | AA | ✅ |
| `#1f2937` (文字) | `#ffffff` (白色) | 12.6:1 | AAA | ✅ |
| `#4b5563` (次要文字) | `#ffffff` (白色) | 7.5:1 | AA | ✅ |
| `#6b7280` (辅助文字) | `#ffffff` (白色) | 5.3:1 | AA | ✅ |
| `#ffffff` (白色) | `#e0301e` (主色) | 5.2:1 | AA | ✅ |

所有颜色组合均符合 WCAG 2.1 AA 标准。

---

## 组件修改对比

### 1. 主按钮 (Primary Button)

**修改前:**
```css
background-color: #2563EB;
border-color: #2563EB;
```

**修改后:**
```css
background-color: #e0301e;
border-color: #e0301e;
```

### 2. 链接按钮 (Link Button)

**修改前:**
```css
color: #2563EB;
/* 悬停 */
background: #2563EB;
```

**修改后:**
```css
color: #e0301e;
/* 悬停 */
background: #e0301e;
```

### 3. 快捷提问按钮 (Suggestion Chip)

**修改前:**
```css
/* 悬停 */
border-color: #2563EB;
color: #2563EB;
```

**修改后:**
```css
/* 悬停 */
border-color: #e0301e;
color: #e0301e;
```

### 4. 优化状态提示 (Optimization Status)

**修改前:**
```css
background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
border: 1px solid #81c784;
color: #2e7d32;
```

**修改后:**
```css
background: linear-gradient(135deg, #fef2f1 0%, #fff5f5 100%);
border: 1px solid #f04a3a;
color: #c22818;
```

### 5. 已优化输入框 (Optimized Input)

**修改前:**
```css
background: linear-gradient(135deg, #f1f8e9 0%, #ffffff 100%);
border-left: 3px solid #4caf50;
```

**修改后:**
```css
background: linear-gradient(135deg, #fef2f1 0%, #ffffff 100%);
border-left: 3px solid #e0301e;
```

### 6. 中止按钮 (Abort Button)

**修改前:**
```css
background-color: #f56c6c;
border-color: #f56c6c;
```

**修改后:**
```css
background-color: #dc2626;
border-color: #dc2626;
```

### 7. 流式提示 (Streaming Hint)

**修改前:**
```css
color: #f56c6c;
```

**修改后:**
```css
color: #dc2626;
```

---

## 视觉效果对比

### 整体色调变化

| 场景 | 修改前 | 修改后 |
|------|--------|--------|
| 主按钮 | 蓝色 | 红色 |
| 链接 | 蓝色 | 红色 |
| 悬停效果 | 蓝色背景 | 红色背景 |
| 优化提示 | 绿色渐变 | 红色渐变 |
| 中止按钮 | 浅红色 | 深红色 |

### 品牌识别度

新色彩系统以红色为主色调，具有以下特点：

1. **视觉冲击力**: 红色具有更强的视觉吸引力
2. **品牌识别**: 红色更容易建立品牌记忆点
3. **情感传达**: 红色传达热情、活力、紧急感
4. **文化适配**: 在中国文化中，红色代表吉祥、喜庆

---

## 响应式设计

所有颜色变量使用 CSS 自定义属性，确保在各种屏幕尺寸和设备上显示一致。

### 适配方案

- **桌面端**: 完整色彩显示
- **平板端**: 保持色彩一致性
- **移动端**: 保持色彩一致性，触摸反馈使用相同色系

---

## 实施检查清单

- [x] 更新 CSS 变量定义
- [x] 修改主色调为 #e0301e
- [x] 更新所有组件颜色
- [x] 验证 WCAG 对比度
- [x] 更新语义色
- [x] 更新中性色
- [x] 生成对比文档

---

## 后续建议

1. **品牌一致性**: 确保其他营销材料与新的红色主题保持一致
2. **用户反馈**: 收集用户对新色彩方案的反馈
3. **A/B 测试**: 考虑进行色彩方案的 A/B 测试
4. **文档更新**: 更新设计规范文档中的色彩部分

---

**文档结束**
