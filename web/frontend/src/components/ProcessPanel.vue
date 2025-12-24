<template>
  <el-card class="process-panel">
    <template #header>
      <div class="card-header">
        <span>实时过程</span>
      </div>
    </template>
    
    <el-collapse v-model="activeCollapse">
      <!-- 翻译过程 -->
      <el-collapse-item title="翻译过程" name="translation">
        <div class="process-log">
          <div
            v-for="(log, index) in translationLogs"
            :key="index"
            class="log-item"
            :class="log.type"
          >
            <div class="log-time">{{ log.time }}</div>
            <div class="log-content">
              <el-tag :type="getLogType(log.type)" size="small">{{ log.stage }}</el-tag>
              <span class="log-message">{{ log.message }}</span>
            </div>
            <!-- 显示翻译结果 -->
            <div v-if="log.translatedText" class="log-translation">
              <div class="translation-label">翻译结果：</div>
              <div class="translation-text">{{ log.translatedText }}</div>
            </div>
          </div>
          <div v-if="translationLogs.length === 0" class="empty-log">
            暂无翻译过程记录
          </div>
        </div>
      </el-collapse-item>
      
      <!-- 评估过程 -->
      <el-collapse-item title="评估过程" name="evaluation">
        <div class="process-log">
          <!-- 评估进行中 -->
          <div v-if="isEvaluating" class="log-item info">
            <div class="log-content">
              <el-tag size="small">评估中</el-tag>
              <span class="log-message">正在评估...</span>
            </div>
          </div>
          
          <!-- 评估结果 -->
          <div v-if="evaluationResult && !isEvaluating" class="evaluation-result">
            <div class="result-title">评估结果</div>
            <div v-for="(score, metric) in evaluationResult.scores" :key="metric" class="score-row">
              <span class="metric-name">{{ metric }}:</span>
              <el-tag type="success" size="small">{{ (score * 100).toFixed(2) }}</el-tag>
            </div>
            <div v-if="evaluationResult.overall !== undefined" class="overall-score">
              <span class="metric-name">总体评分:</span>
              <el-tag type="primary" size="small">{{ (evaluationResult.overall * 100).toFixed(2) }}</el-tag>
            </div>
          </div>
          
          <div v-if="!isEvaluating && !evaluationResult && evaluationLogs.length === 0" class="empty-log">
            暂无评估记录
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelConfig: {
    type: Object,
    default: () => ({})
  },
  translationLogs: {
    type: Array,
    default: () => []
  },
  evaluationLogs: {
    type: Array,
    default: () => []
  },
  isEvaluating: {
    type: Boolean,
    default: false
  },
  evaluationResult: {
    type: Object,
    default: null
  }
})

const activeCollapse = ref(['translation', 'evaluation'])

const getAgentName = (agent) => {
  const names = {
    planner: '任务规划',
    translator_a: '主翻译',
    translator_b: '对照翻译',
    checker: '质量检查',
    stylist: '风格化',
    aggregator: '最终整合'
  }
  return names[agent] || agent
}

const getModelStatus = (model) => {
  // 这里可以根据实际状态返回
  return 'available'
}

const getLogType = (type) => {
  const types = {
    info: '',
    success: 'success',
    warning: 'warning',
    error: 'danger'
  }
  return types[type] || ''
}
</script>

<style scoped>
.process-panel {
  height: 100%;
}

.model-config {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.model-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.agent-name {
  font-weight: 500;
  color: #606266;
}

.process-log {
  max-height: 400px;
  overflow-y: auto;
}

.log-item {
  padding: 10px;
  margin-bottom: 8px;
  border-left: 3px solid #e4e7ed;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.log-item.success {
  border-left-color: #67c23a;
  background-color: #f0f9ff;
}

.log-item.warning {
  border-left-color: #e6a23c;
  background-color: #fdf6ec;
}

.log-item.error {
  border-left-color: #f56c6c;
  background-color: #fef0f0;
}

.log-time {
  font-size: 11px;
  color: #909399;
  margin-bottom: 5px;
}

.log-content {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 5px;
}

.log-message {
  flex: 1;
  font-size: 13px;
  color: #606266;
}

.log-translation {
  margin-top: 10px;
  padding: 10px;
  background-color: #ffffff;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
}

.translation-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
  font-weight: 500;
}

.translation-text {
  font-size: 13px;
  color: #303133;
  line-height: 1.6;
  word-break: break-word;
}

.evaluation-result {
  padding: 15px;
  background-color: #f0f9ff;
  border-radius: 4px;
  border: 1px solid #b3d8ff;
}

.result-title {
  font-size: 14px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.score-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #e4e7ed;
}

.score-row:last-child {
  border-bottom: none;
}

.metric-name {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

.overall-score {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  margin-top: 10px;
  border-top: 2px solid #409eff;
  font-weight: bold;
}

.empty-log {
  text-align: center;
  color: #909399;
  padding: 20px;
  font-size: 13px;
}

.card-header {
  font-weight: bold;
  font-size: 16px;
}
</style>

