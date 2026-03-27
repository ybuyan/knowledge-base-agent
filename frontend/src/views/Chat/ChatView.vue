<script setup lang="ts">
import { ref, computed, nextTick, watch, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/api'
import { renderMarkdown } from '@/utils/markdown'
import { 
  Position, 
  ArrowDown,
  User,
  ChatDotRound,
  Document,
  CopyDocument,
  Check,
  Download,
  RefreshRight,
  CircleClose
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const OptimizeIcon = `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M8 1L9.5 5.5L14 6L10.5 9L11.5 13.5L8 11L4.5 13.5L5.5 9L2 6L6.5 5.5L8 1Z" fill="currentColor"/>
  <circle cx="13" cy="3" r="1.2" fill="currentColor" opacity="0.8"/>
  <circle cx="14.5" cy="5.5" r="0.8" fill="currentColor" opacity="0.6"/>
  <circle cx="13.5" cy="8" r="0.6" fill="currentColor" opacity="0.4"/>
</svg>`

const RevertIcon = `<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M4 5L1.5 8L4 11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M2.5 8H9.5C11.7091 8 13.5 9.79086 13.5 12V12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
</svg>`

const chatStore = useChatStore()
const inputMessage = ref('')
const isStreaming = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)
const showScrollButton = ref(false)
const currentStreamContent = ref('')
const expandedMessages = ref<Set<number>>(new Set())
const copiedMessageId = ref<string | null>(null)
const hoveredUserMessageId = ref<string | null>(null)
const isOptimizing = ref(false)
const isOptimized = ref(false)
const originalQuery = ref('')
const optimizedQuery = ref('')
const abortController = ref<AbortController | null>(null)
const isAborted = ref(false)

const optimizeInput = async () => {
  if (!inputMessage.value.trim() || isOptimizing.value) return
  
  isOptimizing.value = true
  try {
    const result = await chatApi.optimizeQuery(inputMessage.value)
    originalQuery.value = inputMessage.value
    optimizedQuery.value = result.optimized_query
    inputMessage.value = optimizedQuery.value
    isOptimized.value = true
    ElMessage.success('查询已优化')
  } catch (error) {
    ElMessage.error('优化失败')
  } finally {
    isOptimizing.value = false
  }
}

const revertOptimization = () => {
  inputMessage.value = originalQuery.value
  isOptimized.value = false
  originalQuery.value = ''
  optimizedQuery.value = ''
  ElMessage.info('已恢复原始输入')
}

const abortGeneration = () => {
  if (abortController.value) {
    abortController.value.abort()
    abortController.value = null
  }
  isAborted.value = true
  isStreaming.value = false
  regeneratingMessageId.value = null
  
  if (currentStreamContent.value.trim()) {
    chatStore.updateLastAssistantContent(currentStreamContent.value + '\n\n*[回答已中止]*')
  } else {
    chatStore.updateLastAssistantContent('*[回答已中止]*')
  }
  
  ElMessage.warning('回答生成已中止')
}

const toggleMessageSources = (index: number) => {
  if (expandedMessages.value.has(index)) {
    expandedMessages.value.delete(index)
  } else {
    expandedMessages.value.add(index)
  }
}

const isMessageExpanded = (index: number) => {
  return expandedMessages.value.has(index)
}

const getFileExt = (filename: string): string => {
  const ext = filename.split('.').pop()?.toUpperCase() || ''
  return ext
}

const copyMessage = async (content: string, messageId: string) => {
  try {
    await navigator.clipboard.writeText(content)
    copiedMessageId.value = messageId
    ElMessage.success('已复制到剪贴板')
    setTimeout(() => {
      copiedMessageId.value = null
    }, 2000)
  } catch (err) {
    ElMessage.error('复制失败')
  }
}

const exportToPdf = async (message: any) => {
  try {
    ElMessage.info('正在生成PDF...')
    
    const blob = await chatApi.exportPdf(
      message.id,
      chatStore.currentSessionId!,
      'AI问答导出'
    )
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `chat_export_${new Date().toISOString().slice(0, 10)}.pdf`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('PDF导出成功')
  } catch (err) {
    ElMessage.error('导出失败')
  }
}

const regeneratingMessageId = ref<string | null>(null)

const regenerateAnswer = async (message: any, index: number) => {
  if (isStreaming.value) return
  
  const userMessage = chatStore.messages[index - 1]
  if (!userMessage || userMessage.role !== 'user') {
    ElMessage.warning('找不到对应的问题')
    return
  }
  
  regeneratingMessageId.value = message.id
  isStreaming.value = true
  isAborted.value = false
  currentStreamContent.value = ''
  abortController.value = new AbortController()
  
  chatStore.updateLastAssistantContent('')
  chatStore.updateLastAssistantSources([])
  
  try {
    await chatApi.askStreamV2(
      userMessage.content,
      chatStore.currentSessionId!,
      (text) => {
        if (isAborted.value) return
        currentStreamContent.value += text
        chatStore.updateLastAssistantContent(currentStreamContent.value)
      },
      (sources) => {
        if (isAborted.value) return
        chatStore.updateLastAssistantSources(sources)
        isStreaming.value = false
        regeneratingMessageId.value = null
        chatStore.updateSessionActivity()
      },
      (error) => {
        if (error.message === 'ABORTED') return
        ElMessage.error(error.message || '重新生成失败')
        isStreaming.value = false
        regeneratingMessageId.value = null
      },
      (warning) => {
        ElMessage.warning(warning)
      },
      abortController.value.signal
    )
  } catch (error) {
    ElMessage.error('重新生成失败')
    isStreaming.value = false
    regeneratingMessageId.value = null
  }
}

const hasMessages = computed(() => chatStore.messages.length > 0)

const suggestedQuestions = [
  '如何重置我的密码？',
  '公司有哪些节假日？',
  '如何申请休假？',
  '在哪里可以找到员工手册？'
]

const isUserScrolling = ref(false)
const scrollTimeout = ref<number | null>(null)

const scrollToBottom = async (force = false) => {
  await nextTick()
  if (!messagesContainer.value) return
  
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  
  if (force || distanceFromBottom < 100) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const handleScroll = () => {
  if (!messagesContainer.value) return
  const { scrollTop, scrollHeight, clientHeight } = messagesContainer.value
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  showScrollButton.value = distanceFromBottom > 100
  
  isUserScrolling.value = true
  
  if (scrollTimeout.value) {
    clearTimeout(scrollTimeout.value)
  }
  
  scrollTimeout.value = window.setTimeout(() => {
    isUserScrolling.value = false
  }, 150)
}

const sendMessage = async () => {
  const message = inputMessage.value.trim()
  if (!message || isStreaming.value) return

  if (!chatStore.currentSessionId) {
    await chatStore.createSession()
  }

  chatStore.addMessage({ role: 'user', content: message })
  inputMessage.value = ''
  isStreaming.value = true
  isAborted.value = false
  currentStreamContent.value = ''
  abortController.value = new AbortController()
  
  isOptimized.value = false
  originalQuery.value = ''
  optimizedQuery.value = ''

  await scrollToBottom(true)

  chatStore.addMessage({ role: 'assistant', content: '' })

  try {
    await chatApi.askStreamV2(
      message,
      chatStore.currentSessionId,
      (text) => {
        if (isAborted.value) return
        currentStreamContent.value += text
        chatStore.updateLastAssistantContent(currentStreamContent.value)
        scrollToBottom()
      },
      (srcs, suggestedQuestions, relatedLinks) => {
        if (isAborted.value) return
        chatStore.updateLastAssistantSources(srcs)
        if (suggestedQuestions && suggestedQuestions.length > 0) {
          chatStore.updateLastAssistantSuggestedQuestions(suggestedQuestions)
        }
        if (relatedLinks && relatedLinks.length > 0) {
          chatStore.updateLastAssistantRelatedLinks(relatedLinks)
        }
        isStreaming.value = false
        chatStore.updateSessionActivity()
      },
      (error) => {
        if (error.message === 'ABORTED') return
        ElMessage.error(error.message || 'Failed to get response')
        isStreaming.value = false
      },
      (warning) => {
        ElMessage.warning(warning)
      },
      abortController.value.signal
    )
  } catch (error) {
    ElMessage.error('Failed to send message')
    isStreaming.value = false
  }
}

const useSuggestion = (question: string) => {
  chatStore.updateLastAssistantSuggestedQuestions([])
  inputMessage.value = question
  sendMessage()
}

const formatTime = (timestamp: Date | string) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

watch(() => chatStore.messages.length, async (newLength, oldLength) => {
  if (!oldLength || oldLength === 0 || newLength > oldLength) {
    await nextTick()
    scrollToBottom(true)
  } else {
    scrollToBottom()
  }
}, { immediate: true })

onMounted(async () => {
  await nextTick()
  setTimeout(() => {
    scrollToBottom(true)
  }, 100)
})
</script>

<template>
  <div class="chat-view">
    <div v-if="!hasMessages" class="empty-state">
      <div class="empty-content">
        <div class="empty-icon">
          <el-icon :size="48"><ChatDotRound /></el-icon>
        </div>
        <h1 class="empty-title">How can I help you today?</h1>
        <p class="empty-subtitle">Ask me anything about company policies, documents, or general questions.</p>
        
        <div class="suggested-questions">
          <button
            v-for="(question, index) in suggestedQuestions"
            :key="index"
            class="suggestion-chip"
            @click="useSuggestion(question)"
          >
            {{ question }}
          </button>
        </div>
      </div>
    </div>

    <div v-else class="messages-area" ref="messagesContainer" @scroll="handleScroll">
      <div class="messages-list">
        <div
          v-for="(message, index) in chatStore.messages"
          :key="index"
          class="message-wrapper"
          :class="message.role"
          @mouseenter="message.role === 'user' ? hoveredUserMessageId = message.id : null"
          @mouseleave="message.role === 'user' ? hoveredUserMessageId = null : null"
        >
          <div class="message-avatar">
            <el-avatar 
              :size="32" 
              :icon="message.role === 'user' ? User : ChatDotRound"
              :class="message.role"
            />
          </div>
          <div class="message-content">
            <div class="message-bubble" :class="message.role">
              <div 
                v-if="message.role === 'assistant' && index === chatStore.messages.length - 1 && isStreaming && !message.content"
                class="typing-indicator"
              >
                <span></span>
                <span></span>
                <span></span>
              </div>
              <div 
                v-else-if="message.role === 'assistant'"
                class="markdown-body"
                v-html="renderMarkdown(message.content)"
              ></div>
              <div v-else>{{ message.content }}</div>
            </div>
            
            <div 
              v-if="message.role === 'user'"
              class="message-popup-actions"
              v-show="hoveredUserMessageId === message.id"
            >
              <div class="popup-menu">
                <button 
                  class="popup-btn"
                  @click="copyMessage(message.content, message.id)"
                >
                  <el-icon :size="14">
                    <CopyDocument />
                  </el-icon>
                  <span>复制</span>
                </button>
              </div>
            </div>
            
            <div 
              v-if="message.role === 'assistant'"
              class="message-actions"
            >
              <button 
                class="action-btn"
                :disabled="isStreaming"
                @click="copyMessage(message.content, message.id)"
                :title="copiedMessageId === message.id ? '已复制' : '复制'"
              >
                <el-icon :size="14">
                  <Check v-if="copiedMessageId === message.id" />
                  <CopyDocument v-else />
                </el-icon>
              </button>
              <button 
                class="action-btn"
                @click="exportToPdf(message)"
                title="导出为PDF"
                :disabled="isStreaming"
              >
                <el-icon :size="14"><Download /></el-icon>
              </button>
              <button 
                class="action-btn"
                @click="regenerateAnswer(message, index)"
                :disabled="isStreaming"
                title="重新回答"
              >
                <el-icon :size="14" :class="{ 'spin': regeneratingMessageId === message.id }">
                  <RefreshRight />
                </el-icon>
              </button>
            </div>
            
            <div 
              v-if="message.role === 'assistant' && message.sources && message.sources.length > 0" 
              class="message-sources"
            >
              <div class="sources-toggle" @click="toggleMessageSources(index)">
                <el-icon :size="14"><Document /></el-icon>
                <span>{{ message.sources.length }} 个来源</span>
                <el-icon :size="12" :class="{ 'rotate-180': isMessageExpanded(index) }">
                  <ArrowDown />
                </el-icon>
              </div>
              <div v-show="isMessageExpanded(index)" class="sources-content">
                <div 
                  v-for="source in message.sources" 
                  :key="source.id" 
                  class="source-item"
                >
                  <div class="source-header">
                    <span class="source-badge">{{ getFileExt(source.filename) }}</span>
                    <span class="source-filename">{{ source.filename }}</span>
                  </div>
                  <div class="source-text">{{ source.content }}</div>
                </div>
              </div>
            </div>
            
            <div 
              v-if="message.role === 'assistant' && message.relatedLinks && message.relatedLinks.length > 0 && !(index === chatStore.messages.length - 1 && isStreaming)" 
              class="related-links"
            >
              <div class="links-label">相关链接</div>
              <div class="links-list">
                <a 
                  v-for="(link, linkIndex) in message.relatedLinks" 
                  :key="linkIndex"
                  :href="link.url"
                  target="_blank"
                  class="link-btn"
                >
                  <span class="link-icon">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                    </svg>
                  </span>
                  <span class="link-title">{{ link.title }}</span>
                  <span v-if="link.description" class="link-desc">{{ link.description }}</span>
                </a>
              </div>
            </div>
            
            <div 
              v-if="message.role === 'assistant' && index === chatStore.messages.length - 1 && message.suggestedQuestions && message.suggestedQuestions.length > 0 && !isStreaming" 
              class="suggested-questions"
            >
              <div class="suggestions-label">快捷提问</div>
              <div class="suggestions-list">
                <button 
                  v-for="(question, qIndex) in message.suggestedQuestions" 
                  :key="qIndex"
                  class="suggestion-btn"
                  @click="useSuggestion(question)"
                  :title="question"
                >
                  {{ question }}
                </button>
              </div>
            </div>
            
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
      </div>
    </div>

    <button 
      v-if="showScrollButton" 
      class="scroll-bottom-btn"
      @click="() => scrollToBottom(true)"
    >
      <el-icon><ArrowDown /></el-icon>
    </button>

    <div class="input-area">
      <div v-if="isOptimizing" class="optimizing-loading">
        <span class="loading-icon" v-html="OptimizeIcon"></span>
        <span>正在优化查询...</span>
      </div>

      <div v-if="isOptimized" class="optimization-status">
        <span class="status-icon" v-html="OptimizeIcon"></span>
        <span>已优化</span>
      </div>

      <div class="input-wrapper">
        <textarea
          v-model="inputMessage"
          class="chat-input"
          :class="{ 'optimized': isOptimized }"
          placeholder="Type your message..."
          rows="1"
          @keydown.enter.prevent="sendMessage"
        ></textarea>
        <div class="input-actions">
          <button
            v-if="!isOptimized && inputMessage.trim() && !isStreaming"
            class="icon-btn no-border optimize-btn"
            :class="{ 'spin': isOptimizing }"
            :disabled="isOptimizing"
            title="优化查询"
            @click="optimizeInput"
          >
            <span class="custom-icon" v-html="OptimizeIcon"></span>
          </button>
          <button
            v-if="isOptimized && !isStreaming"
            class="icon-btn no-border revert-btn"
            title="撤回优化"
            @click="revertOptimization"
          >
            <span class="custom-icon" v-html="RevertIcon"></span>
          </button>
          <button 
            v-if="isStreaming"
            class="btn btn-danger btn-abort"
            @click="abortGeneration"
            title="中止回答"
          >
            <el-icon :size="18"><CircleClose /></el-icon>
          </button>
          <button 
            v-else
            class="btn btn-primary btn-send"
            :disabled="!inputMessage.trim() || isOptimizing"
            @click="sendMessage"
          >
            <el-icon :size="18"><Position /></el-icon>
          </button>
        </div>
      </div>
      <div class="input-hint">
        <span v-if="isStreaming" class="streaming-hint">
          <span class="streaming-dot"></span>
          正在生成回答... 点击红色按钮可中止
        </span>
        <span v-else-if="isOptimized">已优化查询，点击 可撤回</span>
        <span v-else>Press Enter to send, Shift + Enter for new line</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-view {
  /* Primary Colors - 主题色 #e0301e */
  --color-primary: #e0301e;
  --color-primary-light: #f04a3a;
  --color-primary-dark: #c22818;
  --color-primary-lightest: #fef2f1;
  
  /* Secondary Colors - 辅助色 */
  --color-secondary: #1e3a5f;
  --color-secondary-light: #2d4a6f;
  
  /* Semantic Colors */
  --color-success: #10b981;
  --color-success-light: #d1fae5;
  --color-warning: #f59e0b;
  --color-warning-light: #fef3c7;
  --color-error: #dc2626;
  --color-error-light: #fee2e2;
  
  /* Background Colors */
  --bg-primary: #FFFFFF;
  --bg-secondary: #fafafa;
  --bg-tertiary: #f5f5f5;
  --bg-active: #fef2f1;
  /* Text Colors - 确保WCAG对比度 */
  --text-primary: #1f2937;      /* 对比度 12.6:1 (AAA) */
  --text-secondary: #4b5563;    /* 对比度 7.5:1 (AA) */
  --text-tertiary: #6b7280;     /* 对比度 5.3:1 (AA) */
  --text-disabled: #9ca3af;     /* 对比度 2.7:1 */
  --text-on-primary: #ffffff;   /* 白色在红色上对比度 5.2:1 (AA) */
  --border-light: #E5E7EB;
  --border-medium: #D1D5DB;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-2xl: 24px;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --duration-fast: 150ms;
  --duration-normal: 200ms;
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;
  
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--bg-primary);
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-6);
}

