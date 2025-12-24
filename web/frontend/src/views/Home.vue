<template>
  <div class="home-container">
    <el-row :gutter="20" class="home-layout">
      <!-- 左侧：架构面板 -->
      <el-col :span="6" class="left-panel">
        <ArchitecturePanel 
          :current-stage="translationStore.currentStage" 
          :model-config="modelConfig"
          @update:modelConfigs="handleModelConfigsUpdate"
        />
      </el-col>
      
      <!-- 中间：翻译功能区域 -->
      <el-col :span="10" class="center-panel">
        <el-card class="translation-card">
          <template #header>
            <div class="card-header">
              <span>文本翻译</span>
            </div>
          </template>
          
          <!-- 翻译表单 -->
          <el-form :model="form" label-width="100px" size="default">
            <el-form-item label="源语言">
              <el-autocomplete
                v-model="form.sourceLang"
                :fetch-suggestions="queryLanguage"
                placeholder="输入语言（支持简写/全称/中文，如：en/english/英语）"
                style="width: 100%"
                clearable
                @select="handleLanguageSelect"
              >
                <template #default="{ item }">
                  <div class="language-option">
                    <span class="language-code">{{ item.code }}</span>
                    <span class="language-name">{{ item.name }}</span>
                    <span class="language-english">{{ item.english }}</span>
                  </div>
                </template>
              </el-autocomplete>
            </el-form-item>
            
            <el-form-item label="目标语言">
              <el-select v-model="form.targetLang" style="width: 100%">
                <el-option label="中文" value="zh" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="翻译风格">
              <el-select v-model="form.style" style="width: 100%">
                <el-option
                  v-for="style in styles"
                  :key="style.id"
                  :label="style.name"
                  :value="style.id"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="待翻译文本">
              <el-input
                v-model="form.text"
                type="textarea"
                :rows="6"
                placeholder="请输入要翻译的文本..."
                :maxlength="10000"
                show-word-limit
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                @click="handleTranslate"
                :loading="translationStore.status === 'processing'"
                :disabled="!form.text.trim()"
                size="default"
              >
                开始翻译
              </el-button>
              <el-button @click="handleReset" size="default">重置</el-button>
            </el-form-item>
          </el-form>
          
          <!-- 进度显示 -->
          <div v-if="translationStore.status === 'processing'" class="progress-section">
            <el-progress
              :percentage="translationStore.progress"
              :status="translationStore.status === 'error' ? 'exception' : undefined"
            />
            <p class="progress-text">{{ translationStore.currentStage }}</p>
          </div>
          
          <!-- 翻译结果 -->
          <div v-if="translationStore.result" class="result-section">
            <el-divider>翻译结果</el-divider>
            <div class="result-text">
              {{ translationStore.result.translated_text }}
            </div>
            
            <div class="result-actions">
              <el-button @click="handleCopy" size="small">复制译文</el-button>
              <el-button
                @click="handleEvaluate"
                :loading="evaluationStore.isEvaluating"
                size="small"
                type="success"
              >
                开始评估
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧：过程面板 -->
      <el-col :span="8" class="right-panel">
        <ProcessPanel
          :model-config="modelConfig"
          :translation-logs="translationStore.translationLogs"
          :evaluation-logs="evaluationStore.evaluationLogs"
          :is-evaluating="evaluationStore.isEvaluating"
          :evaluation-result="evaluationStore.evaluationResult"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useTranslationStore } from '../stores/translation'
import { useEvaluationStore } from '../stores/evaluation'
import { configAPI } from '../api/config'
import { ElMessage } from 'element-plus'
import ArchitecturePanel from '../components/ArchitecturePanel.vue'
import ProcessPanel from '../components/ProcessPanel.vue'
import { recognizeLanguage, getSupportedLanguages } from '../utils/languageMapper'

const translationStore = useTranslationStore()
const evaluationStore = useEvaluationStore()

const form = ref({
  text: '',
  sourceLang: 'auto',
  targetLang: 'zh',
  style: 'general'
})

const styles = ref([])
const modelConfig = ref({})
const currentModelConfigs = ref({})  // 当前用户配置的模型和API_KEY

onMounted(async () => {
  // 加载翻译风格
  try {
    styles.value = await configAPI.getStyles()
  } catch (error) {
    console.error('加载风格失败:', error)
  }
  
  // 加载模型配置
  try {
    const config = await configAPI.getModels()
    modelConfig.value = config.models || {}
  } catch (error) {
    console.error('加载模型配置失败:', error)
  }
})

