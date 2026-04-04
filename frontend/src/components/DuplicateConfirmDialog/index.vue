<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { flowGuideApi } from '@/api'
import type { PendingDuplicate } from '@/api'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  visible: boolean
  duplicates: PendingDuplicate[]
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  'resolved': []
}>()

const currentIndex = ref(0)
const processing = ref(false)

const current = computed(() => props.duplicates[currentIndex.value])
const total = computed(() => props.duplicates.length)
const hasMore = computed(() => currentIndex.value < total.value - 1)

watch(() => props.visible, (v) => {
  if (v) currentIndex.value = 0
})

const handleAction = async (action: 'overwrite' | 'keep' | 'save_as_new') => {
  if (!current.value) return
  processing.value = true
  try {
    await flowGuideApi.resolveDuplicate(current.value.id, action)
    const labels = { overwrite: '已覆盖更新', keep: '已保留原有', save_as_new: '已另存为新流程' }
    ElMessage.success(labels[action])

    if (hasMore.value) {
      currentIndex.value++
    } else {
      emit('update:visible', false)
      emit('resolved')
    }
  } catch {
    ElMessage.error('操作失败，请重试')
  } finally {
    processing.value = false
  }
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="emit('update:visible', $event)"
    title="检测到重复流程"
    width="560px"
    :close-on-click-modal="false"
  >
    <template v-if="current">
      <div class="progress-hint" v-if="total > 1">
        正在处理第 {{ currentIndex + 1 }} / {{ total }} 条重复记录
      </div>

      <div class="compare-grid">
        <div class="compare-card existing">
          <div class="card-label">现有流程</div>
          <div class="card-name">{{ current.existing_guide_name }}</div>
          <div class="card-meta">已存在于系统中</div>
        </div>
        <div class="compare-arrow">→</div>
        <div class="compare-card new">
          <div class="card-label">新解析流程</div>
          <div class="card-name">{{ current.new_guide_data?.name }}</div>
          <div class="card-meta">
            来源：{{ current.document_name }}<br />
            步骤数：{{ current.new_guide_data?.steps?.length ?? 0 }}
          </div>
        </div>
      </div>

      <div class="action-hint">请选择如何处理此重复流程：</div>
    </template>

    <template #footer>
      <el-button type="primary" :loading="processing" @click="handleAction('overwrite')">
        覆盖更新
      </el-button>
      <el-button :loading="processing" @click="handleAction('keep')">
        保留原有
      </el-button>
      <el-button type="info" :loading="processing" @click="handleAction('save_as_new')">
        另存为新流程
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.progress-hint {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 16px;
  text-align: center;
}

.compare-grid {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.compare-card {
  flex: 1;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #E5E7EB;
}

.compare-card.existing {
  background: #fafafa;
}

.compare-card.new {
  background: #fef2f1;
  border-color: #e0301e;
}

.compare-arrow {
  font-size: 20px;
  color: #9ca3af;
  flex-shrink: 0;
}

.card-label {
  font-size: 11px;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 6px;
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.card-meta {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.6;
}

.action-hint {
  font-size: 13px;
  color: #4b5563;
  text-align: center;
}
</style>