.empty-content {
  text-align: center;
  max-width: 600px;
}

.empty-icon {
  color: var(--color-primary);
  margin-bottom: var(--space-4);
}

.empty-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-3);
}

.empty-subtitle {
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  margin-bottom: var(--space-6);
}

.suggested-questions {
  margin-top: 12px;
  padding: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  gap: 0;
}

.suggestion-chip {
  padding: 10px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
  line-height: 1.5;
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
  max-width: 100%;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  text-align: left;
}

.suggestion-chip:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--bg-primary);
  transform: translateY(-2px);
  box-shadow: 0 4px 6px -1px rgba(224, 48, 30, 0.1);
}

.related-links {
  margin-top: 20px;
  padding: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
}

.links-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: none;
  letter-spacing: 0.02em;
  margin-bottom: 16px;
  padding-left: 12px;
  border-left: 3px solid var(--color-primary);
  line-height: 1.4;
}

.links-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.link-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  color: var(--color-primary);
  text-decoration: none;
  transition: all var(--duration-fast) var(--ease-default);
}

.link-btn:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--bg-primary);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.link-btn:active {
  background: var(--color-primary-dark);
  border-color: var(--color-primary-dark);
  transform: translateY(0);
}

.link-icon {
  display: flex;
  align-items: center;
  opacity: 0.8;
}

