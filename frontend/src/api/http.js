import axios from 'axios'
import { ElMessage } from 'element-plus'
import { auth, clearAuth } from '@/stores/auth'

const http = axios.create({
  baseURL: '/api',
  timeout: 20000
})

http.interceptors.request.use((config) => {
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code === 0) return body.data
      ElMessage.error(body.message || '请求处理失败')
      return Promise.reject(new Error(body.message || '请求处理失败'))
    }
    return body
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message || error.message || '网络异常，请稍后重试'
    if (status === 401) {
      clearAuth()
      ElMessage.error(message)
      if (!window.location.hash.includes('/login')) {
        window.location.hash = '#/login'
      }
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(new Error(message))
  }
)

export default http
