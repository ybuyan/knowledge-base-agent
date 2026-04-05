<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { flowGuideApi } from '@/api'
import type { FlowGuide } from '@/api'

const props = defineProps<{
  flowId: string
  visible: boolean
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
}>()

const guide = ref<FlowGuide | null>(null)
const loading = ref(false)

// ─── Category Color Theme ──────────────────────────────────────────────────────
interface CategoryTheme {
  primary: string
  light: string
  bg: string
  border: string
  icon: string
}

const categoryThemes: Record<string, CategoryTheme> = {
  '人事行政': { primary: '#e0301e', light: '#ff4d3a', bg: '#fef5f5', border: '#fdd8d4', icon: '👥' },
  '财务报销': { primary: '#1677ff', light: '#409eff', bg: '#eff6ff', border: '#d6eaff', icon: '💰' },
  'IT技术': { primary: '#722ed1', light: '#9254de', bg: '#f9f0ff', border: '#efdbff', icon: '💻' },
  '行政管理': { primary: '#fa8c16', light: '#faad14', bg: '#fff7e6', border: '#ffe7ba', icon: '📋' },
  '采购管理': { primary: '#52c41a', light: '#73d13d', bg: '#f6ffed', border: '#d9f7be', icon: '🛒' },
  '客户服务': { primary: '#eb2f96', light: '#eb40a0', bg: '#fff0f6', border: '#ffadd2', icon: '🎧' }
}

const getCategoryTheme = (category: string): CategoryTheme => {
  return categoryThemes[category] || { 
    primary: '#666666', light: '#888888', bg: '#fafafa', border: '#eeeeee', icon: '📄' 
  }
}

const categoryTheme = computed(() => {
  return guide.value ? getCategoryTheme(guide.value.category) : getCategoryTheme('')
})

const loadGuide = async () => {
  if (!props.flowId) return
  loading.value = true
  try {
    guide.value = await flowGuideApi.getById(props.flowId)
  } catch (e) {
    console.error('加载流程指引失败:', e)
  } finally {
    loading.value = false
  }
}

watch(() => [props.flowId, props.visible], ([id, visible]) => {
  if (visible && id) loadGuide()
}, { immediate: true })
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    width="600px"
    :show-close="true"
    destroy-on-close
    append-to-body
  >
    <template #header>
      <div v-if="guide" class="modal-header" :style="{ '--cat-primary': categoryTheme.primary, '--cat-light': categoryTheme.light, '--cat-bg': categoryTheme.bg, '--cat-border': categoryTheme.border }">
        <div class="guide-title">
          <span class="title-text">{{ guide.name }}</span>
          <el-tag 
            size="small" 
            effect="plain" 
            class="category-tag"
            :style="{ color: categoryTheme.primary, borderColor: categoryTheme.border, background: categoryTheme.bg }"
          >
            <span class="tag-icon">{{ categoryTheme.icon }}</span>
            {{ guide.category }}
          </el-tag>
        </div>
        <div v-if="guide.source_document_name" class="source-doc">
          来源：{{ guide.source_document_name }}
        </div>
      </div>
    </template>

    <div v-loading="loading" class="modal-body">
      <template v-if="guide">
        <div
          v-for="step in guide.steps"
          :key="step.sequence"
          class="step-card"
        >
          <div class="step-header">
            <div class="step-number">{{ step.sequence }}</div>
            <div class="step-info">
              <div class="step-title">{{ step.title }}</div>
              <div v-if="step.description" class="step-desc">{{ step.description }}</div>
            </div>
          </div>
          <a
            v-if="step.entry_link?.label && step.entry_link?.url"
            :href="step.entry_link.url"
            :target="step.entry_link.open_in_new_tab ? '_blank' : '_self'"
            class="entry-link-btn"
          >
            <span class="link-icon">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
              </svg>
            </span>
            {{ step.entry_link.label }}
          </a>
        </div>
      </template>
    </div>
  </el-dialog>
</template>

<style scoped>
.modal-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-left: 12px;
  border-left: 3px solid var(--cat-primary, #e0301e);
}

.guide-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.category-tag {
  flex-shrink: 0;
}

.source-doc {
  font-size: 12px;
  color: #6b7280;
}

.modal-body {
  min-height: 80px;
}

.step-card {
  background: var(--cat-bg, #fafafa);
  border: 1px solid var(--cat-border, #E5E7EB);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  transition: all 0.2s;
}

.step-card:hover {
  border-color: var(--cat-primary, #e0301e);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.step-card:last-child {
  margin-bottom: 0;
}

.step-header {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.step-number {
  width: 28px;
  height: 28px;
  background: var(--cat-primary, #e0301e);
  color: white;
  border-radius: 50%;
  font-weight: 600;
  font-size: 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.step-info {
  flex: 1;
}

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.step-desc {
  font-size: 13px;
  color: #4b5563;
  margin-top: 4px;
  line-height: 1.5;
}

.entry-link-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: var(--cat-bg, #fff);
  border: 1px solid var(--cat-border, #E5E7EB);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--cat-primary, #e0301e);
  text-decoration: none;
  margin-top: 10px;
  transition: all 0.15s;
}

.entry-link-btn:hover {
  background: var(--cat-primary, #e0301e);
  color: white;
  border-color: var(--cat-primary, #e0301e);
}

.link-icon {
  display: flex;
  align-items: center;
}
</style>