.link-icon svg {
  width: 14px;
  height: 14px;
}

.link-title {
  font-weight: var(--font-weight-medium);
}

.link-desc {
  color: var(--text-tertiary);
  font-size: var(--font-size-xs);
}

.link-btn:hover .link-desc {
  color: rgba(255, 255, 255, 0.8);
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-5);
}

.messages-list {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.message-wrapper {
  display: flex;
  gap: var(--space-3);
  animation: slideUp var(--duration-normal) var(--ease-out);
}

.message-wrapper.user {
  flex-direction: row-reverse;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message-avatar .el-avatar {
  background-color: var(--bg-tertiary);
  color: var(--text-tertiary);
}

.message-avatar .el-avatar.user {
  background-color: var(--color-primary);
  color: white;
}

.message-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  max-width: 70%;
  position: relative;
}

.message-wrapper.user .message-content {
  align-items: flex-end;
}

.message-bubble {
  padding: 12px 16px;
  font-size: var(--font-size-md);
  line-height: var(--line-height-relaxed);
  word-wrap: break-word;
}

.message-bubble.user {
  background-color: var(--color-primary);
  color: white;
  border-radius: 18px 18px 4px 18px;
}

.message-bubble.assistant {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border-light);
  border-radius: 18px 18px 18px 4px;
}

