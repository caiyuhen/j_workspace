<template>
  <div class="metadata-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>元数据管理</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索元数据"
              style="width: 250px"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button @click="handleSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              新增元数据
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计卡片 -->
      <el-row :gutter="20" class="stat-row">
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">12,345</div>
            <div class="stat-label">总元数据项</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">89</div>
            <div class="stat-label">数据源</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">456</div>
            <div class="stat-label">数据表</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-item">
            <div class="stat-value">11,800</div>
            <div class="stat-label">字段</div>
          </div>
        </el-col>
      </el-row>

      <!-- 元数据表格 -->
      <el-table :data="tableData" v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="metaCode" label="元数据编码" width="200" show-overflow-tooltip />
        <el-table-column prop="metaName" label="元数据名称" width="150" />
        <el-table-column prop="metaType" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.metaType)">{{ row.metaType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dataType" label="数据类型" width="100" />
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="ownerId" label="负责人" width="100" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="primary" link @click="handleLineage(row)">血缘</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 20px; justify-content: flex-end"
      />
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="元数据编码">
          <el-input v-model="form.metaCode" placeholder="请输入元数据编码" />
        </el-form-item>
        <el-form-item label="元数据名称">
          <el-input v-model="form.metaName" placeholder="请输入元数据名称" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.metaType" placeholder="请选择类型" style="width: 100%">
            <el-option label="DATABASE" value="DATABASE" />
            <el-option label="TABLE" value="TABLE" />
            <el-option label="COLUMN" value="COLUMN" />
            <el-option label="VIEW" value="VIEW" />
          </el-select>
        </el-form-item>
        <el-form-item label="数据类型">
          <el-input v-model="form.dataType" placeholder="请输入数据类型" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(100)
const dialogVisible = ref(false)
const dialogTitle = ref('新增元数据')
const form = ref({})

const tableData = ref([
  { metaCode: 'tcm_db.patient_info', metaName: '患者信息表', metaType: 'TABLE', dataType: '', description: '存储患者基本信息', ownerId: 'admin' },
  { metaCode: 'tcm_db.patient_info.id', metaName: '患者ID', metaType: 'COLUMN', dataType: 'BIGINT', description: '患者唯一标识', ownerId: 'admin' },
  { metaCode: 'tcm_db.patient_info.name', metaName: '患者姓名', metaType: 'COLUMN', dataType: 'VARCHAR', description: '患者真实姓名', ownerId: 'admin' },
  { metaCode: 'tcm_db.diagnosis_record', metaName: '诊断记录表', metaType: 'TABLE', dataType: '', description: '存储中医诊断记录', ownerId: 'admin' },
  { metaCode: 'tcm_db.prescription', metaName: '处方表', metaType: 'TABLE', dataType: '', description: '存储中药处方信息', ownerId: 'admin' },
])

const getTypeTag = (type) => {
  const map = { 'DATABASE': 'primary', 'TABLE': 'success', 'COLUMN': 'info', 'VIEW': 'warning' }
  return map[type] || ''
}

const handleSearch = () => {
  ElMessage.info('搜索: ' + searchKeyword.value)
}

const handleAdd = () => {
  dialogTitle.value = '新增元数据'
  form.value = {}
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑元数据'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确认删除该元数据?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('删除成功')
  })
}

const handleLineage = (row) => {
  ElMessage.info(`查看 ${row.metaName} 的血缘关系`)
}

const handleSubmit = () => {
  dialogVisible.value = false
  ElMessage.success('保存成功')
}
</script>

<style scoped>
.metadata-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.stat-row {
  margin-bottom: 20px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}
</style>
