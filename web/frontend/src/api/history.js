import api from './index'

export const historyAPI = {
  // 获取历史记录
  getHistory(params) {
    return api.get('/api/v1/history', { params })
  },
  
  // 获取历史记录详情
  getHistoryDetail(taskId) {
    return api.get(`/api/v1/history/${taskId}`)
  },
  
  // 更新评估结果
  updateEvaluation(taskId, evaluationResult) {
    return api.put(`/api/v1/history/${taskId}/evaluation`, evaluationResult)
  },
  
  // 删除历史记录
  deleteHistory(taskId) {
    return api.delete(`/api/v1/history/${taskId}`)
  }
}