.message-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  padding: 0 4px;
}

.message-actions {
  display: flex;
  gap: var(--space-1);
  margin-top: var(--space-1);
}

.message-popup-actions {
  position: absolute;
  bottom: -40px;
  right: 0;
  z-index: 100;
}

.popup-menu {
  display: flex;
  align-items: center;
  background-color: white;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: 4px;
}

.popup-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
  white-space: nowrap;
}

.popup-btn:hover {
  background-color: var(--bg-secondary);
  color: var(--color-primary);
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  background: transparent;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
}

.action-btn:hover:not(:disabled) {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
  transform: scale(1.05);
}

.action-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.action-btn .spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 8px 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background-color: var(--text-tertiary);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.message-sources {
  margin-top: var(--space-3);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  overflow: hidden;
  background-color: var(--bg-secondary);
}

.sources-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  cursor: pointer;
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  transition: all var(--duration-fast) var(--ease-default);
}

.sources-toggle:hover {
  background-color: var(--bg-secondary);
  color: var(--color-primary);
}

.sources-toggle .rotate-180 {
  transform: rotate(180deg);
}

.sources-content {
  padding: var(--space-3);
  border-top: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.source-item {
  padding: var(--space-2) var(--space-3);
  background-color: var(--bg-primary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-light);
}

.source-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}

