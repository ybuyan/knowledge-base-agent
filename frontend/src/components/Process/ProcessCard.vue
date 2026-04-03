<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

interface Field {
  key: string
  label: string
  type: 'text' | 'date' | 'select' | 'number'
  required?: boolean
  options?: string[]
}

interface StepOverview {
  index: number
  title: string
  status: 'done' | 'current' | 'pending'
}

interface ProcessNode {
  id: string
  title: string
  type: string
  content: string
  fields: Field[]
}

interface UIComponents {
  type: string
  flow_name: string
  current_step: number
  total_steps: number
  node: ProcessNode
  collected_data: Record<string, any>
  errors: string[]
  can_prev: boolean
  can_next: boolean
  steps_overview: StepOverview[]
}

const props = defineProps<{
  ui: UIComponents
  sessionId: string
}>()

const emit = defineEmits<{
  (e: 'update', result: any): void
}>()

const formData = ref<Record<string, any>>({ ...props.ui.collected_data })
const loading = ref(false)

const flowId = computed(() => props.ui.flow_id || props.ui.flow_name)

// auto_next 节点：渲染后自动触发下一步
onMounted(() => {
  if (props.ui.node.auto_next) {
    setTimeout(() => sendAction('next'), 600)
  }
})

// 节点切换时，如果新节点也是 auto_next，继续自动触发
watch(() => props.ui.node.id, () => {
  if (props.ui.node.auto_next) {
    setTimeout(() => sendAction('next'), 600)
  }
})

async function sendAction(action: string) {
  loading.value = true
  try {
    const token = localStorage.getItem('auth_token')
    const res = await axios.post('/api/process/action', {
      session_id: props.sessionId,
      flow_id: flowId.value,
      action,
      input_data: action === 'next' || action === 'input' ? formData.value : {},
    }, {
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    })
    emit('update', res.data)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  } finally {
    loading.value = false
  }
}

function stepClass(status: string) {
  return {
    'step-done': status === 'done',
    'step-current': status === 'current',
    'step-pending': status === 'pending',
  }
}
</script>

<template>
  <div class="process-card">
    <!-- 流程标题 + 进度 -->
    <div class="process-header">
      <span class="flow-name">{{ ui.flow_name }}</span>
      <span class="step-counter">{{ ui.current_step + 1 }} / {{ ui.total_steps }}</span>
    </div>

    <!-- 步骤进度条 -->
    <div class="steps-bar">
      <div
        v-for="step in ui.steps_overview"
        :key="step.index"
        class="step-dot"
        :class="stepClass(step.status)"
        :title="step.title"
      >
        <span v-if="step.status === 'done'" class="dot-icon">✓</span>
        <span v-else class="dot-index">{{ step.index + 1 }}</span>
      </div>
    </div>

    <!-- 当前节点 -->
    <div class="node-body">
      <div class="node-title">{{ ui.node.title }}</div>
      <div v-if="ui.node.content" class="node-content">{{ ui.node.content }}</div>

      <!-- 信息收集表单 -->
      <div v-if="ui.node.type === 'info_collect' && ui.node.fields.length" class="node-form">
        <div v-for="field in ui.node.fields" :key="field.key" class="form-item">
          <label class="form-label">
            {{ field.label }}
            <span v-if="field.required" class="required">*</span>
          </label>

          <el-select
            v-if="field.type === 'select'"
            v-model="formData[field.key]"
            :placeholder="`请选择${field.label}`"
            class="form-input"
          >
            <el-option
              v-for="opt in field.options"
              :key="opt"
              :label="opt"
              :value="opt"
            />
          </el-select>

          <el-date-picker
            v-else-if="field.type === 'date'"
            v-model="formData[field.key]"
            type="date"
            :placeholder="`请选择${field.label}`"
            value-format="YYYY-MM-DD"
            class="form-input"
          />

          <el-input-number
            v-else-if="field.type === 'number'"
            v-model="formData[field.key]"
            :placeholder="`请输入${field.label}`"
            class="form-input"
          />

          <el-input
            v-else
            v-model="formData[field.key]"
            :placeholder="`请输入${field.label}`"
            class="form-input"
          />
        </div>
      </div>

      <!-- 错误提示 -->
      <div v-if="ui.errors.length" class="error-list">
        <div v-for="err in ui.errors" :key="err" class="error-item">⚠ {{ err }}</div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="process-actions">
      <el-button
        v-if="ui.can_prev"
        size="small"
        @click="sendAction('prev')"
        :loading="loading"
      >上一步</el-button>

      <el-button
        type="primary"
        size="small"
        @click="sendAction('next')"
        :loading="loading"
      >
        {{ ui.current_step + 1 === ui.total_steps ? '提交' : '下一步' }}
      </el-button>

      <el-button
        size="small"
        @click="sendAction('restart')"
        :loading="loading"
      >重新开始</el-button>

      <el-button
        type="danger"
        size="small"
        plain
        @click="sendAction('cancel')"
        :loading="loading"
      >取消</el-button>
    </div>
  </div>
</template>

<style scoped>
.process-card {
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 16px;
  background: var(--bg-sidebar);
  max-width: 480px;
  font-size: 14px;
}

.process-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.flow-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 15px;
}

.step-counter {
  font-size: 12px;
  color: var(--text-tertiary);
}

.steps-bar {
  display: flex;
  gap: 6px;
  margin-bottom: 16px;
  align-items: center;
}

.step-dot {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
  transition: all 0.2s;
}

.step-done {
  background: var(--primary-color);
  color: white;
}

.step-current {
  background: var(--primary-color);
  color: white;
  box-shadow: 0 0 0 3px rgba(var(--primary-rgb, 59, 130, 246), 0.2);
}

.step-pending {
  background: var(--bg-hover);
  color: var(--text-tertiary);
  border: 1px solid var(--border-light);
}

.node-body {
  margin-bottom: 16px;
}

.node-title {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.node-content {
  color: var(--text-secondary);
  margin-bottom: 12px;
  line-height: 1.6;
}

.node-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.required {
  color: #ef4444;
  margin-left: 2px;
}

.form-input {
  width: 100%;
}

.error-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.error-item {
  color: #ef4444;
  font-size: 12px;
}

.process-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
