<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { flowGuideApi } from '@/api'
import type { FlowGuide, FlowStep, ExternalLink } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, Top, Bottom, Grid, List as ListIcon, Lock, Unlock } from '@element-plus/icons-vue'

// ─── State ───────────────────────────────────────────────────────────────────
const guides = ref<FlowGuide[]>([])
const loading = ref(false)
const searchName = ref('')
const filterCategory = ref('')
const filterStatus = ref('')
const viewMode = ref<'grid' | 'list'>('grid')

// Form dialog
const dialogVisible = ref(false)
const isEdit = ref(false)
const formLoading = ref(false)
const externalLinks = ref<ExternalLink[]>([])

interface StepForm extends Omit<FlowStep, 'sequence'> {
  sequence: number
  entryMode: 'system' | 'manual'
  selectedLinkId: string
}

interface GuideForm {
  id?: string
  name: string
  category: string
  description: string
  status: 'active' | 'disabled'
  steps: StepForm[]
}

const emptyStep = (): StepForm => ({
  sequence: 1,
  title: '',
  description: '',
  entryMode: 'manual',
  selectedLinkId: '',
  entry_link: undefined
})

const form = ref<GuideForm>({
  name: '',
  category: '',
  description: '',
  status: 'active',
  steps: [emptyStep()]
})

// ─── Computed ─────────────────────────────────────────────────────────────────
const categories = computed(() => {
  const cats = new Set(guides.value.map(g => g.category))
  return Array.from(cats)
})

const filtered = computed(() => {
  return guides.value.filter(g => {
    const matchName = !searchName.value || g.name.toLowerCase().includes(searchName.value.toLowerCase())
    const matchCat = !filterCategory.value || g.category === filterCategory.value
    const matchStatus = !filterStatus.value || g.status === filterStatus.value
    return matchName && matchCat && matchStatus
  })
})

const stats = computed(() => ({
  total: guides.value.length,
  active: guides.value.filter(g => g.status === 'active').length,
  categories: categories.value.length
}))

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

// ─── Load ─────────────────────────────────────────────────────────────────────
const loadGuides = async () => {
  loading.value = true
  try {
    guides.value = await flowGuideApi.list()
  } catch {
    ElMessage.error('Failed to load process templates')
  } finally {
    loading.value = false
  }
}

const loadExternalLinks = async () => {
  try {
    externalLinks.value = await flowGuideApi.getExternalLinks()
  } catch {
    // non-critical
  }
}

onMounted(() => {
  loadGuides()
  loadExternalLinks()
})

// ─── Dialog ───────────────────────────────────────────────────────────────────
const openCreate = () => {
  isEdit.value = false
  form.value = { name: '', category: '', description: '', status: 'active', steps: [emptyStep()] }
  dialogVisible.value = true
}

const openEdit = (guide: FlowGuide) => {
  isEdit.value = true
  form.value = {
    id: guide.id,
    name: guide.name,
    category: guide.category,
    description: guide.description,
    status: guide.status,
    steps: guide.steps.map(s => ({
      ...s,
      entryMode: s.entry_link?.external_link_id ? 'system' : 'manual',
      selectedLinkId: s.entry_link?.external_link_id || ''
    }))
  }
  dialogVisible.value = true
}

const addStep = () => {
  const seq = form.value.steps.length + 1
  form.value.steps.push({ ...emptyStep(), sequence: seq })
}

const removeStep = (index: number) => {
  form.value.steps.splice(index, 1)
  form.value.steps.forEach((s, i) => { s.sequence = i + 1 })
}

const moveStep = (index: number, dir: 'up' | 'down') => {
  const steps = form.value.steps
  const target = dir === 'up' ? index - 1 : index + 1
  if (target < 0 || target >= steps.length) return
  ;[steps[index], steps[target]] = [steps[target], steps[index]]
  steps.forEach((s, i) => { s.sequence = i + 1 })
}

const onLinkSelect = (step: StepForm) => {
  const link = externalLinks.value.find(l => l.id === step.selectedLinkId)
  if (link) {
    step.entry_link = {
      external_link_id: link.id,
      label: link.title,
      url: link.url,
      open_in_new_tab: true
    }
  }
}

