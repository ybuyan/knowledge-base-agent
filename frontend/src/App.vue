<script setup lang="ts">
import { RouterView } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { onMounted } from 'vue'

const chatStore = useChatStore()

onMounted(async () => {
  await chatStore.initialize()
  if (!chatStore.sessions.length) {
    await chatStore.createSession()
  }
})
</script>

<template>
  <RouterView />
</template>

<style scoped>
</style>
