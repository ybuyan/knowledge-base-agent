<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useRouter, useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { computed, onMounted, ref } from 'vue'
import { 
  ChatDotRound, 
  Plus, 
  User,
  FolderOpened,
  Delete,
  Edit,
  Fold,
  Expand,
  Search,
  FolderRemove,
  Clock,
  Document,
  Box
} from '@element-plus/icons-vue'
import { ElMessageBox, ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const chatStore = useChatStore()

const activeMenu = computed(() => route.path)
const editingSessionId = ref<string>('')
const editingTitle = ref('')
const sidebarCollapsed = ref(false)
const searchInput = ref('')
const searchDebounceTimer = ref<number | null>(null)

const groupedSessions = computed(() => chatStore.groupedSessions)

const handleMenuSelect = (index: string) => {
  router.push(index)
}

const handleNewSession = () => {
  chatStore.createSession()
}

const handleSelectSession = (sessionId: string) => {
  if (editingSessionId.value) return
  chatStore.selectSession(sessionId)
}

const handleDeleteSession = async (sessionId: string, event: Event) => {
  event.stopPropagation()
  
  try {
    await ElMessageBox.confirm(
      '确定要删除这个会话吗？删除后无法恢复。',
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await chatStore.deleteSession(sessionId)
    ElMessage.success('会话已删除')
  } catch {}
}

const handleArchiveSession = async (sessionId: string, event: Event) => {
  event.stopPropagation()
  
  const session = chatStore.sessions.find(s => s.id === sessionId)
  const isArchived = session?.isArchived
  
  try {
    await chatStore.archiveSession(sessionId, !isArchived)
    ElMessage.success(isArchived ? '会话已取消归档' : '会话已归档')
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const startRename = (sessionId: string, currentTitle: string, event: Event) => {
  event.stopPropagation()
  editingSessionId.value = sessionId
  editingTitle.value = currentTitle
}

const finishRename = () => {
  if (editingTitle.value.trim()) {
    chatStore.renameSession(editingSessionId.value, editingTitle.value.trim())
  }
  editingSessionId.value = ''
  editingTitle.value = ''
}

const cancelRename = () => {
  editingSessionId.value = ''
  editingTitle.value = ''
}

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const handleSearchInput = () => {
  if (searchDebounceTimer.value) {
    clearTimeout(searchDebounceTimer.value)
  }
  
  searchDebounceTimer.value = window.setTimeout(() => {
    chatStore.searchSessions(searchInput.value)
  }, 300)
}

const clearSearch = () => {
  searchInput.value = ''
  chatStore.clearSearch()
}

const handleToggleArchived = () => {
  chatStore.toggleShowArchived()
}

const formatTime = (date: Date) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return d.toLocaleDateString()
}

const statsDisplay = computed(() => {
  const stats = chatStore.sessionStats
  return [
    { label: '总会话', value: stats.totalSessions, icon: Document },
    { label: '今日', value: stats.todaySessions, icon: Clock },
    { label: '归档', value: stats.archivedSessions, icon: Box }
  ]
})

onMounted(async () => {
  await chatStore.initialize()
  if (!chatStore.sessions.length) {
    await chatStore.createSession()
  }
})
</script>

<template>
  <div class="chat-layout">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div v-if="!sidebarCollapsed" class="user-card">
          <el-avatar :size="40" :icon="User" />
          <div class="user-info">
            <div class="user-name">员工</div>
            <div class="user-role">普通用户</div>
          </div>
        </div>
        <el-button 
          class="toggle-btn"
          :icon="sidebarCollapsed ? Expand : Fold"
          @click="toggleSidebar"
          text
        />
      </div>

      <el-button 
        v-if="!sidebarCollapsed"
        type="primary" 
        class="new-session-btn"
        @click="handleNewSession"
      >
        <el-icon><Plus /></el-icon>
        新建对话
      </el-button>

      <div v-if="!sidebarCollapsed" class="search-box">
        <el-input
          v-model="searchInput"
          placeholder="搜索会话..."
          :prefix-icon="Search"
          clearable
          @input="handleSearchInput"
          @clear="clearSearch"
        />
      </div>

      <div v-if="!sidebarCollapsed" class="stats-bar">
        <div 
          v-for="stat in statsDisplay" 
          :key="stat.label" 
          class="stat-item"
        >
          <el-icon :size="14"><component :is="stat.icon" /></el-icon>
          <span class="stat-value">{{ stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </div>

      <div v-if="!sidebarCollapsed" class="archive-toggle" @click.stop="handleToggleArchived">
        <div class="toggle-switch" :class="{ active: chatStore.showArchived }">
          <span class="toggle-label">显示归档会话</span>
          <span class="toggle-indicator">{{ chatStore.showArchived ? '开' : '关' }}</span>
        </div>
      </div>

      <div v-if="!sidebarCollapsed" class="session-list scrollbar-thin">
        <template v-if="groupedSessions.length > 0">
          <div 
            v-for="group in groupedSessions" 
            :key="group.label" 
            class="session-group"
          >
            <div class="group-title">{{ group.label }}</div>
            <div 
              v-for="session in group.sessions" 
              :key="session.id"
              class="session-item"
              :class="{ 
                active: session.id === chatStore.currentSessionId,
                archived: session.isArchived 
              }"
              @click="handleSelectSession(session.id)"
            >
              <el-icon class="session-icon"><ChatDotRound /></el-icon>
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
                <div class="session-content">
                  <span class="session-name">{{ session.title }}</span>
                </div>
                <div class="session-right">
                  <span class="session-time">{{ formatTime(session.updatedAt) }}</span>
                  <div class="session-actions">
                    <div
                      class="action-btn archive-btn"
                      :class="{ active: session.isArchived }"
                      :title="session.isArchived ? '取消归档' : '归档'"
                      @click.stop="handleArchiveSession(session.id, $event)"
                    >
                      <el-icon :size="14">
                        <FolderRemove v-if="session.isArchived" />
                        <Box v-else />
                      </el-icon>
                    </div>
                    <div
                      class="action-btn edit-btn"
                      title="重命名"
                      @click.stop="startRename(session.id, session.title, $event)"
                    >
                      <el-icon :size="14"><Edit /></el-icon>
                    </div>
                    <div
                      class="action-btn delete-btn"
                      title="删除"
                      @click.stop="handleDeleteSession(session.id, $event)"
                    >
                      <el-icon :size="14"><Delete /></el-icon>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </template>
        <div v-else class="no-sessions">
          <el-empty description="暂无会话" :image-size="60" />
        </div>
      </div>

      <el-menu
        v-if="!sidebarCollapsed"
        :default-active="activeMenu"
        class="nav-menu"
        @select="handleMenuSelect"
      >
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>智能问答</span>
        </el-menu-item>
        <el-menu-item index="/documents">
          <el-icon><FolderOpened /></el-icon>
          <span>文档管理</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <main class="main-content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.sidebar {
  width: 280px;
  background: var(--bg-white);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  padding: 16px;
  transition: width 0.3s ease;
}

.sidebar.collapsed {
  width: 60px;
  padding: 8px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.toggle-btn {
  flex-shrink: 0;
}

.user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-gray);
  border-radius: var(--radius-md);
  flex: 1;
}

.user-info {
  flex: 1;
  overflow: hidden;
}

.user-name {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
}

.user-role {
  font-size: 12px;
  color: var(--text-tertiary);
}

.new-session-btn {
  width: 100%;
  margin-bottom: 12px;
}

.search-box {
  margin-bottom: 12px;
}

.stats-bar {
  display: flex;
  justify-content: space-around;
  padding: 8px 0;
  margin-bottom: 12px;
  background: var(--bg-gray);
  border-radius: var(--radius-sm);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.stat-label {
  font-size: 11px;
  color: var(--text-tertiary);
}

.archive-toggle {
  margin-bottom: 12px;
  cursor: pointer;
}

.toggle-switch {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-gray);
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.toggle-switch:hover {
  background: var(--primary-bg-light);
}

.toggle-switch.active {
  background: var(--primary-bg-light);
}

.toggle-label {
  font-size: 13px;
  color: var(--text-primary);
}

.toggle-indicator {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-tertiary);
  padding: 2px 8px;
  background: var(--bg-white);
  border-radius: 4px;
}

.toggle-switch.active .toggle-indicator {
  color: var(--primary-color);
  background: var(--bg-white);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
}

.session-group {
  margin-bottom: 8px;
}

.group-title {
  font-size: 12px;
  color: var(--text-tertiary);
  padding: 8px 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 500;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.session-item:hover {
  background: var(--bg-gray);
}

.session-item.active {
  background: var(--primary-bg-light);
  color: var(--primary-color);
}

.session-item.archived {
  opacity: 0.7;
}

.session-icon {
  flex-shrink: 0;
}

.session-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow: hidden;
}

.session-name {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.session-time {
  font-size: 11px;
  color: var(--text-tertiary);
  white-space: nowrap;
  transition: opacity 0.2s;
}

.session-item:hover .session-time {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.session-actions {
  display: flex;
  flex-direction: row;
  gap: 6px;
  align-items: center;
  opacity: 0;
  width: 0;
  overflow: hidden;
  transform: translateX(10px);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.session-item:hover .session-actions {
  opacity: 1;
  width: auto;
  transform: translateX(0);
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  background: #f5f5f5;
  border: 1px solid transparent;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.action-btn:active {
  transform: translateY(0);
}

.archive-btn {
  color: #8c8c8c;
}

.archive-btn:hover {
  background: #e6f7ff;
  border-color: #91d5ff;
  color: #1890ff;
}

.archive-btn.active {
  background: #fff7e6;
  border-color: #ffd591;
  color: #fa8c16;
}

.archive-btn.active:hover {
  background: #fff1b8;
  border-color: #ffc53d;
}

.edit-btn {
  color: #8c8c8c;
}

.edit-btn:hover {
  background: #f0f5ff;
  border-color: #adc6ff;
  color: #2f54eb;
}

.delete-btn {
  color: #8c8c8c;
}

.delete-btn:hover {
  background: #fff1f0;
  border-color: #ffa39e;
  color: #f5222d;
}

.session-title-input {
  flex: 1;
}

.no-sessions {
  text-align: center;
  color: var(--text-tertiary);
  font-size: 14px;
  padding: 20px;
}

.nav-menu {
  border: none;
  background: transparent;
}

.nav-menu .el-menu-item {
  border-radius: var(--radius-sm);
  margin-bottom: 4px;
}

.nav-menu .el-menu-item:hover {
  background: var(--bg-gray);
}

.nav-menu .el-menu-item.is-active {
  background: var(--primary-bg-light);
  color: var(--primary-color);
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-gray);
}

@media (max-width: 768px) {
  .sidebar {
    position: absolute;
    z-index: 100;
    height: 100%;
    box-shadow: var(--shadow-md);
  }
  
  .sidebar.collapsed {
    width: 60px;
  }
  
  .sidebar:not(.collapsed) {
    width: 280px;
  }
}
</style>
