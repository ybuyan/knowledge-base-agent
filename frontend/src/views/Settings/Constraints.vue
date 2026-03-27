<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  RefreshRight, 
  Setting, 
  Document, 
  ChatDotRound,
  Warning,
  InfoFilled
} from '@element-plus/icons-vue'

interface ConstraintConfig {
  retrieval: {
    enabled: boolean
    min_similarity_score: number
    min_relevant_docs: number
    max_relevant_docs: number
    content_coverage_threshold: number
  }
  generation: {
    strict_mode: boolean
    allow_general_knowledge: boolean
    require_citations: boolean
    max_answer_length: number
    forbidden_topics: string[]
    forbidden_keywords: string[]
  }
  validation: {
    enabled: boolean
    check_source_attribution: boolean
    min_confidence_score: number
    hallucination_detection: boolean
  }
  fallback: {
    no_result_message: string
    suggest_similar: boolean
    suggest_contact: boolean
    contact_info: string
  }
}

interface ConstraintStats {
  total_queries: number
  passed_queries: number
  failed_queries: number
  pass_rate: number
  avg_similarity_score: number
}

const loading = ref(false)
const saving = ref(false)
const config = ref<ConstraintConfig | null>(null)
const stats = ref<ConstraintStats | null>(null)
const newForbiddenTopic = ref('')
const newForbiddenKeyword = ref('')

const activeTab = ref('retrieval')

const passRateColor = computed(() => {
  if (!stats.value) return '#999'
  const rate = stats.value.pass_rate
  if (rate >= 0.8) return '#52c41a'
  if (rate >= 0.6) return '#faad14'
  return '#f5222d'
})

const fetchConfig = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/constraints')
    const data = await response.json()
    config.value = data.constraints
  } catch (error) {
    ElMessage.error('加载约束配置失败')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const response = await fetch('/api/constraints/stats')
    const data = await response.json()
    stats.value = data
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
}

const saveConfig = async () => {
  saving.value = true
  try {
    const response = await fetch('/api/constraints', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config.value)
    })
    const data = await response.json()
    if (data.message) {
      ElMessage.success('约束配置保存成功')
    }
  } catch (error) {
    ElMessage.error('保存约束配置失败')
  } finally {
    saving.value = false
  }
}

const resetConfig = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要将所有约束配置重置为默认值吗？',
      '重置确认',
      {
        confirmButtonText: '重置',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await fetch('/api/constraints/reset', {
      method: 'POST'
    })
    const data = await response.json()
    config.value = data.constraints
    ElMessage.success('约束配置已重置为默认值')
  } catch {}
}

const addForbiddenTopic = () => {
  if (newForbiddenTopic.value.trim()) {
    config.value?.generation.forbidden_topics.push(newForbiddenTopic.value.trim())
    newForbiddenTopic.value = ''
  }
}

const removeForbiddenTopic = (index: number) => {
  config.value?.generation.forbidden_topics.splice(index, 1)
}

const addForbiddenKeyword = () => {
  if (newForbiddenKeyword.value.trim()) {
    config.value?.generation.forbidden_keywords.push(newForbiddenKeyword.value.trim())
    newForbiddenKeyword.value = ''
  }
}

const removeForbiddenKeyword = (index: number) => {
  config.value?.generation.forbidden_keywords.splice(index, 1)
}

onMounted(() => {
  fetchConfig()
  fetchStats()
})
</script>

