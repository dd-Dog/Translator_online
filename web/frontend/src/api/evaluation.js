import api from './index'

export const evaluationAPI = {
  // 评估翻译结果
  evaluate(source, translation, reference = null) {
    return api.post('/api/v1/evaluation/evaluate', {
      source,
      translation,
      reference
    })
  },
  
  // 获取评估结果
  getEvaluationResult(taskId) {
    return api.get(`/api/v1/evaluation/${taskId}`)
  }
}

