import api from './index'

export const configAPI = {
  // 获取翻译风格列表
  getStyles() {
    return api.get('/api/v1/config/styles')
  },
  
  // 获取模型配置
  getModels() {
    return api.get('/api/v1/config/models')
  }
}