const buildSteps = (): FlowStep[] => {
  return form.value.steps.map(s => {
    const step: FlowStep = {
      sequence: s.sequence,
      title: s.title,
      description: s.description
    }
    if (s.entryMode === 'system' && s.selectedLinkId) {
      step.entry_link = s.entry_link
    } else if (s.entryMode === 'manual' && s.entry_link?.label && s.entry_link?.url) {
      step.entry_link = {
        label: s.entry_link.label,
        url: s.entry_link.url,
        open_in_new_tab: s.entry_link.open_in_new_tab ?? false
      }
    }
    return step
  })
}

const submitForm = async () => {
  if (!form.value.name.trim() || !form.value.category.trim()) {
    ElMessage.warning('Please enter name and category')
    return
  }
  formLoading.value = true
  try {
    const payload = {
      name: form.value.name,
      category: form.value.category,
      description: form.value.description,
      status: form.value.status,
      steps: buildSteps()
    }
    if (isEdit.value && form.value.id) {
      await flowGuideApi.update(form.value.id, payload)
      ElMessage.success('Updated successfully')
    } else {
      await flowGuideApi.create(payload)
      ElMessage.success('Created successfully')
    }
    dialogVisible.value = false
    loadGuides()
  } catch {
    ElMessage.error('Operation failed')
  } finally {
    formLoading.value = false
  }
}

