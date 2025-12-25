<template>
  <el-card class="architecture-panel">
    <template #header>
      <div class="card-header">
        <span>翻译Agent架构</span>
        <el-button 
          type="text" 
          size="small" 
          @click="loadDefaultConfig"
          style="float: right; padding: 0;"
        >
          加载默认配置
        </el-button>
      </div>
    </template>
    
    <div class="architecture-content">
      <div class="workflow-diagram">
        <!-- 用户输入 -->
        <div class="stage-box input-box">
          <div class="stage-title">用户输入文本</div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 阶段1: Planner -->
        <div class="stage-box" :class="{ active: currentStage === 'planner' }">
          <div class="stage-number">1</div>
          <div class="stage-title">Task Planner</div>
          <div class="stage-config">
            <el-select 
              v-model="modelConfigs.planner.model_type" 
              size="small" 
              style="width: 100%; margin-bottom: 5px;"
              @change="onModelChange('planner')"
            >
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="Qwen" value="qwen" />
              <el-option label="豆包" value="doubao" />
              <el-option label="OpenAI" value="openai" />
              <el-option label="Gemini" value="gemini" />
            </el-select>
            <el-input
              v-model="modelConfigs.planner.api_key"
              type="password"
              size="small"
              placeholder="API Key"
              show-password
              style="width: 100%;"
              @change="onApiKeyChange('planner')"
            />
          </div>
          <div class="stage-desc">语言检测、任务拆分</div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 阶段2-3: 并行翻译 -->
        <div class="parallel-box">
          <div class="stage-box" :class="{ active: currentStage === 'translator_a' }">
            <div class="stage-number">2</div>
            <div class="stage-title">Translator-A</div>
            <div class="stage-config">
              <el-select 
                v-model="modelConfigs.translator_a.model_type" 
                size="small" 
                style="width: 100%; margin-bottom: 5px;"
                @change="onModelChange('translator_a')"
              >
                <el-option label="DeepSeek" value="deepseek" />
                <el-option label="Qwen" value="qwen" />
                <el-option label="豆包" value="doubao" />
                <el-option label="OpenAI" value="openai" />
                <el-option label="Gemini" value="gemini" />
              </el-select>
              <el-input
                v-model="modelConfigs.translator_a.api_key"
                type="password"
                size="small"
                placeholder="API Key"
                show-password
                style="width: 100%;"
                @change="onApiKeyChange('translator_a')"
              />
            </div>
            <div class="stage-desc">主翻译</div>
          </div>
          <div class="stage-box" :class="{ active: currentStage === 'translator_b' }">
            <div class="stage-number">3</div>
            <div class="stage-title">Translator-B</div>
            <div class="stage-config">
              <el-select 
                v-model="modelConfigs.translator_b.model_type" 
                size="small" 
                style="width: 100%; margin-bottom: 5px;"
                @change="onModelChange('translator_b')"
              >
                <el-option label="DeepSeek" value="deepseek" />
                <el-option label="Qwen" value="qwen" />
                <el-option label="豆包" value="doubao" />
                <el-option label="OpenAI" value="openai" />
                <el-option label="Gemini" value="gemini" />
              </el-select>
              <el-input
                v-model="modelConfigs.translator_b.api_key"
                type="password"
                size="small"
                placeholder="API Key"
                show-password
                style="width: 100%;"
                @change="onApiKeyChange('translator_b')"
              />
            </div>
            <div class="stage-desc">对照翻译</div>
          </div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 阶段4: Checker -->
        <div class="stage-box" :class="{ active: currentStage === 'checker' }">
          <div class="stage-number">4</div>
          <div class="stage-title">Checker</div>
          <div class="stage-config">
            <el-select 
              v-model="modelConfigs.checker.model_type" 
              size="small" 
              style="width: 100%; margin-bottom: 5px;"
              @change="onModelChange('checker')"
            >
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="Qwen" value="qwen" />
              <el-option label="豆包" value="doubao" />
              <el-option label="OpenAI" value="openai" />
              <el-option label="Gemini" value="gemini" />
            </el-select>
            <el-input
              v-model="modelConfigs.checker.api_key"
              type="password"
              size="small"
              placeholder="API Key"
              show-password
              style="width: 100%;"
              @change="onApiKeyChange('checker')"
            />
          </div>
          <div class="stage-desc">一致性检查、MQM评分</div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 阶段5: Stylist -->
        <div class="stage-box" :class="{ active: currentStage === 'stylist' }">
          <div class="stage-number">5</div>
          <div class="stage-title">Stylist</div>
          <div class="stage-config">
            <el-select 
              v-model="modelConfigs.stylist.model_type" 
              size="small" 
              style="width: 100%; margin-bottom: 5px;"
              @change="onModelChange('stylist')"
            >
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="Qwen" value="qwen" />
              <el-option label="豆包" value="doubao" />
              <el-option label="OpenAI" value="openai" />
              <el-option label="Gemini" value="gemini" />
            </el-select>
            <el-input
              v-model="modelConfigs.stylist.api_key"
              type="password"
              size="small"
              placeholder="API Key"
              show-password
              style="width: 100%;"
              @change="onApiKeyChange('stylist')"
            />
          </div>
          <div class="stage-desc">术语统一、风格统一</div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 阶段6: Aggregator -->
        <div class="stage-box" :class="{ active: currentStage === 'aggregator' }">
          <div class="stage-number">6</div>
          <div class="stage-title">Aggregator</div>
          <div class="stage-config">
            <el-select 
              v-model="modelConfigs.aggregator.model_type" 
              size="small" 
              style="width: 100%; margin-bottom: 5px;"
              @change="onModelChange('aggregator')"
            >
              <el-option label="DeepSeek" value="deepseek" />
              <el-option label="Qwen" value="qwen" />
              <el-option label="豆包" value="doubao" />
              <el-option label="OpenAI" value="openai" />
              <el-option label="Gemini" value="gemini" />
            </el-select>
            <el-input
              v-model="modelConfigs.aggregator.api_key"
              type="password"
              size="small"
              placeholder="API Key"
              show-password
              style="width: 100%;"
              @change="onApiKeyChange('aggregator')"
            />
          </div>
          <div class="stage-desc">最终整合、生成报告</div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 最终结果 -->
        <div class="stage-box result-box">
          <div class="stage-title">最终翻译结果</div>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup>
