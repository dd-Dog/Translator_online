<template>
  <div class="glossary">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>术语表管理</span>
        </div>
      </template>
      
      <!-- 添加术语 -->
      <el-form :inline="true" class="add-form">
        <el-form-item label="术语">
          <el-input v-model="newTerm.term" placeholder="输入术语" style="width: 200px" />
        </el-form-item>
        <el-form-item label="翻译">
          <el-input v-model="newTerm.translation" placeholder="输入翻译" style="width: 200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleAdd">添加</el-button>
        </el-form-item>
      </el-form>
      
      <el-divider />
      
      <!-- 术语列表 -->
      <el-table :data="glossaryList" style="width: 100%">
        <el-table-column prop="term" label="术语" width="200" />
        <el-table-column prop="translation" label="翻译" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row.term)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-divider />
      
      <!-- 操作按钮 -->
      <el-button @click="handleExport">导出</el-button>
      <el-button @click="handleImport">导入</el-button>
      <el-button type="danger" @click="handleClear">清空</el-button>
    </el-card>
    
    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialog.visible" title="编辑术语" width="400px">
      <el-form>
        <el-form-item label="术语">
          <el-input v-model="editDialog.term" disabled />
        </el-form-item>
        <el-form-item label="翻译">
          <el-input v-model="editDialog.translation" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useGlossaryStore } from '../stores/glossary'
import { ElMessage, ElMessageBox } from 'element-plus'

const glossaryStore = useGlossaryStore()

const newTerm = ref({
  term: '',
  translation: ''
})

const editDialog = ref({
  visible: false,
  term: '',
  translation: ''
})

const glossaryList = computed(() => {
  return Object.entries(glossaryStore.glossary).map(([term, translation]) => ({
    term,
    translation
  }))
})

onMounted(async () => {
  await glossaryStore.load()
})

const handleAdd = async () => {
  if (!newTerm.value.term || !newTerm.value.translation) {
    ElMessage.warning('请填写完整的术语和翻译')
    return
  }
  
  try {
    await glossaryStore.addTerm(newTerm.value.term, newTerm.value.translation)
    newTerm.value = { term: '', translation: '' }
  } catch (error) {
    console.error(error)
  }
}

const handleEdit = (row) => {
  editDialog.value = {
    visible: true,
    term: row.term,
    translation: row.translation
  }
}

const handleSaveEdit = async () => {
  try {
    await glossaryStore.addTerm(editDialog.value.term, editDialog.value.translation)
    editDialog.value.visible = false
  } catch (error) {
    console.error(error)
  }
}

const handleDelete = async (term) => {
  try {
    await ElMessageBox.confirm('确定要删除这个术语吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await glossaryStore.deleteTerm(term)
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}

const handleExport = () => {
  const data = JSON.stringify(glossaryStore.glossary, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'glossary.json'
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('导出成功')
}

const handleImport = () => {
  ElMessage.info('导入功能开发中...')
}

const handleClear = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有术语吗？此操作不可恢复！', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await glossaryStore.update({})
    ElMessage.success('清空成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
    }
  }
}
</script>

<style scoped>
.glossary {
  max-width: 1000px;
  margin: 0 auto;
}

.add-form {
  margin-bottom: 20px;
}
</style>