.source-badge {
  padding: 2px 6px;
  background: linear-gradient(135deg, #e0301e15, #e0301e25);
  border-radius: var(--radius-sm);
  color: #e0301e;
  font-size: 10px;
  font-weight: 600;
}

.source-filename {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.source-text {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  line-height: var(--line-height-normal);
}

.rotate-180 {
  transform: rotate(180deg);
}

.scroll-bottom-btn {
  position: absolute;
  bottom: 100px;
  right: 320px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-md);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-secondary);
  transition: all var(--duration-fast) var(--ease-default);
}

.scroll-bottom-btn:hover {
  background-color: var(--bg-secondary);
  color: var(--text-primary);
}

.input-area {
  padding: var(--space-4) var(--space-5);
  background-color: var(--bg-primary);
  border-top: 1px solid var(--border-light);
}

.input-wrapper {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  gap: var(--space-3);
  padding: var(--space-3);
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-xl);
  transition: all var(--duration-fast) var(--ease-default);
}

.input-wrapper:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--bg-active);
}

.chat-input {
  flex: 1;
  border: none;
  background: transparent;
  font-size: var(--font-size-md);
  color: var(--text-primary);
  resize: none;
  outline: none;
  max-height: 200px;
  min-height: 24px;
}

.chat-input::placeholder {
  color: var(--text-tertiary);
}

