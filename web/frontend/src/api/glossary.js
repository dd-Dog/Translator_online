import api from './index'

export const glossaryAPI = {
  // 获取术语表
  getGlossary() {
    return api.get('/api/v1/glossary')
  },
  
  // 更新术语表
  updateGlossary(glossary) {
    return api.post('/api/v1/glossary', { glossary })
  },
  
  // 更新单个术语
  updateTerm(term, translation) {
    return api.put(`/api/v1/glossary/${term}`, { term, translation })
  },
  
  // 删除术语
  deleteTerm(term) {
    return api.delete(`/api/v1/glossary/${term}`)
  }
}

