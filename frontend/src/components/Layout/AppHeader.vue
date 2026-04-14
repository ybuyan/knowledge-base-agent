<script setup lang="ts">
import { Moon, Sunny, Setting, User } from '@element-plus/icons-vue'
import logoUrl from '../../../public/logo.svg?url'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const isDarkMode = ref(false)

const toggleTheme = () => {
  isDarkMode.value = !isDarkMode.value
  document.documentElement.setAttribute('data-theme', isDarkMode.value ? 'dark' : 'light')
}

const navigateToSettings = () => {
  router.push('/settings/constraints')
}
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <div class="logo">
        <img :src="logoUrl" class="logo-icon" alt="logo" />
        <span class="logo-text">System Answer Assistant</span>
      </div>
    </div>
    
    <div class="header-right">
      <button class="icon-btn no-border" @click="toggleTheme" :title="isDarkMode ? 'Light Mode' : 'Dark Mode'">
        <el-icon :size="18">
          <Sunny v-if="isDarkMode" />
          <Moon v-else />
        </el-icon>
      </button>
      
      <button v-if="authStore.isHR" class="icon-btn no-border" title="设置" @click="navigateToSettings">
        <el-icon :size="18"><Setting /></el-icon>
      </button>
      
      <div class="user-avatar">
        <el-avatar :size="32" :icon="User" />
      </div>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-5);
  background-color: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.logo-icon {
  width: 52px;
  height: 41px;
  object-fit: contain;
  position: relative;
  top: -6px;
}

.logo-text {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.user-avatar {
  margin-left: var(--space-2);
  cursor: pointer;
}

.user-avatar :deep(.el-avatar) {
  background-color: var(--bg-tertiary);
  color: var(--text-secondary);
}
</style>
