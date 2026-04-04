<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useDocumentStore } from '@/stores/document'
import { documentApi, flowGuideApi } from '@/api'
import type { PendingDuplicate } from '@/api'
import { 
  Upload, 
  Document, 
  Delete, 
  RefreshRight,
  Search,
  DocumentChecked,
  Warning,
  Loading
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getFileExtension, getFileIconStyle } from '@/utils/fileColors'
import { DOCUMENT_CONSTANTS } from '@/constants'
import DuplicateConfirmDialog from '@/components/DuplicateConfirmDialog/index.vue'

const documentStore = useDocumentStore()
const searchQuery = ref('')
const isUploading = ref(false)
const uploadProgress = ref(0)
const showDuplicateDialog = ref(false)
const pendingDuplicates = ref<PendingDuplicate[]>([])

const checkPendingDuplicates = async () => {
  // 延迟 2 秒等待后端异步提取完成
  setTimeout(async () => {
    try {
      const list = await flowGuideApi.getPendingDuplicates()
      if (list.length > 0) {
        pendingDuplicates.value = list
        showDuplicateDialog.value = true
      }
    } catch {
      // 非关键功能，静默失败
    }
  }, 2000)
}

// Auto-refresh interval for processing documents
let refreshInterval: number | null = null

// Check if any document is in processing state
const hasProcessingDocuments = computed(() => {
  return documentStore.documents.some(doc => 
    doc.status === 'INDEXING' || doc.status === 'QUEUED'
  )
})

const statusMap: Record<string, { label: string; type: string; icon: any }> = {
  READY: { label: 'Completed', type: 'success', icon: DocumentChecked },
  INDEXING: { label: 'Processing', type: 'warning', icon: Loading },
  QUEUED: { label: 'Pending', type: 'info', icon: Document },
  ERROR: { label: 'Failed', type: 'danger', icon: Warning }
}

