<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useDocumentStore, type DocumentStatus } from '@/stores/document'
import { documentApi } from '@/api'
import { 
  Upload, 
  Document, 
  Delete, 
  RefreshRight,
  Loading
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const documentStore = useDocumentStore()
const uploading = ref(false)
const uploadProgress = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const totalDocuments = ref(0)
let pollingTimer: number | null = null

const acceptTypes = '.pdf,.docx,.txt,.xlsx,.pptx,.png,.jpg,.jpeg,.gif,.bmp,.webp'

const getStatusType = (status: DocumentStatus): 'success' | 'warning' | 'danger' | 'info' => {
  const map: Record<DocumentStatus, 'success' | 'warning' | 'danger' | 'info'> = {
    READY: 'success',
    INDEXING: 'info',
    QUEUED: 'warning',
    ERROR: 'danger'
  }
  return map[status]
}

const getStatusText = (status: DocumentStatus): string => {
  const map: Record<DocumentStatus, string> = {
    READY: '就绪',
    INDEXING: '索引中',
    QUEUED: '排队中',
    ERROR: '错误'
  }
  return map[status]
}

const hasProcessingDocuments = computed(() => 
  documentStore.documents.some(doc => doc.status === 'INDEXING' || doc.status === 'QUEUED')
)

const formatSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatDate = (date: Date | string): string => {
  const d = new Date(date)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleUpload = async (options: any) => {
  const { file } = options
  uploading.value = true
  uploadProgress.value = 0
  
  try {
    const result = await documentApi.upload(file, (progress) => {
      uploadProgress.value = progress
    })
    
    documentStore.addDocument({
      id: result.id,
      filename: result.filename,
      status: result.status as DocumentStatus,
      size: result.size,
      uploadTime: new Date(result.uploadTime)
    })
    
    ElMessage.success('文档上传成功，正在处理中...')
    startPolling()
  } catch (error) {
    console.error('Upload error:', error)
    ElMessage.error('文档上传失败')
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

const handleDelete = async (doc: { id: string; filename: string }) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${doc.filename}" 吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await documentApi.delete(doc.id)
    documentStore.removeDocument(doc.id)
    totalDocuments.value--
    ElMessage.success('文档已删除')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
      ElMessage.error('删除失败')
    }
  }
}

const handleReindex = async (doc: { id: string; filename: string }) => {
  try {
    documentStore.updateDocument(doc.id, { status: 'INDEXING' })
    await documentApi.reindex(doc.id)
    ElMessage.success(`文档 "${doc.filename}" 开始重新索引`)
    startPolling()
  } catch (error) {
    console.error('Reindex error:', error)
    documentStore.updateDocument(doc.id, { status: 'ERROR' })
    ElMessage.error('重新索引失败')
  }
}

const handleReindexAll = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要重新索引所有文档吗？这可能需要一些时间。',
      '重新索引全部',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    for (const doc of documentStore.documents) {
      if (doc.status === 'READY') {
        documentStore.updateDocument(doc.id, { status: 'INDEXING' })
        await documentApi.reindex(doc.id)
      }
    }
    ElMessage.success('所有文档开始重新索引')
    startPolling()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Reindex all error:', error)
      ElMessage.error('重新索引失败')
    }
  }
}

const loadDocuments = async () => {
  try {
    const result = await documentApi.list(currentPage.value, pageSize.value)
    totalDocuments.value = result.total
    documentStore.setDocuments(result.documents.map(doc => ({
      id: doc.id,
      filename: doc.filename,
      status: doc.status as DocumentStatus,
      size: doc.size,
      uploadTime: new Date(doc.uploadTime),
      chunk_count: doc.chunk_count,
      error: doc.error
    })))
  } catch (error) {
    console.error('Load documents error:', error)
  }
}

const startPolling = () => {
  if (pollingTimer) return
  
  pollingTimer = window.setInterval(async () => {
    if (!hasProcessingDocuments.value) {
      stopPolling()
      return
    }
    await loadDocuments()
  }, 3000)
}

const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

onMounted(() => {
  loadDocuments()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="documents-page">
    <div class="documents-header">
      <h1 class="page-title">知识库文档管理</h1>
      <el-button 
        type="primary" 
        :icon="RefreshRight"
        @click="handleReindexAll"
        :disabled="!documentStore.readyCount"
      >
        重新索引全部
      </el-button>
    </div>

    <div class="upload-section">
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        :accept="acceptTypes"
        :show-file-list="false"
        :http-request="handleUpload"
        :disabled="uploading"
      >
        <div class="upload-content">
          <el-icon v-if="!uploading" class="upload-icon"><Upload /></el-icon>
          <el-icon v-else class="upload-icon is-loading"><Loading /></el-icon>
          <div class="upload-text">
            <template v-if="!uploading">
              <p class="upload-title">拖拽文件到此处上传，或<em>点击上传</em></p>
              <p class="upload-hint">支持 PDF、DOCX、TXT 格式</p>
            </template>
            <template v-else>
              <p class="upload-title">正在上传...</p>
              <el-progress 
                :percentage="uploadProgress" 
                :stroke-width="6"
                class="upload-progress"
              />
            </template>
          </div>
        </div>
      </el-upload>
    </div>

    <div class="documents-table">
      <el-table 
        :data="documentStore.documents" 
        style="width: 100%"
        row-key="id"
      >
        <el-table-column label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="filename-cell">
              <el-icon class="file-icon" :size="20"><Document /></el-icon>
              <span class="filename">{{ row.filename }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tooltip v-if="row.status === 'ERROR' && row.error" :content="row.error" placement="top">
              <el-tag :type="getStatusType(row.status)" size="small">
                {{ getStatusText(row.status) }}
              </el-tag>
            </el-tooltip>
            <el-tag v-else :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="大小" width="100" align="right">
          <template #default="{ row }">
            {{ formatSize(row.size) }}
          </template>
        </el-table-column>
        
        <el-table-column label="上传时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.uploadTime) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" align="center">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              text 
              :icon="RefreshRight"
              @click="handleReindex(row)"
              :disabled="row.status === 'INDEXING'"
            >
              重新索引
            </el-button>
            <el-button 
              type="danger" 
              text 
              :icon="Delete"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!documentStore.documents.length" class="empty-table">
        <el-empty description="暂无文档，请上传" />
      </div>

      <div v-if="documentStore.documents.length" class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalDocuments"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="loadDocuments"
          @current-change="loadDocuments"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.documents-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.documents-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.upload-section {
  margin-bottom: 24px;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload) {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: auto;
  min-height: 160px;
  border: 2px dashed var(--border-color);
  border-radius: var(--radius-lg);
  background: var(--bg-white);
  transition: all 0.3s;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--primary-color);
  background: var(--primary-bg-light);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
}

.upload-icon {
  font-size: 48px;
  color: var(--primary-color);
  margin-bottom: 16px;
}

.upload-text {
  text-align: center;
}

.upload-title {
  font-size: 16px;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.upload-title em {
  color: var(--primary-color);
  font-style: normal;
}

.upload-hint {
  font-size: 14px;
  color: var(--text-tertiary);
}

.upload-progress {
  width: 200px;
  margin-top: 12px;
}

.documents-table {
  background: var(--bg-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.filename-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: var(--primary-color);
}

.filename {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-table {
  padding: 40px;
}

.pagination {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid var(--border-color);
}
</style>
