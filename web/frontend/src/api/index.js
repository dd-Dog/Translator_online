import axios from 'axios'

// 自动检测API地址
// 开发环境：使用localhost
// 生产环境：使用当前域名（同源）或环境变量配置
const getApiBaseURL = () => {
  // 优先使用环境变量
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  
  // 如果是生产环境（非localhost），使用当前域名
  const currentHost = window.location.hostname
  const currentPort = window.location.port
  if (currentHost !== 'localhost' && currentHost !== '127.0.0.1') {
    // 使用当前协议和域名，端口8000（或从环境变量读取）
    const apiPort = import.meta.env.VITE_API_PORT || '8000'
    return `${window.location.protocol}//${currentHost}:${apiPort}`
  }
  
  // 默认开发环境
  return 'http://localhost:8000'
}

const api = axios.create({
  baseURL: getApiBaseURL(),
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