import { ref, watch, onMounted, defineExpose } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  currentStage: {
    type: String,
    default: ''
  },
  modelConfig: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelConfigs'])

// localStorage 的 key
const STORAGE_KEY = 'translation_model_configs'

// 默认配置
const defaultConfigs = {
  planner: { model_type: 'deepseek', api_key: '' },
  translator_a: { model_type: 'deepseek', api_key: '' },
  translator_b: { model_type: 'qwen', api_key: '' },
  checker: { model_type: 'deepseek', api_key: '' },
  stylist: { model_type: 'qwen', api_key: '' },
  aggregator: { model_type: 'deepseek', api_key: '' }
}

// 从 localStorage 加载配置
const loadConfigsFromStorage = () => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      // 合并保存的配置和默认配置，确保所有阶段都有配置
      return {
        ...defaultConfigs,
        ...parsed
      }
    }
  } catch (error) {
    console.error('加载保存的配置失败:', error)
    ElMessage.warning('加载保存的配置失败，使用默认配置')
  }
  return defaultConfigs
}

// 保存配置到 localStorage
const saveConfigsToStorage = (configs) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(configs))
    console.log('配置已保存到本地存储')
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  }
}

// 模型配置，每个阶段都有model_type和api_key
const modelConfigs = ref(loadConfigsFromStorage())

// 监听配置变化，通知父组件并保存到本地
const notifyAndSave = () => {
  emit('update:modelConfigs', { ...modelConfigs.value })
  saveConfigsToStorage(modelConfigs.value)
}

// 监听配置变化，通知父组件
const onModelChange = (stage) => {
  notifyAndSave()
}

const onApiKeyChange = (stage) => {
  notifyAndSave()
}

// 监听props变化，更新本地配置（但不覆盖已保存的配置）
watch(() => props.modelConfig, (newConfig) => {
  if (newConfig && Object.keys(newConfig).length > 0) {
    // 如果父组件传入了配置，更新本地配置（但保留已保存的API_KEY）
    Object.keys(modelConfigs.value).forEach(stage => {
      if (newConfig[stage]) {
        // 只更新model_type，保留已有的api_key（如果已保存）
        if (newConfig[stage].model_type) {
          modelConfigs.value[stage].model_type = newConfig[stage].model_type
        }
        // 如果本地没有保存的api_key，才使用传入的
        if (!modelConfigs.value[stage].api_key && newConfig[stage].api_key) {
          modelConfigs.value[stage].api_key = newConfig[stage].api_key
        }
      }
    })
    notifyAndSave()
  }
}, { deep: true })

// 加载默认配置文件
const loadDefaultConfig = async () => {
  try {
    const response = await fetch('/model-config.example.json')
    if (response.ok) {
      const defaultConfig = await response.json()
      // 合并默认配置，保留已有的API_KEY（如果已配置）
      Object.keys(defaultConfig).forEach(stage => {
        if (defaultConfig[stage]) {
          modelConfigs.value[stage].model_type = defaultConfig[stage].model_type || modelConfigs.value[stage].model_type
          // 只有当本地没有配置API_KEY时，才使用默认配置中的（通常是占位符）
          if (!modelConfigs.value[stage].api_key || modelConfigs.value[stage].api_key === '') {
            const defaultKey = defaultConfig[stage].api_key || ''
            // 如果默认配置中的key不是占位符，才使用
            if (defaultKey && !defaultKey.includes('your-') && !defaultKey.includes('here')) {
              modelConfigs.value[stage].api_key = defaultKey
            }
          }
        }
      })
      notifyAndSave()
      ElMessage.success('默认配置已加载')
    } else {
      ElMessage.warning('默认配置文件不存在，请手动配置')
    }
  } catch (error) {
    console.error('加载默认配置失败:', error)
    ElMessage.error('加载默认配置失败，请检查文件是否存在')
  }
}

onMounted(() => {
  // 初始化时通知父组件
  emit('update:modelConfigs', { ...modelConfigs.value })
  
  // 自动加载默认配置
  loadDefaultConfig()
})

// 暴露方法给父组件调用
defineExpose({
  loadDefaultConfig
})
</script>

<style scoped>
.architecture-panel {
  height: 100%;
}

.architecture-content {
  padding: 10px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.workflow-diagram {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.stage-box {
  width: 100%;
  padding: 15px;
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  background-color: #f5f7fa;
  text-align: center;
  transition: all 0.3s;
}

.stage-box.active {
  border-color: #409eff;
  background-color: #ecf5ff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.3);
}

.stage-box.input-box,
.stage-box.result-box {
  background-color: #f0f9ff;
  border-color: #409eff;
}

.stage-number {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 5px;
}

.stage-title {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 8px;
}

.stage-config {
  margin-bottom: 8px;
}

.stage-desc {
  font-size: 11px;
  color: #606266;
  margin-top: 5px;
}

.parallel-box {
  display: flex;
  width: 100%;
  gap: 10px;
}

.parallel-box .stage-box {
  flex: 1;
}

.arrow {
  font-size: 20px;
  color: #409eff;
  font-weight: bold;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}
</style>
