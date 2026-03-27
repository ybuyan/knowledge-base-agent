import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { chatApi } from '@/api'

function parseUTCDate(dateStr: string | Date): Date {
  if (dateStr instanceof Date) return dateStr
  if (dateStr.endsWith('Z')) return new Date(dateStr)
  return new Date(dateStr + 'Z')
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  suggestedQuestions?: string[]
  relatedLinks?: Link[]
  timestamp: Date | string
}

export interface Link {
  id: string
  title: string
  url: string
  description?: string
}

export interface Source {
  id: string
  filename: string
  page?: number
  paragraph?: string
  content: string
}

export interface Session {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  messageCount?: number
  lastMessage?: string
  isArchived?: boolean
}

export interface SessionStats {
  totalSessions: number
  archivedSessions: number
  todaySessions: number
  weekSessions: number
  totalMessages: number
}

export interface SessionGroup {
  label: string
  sessions: Session[]
}

export const useChatStore = defineStore('chat', () => {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref<string>('')
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const isInitialized = ref(false)
  const searchKeyword = ref('')
  const isSearching = ref(false)
  const showArchived = ref(false)
  const sessionStats = ref<SessionStats>({
    totalSessions: 0,
    archivedSessions: 0,
    todaySessions: 0,
    weekSessions: 0,
    totalMessages: 0
  })
  const hasMoreMessages = ref(false)
  const messageCursor = ref<string | undefined>()

  const currentSession = computed(() => 
    sessions.value.find(s => s.id === currentSessionId.value)
  )

  const sortedSessions = computed(() => 
    [...sessions.value].sort((a, b) => 
      new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
    )
  )

  const activeSessions = computed(() => 
    sortedSessions.value.filter(s => !s.isArchived)
  )

  const archivedSessions = computed(() => 
    sortedSessions.value.filter(s => s.isArchived)
  )

  const groupedSessions = computed((): SessionGroup[] => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
    const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)

    const groups: { [key: string]: Session[] } = {
      '今天': [],
      '昨天': [],
      '本周': [],
      '更早': []
    }

    const sessionsToGroup = showArchived.value ? sortedSessions.value : activeSessions.value

    sessionsToGroup.forEach(session => {
      const sessionDate = new Date(session.updatedAt)
      if (sessionDate >= today) {
        groups['今天'].push(session)
      } else if (sessionDate >= yesterday) {
        groups['昨天'].push(session)
      } else if (sessionDate >= weekAgo) {
        groups['本周'].push(session)
      } else {
        groups['更早'].push(session)
      }
    })

    return Object.entries(groups)
      .filter(([, sessions]) => sessions.length > 0)
      .map(([label, sessions]) => ({ label, sessions }))
  })

  async function initialize() {
    if (isInitialized.value) {
      console.log('[ChatStore] Already initialized, skipping')
      return
    }
    
    isLoading.value = true
    try {
      console.log('[ChatStore] Initializing...')
      const [sessionsData, statsData] = await Promise.all([
        chatApi.getSessions(showArchived.value),
        chatApi.getSessionStats()
      ])
      
      console.log('[ChatStore] Loaded sessions:', sessionsData.length)
      
      sessions.value = sessionsData.map(s => ({
        ...s,
        createdAt: parseUTCDate(s.createdAt),
        updatedAt: parseUTCDate(s.updatedAt)
      }))
      
      sessionStats.value = {
        totalSessions: statsData.total_sessions,
        archivedSessions: statsData.archived_sessions,
        todaySessions: statsData.today_sessions,
        weekSessions: statsData.week_sessions,
        totalMessages: statsData.total_messages
      }
      
      if (sessions.value.length > 0) {
        const firstActive = sessions.value.find(s => !s.isArchived)
        console.log('[ChatStore] First active session:', firstActive?.id, firstActive?.title)
        if (firstActive) {
          await selectSession(firstActive.id)
        }
      }
      isInitialized.value = true
      console.log('[ChatStore] Initialization complete')
    } catch (error) {
      console.error('[ChatStore] 初始化会话列表失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function reloadSessions() {
    isLoading.value = true
    try {
      const sessionsData = await chatApi.getSessions(showArchived.value)
      sessions.value = sessionsData.map(s => ({
        ...s,
        createdAt: parseUTCDate(s.createdAt),
        updatedAt: parseUTCDate(s.updatedAt)
      }))
    } catch (error) {
      console.error('重新加载会话列表失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  async function createSession(): Promise<string> {
    try {
      // 检查是否已存在空的"新对话"
      const emptyNewChat = sessions.value.find(s => 
        s.title === '新对话' && 
        (s.messageCount === 0 || s.messageCount === undefined) &&
        !s.isArchived
      )
      
      if (emptyNewChat) {
        // 如果已存在空的"新对话"，直接切换到该会话
        console.log('[ChatStore] Found existing empty "新对话", switching to it:', emptyNewChat.id)
        currentSessionId.value = emptyNewChat.id
        await loadMessages(emptyNewChat.id)
        return emptyNewChat.id
      }
      
      // 否则创建新会话
      const session = await chatApi.createSession('新对话')
      sessions.value.unshift({
        id: session.id,
        title: session.title,
        createdAt: new Date(session.createdAt),
        updatedAt: new Date(session.updatedAt),
        messageCount: 0
      })
      currentSessionId.value = session.id
      messages.value = []
      hasMoreMessages.value = false
      messageCursor.value = undefined
      
      sessionStats.value.totalSessions++
      sessionStats.value.todaySessions++
      
      return session.id
    } catch (error) {
      console.error('创建会话失败:', error)
      throw error
    }
  }

  async function selectSession(sessionId: string) {
    currentSessionId.value = sessionId
    await loadMessages(sessionId)
  }

  async function loadMessages(sessionId: string) {
    console.log('[ChatStore] Loading messages for session:', sessionId)
    isLoading.value = true
    try {
      const response = await chatApi.getMessages(sessionId)
      console.log('[ChatStore] Loaded messages:', response.messages.length, 'messages')
      messages.value = response.messages.map(m => ({
        ...m,
        timestamp: new Date(m.timestamp)
      }))
      hasMoreMessages.value = response.has_more || false
      messageCursor.value = response.next_cursor
    } catch (error) {
      console.error('[ChatStore] 加载消息失败:', error)
      messages.value = []
    } finally {
      isLoading.value = false
    }
  }

  async function loadMoreMessages() {
    if (!currentSessionId.value || !hasMoreMessages.value || !messageCursor.value) return
    
    isLoading.value = true
    try {
      const response = await chatApi.loadMoreMessages(
        currentSessionId.value, 
        messageCursor.value
      )
      
      const olderMessages = response.messages.map(m => ({
        ...m,
        timestamp: new Date(m.timestamp)
      }))
      
      messages.value = [...olderMessages, ...messages.value]
      hasMoreMessages.value = response.has_more || false
      messageCursor.value = response.next_cursor
    } catch (error) {
      console.error('加载更多消息失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  function addMessage(message: Omit<Message, 'id' | 'timestamp'>) {
    const newMessage: Message = {
      ...message,
      id: `msg_${Date.now()}`,
      timestamp: new Date(),
      sources: message.role === 'assistant' ? [] : undefined,
      suggestedQuestions: message.role === 'assistant' ? [] : undefined
    }
    messages.value.push(newMessage)
    
    // 更新会话信息
    const session = sessions.value.find(s => s.id === currentSessionId.value)
    if (session) {
      // 如果是第一条用户消息，更新标题
      if (messages.value.length === 1 && message.role === 'user') {
        const newTitle = message.content.slice(0, 30) + (message.content.length > 30 ? '...' : '')
        session.title = newTitle
        session.updatedAt = new Date()
        chatApi.updateSession(currentSessionId.value, newTitle).catch(console.error)
      }
      
      // 更新消息计数
      if (message.role === 'user') {
        session.messageCount = (session.messageCount || 0) + 1
      }
      session.updatedAt = new Date()
    }
  }

  function updateLastAssistantContent(content: string) {
    const lastAssistant = [...messages.value].reverse().find(m => m.role === 'assistant')
    if (lastAssistant) {
      lastAssistant.content = content
    }
  }

  function updateLastAssistantSources(sources: Source[]) {
    const lastAssistant = [...messages.value].reverse().find(m => m.role === 'assistant')
    if (lastAssistant) {
      lastAssistant.sources = sources
    }
  }
  
  function updateLastAssistantSuggestedQuestions(questions: string[]) {
    const lastAssistant = [...messages.value].reverse().find(m => m.role === 'assistant')
    if (lastAssistant) {
      lastAssistant.suggestedQuestions = questions
    }
  }
  
  function updateLastAssistantRelatedLinks(links: Link[]) {
    const lastAssistant = [...messages.value].reverse().find(m => m.role === 'assistant')
    if (lastAssistant) {
      lastAssistant.relatedLinks = links
    }
  }
  
  function setLoading(loading: boolean) {
    isLoading.value = loading
  }

  function clearMessages() {
    messages.value = []
    hasMoreMessages.value = false
    messageCursor.value = undefined
  }

  async function deleteSession(sessionId: string) {
    try {
      await chatApi.deleteSession(sessionId)
      const index = sessions.value.findIndex(s => s.id === sessionId)
      if (index !== -1) {
        const wasArchived = sessions.value[index].isArchived
        sessions.value.splice(index, 1)
        
        sessionStats.value.totalSessions--
        if (wasArchived) {
          sessionStats.value.archivedSessions--
        }
      }
      
      if (sessionId === currentSessionId.value) {
        if (sessions.value.length > 0) {
          const firstActive = sessions.value.find(s => !s.isArchived)
          if (firstActive) {
            await selectSession(firstActive.id)
          } else {
            currentSessionId.value = ''
            messages.value = []
          }
        } else {
          currentSessionId.value = ''
          messages.value = []
        }
      }
    } catch (error) {
      console.error('删除会话失败:', error)
      throw error
    }
  }

  async function renameSession(sessionId: string, newTitle: string) {
    try {
      await chatApi.updateSession(sessionId, newTitle)
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        session.title = newTitle
        session.updatedAt = new Date()
      }
    } catch (error) {
      console.error('重命名会话失败:', error)
      throw error
    }
  }

  async function archiveSession(sessionId: string, isArchived: boolean = true) {
    try {
      await chatApi.archiveSession(sessionId, isArchived)
      const session = sessions.value.find(s => s.id === sessionId)
      if (session) {
        session.isArchived = isArchived
        session.updatedAt = new Date()
        
        if (isArchived) {
          sessionStats.value.archivedSessions++
        } else {
          sessionStats.value.archivedSessions--
        }
      }
      
      if (sessionId === currentSessionId.value && isArchived) {
        const firstActive = sessions.value.find(s => !s.isArchived)
        if (firstActive) {
          await selectSession(firstActive.id)
        } else {
          currentSessionId.value = ''
          messages.value = []
        }
      }
    } catch (error) {
      console.error('归档会话失败:', error)
      throw error
    }
  }

  async function searchSessions(keyword: string) {
    if (!keyword.trim()) {
      searchKeyword.value = ''
      isSearching.value = false
      await initialize()
      return
    }
    
    searchKeyword.value = keyword
    isSearching.value = true
    isLoading.value = true
    
    try {
      const results = await chatApi.searchSessions(keyword, showArchived.value)
      sessions.value = results.map(s => ({
        ...s,
        createdAt: parseUTCDate(s.createdAt),
        updatedAt: parseUTCDate(s.updatedAt)
      }))
    } catch (error) {
      console.error('搜索会话失败:', error)
    } finally {
      isLoading.value = false
    }
  }

  function clearSearch() {
    searchKeyword.value = ''
    isSearching.value = false
    initialize()
  }

  function toggleShowArchived() {
    showArchived.value = !showArchived.value
    reloadSessions()
  }

  function updateSessionActivity() {
    const session = sessions.value.find(s => s.id === currentSessionId.value)
    if (session) {
      session.updatedAt = new Date()
      const idx = sessions.value.findIndex(s => s.id === currentSessionId.value)
      if (idx > 0) {
        const [s] = sessions.value.splice(idx, 1)
        sessions.value.unshift(s)
      }
    }
  }

  async function refreshStats() {
    try {
      const stats = await chatApi.getSessionStats()
      sessionStats.value = {
        totalSessions: stats.total_sessions,
        archivedSessions: stats.archived_sessions,
        todaySessions: stats.today_sessions,
        weekSessions: stats.week_sessions,
        totalMessages: stats.total_messages
      }
    } catch (error) {
      console.error('刷新统计失败:', error)
    }
  }

  return {
    sessions,
    currentSessionId,
    messages,
    isLoading,
    isInitialized,
    currentSession,
    sortedSessions,
    activeSessions,
    archivedSessions,
    groupedSessions,
    searchKeyword,
    isSearching,
    showArchived,
    sessionStats,
    hasMoreMessages,
    messageCursor,
    initialize,
    reloadSessions,
    createSession,
    selectSession,
    loadMessages,
    loadMoreMessages,
    addMessage,
    updateLastAssistantContent,
    updateLastAssistantSources,
    updateLastAssistantSuggestedQuestions,
    updateLastAssistantRelatedLinks,
    setLoading,
    clearMessages,
    deleteSession,
    renameSession,
    archiveSession,
    searchSessions,
    clearSearch,
    toggleShowArchived,
    updateSessionActivity,
    refreshStats
  }
})
