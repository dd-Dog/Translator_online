<template>
  <el-card class="architecture-panel">
    <template #header>
      <div class="card-header">
        <span>翻译Agent架构</span>
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
          <div class="stage-model">{{ getModelName('planner') }}</div>
          <div class="stage-desc">语言检测、任务拆分</div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 阶段2-3: 并行翻译 -->
        <div class="parallel-box">
          <div class="stage-box" :class="{ active: currentStage === 'translator_a' }">
            <div class="stage-number">2</div>
            <div class="stage-title">Translator-A</div>
            <div class="stage-model">{{ getModelName('translator_a') }}</div>
            <div class="stage-desc">主翻译</div>
          </div>
          <div class="stage-box" :class="{ active: currentStage === 'translator_b' }">
            <div class="stage-number">3</div>
            <div class="stage-title">Translator-B</div>
            <div class="stage-model">{{ getModelName('translator_b') }}</div>
            <div class="stage-desc">对照翻译</div>
          </div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 阶段4: Checker -->
        <div class="stage-box" :class="{ active: currentStage === 'checker' }">
          <div class="stage-number">4</div>
          <div class="stage-title">Checker</div>
          <div class="stage-model">{{ getModelName('checker') }}</div>
          <div class="stage-desc">一致性检查、MQM评分</div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 阶段5: Stylist -->
        <div class="stage-box" :class="{ active: currentStage === 'stylist' }">
          <div class="stage-number">5</div>
          <div class="stage-title">Stylist</div>
          <div class="stage-model">{{ getModelName('stylist') }}</div>
          <div class="stage-desc">术语统一、风格统一</div>
        </div>
        
        <div class="arrow">↓</div>
        
        <!-- 阶段6: Aggregator -->
        <div class="stage-box" :class="{ active: currentStage === 'aggregator' }">
          <div class="stage-number">6</div>
          <div class="stage-title">Aggregator</div>
          <div class="stage-model">{{ getModelName('aggregator') }}</div>
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

const getModelName = (agent) => {
  const model = props.modelConfig[agent]
  if (model) {
    // 简化模型名称显示
    const modelLower = model.toLowerCase()
    if (modelLower.includes('deepseek')) return 'DeepSeek'
    if (modelLower.includes('qwen')) return 'Qwen'
    if (modelLower.includes('gpt')) return 'GPT'
    if (modelLower.includes('claude')) return 'Claude'
    if (modelLower.includes('gemini')) return 'Gemini'
    return model.split('/').pop() || model
  }
  return '未配置'
}
</script>

<style scoped>
.architecture-panel {
  height: 100%;
}

.architecture-content {
  padding: 10px;
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
  margin-bottom: 5px;
}

.stage-model {
  font-size: 12px;
  color: #909399;
  margin-bottom: 3px;
}

.stage-desc {
  font-size: 11px;
  color: #606266;
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

