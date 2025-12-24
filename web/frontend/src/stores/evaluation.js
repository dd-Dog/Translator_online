import { defineStore } from 'pinia'
import { evaluationAPI } from '../api/evaluation'
import { ElMessage } from 'element-plus'

export const useEvaluationStore = defineStore('evaluation', {
  state: () => ({
    evaluationLogs: [],
    evaluationResult: null,
    isEvaluating: false
  }),
  
  actions: {
    async evaluate(source, translation, reference = null) {
      try {
        this.isEvaluating = true
        this.evaluationLogs = []
        this.evaluationResult = null
        
        // 调用评估API
        const response = await evaluationAPI.evaluate(source, translation, reference)
        
        // 处理评估结果
        if (response.scores && Object.keys(response.scores).length > 0) {
          this.evaluationResult = {
            scores: response.scores,
            overall: response.overall || 0.0
          }
        } else if (response.error) {
          ElMessage.warning(response.message || '评估失败')
        }
        
        this.isEvaluating = false
        
      } catch (error) {
        this.isEvaluating = false
        ElMessage.error('评估失败')
        console.error(error)
      }
    },
    
    addLog(type, metric, message, score = undefined) {
      const now = new Date()
      const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
      this.evaluationLogs.push({
        type,
        metric,
        message,
        score,
        time
      })
    },
    
    reset() {
      this.evaluationLogs = []
      this.evaluationResult = null
      this.isEvaluating = false
    }
  }
})

