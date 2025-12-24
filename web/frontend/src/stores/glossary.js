import { defineStore } from 'pinia'
import { glossaryAPI } from '../api/glossary'
import { ElMessage } from 'element-plus'

export const useGlossaryStore = defineStore('glossary', {
  state: () => ({
    glossary: {}
  }),
  
  actions: {
    async load() {
      try {
        const response = await glossaryAPI.getGlossary()
        this.glossary = response.glossary || {}
      } catch (error) {
        console.error('加载术语表失败:', error)
      }
    },
    
    async update(glossary) {
      try {
        await glossaryAPI.updateGlossary(glossary)
        this.glossary = glossary
        ElMessage.success('术语表更新成功')
      } catch (error) {
        ElMessage.error('更新术语表失败')
        throw error
      }
    },
    
    async addTerm(term, translation) {
      try {
        await glossaryAPI.updateTerm(term, translation)
        this.glossary[term] = translation
        ElMessage.success('添加术语成功')
      } catch (error) {
        ElMessage.error('添加术语失败')
        throw error
      }
    },
    
    async deleteTerm(term) {
      try {
        await glossaryAPI.deleteTerm(term)
        delete this.glossary[term]
        ElMessage.success('删除术语成功')
      } catch (error) {
        ElMessage.error('删除术语失败')
        throw error
      }
    }
  }
})