.input-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.btn-send {
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 50%;
  flex-shrink: 0;
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-abort {
  width: 40px;
  height: 40px;
  padding: 0;
  border-radius: 50%;
  flex-shrink: 0;
  background-color: var(--color-error);
  border-color: var(--color-error);
  color: white;
  animation: pulse-abort 1.5s ease-in-out infinite;
}

.btn-abort:hover {
  background-color: #ef4444;
  border-color: #ef4444;
  transform: scale(1.05);
}

.btn-abort:active {
  transform: scale(0.95);
}

@keyframes pulse-abort {
  0%, 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(220, 38, 38, 0); }
}

.input-hint {
  text-align: center;
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-2);
}

.streaming-hint {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-error);
}

.streaming-dot {
  width: 8px;
  height: 8px;
  background-color: var(--color-error);
  border-radius: 50%;
  animation: pulse-dot 1s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.optimizing-loading {
  max-width: 800px;
  margin: 0 auto var(--space-3);
  padding: var(--space-3);
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.loading-icon {
  animation: spin 1.5s linear infinite;
  color: var(--color-primary);
  width: 16px;
  height: 16px;
}

.optimization-status {
  max-width: 800px;
  margin: 0 auto var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: linear-gradient(135deg, var(--color-primary-lightest) 0%, #fff5f5 100%);
  border: 1px solid var(--color-primary-light);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-primary-dark);
  animation: slideDown var(--duration-fast) var(--ease-out);
}

.status-icon {
  color: var(--color-primary);
  width: 14px;
  height: 14px;
}

.custom-icon {
  width: 16px;
  height: 16px;
}

.optimize-btn {
  color: var(--color-primary);
}

.optimize-btn:hover:not(:disabled) {
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
  transform: scale(1.05);
}

.chat-input.optimized {
  background: linear-gradient(135deg, var(--color-primary-lightest) 0%, #ffffff 100%);
  border-left: 3px solid var(--color-primary);
}

.revert-btn {
  color: #f44336;
}

.revert-btn:hover:not(:disabled) {
  background-color: #f44336;
  border-color: #f44336;
  color: white;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.suggestions-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: none;
  letter-spacing: 0.02em;
  margin-bottom: 16px;
  padding-left: 12px;
  border-left: 3px solid var(--color-primary);
  line-height: 1.4;
}

.suggestions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.suggestion-btn {
  padding: var(--space-2) var(--space-4);
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
  max-width: 280px;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  text-align: left;
}

.suggestion-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--bg-secondary);
}

.suggestion-btn:active {
  background: var(--bg-active);
  transform: scale(0.98);
}

.markdown-body {
  line-height: var(--line-height-relaxed);
}

.markdown-body :deep(p) {
  margin-bottom: var(--space-3);
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(code) {
  padding: 2px 6px;
  background-color: var(--bg-tertiary);
  border-radius: var(--radius-sm);
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  padding: var(--space-4);
  background-color: #1e1e1e;
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin-bottom: var(--space-3);
}

.markdown-body :deep(pre code) {
  background-color: transparent;
  color: #d4d4d4;
  padding: 0;
}

.markdown-body :deep(ul), .markdown-body :deep(ol) {
  margin-bottom: var(--space-3);
  padding-left: var(--space-5);
}

.markdown-body :deep(li) {
  margin-bottom: var(--space-1);
}

.markdown-body :deep(blockquote) {
  padding-left: var(--space-4);
  border-left: 3px solid var(--color-primary);
  color: var(--text-secondary);
  margin-bottom: var(--space-3);
}

/* 响应式排版优化 */
@media (max-width: 1024px) {
  .related-links,
  .suggested-questions {
    padding: 16px;
  }
}

@media (max-width: 768px) {
  .links-label,
  .suggestions-label {
    font-size: 14px;
    font-weight: 600;
  }
  
  .related-links,
  .suggested-questions {
    padding: 16px;
    margin-top: 12px;
  }
  
  .links-list,
  .suggestions-list {
    gap: 8px;
  }
  
  .link-btn,
  .suggestion-btn,
  .suggestion-chip {
    width: 100%;
    justify-content: center;
    padding: 12px 16px;
  }
}

@media (max-width: 375px) {
  .links-label,
  .suggestions-label {
    font-size: 15px;
  }
  
  .related-links,
  .suggested-questions {
    padding: 12px;
  }
}
</style>
