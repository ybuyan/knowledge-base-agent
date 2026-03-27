<script setup lang="ts">
import { ref, nextTick, computed, onMounted, onUnmounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/api'
import { renderMarkdown } from '@/utils/markdown'
import { getContentProtectionConfig } from '@/config/security'
import { 
  Position, 
  ChatDotRound,
  Document,
  Microphone,
  Upload,
  Loading
} from '@element-plus/icons-vue'
import type { Source } from '@/stores/chat'

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesContainer = ref<HTMLElement>()
const currentSources = ref<Source[]>([])
const streamingContent = ref('')

// 获取内容保护配置
const protectionConfig = getContentProtectionConfig()

const suggestedQuestions = [
  '年假怎么计算？',
  '请假需要提交什么材料？',
  '报销流程怎么走？',
  '入职需要准备哪些文件？'
]

const topicClusters = [
  '请假制度', '考勤规范', '报销流程', '入职流程', '离职流程', '薪酬福利'
]

const systemStatus = computed(() => ({
  documents: 12,
  chunks: 156,
  lastUpdate: '2024-01-15 10:30'
}))

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const handleSend = async () => {
  if (!inputMessage.value.trim() || chatStore.isLoading) return
  
  const question = inputMessage.value.trim()
  inputMessage.value = ''
  
  // 确保 session 存在
  if (!chatStore.currentSessionId) {
    await chatStore.createSession()
  }
  
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
  
  await chatApi.askStreamV2(
    question,
    chatStore.currentSessionId,
    (text) => {
      streamingContent.value += text
      chatStore.updateLastAssistantContent(streamingContent.value)
      scrollToBottom()
    },
    (sources) => {
      currentSources.value = sources
      chatStore.updateLastAssistantSources(sources)
      chatStore.setLoading(false)
      chatStore.updateSessionActivity()
    },
    (error) => {
      console.error('Stream error:', error)
      chatStore.updateLastAssistantContent('抱歉，发生了错误，请稍后重试。')
      chatStore.setLoading(false)
    }
  )
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

const handleSuggestedQuestion = (question: string) => {
  inputMessage.value = question
  handleSend()
}

const renderMessage = (content: string, role: 'user' | 'assistant') => {
  if (role === 'user') {
    return content.replace(/\n/g, '<br>')
  }
  return renderMarkdown(content)
}

const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
  } catch {}
}

// 禁用右键菜单（针对助手回复）
const handleContextMenu = (e: MouseEvent, role: string) => {
  if (role === 'assistant' && protectionConfig.disableContextMenu) {
    e.preventDefault()
    return false
  }
}

// 禁用键盘复制快捷键（针对助手回复）
const handleKeyDown = (e: KeyboardEvent) => {
  if (!protectionConfig.disableKeyboardShortcuts) return
  
  // 检测 Ctrl+C 或 Cmd+C
  if ((e.ctrlKey || e.metaKey) && e.key === 'c') {
    const selection = window.getSelection()
    if (selection && selection.toString()) {
      // 检查选中的内容是否在助手消息中
      const range = selection.getRangeAt(0)
      const container = range.commonAncestorContainer
      const messageElement = (container as HTMLElement).closest?.('.message.assistant')
      if (messageElement) {
        e.preventDefault()
        return false
      }
    }
  }
}

onMounted(() => {
  scrollToBottom()
  // 添加全局键盘事件监听
  if (protectionConfig.disableKeyboardShortcuts) {
    document.addEventListener('keydown', handleKeyDown)
  }
})

onUnmounted(() => {
  if (protectionConfig.disableKeyboardShortcuts) {
    document.removeEventListener('keydown', handleKeyDown)
  }
})
</script>

