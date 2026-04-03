import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const role = ref<string | null>(localStorage.getItem('auth_role'))
  const displayName = ref<string | null>(localStorage.getItem('auth_display_name'))

  const isLoggedIn = computed(() => !!token.value)
  const isHR = computed(() => role.value === 'hr')

  async function login(username: string, password: string) {
    const res = await axios.post('/api/auth/login', { username, password })
    token.value = res.data.access_token
    role.value = res.data.role
    displayName.value = res.data.display_name
    localStorage.setItem('auth_token', token.value!)
    localStorage.setItem('auth_role', role.value!)
    localStorage.setItem('auth_display_name', displayName.value!)
  }

  function logout() {
    token.value = null
    role.value = null
    displayName.value = null
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_role')
    localStorage.removeItem('auth_display_name')
  }

  return { token, role, displayName, isLoggedIn, isHR, login, logout }
})
