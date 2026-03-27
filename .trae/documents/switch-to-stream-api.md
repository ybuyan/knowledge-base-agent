# 将前端 ask 接口替换为 ask/stream 流式接口

## 背景

当前 `ChatContent.vue` 使用的是非流式接口 `chatApi.ask`，需要切换回流式接口 `chatApi.askStream`，实现打字机效果的流式输出。

## 当前状态

- **ChatContent.vue** 第 68 行：使用 `chatApi.ask` 非流式接口
- **api/index.ts**：`askStream` 方法已存在且已优化（支持缓冲区处理）

## 修改步骤

### 步骤 1：修改 ChatContent.vue 的 handleSend 函数

**文件**: `frontend/src/views/Chat/ChatContent.vue`

将 `handleSend` 函数从非流式调用改为流式调用：

```typescript
// 修改前（非流式）
const result = await chatApi.ask(question, chatStore.currentSessionId)
chatStore.updateLastAssistantContent(result.answer)
currentSources.value = result.sources

// 修改后（流式）
let streamingContent = ''
await chatApi.askStream(
  question,
  chatStore.currentSessionId,
  (text) => {
    streamingContent += text
    chatStore.updateLastAssistantContent(streamingContent)
    scrollToBottom()
  },
  (sources) => {
    currentSources.value = sources
    chatStore.setLoading(false)
  },
  (error) => {
    console.error('Stream error:', error)
    chatStore.updateLastAssistantContent('抱歉，发生了错误，请稍后重试。')
    chatStore.setLoading(false)
  }
)
```

### 步骤 2：添加 streamingContent 变量

在 `ChatContent.vue` 的 `<script setup>` 中添加流式内容累积变量：

```typescript
const streamingContent = ref('')
```

### 步骤 3：更新 handleSend 函数完整逻辑

```typescript
const handleSend = async () => {
  if (!inputMessage.value.trim() || chatStore.isLoading) return
  
  const question = inputMessage.value.trim()
  inputMessage.value = ''
  
  chatStore.addMessage({
    role: 'user',
    content: question
  })
  
  chatStore.setLoading(true)
  streamingContent.value = ''
  currentSources.value = []
  
  chatStore.addMessage({
    role: 'assistant',
    content: ''
  })
  
  scrollToBottom()
  
  await chatApi.askStream(
    question,
    chatStore.currentSessionId,
    (text) => {
      streamingContent.value += text
      chatStore.updateLastAssistantContent(streamingContent.value)
      scrollToBottom()
    },
    (sources) => {
      currentSources.value = sources
      chatStore.setLoading(false)
    },
    (error) => {
      console.error('Stream error:', error)
      chatStore.updateLastAssistantContent('抱歉，发生了错误，请稍后重试。')
      chatStore.setLoading(false)
    }
  )
}
```

### 步骤 4：更新加载状态显示逻辑

修改模板中的加载指示器条件，从：
```html
<div v-if="chatStore.isLoading" class="message-wrapper">
```

改为：
```html
<div v-if="chatStore.isLoading && !streamingContent" class="message-wrapper">
```

这样在有流式内容输出时，不会显示"正在思考..."的加载指示器。

## 文件修改清单

| 文件 | 修改内容 |
|------|----------|
| `frontend/src/views/Chat/ChatContent.vue` | 修改 handleSend 函数，添加 streamingContent 变量 |

## 预期效果

1. 用户发送问题后，AI 回答会逐字显示（打字机效果）
2. 流式输出过程中显示加载状态
3. 输出完成后显示参考来源
4. 错误时显示友好的错误提示