<template>
  <div class="chat-page">
    <div class="chat-area">
      <div class="messages-container scrollbar-thin" ref="messagesContainer">
        <div v-if="!chatStore.messages.length" class="empty-state">
          <el-icon :size="64" color="#e0301e"><ChatDotRound /></el-icon>
          <h2>欢迎使用公司制度问答助手</h2>
          <p>请输入您的问题，我将基于公司制度为您解答</p>
        </div>
        
        <div v-for="message in chatStore.messages" :key="message.id" class="message-wrapper">
          <div v-if="message.content || message.role === 'user'" class="message" :class="message.role">
            <div class="message-avatar">
              <el-avatar v-if="message.role === 'user'" :size="32" :icon="Position" />
              <el-avatar v-else :size="32" class="assistant-avatar">
                <el-icon><ChatDotRound /></el-icon>
              </el-avatar>
            </div>
            <div class="message-content">
              <div 
                class="message-text markdown-body" 
                v-html="renderMessage(message.content, message.role)"
                @contextmenu="(e) => handleContextMenu(e, message.role)"
              ></div>
              <div v-if="message.role === 'assistant' && message.content" class="message-actions">
                <!-- 复制功能已禁用 -->
              </div>
            </div>
          </div>
        </div>
        
        <div v-if="chatStore.isLoading && !streamingContent" class="message-wrapper">
          <div class="message assistant">
            <div class="message-avatar">
              <el-avatar :size="32" class="assistant-avatar">
                <el-icon><ChatDotRound /></el-icon>
              </el-avatar>
            </div>
            <div class="message-content">
              <div class="loading-indicator">
                <el-icon class="is-loading"><Loading /></el-icon>
                <span>正在思考...</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="currentSources.length" class="sources-section">
        <div class="sources-title">
          <el-icon><Document /></el-icon>
          参考来源
        </div>
        <div class="sources-list">
          <div v-for="(source, index) in currentSources" :key="source.id" class="source-card">
            <div class="source-index">[{{ index + 1 }}]</div>
            <div class="source-info">
              <div class="source-filename">{{ source.filename }}</div>
              <div v-if="source.page" class="source-meta">第 {{ source.page }} 页</div>
            </div>
          </div>
        </div>
      </div>

      <div class="input-area">
        <div class="input-container">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="1"
            :autosize="{ minRows: 1, maxRows: 4 }"
            placeholder="输入您的问题..."
            @keydown="handleKeydown"
            class="message-input"
          />
          <div class="input-actions">
            <el-button :icon="Upload" circle title="上传文件" />
            <el-button :icon="Microphone" circle title="语音输入" />
            <el-button 
              type="primary" 
              :icon="Position" 
              circle 
              @click="handleSend"
              :disabled="!inputMessage.trim() || chatStore.isLoading"
              title="发送"
            />
          </div>
        </div>
      </div>
    </div>

    <aside class="right-panel">
      <div class="panel-section">
        <div class="section-title">推荐问题</div>
        <div class="suggested-list">
          <div 
            v-for="question in suggestedQuestions" 
            :key="question"
            class="suggested-item"
            @click="handleSuggestedQuestion(question)"
          >
            {{ question }}
          </div>
        </div>
      </div>

      <div class="panel-section">
        <div class="section-title">话题分类</div>
        <div class="topic-clusters">
          <el-tag 
            v-for="topic in topicClusters" 
            :key="topic"
            effect="plain"
            class="topic-tag"
          >
            {{ topic }}
          </el-tag>
        </div>
      </div>

      <div class="panel-section">
        <div class="section-title">系统状态</div>
        <div class="status-list">
          <div class="status-item">
            <span class="status-label">文档数量</span>
            <span class="status-value">{{ systemStatus.documents }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">知识片段</span>
            <span class="status-value">{{ systemStatus.chunks }}</span>
          </div>
          <div class="status-item">
            <span class="status-label">最后更新</span>
            <span class="status-value">{{ systemStatus.lastUpdate }}</span>
          </div>
        </div>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.chat-page {
  display: flex;
  flex: 1;
  height: 100%;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
  min-height: 0;
  padding: 0 24px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-secondary);
}

.empty-state h2 {
  margin-top: 24px;
  font-size: 24px;
  color: var(--text-primary);
}

.empty-state p {
  margin-top: 8px;
  font-size: 14px;
}

.message-wrapper {
  margin-bottom: 24px;
}

.message {
  display: flex;
  gap: 12px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.assistant-avatar {
  background: var(--primary-color);
}

.message-content {
  max-width: 85%;
  width: 100%;
}

.message.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-text {
  padding: 12px 16px;
  border-radius: var(--radius-lg);
  line-height: 1.6;
  font-size: 14px;
}

.message.user .message-text {
  background: var(--primary-color);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-text {
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-bottom-left-radius: 4px;
  /* 禁用文本选择 */
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  color: var(--text-secondary);
}

.sources-section {
  padding: 0 24px 16px;
}

.sources-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.sources-list {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.source-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 13px;
}

.source-index {
  color: var(--primary-color);
  font-weight: 600;
}

.source-filename {
  color: var(--text-primary);
}

.source-meta {
  color: var(--text-tertiary);
  font-size: 12px;
}

.input-area {
  padding: 16px 24px 24px;
}

.input-container {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  background: var(--bg-white);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 12px 16px;
  box-shadow: var(--shadow-sm);
}

.message-input {
  flex: 1;
}

.message-input :deep(.el-textarea__inner) {
  border: none;
  padding: 0;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
}

.message-input :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.input-actions {
  display: flex;
  gap: 8px;
}

.right-panel {
  width: 280px;
  background: var(--bg-white);
  border-left: 1px solid var(--border-color);
  padding: 20px;
  overflow-y: auto;
}

.panel-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.suggested-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggested-item {
  padding: 10px 12px;
  background: var(--bg-gray);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.suggested-item:hover {
  background: var(--primary-bg-light);
  color: var(--primary-color);
}

.topic-clusters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-tag {
  cursor: pointer;
}

.topic-tag:hover {
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.status-item:last-child {
  border-bottom: none;
}

.status-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.status-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
</style>
