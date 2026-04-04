<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import { 
  Search, 
  FolderOpened, 
  ChatDotRound, 
  Plus,
  More,
  Edit,
  Delete,
  SwitchButton,
  List
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const chatStore = useChatStore()
const authStore = useAuthStore()

const searchQuery = ref('')
const editingSessionId = ref('')
const editingTitle = ref('')

const isChatActive = computed(() => route.path === '/chat')
const isDocumentsActive = computed(() => route.path === '/documents')
const isFlowManagerActive = computed(() => route.path === '/flow-manager')
const isAdminOrManager = computed(() => authStore.isHR)

const filteredSessions = computed(() => {
  if (!searchQuery.value) return chatStore.sessions
  return chatStore.sessions.filter(s => 
    s.title.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const navigateToChat = () => router.push('/chat')
const navigateToDocuments = () => router.push('/documents')
const navigateToFlowManager = () => router.push('/flow-manager')

const createNewChat = async () => {
  await chatStore.createSession()
  navigateToChat()
}

const selectSession = (sessionId: string) => {
  chatStore.selectSession(sessionId)
  navigateToChat()
}

const startRename = (session: any, event: Event) => {
  event.stopPropagation()
  editingSessionId.value = session.id
  editingTitle.value = session.title
}

const finishRename = () => {
  if (editingTitle.value.trim() && editingSessionId.value) {
    chatStore.renameSession(editingSessionId.value, editingTitle.value.trim())
  }
  editingSessionId.value = ''
  editingTitle.value = ''
}

const cancelRename = () => {
  editingSessionId.value = ''
  editingTitle.value = ''
}

const deleteSession = async (session: any, event: Event) => {
  event.stopPropagation()
  try {
    await ElMessageBox.confirm(
      'Are you sure you want to delete this session? This action cannot be undone.',
      'Delete Confirmation',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    await chatStore.deleteSession(session.id)
    ElMessage.success('Session deleted')
  } catch {}
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

const formatTime = (date: Date) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  if (diff < 60000) return 'Just now'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
  return d.toLocaleDateString()
}
</script>

<template>
  <aside class="app-sidebar">
    <!-- Search -->
    <div class="sidebar-search">
      <el-input
        v-model="searchQuery"
        placeholder="Search conversations..."
        :prefix-icon="Search"
        clearable
        class="search-input"
      />
    </div>

    <!-- Navigation -->
    <nav class="sidebar-nav">
      <div 
        class="nav-item" 
        :class="{ active: isChatActive }"
        @click="navigateToChat"
      >
        <el-icon :size="20"><ChatDotRound /></el-icon>
        <span>Chat</span>
      </div>

      <div 
        v-if="isAdminOrManager"
        class="nav-item" 
        :class="{ active: isDocumentsActive }"
        @click="navigateToDocuments"
      >
        <el-icon :size="20"><FolderOpened /></el-icon>
        <span>Documents</span>
      </div>
      
      <div
        v-if="isAdminOrManager"
        class="nav-item"
        :class="{ active: isFlowManagerActive }"
        @click="navigateToFlowManager"
      >
        <el-icon :size="20"><List /></el-icon>
        <span>Process Templates</span>
      </div>
    </nav>

    <!-- New Chat Button -->
    <div class="sidebar-actions">
      <button class="btn btn-primary btn-new-chat" @click="createNewChat">
        <el-icon :size="18"><Plus /></el-icon>
        <span>New Chat</span>
      </button>
    </div>

    <!-- Session List -->
    <div class="sidebar-section">
      <div class="section-title">Recent Conversations</div>
      <div class="session-list">
        <div
          v-for="session in filteredSessions.slice(0, 10)"
          :key="session.id"
          class="session-item"
          :class="{ active: session.id === chatStore.currentSessionId }"
          @click="selectSession(session.id)"
        >
          <el-icon :size="16" class="session-icon"><ChatDotRound /></el-icon>
          
          <template v-if="editingSessionId === session.id">
            <el-input
              v-model="editingTitle"
              size="small"
              @keyup.enter="finishRename"
              @keyup.escape="cancelRename"
              @blur="finishRename"
              @click.stop
              class="session-title-input"
            />
          </template>
          <template v-else>
            <div class="session-info">
              <span class="session-name">{{ session.title }}</span>
              <span class="session-time">{{ formatTime(session.updatedAt) }}</span>
            </div>
            
            <div class="session-actions" @click.stop>
              <el-dropdown trigger="click" :hide-on-click="false">
                <button class="btn btn-ghost btn-icon btn-more">
                  <el-icon :size="16"><More /></el-icon>
                </button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="startRename(session, $event)">
                      <el-icon><Edit /></el-icon> Rename
                    </el-dropdown-item>
                    <el-dropdown-item divided @click="deleteSession(session, $event)">
                      <el-icon><Delete /></el-icon> Delete
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- User Info & Logout -->
    <div class="sidebar-user">
      <div class="user-info">
        <span class="user-name">{{ authStore.displayName }}</span>
        <el-tag size="small" :type="authStore.isHR ? 'warning' : 'info'" effect="plain">
          {{ authStore.isHR ? 'HR' : '员工' }}
        </el-tag>
      </div>
      <button class="btn btn-ghost btn-icon" @click="handleLogout" title="退出登录">
        <el-icon :size="18"><SwitchButton /></el-icon>
      </button>
    </div>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: var(--sidebar-width);
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border-light);
  display: flex;
  flex-direction: column;
  padding: var(--space-4);
  overflow: hidden;
}

.sidebar-search {
  margin-bottom: var(--space-4);
}

.search-input :deep(.el-input__wrapper) {
  background-color: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  box-shadow: none;
}

.search-input :deep(.el-input__wrapper:hover) {
  border-color: var(--border-default);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px var(--bg-active);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  margin-bottom: var(--space-4);
}

.sidebar-actions {
  margin-bottom: var(--space-4);
}

.btn-new-chat {
  width: 100%;
  justify-content: center;
}

.sidebar-section {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.section-title {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: var(--space-2) var(--space-3);
  margin-bottom: var(--space-2);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.session-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 10px var(--space-3);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
  position: relative;
}

.session-item:hover {
  background-color: var(--bg-hover);
}

.session-item.active {
  background-color: var(--bg-active);
}

.session-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 20px;
  background-color: var(--primary-color);
  border-radius: 0 2px 2px 0;
}

.session-icon {
  color: var(--text-tertiary);
  flex-shrink: 0;
}

.session-item.active .session-icon {
  color: var(--primary-color);
}

.session-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.session-name {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.session-actions {
  opacity: 0;
  transition: opacity var(--duration-fast) var(--ease-default);
}

.session-item:hover .session-actions {
  opacity: 1;
}

.btn-more {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background-color: transparent;
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-default);
}

.btn-more:hover {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
  transform: scale(1.05);
}

.btn-more:active {
  transform: scale(0.95);
}

.session-title-input {
  flex: 1;
}

.session-title-input :deep(.el-input__wrapper) {
  padding: 2px 8px;
}

.sidebar-user {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3);
  border-top: 1px solid var(--border-light);
  margin-top: var(--space-2);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.user-name {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
