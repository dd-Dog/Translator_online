import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 添加Token（如果配置了）
const token = import.meta.env.VITE_SHARED_TOKEN
if (token) {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`
}

// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 使用setTimeout避免在拦截器中直接使用ElMessage
    setTimeout(() => {
      if (error.response) {
        const { status, data } = error.response
        console.error(`API错误 [${status}]:`, data.detail || '请求失败')
      } else {
        console.error('网络错误:', error.message)
      }
    }, 0)
    return Promise.reject(error)
  }
)

export default api

