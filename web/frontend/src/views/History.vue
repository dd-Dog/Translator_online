<template>
  <div class="history">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>翻译历史</span>
        </div>
      </template>
      
      <!-- 筛选 -->
      <el-form :inline="true" class="filter-form">
        <el-form-item label="源语言">
          <el-select v-model="filters.sourceLang" placeholder="全部" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="英语" value="en" />
            <el-option label="日语" value="ja" />
            <el-option label="法语" value="fr" />
          </el-select>
        </el-form-item>
        <el-form-item label="风格">
          <el-select v-model="filters.style" placeholder="全部" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option
              v-for="style in styles"
              :key="style.id"
              :label="style.name"
              :value="style.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadHistory">查询</el-button>
        </el-form-item>
      </el-form>
      
      <!-- 历史记录列表 -->
      <div class="table-container">
        <el-table :data="historyItems" style="width: 100%">
        <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="source_lang" label="源语言" width="100" />
        <el-table-column prop="style" label="风格" width="120" />
        <el-table-column prop="source_text" label="原文" show-overflow-tooltip />
        <el-table-column prop="translated_text" label="译文" show-overflow-tooltip />
        <el-table-column prop="quality_score" label="评分" width="120">
          <template #default="{ row }">
            <el-tag v-if="hasScore(row)" type="success">
              {{ calculateAverageScore(row).toFixed(2) }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="handleView(row)">详情</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.task_id)">删除</el-button>
          </template>
        </el-table-column>
        </el-table>
      </div>
      
      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next, jumper"
        @current-change="loadHistory"
        style="margin-top: 20px; justify-content: center;"
      />
    </el-card>
    
    <!-- 详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="翻译详情"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="detailData" class="detail-content">
        <!-- 基本信息 -->
        <el-card class="detail-section" shadow="never">
          <template #header>
            <span>基本信息</span>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务ID">{{ detailData.task_id }}</el-descriptions-item>
            <el-descriptions-item label="创建时间">{{ formatDate(detailData.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="源语言">{{ detailData.source_lang }}</el-descriptions-item>
            <el-descriptions-item label="目标语言">{{ detailData.target_lang }}</el-descriptions-item>
            <el-descriptions-item label="风格">{{ detailData.style }}</el-descriptions-item>
            <el-descriptions-item label="评分">
              <el-tag v-if="detailData.quality_score !== null && detailData.quality_score !== undefined" type="success">
                {{ (detailData.quality_score * 100).toFixed(2) }}
              </el-tag>
              <span v-else>-</span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
        
        <!-- 原文和译文 -->
        <el-card class="detail-section" shadow="never">
          <template #header>
            <span>翻译内容</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="text-block">
                <div class="text-label">原文</div>
                <div class="text-content">{{ detailData.source_text }}</div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="text-block">
                <div class="text-label">译文</div>
                <div class="text-content">{{ detailData.translated_text }}</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
        
        <!-- 处理过程 -->
        <el-card v-if="detailData.processing_stages && detailData.processing_stages.length > 0" class="detail-section" shadow="never">
          <template #header>
            <span>处理过程</span>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="(stage, index) in detailData.processing_stages"
              :key="index"
              :timestamp="getStageTimestamp(stage)"
              placement="top"
            >
              <el-card shadow="hover" style="margin-bottom: 10px">
                <template #header>
                  <div style="display: flex; justify-content: space-between; align-items: center">
                    <span style="font-weight: bold">{{ getStageName(stage) }}</span>
                    <el-tag v-if="getStageModel(stage)" type="info" size="small">{{ getStageModel(stage) }}</el-tag>
                  </div>
                </template>
                <div style="margin-bottom: 10px">
                  <div style="font-weight: 500; margin-bottom: 5px; color: #606266">输入：</div>
                  <div style="background: #f5f7fa; padding: 8px; border-radius: 4px; white-space: pre-wrap; word-break: break-word">
                    {{ formatStageInput(stage) }}
                  </div>
                </div>
                <div>
                  <div style="font-weight: 500; margin-bottom: 5px; color: #606266">输出：</div>
                  <div style="background: #ecf5ff; padding: 8px; border-radius: 4px; white-space: pre-wrap; word-break: break-word">
                    {{ formatStageOutput(stage) }}
                  </div>
                </div>
                <div v-if="getStageExtraInfo(stage)" style="margin-top: 10px; font-size: 12px; color: #909399">
                  <div v-for="(value, key) in getStageExtraInfo(stage)" :key="key" style="margin-top: 5px">
                    <span style="font-weight: 500">{{ key }}:</span> {{ formatExtraInfo(value) }}
                  </div>
                </div>
              </el-card>
            </el-timeline-item>
          </el-timeline>
        </el-card>
        
        <!-- 可解释性报告 -->
        <el-card v-if="detailData.explainability_report && Object.keys(detailData.explainability_report).length > 0" class="detail-section" shadow="never">
          <template #header>
            <span>可解释性报告</span>
          </template>
          <div v-if="detailData.explainability_report.modifications && detailData.explainability_report.modifications.length > 0">
            <div class="section-title">修改记录</div>
            <el-table :data="detailData.explainability_report.modifications" style="width: 100%">
              <el-table-column prop="stage" label="阶段" width="120" />
              <el-table-column prop="segment_id" label="段落ID" width="120" />
              <el-table-column prop="reason" label="原因" />
              <el-table-column prop="original" label="原文" show-overflow-tooltip />
              <el-table-column prop="modified" label="修改后" show-overflow-tooltip />
            </el-table>
          </div>
          <div v-if="detailData.explainability_report.quality_improvements && Object.keys(detailData.explainability_report.quality_improvements).length > 0" style="margin-top: 20px">
            <div class="section-title">质量改进</div>
            <el-descriptions :column="2" border>
              <el-descriptions-item
                v-for="(value, key) in detailData.explainability_report.quality_improvements"
                :key="key"
                :label="key"
              >
                {{ value }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
        
        <!-- 评估结果 -->
        <el-card v-if="detailData.evaluation_result && Object.keys(detailData.evaluation_result).length > 0" class="detail-section" shadow="never">
          <template #header>
            <span>评估结果</span>
          </template>
          <div v-if="detailData.evaluation_result.scores">
            <el-descriptions :column="2" border>
              <el-descriptions-item
                v-for="(score, metric) in detailData.evaluation_result.scores"
                :key="metric"
                :label="metric"
              >
                <el-tag type="success">{{ (score * 100).toFixed(2) }}</el-tag>
              </el-descriptions-item>
            </el-descriptions>
            <div v-if="detailData.evaluation_result.overall !== undefined" style="margin-top: 15px">
              <el-divider />
              <div class="overall-score">
                <span class="score-label">总体评分：</span>
                <el-tag type="primary" size="large">{{ (detailData.evaluation_result.overall * 100).toFixed(2) }}</el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { historyAPI } from '../api/history'
import { configAPI } from '../api/config'
import { ElMessage, ElMessageBox } from 'element-plus'

const historyItems = ref([])
const styles = ref([])
const filters = ref({
  sourceLang: '',
  style: ''
})
const pagination = ref({
  page: 1,
  pageSize: 15,
  total: 0
})

onMounted(async () => {
  await loadStyles()
  await loadHistory()
})

const loadStyles = async () => {
  try {
    styles.value = await configAPI.getStyles()
  } catch (error) {
    console.error('加载风格失败:', error)
  }
}

const loadHistory = async () => {
  try {
    console.log('开始加载历史记录...', {
      page: pagination.value.page,
      pageSize: pagination.value.pageSize,
      filters: filters.value
    })
    
    const response = await historyAPI.getHistory({
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      source_lang: filters.value.sourceLang || undefined,
      style: filters.value.style || undefined
    })
    
    console.log('历史记录API响应:', response)
    console.log('响应类型:', typeof response)
    console.log('items类型:', typeof response.items)
    console.log('items数量:', response.items?.length || 0)
    if (response.items && response.items.length > 0) {
      console.log('第一条记录:', response.items[0])
      console.log('第一条记录的quality_score:', response.items[0].quality_score)
      console.log('第一条记录的evaluation_result:', response.items[0].evaluation_result)
    }
    
    if (response && response.items) {
      historyItems.value = response.items
      pagination.value.total = response.total || 0
      console.log('历史记录加载成功:', historyItems.value.length, '条')
    } else {
      console.warn('响应格式异常:', response)
      historyItems.value = []
      pagination.value.total = 0
    }
  } catch (error) {
    ElMessage.error('加载历史记录失败: ' + (error.response?.data?.detail || error.message))
    console.error('加载历史记录错误详情:', error)
    console.error('错误响应:', error.response)
    historyItems.value = []
    pagination.value.total = 0
  }
}

const detailDialogVisible = ref(false)
const detailData = ref(null)

const handleView = async (row) => {
  try {
    const detail = await historyAPI.getHistoryDetail(row.task_id)
    detailData.value = detail
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取详情失败')
    console.error(error)
  }
}

const handleDelete = async (taskId) => {
  try {
    await ElMessageBox.confirm('确定要删除这条历史记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await historyAPI.deleteHistory(taskId)
    ElMessage.success('删除成功')
    await loadHistory()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
      console.error(error)
    }
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) {
      return dateStr
    }
    return date.toLocaleString('zh-CN')
  } catch (e) {
    return String(dateStr)
  }
}

const hasScore = (row) => {
  return (row.quality_score !== null && row.quality_score !== undefined) ||
         (row.evaluation_result && row.evaluation_result.scores && Object.keys(row.evaluation_result.scores).length > 0) ||
         (row.evaluation_result && row.evaluation_result.overall !== undefined)
}

const calculateAverageScore = (row) => {
  // 优先使用quality_score
  if (row.quality_score !== null && row.quality_score !== undefined) {
    return row.quality_score * 100
  }
  
  // 如果有评估结果，计算平均分
  if (row.evaluation_result && row.evaluation_result.scores) {
    const scores = Object.values(row.evaluation_result.scores)
    if (scores.length > 0) {
      const avg = scores.reduce((sum, score) => sum + score, 0) / scores.length
      return avg * 100
    }
  }
  
  // 如果有总体评分
  if (row.evaluation_result && row.evaluation_result.overall !== undefined) {
    return row.evaluation_result.overall * 100
  }
  
  return 0
}

// 处理阶段信息的辅助函数
const getStageName = (stage) => {
  if (typeof stage === 'string') {
    const names = {
      'planner': '任务规划',
      'translator_a': '主翻译',
      'translator_b': '对照翻译',
      'checker': '质量检查',
      'stylist': '风格化',
      'aggregator': '最终整合'
    }
    return names[stage] || stage
  }
  return stage.stage_name || stage.stage || '未知阶段'
}

const getStageModel = (stage) => {
  if (typeof stage === 'object' && stage.model) {
    return stage.model
  }
  return null
}

const getStageTimestamp = (stage) => {
  if (typeof stage === 'object' && stage.timestamp) {
    return formatDate(stage.timestamp)
  }
  return ''
}

const formatStageInput = (stage) => {
  if (typeof stage === 'string') {
    return '-'
  }
  if (typeof stage.input === 'string') {
    return stage.input
  }
  if (typeof stage.input === 'object') {
    if (stage.input.text) {
      return stage.input.text
    }
    if (stage.input.source_text) {
      return `原文: ${stage.input.source_text}${stage.input.draft_a ? '\n主翻译: ' + stage.input.draft_a : ''}${stage.input.draft_b ? '\n对照翻译: ' + stage.input.draft_b : ''}${stage.input.stylist_result ? '\n风格化结果: ' + stage.input.stylist_result : ''}`
    }
    return JSON.stringify(stage.input, null, 2)
  }
  return '-'
}

const formatStageOutput = (stage) => {
  if (typeof stage === 'string') {
    return '-'
  }
  if (typeof stage.output === 'string') {
    return stage.output
  }
  if (typeof stage.output === 'object') {
    return JSON.stringify(stage.output, null, 2)
  }
  return '-'
}

const getStageExtraInfo = (stage) => {
  if (typeof stage !== 'object') {
    return null
  }
  const extra = {}
  if (stage.self_check) {
    extra['自检报告'] = `不确定段落: ${stage.self_check.uncertain_segments || 0}`
  }
  if (stage.report) {
    if (stage.report.quality_scores) {
      extra['质量评分'] = `充分性: ${(stage.report.quality_scores.adequacy * 100).toFixed(2)}, 流畅性: ${(stage.report.quality_scores.fluency * 100).toFixed(2)}, 术语: ${(stage.report.quality_scores.terminology * 100).toFixed(2)}, 总体: ${(stage.report.quality_scores.overall * 100).toFixed(2)}`
    }
    if (stage.report.conflicting_segments_count) {
      extra['冲突段落数'] = stage.report.conflicting_segments_count
    }
  }
  if (stage.changes) {
    if (stage.changes.terminology_changes && stage.changes.terminology_changes.length > 0) {
      extra['术语变更数'] = stage.changes.terminology_changes.length
    }
    if (stage.changes.style_changes_count) {
      extra['风格变更数'] = stage.changes.style_changes_count
    }
  }
  return Object.keys(extra).length > 0 ? extra : null
}

const formatExtraInfo = (value) => {
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return value
}
</script>

<style scoped>
.history {
  max-width: 1400px;
  margin: 0 auto;
}

.filter-form {
  margin-bottom: 20px;
}

.table-container {
  max-height: calc(100vh - 350px);
  overflow-y: auto;
  overflow-x: auto;
}

.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 20px;
}

.text-block {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  min-height: 150px;
}

.text-label {
  font-weight: bold;
  margin-bottom: 10px;
  color: #606266;
}

.text-content {
  line-height: 1.8;
  color: #303133;
  white-space: pre-wrap;
  word-break: break-word;
}

.section-title {
  font-weight: bold;
  margin-bottom: 10px;
  color: #303133;
}

.overall-score {
  text-align: center;
  padding: 15px;
  background-color: #f0f9ff;
  border-radius: 4px;
}

.score-label {
  font-size: 16px;
  font-weight: bold;
  margin-right: 10px;
  color: #303133;
}
</style>

