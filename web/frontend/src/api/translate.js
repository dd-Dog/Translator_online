import api from './index'

export const translateAPI = {
  // 创建翻译任务
  createTask(data) {
    return api.post('/api/v1/translate', data)
  },
  
  // 获取翻译结果
  getResult(taskId) {
    return api.get(`/api/v1/translate/${taskId}`)
  },
  
  // 获取任务状态
  getStatus(taskId) {
    return api.get(`/api/v1/translate/${taskId}/status`)
  }
}