// ─── Actions ──────────────────────────────────────────────────────────────────
const deleteGuide = async (guide: FlowGuide) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure to delete "${guide.name}"? This action cannot be undone.`,
      'Confirm Delete',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    await flowGuideApi.delete(guide.id)
    ElMessage.success('Deleted successfully')
    loadGuides()
  } catch {}
}

const toggleStatus = async (guide: FlowGuide) => {
  const newStatus = guide.status === 'active' ? 'disabled' : 'active'
  try {
    await flowGuideApi.toggleStatus(guide.id, newStatus)
    guide.status = newStatus
    ElMessage.success(newStatus === 'active' ? 'Enabled' : 'Disabled')
  } catch {
    ElMessage.error('Operation failed')
  }
}
</script>

<template>
  <div class="process-templates">
    <!-- Header -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">Process Templates</h1>
        <p class="page-subtitle">Manage and organize your workflow templates</p>
      </div>
      <div class="header-right">
        <el-button-group class="view-toggle">
          <el-button 
            :type="viewMode === 'grid' ? 'primary' : ''" 
            :icon="Grid" 
            @click="viewMode = 'grid'"
          />
          <el-button 
            :type="viewMode === 'list' ? 'primary' : ''" 
            :icon="ListIcon" 
            @click="viewMode = 'list'"
          />
        </el-button-group>
        <el-button type="primary" :icon="Plus" @click="openCreate">New Template</el-button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon total">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">Total Templates</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon active">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.active }}</div>
          <div class="stat-label">Active</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon categories">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.categories }}</div>
          <div class="stat-label">Categories</div>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-input
        v-model="searchName"
        placeholder="Search templates..."
        :prefix-icon="Search"
        clearable
        class="search-input"
      />
      <el-select v-model="filterCategory" placeholder="All Categories" clearable class="filter-select">
        <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="All Status" clearable class="filter-select">
        <el-option label="Active" value="active" />
        <el-option label="Disabled" value="disabled" />
      </el-select>
    </div>

    <!-- Content -->
    <div v-loading="loading" class="content-area">
      <!-- Grid View -->
      <div v-if="viewMode === 'grid'" class="grid-view">
        <TransitionGroup name="card-list">
          <div
            v-for="guide in filtered"
            :key="guide.id"
            class="template-card"
            :class="{ disabled: guide.status === 'disabled' }"
            :style="{ '--cat-primary': getCategoryTheme(guide.category).primary, '--cat-bg': getCategoryTheme(guide.category).bg, '--cat-border': getCategoryTheme(guide.category).border }"
          >
            <div class="card-accent-bar"></div>
            <div class="card-header">
              <div class="card-category" :style="{ color: getCategoryTheme(guide.category).primary, background: getCategoryTheme(guide.category).bg }">
                <span class="category-icon">{{ getCategoryTheme(guide.category).icon }}</span>
                {{ guide.category }}
              </div>
              <el-tag 
                :type="guide.status === 'active' ? 'success' : 'info'" 
                size="small"
                effect="light"
              >
                {{ guide.status === 'active' ? 'Active' : 'Disabled' }}
              </el-tag>
            </div>
            
            <div class="card-body">
              <h3 class="card-title">{{ guide.name }}</h3>
              <p class="card-description">{{ guide.description || 'No description provided' }}</p>
              
              <div class="card-meta">
                <div class="meta-item">
                  <span class="meta-label">Steps</span>
                  <span class="meta-value">{{ guide.steps?.length ?? 0 }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">Source</span>
                  <span class="meta-value source">{{ guide.source_document_name || 'Manual' }}</span>
                </div>
              </div>
            </div>

            <div class="card-footer">
              <div class="card-time">
                {{ new Date(guide.updated_at).toLocaleDateString() }}
              </div>
              <div class="card-actions">
                <el-button size="small" text :icon="Edit" class="edit-btn" @click="openEdit(guide)">Edit</el-button>
                <el-dropdown trigger="click">
                  <el-button size="small" text>More</el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="toggleStatus(guide)">
                        {{ guide.status === 'active' ? 'Disable' : 'Enable' }}
                      </el-dropdown-item>
                      <el-dropdown-item divided @click="deleteGuide(guide)">
                        <span style="color: #f56c6c">Delete</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </div>
          </div>
        </TransitionGroup>

        <!-- Empty State -->
        <div v-if="!filtered.length && !loading" class="empty-state">
          <div class="empty-icon">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
            </svg>
          </div>
          <h3 class="empty-title">No templates found</h3>
          <p class="empty-description">
            {{ searchName || filterCategory || filterStatus 
               ? 'Try adjusting your search or filters' 
               : 'Get started by creating your first template' }}
          </p>
          <el-button v-if="!searchName && !filterCategory && !filterStatus" type="primary" :icon="Plus" @click="openCreate">
            Create Template
          </el-button>
        </div>
      </div>

      <!-- List View -->
      <div v-else class="list-view">
        <el-table :data="filtered" class="modern-table">
          <el-table-column prop="name" label="Template Name" min-width="200">
            <template #default="{ row }">
              <div class="name-cell">
                <span class="name-text">{{ row.name }}</span>
                <el-tag 
                  size="small" 
                  effect="plain" 
                  class="category-tag"
                  :style="{ color: getCategoryTheme(row.category).primary, borderColor: getCategoryTheme(row.category).border, background: getCategoryTheme(row.category).bg }"
                >
                  <span class="tag-icon">{{ getCategoryTheme(row.category).icon }}</span>
                  {{ row.category }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="Steps" width="80" align="center">
            <template #default="{ row }">
              <span class="step-count" :style="{ color: getCategoryTheme(row.category).primary }">{{ row.steps?.length ?? 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="Status" width="100" align="center">
            <template #default="{ row }">
              <el-tag 
                :type="row.status === 'active' ? 'success' : 'info'" 
                size="small"
                effect="light"
              >
                {{ row.status === 'active' ? 'Active' : 'Disabled' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="source_document_name" label="Source" min-width="140" show-overflow-tooltip />
          <el-table-column label="Updated" width="160">
            <template #default="{ row }">{{ new Date(row.updated_at).toLocaleString() }}</template>
          </el-table-column>
          <el-table-column label="Actions" width="140" fixed="right" align="center">
            <template #default="{ row }">
              <el-tooltip content="Edit" placement="top">
                <el-button size="small" circle :icon="Edit" @click="openEdit(row)" class="action-icon-btn" />
              </el-tooltip>
              <el-tooltip :content="row.status === 'active' ? 'Disable' : 'Enable'" placement="top">
                <el-button
                  size="small"
                  circle
                  :icon="row.status === 'active' ? Lock : Unlock"
                  @click="toggleStatus(row)"
                  class="action-icon-btn"
                />
              </el-tooltip>
              <el-tooltip content="Delete" placement="top">
                <el-button
                  size="small"
                  circle
                  type="danger"
                  :icon="Delete"
                  @click="deleteGuide(row)"
                  class="action-icon-btn"
                />
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? 'Edit Template' : 'Create New Template'"
      width="720px"
      destroy-on-close
      class="template-dialog"
    >
      <el-form label-position="top" class="guide-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Template Name" required>
              <el-input v-model="form.name" placeholder="Enter template name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Category" required>
              <el-autocomplete
                v-model="form.category"
                :fetch-suggestions="(q: string, cb: (results: {value: string}[]) => void) => cb(categories.filter((c: string) => c.includes(q)).map((c: string) => ({ value: c })))"
                placeholder="Enter or select category"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="Description">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="Brief description of this template (optional)" />
        </el-form-item>

        <el-form-item label="Status">
          <el-radio-group v-model="form.status">
            <el-radio value="active">Active</el-radio>
            <el-radio value="disabled">Disabled</el-radio>
          </el-radio-group>
        </el-form-item>

        <!-- Steps Section -->
        <div class="steps-section">
          <div class="steps-header">
            <span class="steps-title">Workflow Steps</span>
            <el-button size="small" :icon="Plus" type="primary" plain @click="addStep">Add Step</el-button>
          </div>

          <div v-for="(step, index) in form.steps" :key="index" class="step-card">
            <div class="step-card-header">
              <div class="step-number">{{ step.sequence }}</div>
              <div class="step-card-actions">
                <el-tooltip content="Move up" placement="top">
                  <el-button size="small" :icon="Top" circle :disabled="index === 0" @click="moveStep(index, 'up')" />
                </el-tooltip>
                <el-tooltip content="Move down" placement="top">
                  <el-button size="small" :icon="Bottom" circle :disabled="index === form.steps.length - 1" @click="moveStep(index, 'down')" />
                </el-tooltip>
                <el-tooltip content="Remove step" placement="top">
                  <el-button size="small" type="danger" :icon="Delete" circle @click="removeStep(index)" />
                </el-tooltip>
              </div>
            </div>

            <el-input v-model="step.title" placeholder="Step title (required)" class="mb-8" />
            <el-input v-model="step.description" type="textarea" :rows="2" placeholder="Step description (optional)" class="mb-8" />

            <!-- Entry link collapsible - enhanced visibility -->
            <div class="entry-link-section">
              <el-collapse>
                <el-collapse-item name="entry-link">
                  <template #title>
                    <div class="collapse-header">
                      <div class="collapse-header-left">
                        <span class="link-icon">🔗</span>
                        <span class="collapse-title">Entry Link Configuration</span>
                        <el-tag size="small" type="info" effect="plain" round>Optional</el-tag>
                      </div>
                      <span class="collapse-hint">Click to configure →</span>
                    </div>
                  </template>
                <el-radio-group v-model="step.entryMode" class="mb-8">
                  <el-radio value="system">Select from system links</el-radio>
                  <el-radio value="manual">Enter manually</el-radio>
                </el-radio-group>

                <template v-if="step.entryMode === 'system'">
                  <el-select
                    v-model="step.selectedLinkId"
                    placeholder="Choose a system link"
                    style="width: 100%"
                    @change="onLinkSelect(step)"
                    class="mb-8"
                  >
                    <el-option
                      v-for="link in externalLinks"
                      :key="link.id"
                      :label="link.title"
                      :value="link.id"
                    />
                  </el-select>
                  <el-input
                    v-if="step.entry_link"
                    v-model="step.entry_link.label"
                    placeholder="Button label (override if needed)"
                  />
                </template>

                <template v-else>
                  <el-input
                    :model-value="step.entry_link?.label || ''"
                    @update:model-value="(v: string) => { if (!step.entry_link) step.entry_link = { open_in_new_tab: true }; step.entry_link!.label = v }"
                    placeholder="Button label"
                    class="mb-8"
                  />
                  <el-input
                    :model-value="step.entry_link?.url || ''"
                    @update:model-value="(v: string) => { if (!step.entry_link) step.entry_link = { open_in_new_tab: true }; step.entry_link!.url = v }"
                    placeholder="URL address"
                    class="mb-8"
                  />
                  <el-checkbox
                    v-if="step.entry_link"
                    v-model="step.entry_link.open_in_new_tab"
                  >Open in new tab</el-checkbox>
                </template>
              </el-collapse-item>
            </el-collapse>
            </div>
          </div>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">Cancel</el-button>
        <el-button type="primary" :loading="formLoading" @click="submitForm">
          {{ isEdit ? 'Update' : 'Create' }} Template
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.process-templates {
  padding: 32px;
  /* background: linear-gradient(135deg, #fef5f5 0%, #fff5f5 100%); */
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

/* Custom Scrollbar */
.process-templates::-webkit-scrollbar {
  width: 8px;
}

.process-templates::-webkit-scrollbar-track {
  background: transparent;
}

.process-templates::-webkit-scrollbar-thumb {
  background: rgba(224, 48, 30, 0.2);
  border-radius: 4px;
}

.process-templates::-webkit-scrollbar-thumb:hover {
  background: rgba(224, 48, 30, 0.4);
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 6px 0;
  letter-spacing: -0.5px;
}

.page-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  font-weight: 400;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.view-toggle {
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(224, 48, 30, 0.08);
}

.view-toggle :deep(.el-button) {
  color: #6b7280;
}

.view-toggle :deep(.el-button--primary) {
  background-color: #e0301e !important;
  border-color: #e0301e !important;
  color: white !important;
}

.view-toggle :deep(.el-button:not(.el-button--primary):hover) {
  color: #e0301e;
  background-color: rgba(224, 48, 30, 0.08);
}

/* Stats Cards */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 20px;
  margin-bottom: 28px;
}

.stat-card {
  background: white;
  border-radius: 16px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 3px rgba(224, 48, 30, 0.06);
  transition: all 0.3s ease;
  border: 1px solid rgba(224, 48, 30, 0.04);
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(224, 48, 30, 0.12);
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.stat-icon.total {
  background: linear-gradient(135deg, #e0301e 0%, #c41d18 100%);
}

.stat-icon.active {
  background: linear-gradient(135deg, #ff6b4a 0%, #e0301e 100%);
}

.stat-icon.categories {
  background: linear-gradient(135deg, #ff8a65 0%, #ff5722 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1.2;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

/* Filter Bar */
.filter-bar {
  display: flex;
  gap: 14px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.search-input {
  width: 300px;
}

.search-input :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(224, 48, 30, 0.06);
  transition: all 0.3s ease;
}

.search-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(224, 48, 30, 0.1);
}

.search-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 3px rgba(224, 48, 30, 0.1);
  border-color: #e0301e;
}

.filter-select {
  width: 170px;
}

.filter-select :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(224, 48, 30, 0.06);
}

.filter-select :deep(.el-input__wrapper:hover) {
  box-shadow: 0 2px 8px rgba(224, 48, 30, 0.1);
}

/* Content Area */
.content-area {
  min-height: 400px;
}

/* Grid View */
.grid-view {
  padding-top: 4px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
}

.template-card {
  background: white;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(224, 48, 30, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid var(--cat-border, rgba(224, 48, 30, 0.06));
  display: flex;
  flex-direction: column;
  position: relative;
}

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(224, 48, 30, 0.12);
  border-color: var(--cat-primary, rgba(224, 48, 30, 0.2));
}

.card-accent-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--cat-primary, #e0301e) 0%, var(--cat-light, #ff4d3a) 100%);
}

.template-card.disabled {
  opacity: 0.65;
}

.template-card.disabled .card-header,
.template-card.disabled .card-body,
.template-card.disabled .card-footer .edit-btn {
  pointer-events: none;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px 0;
}

.card-category {
  font-size: 12px;
  font-weight: 600;
  color: var(--cat-primary, #e0301e);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 20px;
  background: var(--cat-bg, #fef5f5);
}

.category-icon {
  font-size: 14px;
  line-height: 1;
}

.card-body {
  padding: 16px 20px;
  flex: 1;
}

.card-title {
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 8px 0;
  line-height: 1.3;
}

.card-description {
  font-size: 13px;
  color: #6b7280;
  margin: 0 0 16px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  gap: 20px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label {
  font-size: 11px;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-weight: 500;
}

.meta-value {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.meta-value.source {
  font-weight: 400;
  color: #6b7280;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  border-top: 1px solid #f3f4f6;
  background: #fafafa;
}

.card-time {
  font-size: 12px;
  color: #9ca3af;
}

.card-actions {
  display: flex;
  gap: 4px;
}

/* Card Action Buttons Hover */
.card-actions :deep(.el-button) {
  color: #6b7280;
  transition: all 0.2s ease;
}

.card-actions :deep(.el-button:hover) {
  color: #e0301e;
  background-color: rgba(224, 48, 30, 0.08);
}

/* Empty State */
.empty-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 80px 20px;
}

.empty-icon {
  color: #d1d5db;
  margin-bottom: 16px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #374151;
  margin: 0 0 8px 0;
}

.empty-description {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 24px 0;
}

/* List View */
.list-view {
  background: white;
  border-radius: 16px;
  padding: 8px;
  box-shadow: 0 1px 3px rgba(224, 48, 30, 0.06);
  overflow: auto;
}

/* List View Scrollbar */
.list-view::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.list-view::-webkit-scrollbar-track {
  background: transparent;
}

.list-view::-webkit-scrollbar-thumb {
  background: rgba(224, 48, 30, 0.2);
  border-radius: 3px;
}

.list-view::-webkit-scrollbar-thumb:hover {
  background: rgba(224, 48, 30, 0.4);
}

.modern-table {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: transparent;
}

.modern-table :deep(th) {
  font-weight: 600;
  color: #374151;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  background: transparent !important;
}

.modern-table :deep(td) {
  border-bottom: 1px solid #f3f4f6;
}

.modern-table :deep(tr:hover > td) {
  background-color: #f9fafb !important;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.name-text {
  font-weight: 500;
  color: #1a1a1a;
}

.category-tag {
  font-size: 11px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}

.tag-icon {
  font-size: 12px;
  line-height: 1;
}

.step-count {
  font-weight: 600;
}

/* Table Action Icon Buttons */
.action-icon-btn {
  transition: all 0.2s ease !important;
}

.action-icon-btn:not(.el-button--danger):hover {
  color: #e0301e !important;
  background-color: rgba(224, 48, 30, 0.1) !important;
  border-color: transparent !important;
}

.action-icon-btn.el-button--danger:hover {
  background-color: #f56c6c !important;
}

/* Page Primary Button Override */
.process-templates :deep(.el-button--primary) {
  background: linear-gradient(135deg, #e0301e 0%, #c41d18 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(224, 48, 30, 0.25);
  transition: all 0.3s ease;
}

.process-templates :deep(.el-button--primary:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(224, 48, 30, 0.35);
}

/* Card Transitions */
.card-list-enter-active,
.card-list-leave-active {
  transition: all 0.4s ease;
}

.card-list-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.card-list-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.card-list-move {
  transition: transform 0.4s ease;
}

/* Dialog Styles */
.template-dialog :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
}

.template-dialog :deep(.el-dialog__header) {
  padding: 24px 28px 0;
  border-bottom: 1px solid #f3f4f6;
}

.template-dialog :deep(.el-dialog__title) {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a1a;
}

.template-dialog :deep(.el-dialog__body) {
  padding: 24px 28px;
  max-height: 70vh;
  overflow-y: auto;
}

/* Dialog Scrollbar */
.template-dialog :deep(.el-dialog__body)::-webkit-scrollbar {
  width: 6px;
}

.template-dialog :deep(.el-dialog__body)::-webkit-scrollbar-track {
  background: transparent;
}

.template-dialog :deep(.el-dialog__body)::-webkit-scrollbar-thumb {
  background: rgba(224, 48, 30, 0.2);
  border-radius: 3px;
}

.template-dialog :deep(.el-dialog__body)::-webkit-scrollbar-thumb:hover {
  background: rgba(224, 48, 30, 0.4);
}

.template-dialog :deep(.el-dialog__footer) {
  padding: 16px 28px 24px;
  border-top: 1px solid #f3f4f6;
}

.guide-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 13px;
  padding-bottom: 6px;
}

/* Button & Input Focus Styles */
.template-dialog :deep(.el-button--primary) {
  background-color: #e0301e;
  border-color: #e0301e;
}

.template-dialog :deep(.el-button--primary:hover) {
  background-color: #c41d18;
  border-color: #c41d18;
}

/* Textarea Focus - handled globally in style.css, keep for dialog specificity */
.template-dialog :deep(.el-textarea__inner:focus),
.template-dialog :deep(.el-input__inner:focus) {
  border-color: #e0301e !important;
  box-shadow: 0 0 0 1px var(--primary-color) inset !important;
  outline: none !important;
}

/* Radio Group Active Color - handled globally in style.css */
/* (kept for reference - global styles in style.css take precedence) */

/* Step Editor Input Focus - use consistent inset shadow */
.step-card :deep(.el-input__inner:focus),
.step-card :deep(.el-textarea__inner:focus) {
  border-color: #e0301e !important;
  /* box-shadow: 0 0 0 1px var(--primary-color) inset !important; */
}

/* Select Focus */
.step-card :deep(.el-select .el-input.is-focus .el-input__wrapper),
.step-card :deep(.el-select .el-input__wrapper:hover) {
  border-color: #e0301e !important;
  box-shadow: 0 0 0 1px var(--primary-color) inset !important;
}

/* Steps Section */
.steps-section {
  margin-top: 16px;
  padding-top: 20px;
  border-top: 1px dashed #e5e7eb;
}

.steps-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.steps-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.step-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 18px;
  margin-bottom: 14px;
  transition: all 0.2s ease;
}

.step-card:hover {
  border-color: #e0301e;
  box-shadow: 0 2px 8px rgba(224, 48, 30, 0.15);
}

.step-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.step-number {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #e0301e 0%, #c41d18 100%);
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(224, 48, 30, 0.3);
}

.step-card-actions {
  display: flex;
  gap: 6px;
}

.mb-8 {
  margin-bottom: 10px;
}

.guide-form :deep(.el-collapse-item__header) {
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

/* Entry Link Section - Enhanced Visibility */
.entry-link-section {
  margin-top: 8px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px dashed rgba(224, 48, 30, 0.3);
  background: linear-gradient(135deg, rgba(224, 48, 30, 0.03) 0%, rgba(255, 107, 74, 0.03) 100%);
}

.entry-link-section :deep(.el-collapse) {
  border: none;
}

.entry-link-section :deep(.el-collapse-item) {
  border-bottom: none;
}

.entry-link-section :deep(.el-collapse-item__header) {
  height: auto;
  min-height: 48px;
  padding: 12px 16px;
  background-color: transparent;
  transition: all 0.2s ease;
}

.entry-link-section :deep(.el-collapse-item__header:hover) {
  background-color: rgba(224, 48, 30, 0.06);
}

.entry-link-section :deep(.el-collapse-item__header.is-active) {
  background-color: rgba(224, 48, 30, 0.08);
  border-bottom: 1px solid rgba(224, 48, 30, 0.15);
}

.entry-link-section :deep(.el-collapse-item__arrow) {
  color: #e0301e;
  font-weight: 700;
  transform: scale(1.1);
  transition: transform 0.3s ease;
}

.entry-link-section :deep(.el-collapse-item__arrow.is-active) {
  transform: rotate(90deg) scale(1.1);
}

.entry-link-section :deep(.el-collapse-item__content) {
  padding: 20px;
}

.collapse-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 12px;
}

.collapse-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.link-icon {
  font-size: 16px;
  line-height: 1;
}

.collapse-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.collapse-hint {
  font-size: 11px;
  color: #e0301e;
  font-weight: 500;
  opacity: 0.8;
  white-space: nowrap;
  letter-spacing: 0.3px;
}

/* Responsive */
@media (max-width: 768px) {
  .process-templates {
    padding: 20px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }

  .header-right {
    width: 100%;
    justify-content: space-between;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .grid-view {
    grid-template-columns: 1fr;
  }

  .filter-bar {
    flex-direction: column;
  }

  .search-input {
    width: 100%;
  }

  .filter-select {
    width: 100%;
  }
}
</style>
