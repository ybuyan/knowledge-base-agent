<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import { chatApi } from '@/api'
import { Lightning, InfoFilled, Top } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { getFileTypeColor, getFileExtension } from '@/utils/fileColors'

const chatStore = useChatStore()

const hasMessages = computed(() => chatStore.messages.length > 0)

const suggestedQuestions = [
  '如何重置我的密码？',
  '公司有哪些节假日？',
  '如何申请休假？',
  '在哪里可以找到员工手册？'
]

interface HotDocument {
  filename: string
  query_count: number
  last_queried: string
}

const hotDocuments = ref<HotDocument[]>([])
const isLoadingDocs = ref(false)

const getFileExt = (filename: string): string => {
  return getFileExtension(filename)
}

const getFileBadgeStyle = (filename: string) => {
  const color = getFileTypeColor(filename)
  return {
    backgroundColor: color.lightBg,
    color: color.text,
    border: `1px solid ${color.border}`
  }
}

const loadHotDocuments = async () => {
  isLoadingDocs.value = true
  try {
    hotDocuments.value = await chatApi.getMostQueriedDocuments(5)
  } catch (error) {
    ElMessage.error('加载热门文档失败')
  } finally {
    isLoadingDocs.value = false
  }
}

onMounted(() => {
  loadHotDocuments()
})

// Watch for new messages and refresh hot documents
watch(() => chatStore.messages.length, (newLength, oldLength) => {
  if (newLength > oldLength) {
    // New message added, refresh hot documents
    loadHotDocuments()
  }
})
</script>

<template>
  <aside class="right-panel">
    <!-- Hot Documents Section -->
    <div class="panel-section">
      <div class="section-header">
        <el-icon :size="18"><Top /></el-icon>
        <span>Hot Documents</span>
      </div>
      <div class="section-content">
        <div v-if="isLoadingDocs" class="loading-text">加载中...</div>
        <div v-else-if="hotDocuments.length === 0" class="empty-text">暂无数据</div>
        <div 
          v-for="(doc, index) in hotDocuments" 
          :key="index"
          class="doc-item"
        >
          <span class="doc-type" :style="getFileBadgeStyle(doc.filename)">{{ getFileExt(doc.filename) }}</span>
          <span class="doc-title">{{ doc.filename }}</span>
          <span class="doc-count">{{ doc.query_count }}次</span>
        </div>
      </div>
    </div>

    <!-- Suggested Questions -->
    <!-- <div class="panel-section" v-if="!hasMessages">
      <div class="section-header">
        <el-icon :size="18"><Lightning /></el-icon>
        <span>Suggested Questions</span>
      </div>
      <div class="section-content">
        <button
          v-for="(question, index) in suggestedQuestions"
          :key="index"
          class="suggestion-btn"
          @click="chatStore.addMessage({ role: 'user', content: question })"
        >
          {{ question }}
        </button>
      </div>
    </div> -->

    <!-- System Info -->
    <div class="panel-section">
      <div class="section-header">
        <el-icon :size="18"><InfoFilled /></el-icon>
        <span>System Status</span>
      </div>
      <div class="section-content">
        <div class="status-item">
          <span class="status-label">Model</span>
          <span class="status-value">GPT-4</span>
        </div>
        <div class="status-item">
          <span class="status-label">Status</span>
          <span class="status-value online">Online</span>
        </div>
        <div class="status-item">
          <span class="status-label">Response Time</span>
          <span class="status-value">< 2s</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<style scoped>
.right-panel {
  width: var(--right-panel-width);
  background-color: var(--bg-secondary);
  border-left: 1px solid var(--border-light);
  padding: var(--space-5);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.panel-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.section-header .el-icon {
  color: var(--text-tertiary);
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.doc-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
}

.doc-item:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-sm);
}

.doc-type {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.doc-title {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-btn {
  text-align: left;
  padding: var(--space-3);
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
}

.suggestion-btn:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background-color: var(--bg-active);
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) 0;
  font-size: var(--font-size-sm);
}

.status-label {
  color: var(--text-tertiary);
}

.status-value {
  color: var(--text-primary);
  font-weight: var(--font-weight-medium);
}

.status-value.online {
  color: var(--success-color);
}

.loading-text,
.empty-text {
  text-align: center;
  padding: var(--space-4);
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
}

.doc-count {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-left: auto;
  padding-left: var(--space-2);
}
</style>
