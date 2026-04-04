<script setup lang="ts">
import { ref, watch } from 'vue'
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
      <div v-if="guide" class="modal-header">
        <div class="guide-title">
          <span class="title-text">{{ guide.name }}</span>
          <el-tag size="small" type="info" effect="plain" class="category-tag">{{ guide.category }}</el-tag>
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
  border-left: 3px solid #e0301e;
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
  background: #fafafa;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
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
  background: #e0301e;
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
  background: #fff;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  color: #e0301e;
  text-decoration: none;
  margin-top: 10px;
  transition: all 0.15s;
}

.entry-link-btn:hover {
  background: #e0301e;
  color: white;
  border-color: #e0301e;
}

.link-icon {
  display: flex;
  align-items: center;
}
</style>
