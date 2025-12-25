import axios from 'axios'

// API baseURL 规则：
// - 生产环境：使用同源相对路径 /api（走 nginx）
// - 开发环境：localhost:8000
const getApiBaseURL = () => {
  // 显式环境变量优先（给 dev / docker 用）
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }

  const host = window.location.hostname

  // 生产环境（非 localhost）
  if (host !== 'localhost' && host !== '127.0.0.1') {
    // ★关键：必须是相对路径
    return '/api'
  }

  // 本地开发
  return 'http://localhost:8000'
}

const api = axios.create({
  baseURL: getApiBaseURL(),
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token（可选）
const token = import.meta.env.VITE_SHARED_TOKEN
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// 请求拦截器
api.interceptors.request.use(
  config => config,
  error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  response => response.data,
  error => {
    setTimeout(() => {
      if (error.response) {
        console.error(
          `API错误 [${error.response.status}]:`,
          error.response.data?.detail || '请求失败'
        )
      } else {
        console.error('网络错误:', error.message)
      }
    }, 0)
    return Promise.reject(error)
  }
)

export default api
