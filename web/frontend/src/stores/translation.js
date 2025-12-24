import { defineStore } from 'pinia'
import { translateAPI } from '../api/translate'
import { WebSocketClient } from '../api/websocket'
import { ElMessage } from 'element-plus'

export const useTranslationStore = defineStore('translation', {
  state: () => ({
    currentTask: null,
    result: null,
    progress: 0,
    currentStage: '',
    status: 'idle', // idle, processing, completed, error
    wsClient: null,
    translationLogs: [], // 翻译过程日志
    sourceText: '', // 保存原文用于评估
    stageResults: {} // 各阶段的翻译结果 {stage: translated_text}
  }),
  
  actions: {
    async translate(text, options = {}) {
      try {
        this.status = 'processing'
        this.progress = 0
        this.currentStage = '创建任务...'
        this.sourceText = text
        this.translationLogs = []
        this.stageResults = {} // 重置阶段结果
        
        // 添加初始日志
        this.addLog('info', '系统', '开始翻译任务...')
        
        // 创建翻译任务
        const response = await translateAPI.createTask({
          text,
          source_lang: options.sourceLang || 'auto',
          target_lang: options.targetLang || 'zh',
          style: options.style || 'general',
          glossary: options.glossary || {},
          stream: true
        })
        
        this.currentTask = response.task_id
        this.addLog('success', '系统', '翻译任务已创建')
        
        // 建立WebSocket连接（在任务开始前建立，确保不遗漏消息）
        const wsUrl = `ws://localhost:8000/ws/translate/${response.task_id}`
        this.wsClient = new WebSocketClient(wsUrl)
        
        // 添加调试日志
        console.log('正在建立WebSocket连接:', wsUrl)
        
        // 监听所有消息（用于调试）
        this.wsClient.on('*', (data) => {
          console.log('收到WebSocket消息:', data)
        })
        
        // 监听连接确认
        this.wsClient.on('connected', (data) => {
          console.log('WebSocket连接已确认:', data)
          this.addLog('info', '系统', 'WebSocket连接已建立')
        })
        
        // 监听进度消息
        this.wsClient.on('progress', (data) => {
          console.log('收到进度消息:', data)
          const { data: progressData } = data
          this.progress = progressData.progress || 0
          const stage = progressData.stage || ''
          this.currentStage = stage
          
          // 添加过程日志
          if (stage) {
            const stageNames = {
              planner: '任务规划',
              translator_a: '主翻译',
              translator_b: '对照翻译',
              checker: '质量检查',
              stylist: '风格化',
              aggregator: '最终整合',
              starting: '系统'
            }
            this.addLog('info', stageNames[stage] || stage, progressData.message || '处理中...')
          } else if (progressData.message) {
            this.addLog('info', '系统', progressData.message)
          }
        })
        
        // 监听阶段结果消息
        this.wsClient.on('stage_result', (data) => {
          console.log('收到阶段结果消息:', data)
          const { data: stageData } = data
          const stage = stageData.stage
          const translatedText = stageData.translated_text
          
          // 保存阶段结果
          this.stageResults[stage] = translatedText
          
          // 更新进度
          this.progress = stageData.progress || this.progress
          
          // 添加成功日志
          this.addLog('success', stageData.stage_name || stage, '完成', translatedText)
        })
        
        this.wsClient.on('completed', async (data) => {
          this.status = 'completed'
          this.progress = 100
          this.addLog('success', '系统', '翻译完成')
          // 获取最终结果
          await this.fetchResult()
          this.wsClient?.close()
        })
        
        this.wsClient.on('error', (data) => {
          this.status = 'error'
          this.addLog('error', '系统', data.data?.message || '翻译失败')
          ElMessage.error(data.data?.message || '翻译失败')
          this.wsClient?.close()
        })
        
        // 连接WebSocket
        await this.wsClient.connect()
        
        // 轮询获取结果（作为WebSocket的备用）
        this.pollResult()
        
      } catch (error) {
        this.status = 'error'
        this.addLog('error', '系统', '创建翻译任务失败')
        ElMessage.error('创建翻译任务失败')
        console.error(error)
      }
    },
    
    addLog(type, stage, message, translatedText = null) {
      const now = new Date()
      const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
      this.translationLogs.push({
        type,
        stage,
        message,
        time,
        translatedText // 添加翻译结果
      })
    },
    
    async fetchResult() {
      if (!this.currentTask) return
      
      try {
        const response = await translateAPI.getResult(this.currentTask)
        if (response.status === 'completed') {
          this.result = response.result
          this.status = 'completed'
        } else if (response.status === 'failed') {
          this.status = 'error'
          ElMessage.error(response.error || '翻译失败')
        }
      } catch (error) {
        console.error('获取翻译结果失败:', error)
      }
    },
    
    pollResult() {
      const interval = setInterval(async () => {
        if (this.status === 'completed' || this.status === 'error') {
          clearInterval(interval)
          return
        }
        await this.fetchResult()
      }, 2000) // 每2秒轮询一次
    },
    
    reset() {
      this.currentTask = null
      this.result = null
      this.progress = 0
      this.currentStage = ''
      this.status = 'idle'
      this.translationLogs = []
      this.sourceText = ''
      this.stageResults = {}
      if (this.wsClient) {
        this.wsClient.close()
        this.wsClient = null
      }
    }
  }
})