onUnmounted(() => {
  translationStore.reset()
  evaluationStore.reset()
})

const handleModelConfigsUpdate = (configs) => {
  currentModelConfigs.value = configs
}

// 语言自动完成
const supportedLanguages = getSupportedLanguages()

const queryLanguage = (queryString, cb) => {
  const results = queryString
    ? supportedLanguages.filter(lang => 
        lang.code.toLowerCase().includes(queryString.toLowerCase()) ||
        lang.name.includes(queryString) ||
        lang.english.toLowerCase().includes(queryString.toLowerCase())
      )
    : supportedLanguages
  
  // 如果用户输入的是自定义文本，也添加到结果中
  if (queryString && queryString.trim() && !results.find(l => l.code === recognizeLanguage(queryString))) {
    const recognized = recognizeLanguage(queryString)
    if (recognized !== queryString.trim()) {
      // 如果能识别，添加到结果中
      const matched = supportedLanguages.find(l => l.code === recognized)
      if (matched && !results.find(l => l.code === recognized)) {
        results.unshift(matched)
      }
    }
  }
  
  cb(results)
}

const handleLanguageSelect = (item) => {
  form.value.sourceLang = item.code
}

const handleTranslate = async () => {
  if (!form.value.text.trim()) {
    ElMessage.warning('请输入要翻译的文本')
    return
  }
  
  // 识别并规范化源语言
  const recognizedLang = recognizeLanguage(form.value.sourceLang)
  if (recognizedLang !== form.value.sourceLang) {
    form.value.sourceLang = recognizedLang
  }
  
  // 检查是否所有阶段都配置了API_KEY
  const missingKeys = []
  Object.keys(currentModelConfigs.value).forEach(stage => {
    if (!currentModelConfigs.value[stage].api_key) {
      missingKeys.push(stage)
    }
  })
  
  if (missingKeys.length > 0) {
    ElMessage.warning(`请为以下阶段配置API_KEY: ${missingKeys.join(', ')}`)
    return
  }
  
  await translationStore.translate(form.value.text, {
    sourceLang: form.value.sourceLang,
    targetLang: form.value.targetLang,
    style: form.value.style,
    modelConfigs: currentModelConfigs.value
  })
}

const handleReset = () => {
  form.value.text = ''
  translationStore.reset()
  evaluationStore.reset()
}

const handleCopy = () => {
  if (translationStore.result) {
    navigator.clipboard.writeText(translationStore.result.translated_text)
    ElMessage.success('已复制到剪贴板')
  }
}

const handleEvaluate = async () => {
  if (!translationStore.result || !translationStore.sourceText) {
    ElMessage.warning('请先完成翻译')
    return
  }
  
  await evaluationStore.evaluate(
    translationStore.sourceText,
    translationStore.result.translated_text
  )
  
  // 如果评估完成且有结果，保存到历史记录
  if (translationStore.currentTask && evaluationStore.evaluationResult) {
    try {
      const { historyAPI } = await import('../api/history')
      await historyAPI.updateEvaluation(translationStore.currentTask, evaluationStore.evaluationResult)
    } catch (error) {
      console.error('保存评估结果失败:', error)
    }
  }
}
</script>

<style scoped>
.home-container {
  height: calc(100vh - 120px);
  padding: 0;
}

.home-layout {
  height: 100%;
}

.left-panel,
.center-panel,
.right-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.translation-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.translation-card :deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.progress-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.progress-text {
  margin-top: 10px;
  text-align: center;
  color: #606266;
  font-size: 13px;
}

.result-section {
  margin-top: 20px;
  flex: 1;
}

.result-text {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  line-height: 1.8;
  font-size: 14px;
  min-height: 80px;
  max-height: 300px;
  overflow-y: auto;
}

.quality-score {
  margin-top: 15px;
}

.score-item {
  text-align: center;
  margin-bottom: 15px;
}

.score-label {
  margin-bottom: 8px;
  font-weight: 500;
  color: #606266;
  font-size: 13px;
}

.result-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}

/* 确保面板高度一致 */
:deep(.el-card) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

:deep(.el-card__body) {
  flex: 1;
  overflow-y: auto;
}

.language-option {
  display: flex;
  gap: 10px;
  align-items: center;
}

.language-code {
  font-weight: bold;
  color: #409eff;
  min-width: 40px;
}

.language-name {
  flex: 1;
  color: #303133;
}

.language-english {
  color: #909399;
  font-size: 12px;
}
</style>
