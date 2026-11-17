import { reactive } from 'vue'

const STORAGE_KEY = 'zhuce.auth'

function readStorage() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null')
  } catch {
    return null
  }
}

const stored = readStorage()

export const auth = reactive({
  token: stored?.token || '',
  user: stored?.user || null
})

export function setAuth(payload) {
  auth.token = payload.access_token
  auth.user = payload.user
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ token: auth.token, user: auth.user })
  )
}

export function clearAuth() {
  auth.token = ''
  auth.user = null
  localStorage.removeItem(STORAGE_KEY)
}

export function isAdmin() {
  return auth.user?.role === 'ADMIN'
}

export function canEdit() {
  return ['ADMIN', 'ENGINEER'].includes(auth.user?.role)
}

export function roleLabel(role) {
  return { ADMIN: '管理员', ENGINEER: '检测工程师', VIEWER: '查阅人员' }[role] || role
}
