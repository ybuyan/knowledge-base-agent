import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('@/components/Layout/MainLayout.vue'),
    redirect: '/chat',
    children: [
      {
        path: 'chat',
        name: 'Chat',
        component: () => import('@/views/Chat/ChatView.vue'),
        meta: { title: 'Chat' }
      },
      {
        path: 'documents',
        name: 'Documents',
        component: () => import('@/views/Documents/DocumentsView.vue'),
        meta: { title: 'Documents' }
      },
      {
        path: 'settings/constraints',
        name: 'Constraints',
        component: () => import('@/views/Settings/Constraints.vue'),
        meta: { title: 'Constraints' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  document.title = (to.meta.title as string) ? `${to.meta.title} | AI Knowledge Base` : 'AI Knowledge Base'
})

export default router
