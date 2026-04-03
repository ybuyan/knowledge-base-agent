<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { processGuideApi } from '@/api'
import type { QuickPromptGroup, QuickPrompt } from '@/stores/chat'

const emit = defineEmits<{
  promptClick: [text: string]
}>()

const promptGroups = ref<QuickPromptGroup[]>([])
const isExpanded = ref(false)
const activeCategory = ref<string | null>(null)

let expandTimer: number | null = null
let collapseTimer: number | null = null
let categoryTimer: number | null = null

onMounted(async () => {
  try {
    promptGroups.value = []//await processGuideApi.getQuickPromptsGrouped()
  } catch (error) {
    console.error('加载快捷提示词失败:', error)
  }
})

const handleButtonEnter = () => {
  if (collapseTimer) {
    clearTimeout(collapseTimer)
    collapseTimer = null
  }
  expandTimer = window.setTimeout(() => {
    isExpanded.value = true
  }, 100)
}

const handleButtonLeave = () => {
  if (expandTimer) {
    clearTimeout(expandTimer)
    expandTimer = null
  }
  collapseTimer = window.setTimeout(() => {
    if (!activeCategory.value) {
      isExpanded.value = false
    }
  }, 200)
}

const handleCategoryEnter = (category: string) => {
  if (categoryTimer) {
    clearTimeout(categoryTimer)
    categoryTimer = null
  }
  activeCategory.value = category
}

const handleCategoryLeave = () => {
  categoryTimer = window.setTimeout(() => {
    activeCategory.value = null
  }, 200)
}

const handlePanelEnter = () => {
  if (categoryTimer) {
    clearTimeout(categoryTimer)
    categoryTimer = null
  }
  if (collapseTimer) {
    clearTimeout(collapseTimer)
    collapseTimer = null
  }
}

const handlePanelLeave = () => {
  activeCategory.value = null
  isExpanded.value = false
}

const handlePromptClick = (prompt: QuickPrompt) => {
  emit('promptClick', prompt.prompt_text)
  activeCategory.value = null
  isExpanded.value = false
}
</script>

<template>
  <div class="quick-prompt-container">
    <!-- 悬浮按钮 -->
    <div 
      class="floating-button"
      :class="{ expanded: isExpanded }"
      @mouseenter="handleButtonEnter"
      @mouseleave="handleButtonLeave"
    >
      <span v-if="!isExpanded" class="trigger-icon">⚡</span>
      
      <!-- 胶囊菜单 -->
      <div v-if="isExpanded" class="category-list">
        <div
          v-for="group in promptGroups"
          :key="group.category"
          class="category-item"
          :class="{ active: activeCategory === group.category }"
          @mouseenter="handleCategoryEnter(group.category)"
          @mouseleave="handleCategoryLeave"
        >
          {{ group.category }}
        </div>
      </div>
    </div>

    <!-- 手风琴展开面板 -->
    <div
      v-if="activeCategory"
      class="prompts-panel"
      @mouseenter="handlePanelEnter"
      @mouseleave="handlePanelLeave"
    >
      <div class="panel-header">{{ activeCategory }}</div>
      <div class="prompts-list">
        <div
          v-for="prompt in promptGroups.find(g => g.category === activeCategory)?.prompts || []"
          :key="prompt.id"
          class="prompt-item"
          @click="handlePromptClick(prompt)"
        >
          <div class="prompt-title">{{ prompt.title }}</div>
          <div class="prompt-description">{{ prompt.description }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.quick-prompt-container {
  position: absolute;
  right: 300px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 100;
}

/* 悬浮按钮 */
.floating-button {
  width: 56px;
  height: 56px;
  border-radius: 28px;
  background: #e0301e;
  color: white;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(224, 48, 30, 0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  flex-shrink: 0;
}

.floating-button.expanded {
  width: 140px;
  height: auto;
  min-height: 200px;
  border-radius: 28px;
  background: white;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  padding: 12px 0;
}

/* 按钮图标 */
.trigger-icon {
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 胶囊菜单 */
.category-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.category-item {
  position: relative;
  padding: 12px 16px;
  font-size: 14px;
  font-weight: 500;
  color: #1f1f1f;
  cursor: pointer;
  transition: all 0.2s;
  background: transparent;
  text-align: center;
  white-space: nowrap;
  border-radius: 8px;
  opacity: 0;
  animation: slideInFade 0.3s ease-out forwards;
}

/* 为每个分类项添加延迟，创建级联效果 */
.category-item:nth-child(1) {
  animation-delay: 0.05s;
}

.category-item:nth-child(2) {
  animation-delay: 0.1s;
}

.category-item:nth-child(3) {
  animation-delay: 0.15s;
}

.category-item:nth-child(4) {
  animation-delay: 0.2s;
}

.category-item:nth-child(5) {
  animation-delay: 0.25s;
}

.category-item:nth-child(6) {
  animation-delay: 0.3s;
}

@keyframes slideInFade {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.category-item:hover,
.category-item.active {
  background: rgba(224, 48, 30, 0.08);
  color: #e0301e;
}

/* 手风琴展开面板 */
.prompts-panel {
  position: absolute;
  right: calc(100% + 12px);
  top: 0;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  min-width: 320px;
  max-width: 400px;
  max-height: 500px;
  overflow-y: auto;
  z-index: 1000;
  animation: slideInLeft 0.3s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.panel-header {
  font-size: 15px;
  font-weight: 600;
  color: #e0301e;
  padding: 16px;
  margin-bottom: 0;
  border-bottom: 1px solid #f0f0f0;
}

.prompts-list {
  padding: 12px 16px 16px;
}

.prompt-item {
  padding: 12px 16px;
  margin-bottom: 8px;
  background: #f7f7f8;
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.prompt-item:hover {
  background: rgba(224, 48, 30, 0.08);
  border-color: #e0301e;
  transform: translateX(-4px);
}

.prompt-item:last-child {
  margin-bottom: 0;
}

.prompt-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f1f1f;
  margin-bottom: 4px;
}

.prompt-description {
  font-size: 12px;
  color: #5f5f5f;
  line-height: 1.4;
}

/* 滚动条样式 */
.prompts-panel::-webkit-scrollbar {
  width: 6px;
}

.prompts-panel::-webkit-scrollbar-track {
  background: transparent;
}

.prompts-panel::-webkit-scrollbar-thumb {
  background: #d1d1d1;
  border-radius: 3px;
}

.prompts-panel::-webkit-scrollbar-thumb:hover {
  background: #b4b4b4;
}
</style>
