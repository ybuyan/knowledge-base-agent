<script setup lang="ts">
import AppHeader from '@/components/Layout/AppHeader.vue'
import AppSidebar from '@/components/Layout/AppSidebar.vue'
import RightPanel from '@/components/Layout/RightPanel.vue'
</script>

<template>
  <div class="app-container">
    <AppHeader />
    <div class="main-layout">
      <AppSidebar />
      <div class="content-area">
        <RouterView />
      </div>
      <RightPanel />
    </div>
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

.main-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background-color: var(--bg-primary);
}
</style>