const filteredDocuments = computed(() => {
  if (!searchQuery.value) return documentStore.documents
  return documentStore.documents.filter(doc =>
    doc.filename.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const handleUpload = async (file: any) => {
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    await documentApi.upload(file, (progress) => {
      uploadProgress.value = progress
    })
    ElMessage.success('Document uploaded successfully')
    await loadDocuments()
    // 检查是否有待处理的重复流程
    checkPendingDuplicates()
  } catch (error) {
    ElMessage.error('Upload failed')
  } finally {
    isUploading.value = false
    uploadProgress.value = 0
  }
}

const loadDocuments = async () => {
  try {
    const result = await documentApi.list()
    const docs = result.documents.map((d: any) => ({
      ...d,
      uploadTime: new Date(d.uploadTime)
    }))
    documentStore.setDocuments(docs)
    // Check if we need to start/stop auto-refresh after loading
    setupAutoRefreshWatcher()
  } catch (error) {
    console.error('Failed to load documents:', error)
  }
}

const deleteDocument = async (doc: any) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete "${doc.filename}"?`,
      'Delete Confirmation',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    await documentApi.delete(doc.id)
    ElMessage.success('Document deleted')
    await loadDocuments()
  } catch {}
}

const reindexDocument = async (doc: any) => {
  try {
    await documentApi.reindex(doc.id)
    ElMessage.success('Reindexing started')
    await loadDocuments()
  } catch {
    ElMessage.error('Reindex failed')
  }
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (date: Date) => {
  return new Date(date).toLocaleDateString()
}

const getFileExt = (filename: string): string => {
  return getFileExtension(filename)
}

// Start auto-refresh when there are processing documents
const startAutoRefresh = () => {
  if (refreshInterval) return
  refreshInterval = window.setInterval(() => {
    loadDocuments()
  }, 3000) // Refresh every 3 seconds
}

// Stop auto-refresh
const stopAutoRefresh = () => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
}

// Watch for processing documents and manage auto-refresh
const setupAutoRefreshWatcher = () => {
  if (hasProcessingDocuments.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

onMounted(() => {
  loadDocuments()
  // Initial check for processing documents
  setupAutoRefreshWatcher()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<template>
  <div class="documents-view">
    <!-- Header -->
    <div class="page-header">
      <div class="header-title">
        <h1>Documents</h1>
        <p class="header-subtitle">Manage your knowledge base documents</p>
      </div>
      <div class="header-actions">
        <el-input
          v-model="searchQuery"
          placeholder="Search documents..."
          :prefix-icon="Search"
          class="search-input"
          clearable
        />
        <el-upload
          :accept="DOCUMENT_CONSTANTS.ACCEPT_TYPES"
          :auto-upload="false"
          :show-file-list="false"
          :on-change="(file: any) => handleUpload(file.raw)"
        >
          <button class="btn btn-primary">
            <el-icon :size="18"><Upload /></el-icon>
            <span>Upload Document</span>
          </button>
        </el-upload>
      </div>
    </div>

    <!-- Upload Progress -->
    <div v-if="isUploading" class="upload-progress">
      <el-progress 
        :percentage="uploadProgress" 
        :stroke-width="8"
        :show-text="true"
      />
    </div>

    <!-- Documents Grid -->
    <div class="documents-content">
      <div v-if="filteredDocuments.length === 0" class="empty-state">
        <el-empty description="No documents yet">
          <template #image>
            <el-icon :size="64" color="#d1d1d1"><Document /></el-icon>
          </template>
          <p>Upload your first document to get started</p>
        </el-empty>
      </div>

      <div v-else class="documents-grid">
        <div
          v-for="doc in filteredDocuments"
          :key="doc.id"
          class="document-card"
        >
          <!-- Left: File Icon -->
          <div 
            class="doc-icon"
            :style="getFileIconStyle(doc.filename)"
          >
            <span class="file-ext">{{ getFileExt(doc.filename) }}</span>
          </div>
          
          <!-- Center: File Info -->
          <div class="doc-content">
            <!-- Row 1: Filename and Size -->
            <div class="doc-main-row">
              <span class="doc-name" :title="doc.filename">{{ doc.filename }}</span>
              <span class="doc-size">{{ formatFileSize(doc.size) }}</span>
            </div>
            
            <!-- Row 2: Date, Status and Actions -->
            <div class="doc-sub-row">
              <span class="doc-date">{{ formatDate(doc.uploadTime) }}</span>
              
              <div class="doc-right-section">
                <div 
                  class="status-badge"
                  :class="doc.status.toLowerCase()"
                >
                  <el-icon :size="12">
                    <component :is="statusMap[doc.status].icon" />
                  </el-icon>
                  <span>{{ statusMap[doc.status].label }}</span>
                </div>
                
                <div class="doc-actions">
                  <button 
                    class="action-btn"
                    title="Reindex"
                    @click="reindexDocument(doc)"
                    :disabled="doc.status === 'INDEXING'"
                  >
                    <el-icon :size="14"><RefreshRight /></el-icon>
                  </button>
                  <button 
                    class="action-btn"
                    title="Delete"
                    @click="deleteDocument(doc)"
                  >
                    <el-icon :size="14"><Delete /></el-icon>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <DuplicateConfirmDialog
    v-model:visible="showDuplicateDialog"
    :duplicates="pendingDuplicates"
    @resolved="pendingDuplicates = []"
  />
</template>

<style scoped>
.documents-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: var(--space-5);
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-5);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--border-light);
}

.header-title h1 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}

.header-subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.header-actions {
  display: flex;
  gap: var(--space-3);
  align-items: center;
}

.search-input {
  width: 280px;
}

.search-input :deep(.el-input__wrapper) {
  background-color: var(--bg-secondary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  box-shadow: none;
}

/* Upload Progress */
.upload-progress {
  margin-bottom: var(--space-4);
  padding: var(--space-3);
  background-color: var(--bg-secondary);
  border-radius: var(--radius-md);
}

/* Content */
.documents-content {
  flex: 1;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-tertiary);
}

.empty-state p {
  margin-top: var(--space-3);
  font-size: var(--font-size-sm);
}

/* Grid */
.documents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-4);
}

/* Document Card */
.document-card {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4);
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  transition: all var(--duration-fast) var(--ease-default);
}

.document-card:hover {
  border-color: var(--border-default);
  box-shadow: var(--shadow-sm);
}

.doc-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  flex-shrink: 0;
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-xs);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  transition: all var(--duration-fast) var(--ease-default);
}

.document-card:hover .doc-icon {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.file-ext {
  font-size: 10px;
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.5px;
}

/* Document Content */
.doc-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* Row 1: Filename and Size */
.doc-main-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.doc-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.doc-size {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  font-weight: var(--font-weight-medium);
  white-space: nowrap;
  flex-shrink: 0;
  background-color: var(--bg-secondary);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

/* Row 2: Date, Status and Actions */
.doc-sub-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.doc-date {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.doc-right-section {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* Status Badge */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: var(--font-weight-medium);
  transition: all var(--duration-fast) var(--ease-default);
}

.status-badge.ready,
.status-badge.completed {
  background-color: #e6f7e6;
  color: #52c41a;
}

.status-badge.indexing,
.status-badge.processing {
  background-color: #fff7e6;
  color: #fa8c16;
}

.status-badge.queued,
.status-badge.pending {
  background-color: #e6f4ff;
  color: #1890ff;
}

.status-badge.error,
.status-badge.failed {
  background-color: #fff1f0;
  color: #f5222d;
}

/* Action Buttons */
.doc-actions {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  padding: 0;
  background-color: transparent;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
}

.action-btn:hover:not(:disabled) {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
  transform: scale(1.05);
}

.action-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: var(--space-4);
  }

  .header-actions {
    width: 100%;
    flex-direction: column;
  }

  .search-input {
    width: 100%;
  }

  .documents-grid {
    grid-template-columns: 1fr;
  }
}
</style>
