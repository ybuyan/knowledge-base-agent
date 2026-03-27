# 内容保护功能实现

## 需求

在AI回答内容的过程中禁用下载和复制功能，保护公司制度文档的版权和安全性。

## 实现方案

### 1. 前端保护措施

#### 1.1 禁用复制功能

**移除复制按钮**
- 文件：`frontend/src/views/Chat/ChatContent.vue`
- 修改：移除助手回复下方的"复制"按钮

**禁用文本选择**
```css
.message.assistant .message-text {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}
```

**禁用键盘快捷键**
- 拦截 `Ctrl+C` / `Cmd+C`
- 检测选中内容是否在助手消息中
- 阻止复制操作

#### 1.2 禁用右键菜单

```typescript
const handleContextMenu = (e: MouseEvent, role: string) => {
  if (role === 'assistant' && protectionConfig.disableContextMenu) {
    e.preventDefault()
    return false
  }
}
```

#### 1.3 禁用代码块复制

- 文件：`frontend/src/utils/markdown.ts`
- 修改：移除代码块中的"复制"按钮

```typescript
// 移除复制按钮
return `<pre class="code-block"><code class="hljs language-${lang}">${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`
```

#### 1.4 禁用链接下载

```typescript
md.renderer.rules.link_open = function(tokens, idx) {
  const token = tokens[idx]
  const hrefIndex = token.attrIndex('href')
  
  if (hrefIndex >= 0) {
    const href = token.attrs![hrefIndex][1]
    // 移除 download 属性，禁用点击
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" onclick="return false;">`
  }
  
  return '<a>'
}
```

### 2. 配置管理

创建了配置文件 `frontend/src/config/security.ts`：

```typescript
export interface ContentProtectionConfig {
  disableCopy: boolean
  disableContextMenu: boolean
  disableKeyboardShortcuts: boolean
  disableDownload: boolean
  disableTextSelection: boolean
  disableCodeCopy: boolean
}

export const contentProtection: ContentProtectionConfig = {
  disableCopy: true,
  disableContextMenu: true,
  disableKeyboardShortcuts: true,
  disableDownload: true,
  disableTextSelection: true,
  disableCodeCopy: true
}
```

### 3. 保护范围

**受保护的内容**
- ✓ 助手的回复内容
- ✓ 代码块内容
- ✓ 链接和下载
- ✓ Markdown 渲染的所有内容

**不受影响的功能**
- ✓ 用户自己的消息可以复制
- ✓ 正常的阅读和浏览
- ✓ 界面交互和操作

## 文件清单

### 修改的文件

1. `frontend/src/views/Chat/ChatContent.vue`
   - 移除复制按钮
   - 添加右键菜单拦截
   - 添加键盘快捷键拦截
   - 添加 CSS 禁用文本选择

2. `frontend/src/utils/markdown.ts`
   - 移除代码块复制按钮
   - 禁用链接下载

### 新增的文件

1. `frontend/src/config/security.ts`
   - 内容保护配置

2. `frontend/docs/CONTENT_PROTECTION.md`
   - 功能文档

3. `frontend/src/views/Test/ContentProtectionTest.vue`
   - 测试页面

4. `backend/docs/devplan/CONTENT_PROTECTION_IMPLEMENTATION.md`
   - 实现文档（本文件）

## 测试验证

### 手动测试

1. **文本选择测试**
   - 尝试选择助手回复内容
   - 预期：无法选择

2. **复制测试**
   - 尝试使用 Ctrl+C 复制
   - 预期：无法复制

3. **右键菜单测试**
   - 在助手回复上右键点击
   - 预期：菜单不弹出

4. **代码块测试**
   - 查看代码块
   - 预期：无复制按钮

5. **链接测试**
   - 点击链接
   - 预期：无法下载

### 使用测试页面

访问测试页面进行验证：
```
/test/content-protection
```

## 安全说明

### 前端保护的局限性

前端保护可以防止普通用户的复制和下载，但无法完全防止技术用户：

1. 浏览器开发者工具可以查看 DOM
2. 网络请求可以被拦截
3. 截图和录屏无法阻止

### 建议的后端增强

1. **添加水印**
   ```python
   # 在回复中添加隐藏水印
   def add_watermark(content: str, user_id: str) -> str:
       timestamp = datetime.now().isoformat()
       watermark = f"<!-- User: {user_id}, Time: {timestamp} -->"
       return content + watermark
   ```

2. **查询限流**
   ```python
   # 限制查询频率
   @rate_limit(max_requests=10, window=60)
   async def ask_question(question: str):
       pass
   ```

3. **审计日志**
   ```python
   # 记录所有查询
   async def log_query(user_id: str, question: str, answer: str):
       await QueryLog.create(
           user_id=user_id,
           question=question,
           answer=answer,
           timestamp=datetime.now()
       )
   ```

## 配置调整

### 临时禁用保护（开发环境）

修改 `frontend/src/config/security.ts`：

```typescript
export function getContentProtectionConfig(): ContentProtectionConfig {
  const isDev = import.meta.env.DEV
  
  // 开发环境使用宽松配置
  return isDev ? devContentProtection : contentProtection
}
```

### 部分禁用保护

```typescript
export const contentProtection: ContentProtectionConfig = {
  disableCopy: true,
  disableContextMenu: true,
  disableKeyboardShortcuts: false,  // 允许键盘复制
  disableDownload: true,
  disableTextSelection: true,
  disableCodeCopy: true
}
```

## 部署说明

1. 确保前端代码已编译
2. 清除浏览器缓存
3. 验证保护功能是否生效
4. 监控用户反馈

## 维护建议

1. 定期检查保护功能是否正常
2. 关注浏览器更新可能带来的影响
3. 收集用户反馈，调整保护级别
4. 考虑添加后端保护措施

## 总结

已实现的内容保护功能：
- ✓ 禁用复制（按钮、快捷键、右键菜单）
- ✓ 禁用文本选择
- ✓ 禁用代码块复制
- ✓ 禁用链接下载
- ✓ 可配置的保护级别
- ✓ 测试页面

这些措施可以有效防止普通用户的复制和下载行为，保护公司制度文档的版权和安全性。
