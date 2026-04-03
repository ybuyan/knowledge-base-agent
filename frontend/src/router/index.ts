import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login/LoginView.vue'),
    meta: { title: 'Login', public: true }
  },
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
        meta: { title: 'Documents', requiresHR: true }
      },
      {
        path: 'settings/constraints',
        name: 'Constraints',
        component: () => import('@/views/Settings/Constraints.vue'),
        meta: { title: 'Constraints', requiresHR: true }
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

  const token = localStorage.getItem('auth_token')
  const role = localStorage.getItem('auth_role')

  // 未登录跳登录页
  if (!to.meta.public && !token) {
    return { name: 'Login' }
  }

  // 已登录不能再访问登录页
  if (to.name === 'Login' && token) {
    return { name: 'Chat' }
  }

  // HR 专属页面
  if (to.meta.requiresHR && role !== 'hr') {
    return { name: 'Chat' }
  }
})

export default router