<template>
  <div class="constraints-page">
    <!-- Header -->
    <div class="page-header">
      <div class="header-title">
        <h1>约束设置</h1>
        <p class="header-subtitle">配置知识库约束和验证规则</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-secondary" @click="resetConfig">
          <el-icon :size="16"><RefreshRight /></el-icon>
          恢复默认
        </button>
        <button class="btn btn-primary" @click="saveConfig" :disabled="saving">
          <el-icon :size="16"><Setting /></el-icon>
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </div>

    <!-- Stats Overview -->
    <div v-if="stats" class="stats-overview">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total_queries }}</div>
        <div class="stat-label">总查询数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value success">{{ stats.passed_queries }}</div>
        <div class="stat-label">通过</div>
      </div>
      <div class="stat-card">
        <div class="stat-value danger">{{ stats.failed_queries }}</div>
        <div class="stat-label">拒绝</div>
      </div>
      <div class="stat-card">
        <div class="stat-value" :style="{ color: passRateColor }">
          {{ (stats.pass_rate * 100).toFixed(1) }}%
        </div>
        <div class="stat-label">通过率</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.avg_similarity_score.toFixed(2) }}</div>
        <div class="stat-label">平均相似度</div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs-container">
      <div class="tabs">
        <button 
          class="tab" 
          :class="{ active: activeTab === 'retrieval' }"
          @click="activeTab = 'retrieval'"
        >
          <el-icon :size="16"><Document /></el-icon>
          检索约束
        </button>
        <button 
          class="tab" 
          :class="{ active: activeTab === 'generation' }"
          @click="activeTab = 'generation'"
        >
          <el-icon :size="16"><ChatDotRound /></el-icon>
          生成约束
        </button>
        <button 
          class="tab" 
          :class="{ active: activeTab === 'validation' }"
          @click="activeTab = 'validation'"
        >
          <el-icon :size="16"><Warning /></el-icon>
          验证约束
        </button>
        <button 
          class="tab" 
          :class="{ active: activeTab === 'fallback' }"
          @click="activeTab = 'fallback'"
        >
          <el-icon :size="16"><InfoFilled /></el-icon>
          兜底策略
        </button>
      </div>
    </div>

    <!-- Content -->
    <div v-if="config" class="tab-content">
      <!-- Retrieval Tab -->
      <div v-show="activeTab === 'retrieval'" class="config-section">
        <div class="section-title">检索约束</div>
        <p class="section-desc">控制如何从知识库中检索文档。</p>
        
        <div class="form-group">
          <label>启用检索约束</label>
          <el-switch v-model="config.retrieval.enabled" />
        </div>
        
        <div class="form-group">
          <label>最小相似度分数</label>
          <el-slider 
            v-model="config.retrieval.min_similarity_score" 
            :min="0" 
            :max="1" 
            :step="0.05"
            show-input
          />
          <span class="hint">相似度低于此阈值的文档将被忽略</span>
        </div>
        
        <div class="form-group">
          <label>最少相关文档数</label>
          <el-input-number 
            v-model="config.retrieval.min_relevant_docs" 
            :min="1" 
            :max="10"
          />
          <span class="hint">回答问题所需的最少相关文档数量</span>
        </div>
        
        <div class="form-group">
          <label>最多相关文档数</label>
          <el-input-number 
            v-model="config.retrieval.max_relevant_docs" 
            :min="1" 
            :max="20"
          />
          <span class="hint">包含在上下文中的最大文档数量</span>
        </div>
        
        <div class="form-group">
          <label>内容覆盖率阈值</label>
          <el-slider 
            v-model="config.retrieval.content_coverage_threshold" 
            :min="0" 
            :max="1" 
            :step="0.05"
            show-input
          />
          <span class="hint">检索文档中最小关键词覆盖率</span>
        </div>
      </div>

      <!-- Generation Tab -->
      <div v-show="activeTab === 'generation'" class="config-section">
        <div class="section-title">生成约束</div>
        <p class="section-desc">控制AI如何生成回答。</p>
        
        <div class="form-group">
          <label>严格模式</label>
          <el-switch v-model="config.generation.strict_mode" />
          <span class="hint">只使用知识库内容回答问题</span>
        </div>
        
        <div class="form-group">
          <label>允许通用知识</label>
          <el-switch v-model="config.generation.allow_general_knowledge" />
          <span class="hint">当知识库没有答案时允许AI使用通用知识</span>
        </div>
        
        <div class="form-group">
          <label>要求引用来源</label>
          <el-switch v-model="config.generation.require_citations" />
          <span class="hint">回答中必须标注来源引用</span>
        </div>
        
        <div class="form-group">
          <label>最大回答长度</label>
          <el-input-number 
            v-model="config.generation.max_answer_length" 
            :min="100" 
            :max="2000"
            :step="100"
          />
          <span class="hint">生成回答的最大字符数</span>
        </div>
        
        <div class="form-group">
          <label>禁止主题</label>
          <div class="tag-list">
            <el-tag 
              v-for="(topic, index) in config.generation.forbidden_topics" 
              :key="index"
              closable
              @close="removeForbiddenTopic(index)"
            >
              {{ topic }}
            </el-tag>
          </div>
          <div class="input-row">
            <el-input 
              v-model="newForbiddenTopic" 
              placeholder="添加禁止主题"
              @keyup.enter="addForbiddenTopic"
            />
            <button class="btn btn-secondary" @click="addForbiddenTopic">添加</button>
          </div>
        </div>
        
        <div class="form-group">
          <label>禁止关键词</label>
          <div class="tag-list">
            <el-tag 
              v-for="(keyword, index) in config.generation.forbidden_keywords" 
              :key="index"
              type="warning"
              closable
              @close="removeForbiddenKeyword(index)"
            >
              {{ keyword }}
            </el-tag>
          </div>
          <div class="input-row">
            <el-input 
              v-model="newForbiddenKeyword" 
              placeholder="添加禁止关键词"
              @keyup.enter="addForbiddenKeyword"
            />
            <button class="btn btn-secondary" @click="addForbiddenKeyword">添加</button>
          </div>
        </div>
      </div>

      <!-- Validation Tab -->
      <div v-show="activeTab === 'validation'" class="config-section">
        <div class="section-title">验证约束</div>
        <p class="section-desc">在返回回答前验证生成内容。</p>
        
        <div class="form-group">
          <label>启用验证</label>
          <el-switch v-model="config.validation.enabled" />
        </div>
        
        <div class="form-group">
          <label>检查来源归属</label>
          <el-switch v-model="config.validation.check_source_attribution" />
          <span class="hint">验证回答是否有来源引用</span>
        </div>
        
        <div class="form-group">
          <label>最小置信度分数</label>
          <el-slider 
            v-model="config.validation.min_confidence_score" 
            :min="0" 
            :max="1" 
            :step="0.1"
            show-input
          />
          <span class="hint">回答所需的最小置信度</span>
        </div>
        
        <div class="form-group">
          <label>幻觉检测</label>
          <el-switch v-model="config.validation.hallucination_detection" />
          <span class="hint">检测并标记可能的编造内容</span>
        </div>
      </div>

      <!-- Fallback Tab -->
      <div v-show="activeTab === 'fallback'" class="config-section">
        <div class="section-title">兜底策略</div>
        <p class="section-desc">配置未找到相关信息时的行为。</p>
        
        <div class="form-group">
          <label>无结果提示语</label>
          <el-input 
            v-model="config.fallback.no_result_message" 
            type="textarea"
            :rows="3"
          />
          <span class="hint">未找到相关文档时显示的消息</span>
        </div>
        
        <div class="form-group">
          <label>建议相关问题</label>
          <el-switch v-model="config.fallback.suggest_similar" />
          <span class="hint">未找到答案时显示相关问题建议</span>
        </div>
        
        <div class="form-group">
          <label>建议联系管理员</label>
          <el-switch v-model="config.fallback.suggest_contact" />
          <span class="hint">未找到答案时显示联系信息</span>
        </div>
        
        <div class="form-group">
          <label>联系信息</label>
          <el-input 
            v-model="config.fallback.contact_info" 
            type="textarea"
            :rows="2"
          />
          <span class="hint">未找到答案时显示的联系信息</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.constraints-page {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: var(--space-5);
  max-width: 900px;
  margin: 0 auto;
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
}

/* Stats Overview */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-3);
  margin-bottom: var(--space-5);
}

.stat-card {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  text-align: center;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}

.stat-value.success {
  color: var(--success-color);
}

.stat-value.danger {
  color: var(--error-color);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

/* Tabs */
.tabs-container {
  margin-bottom: var(--space-4);
}

.tabs {
  display: flex;
  gap: var(--space-2);
  border-bottom: 1px solid var(--border-light);
  padding-bottom: var(--space-2);
}

.tab {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all var(--duration-fast) var(--ease-default);
}

.tab:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.tab.active {
  background: var(--bg-active);
  color: var(--primary-color);
}

/* Content */
.tab-content {
  flex: 1;
  overflow-y: auto;
}

.config-section {
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
}

.section-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.section-desc {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-5);
}

/* Form */
.form-group {
  margin-bottom: var(--space-5);
}

.form-group label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.form-group .hint {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--space-1);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.input-row {
  display: flex;
  gap: var(--space-2);
}

.input-row .el-input {
  flex: 1;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: var(--space-4);
  }
  
  .stats-overview {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .tabs {
    flex-wrap: wrap;
  }
}
</style>
