<template>
  <div class="management-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>资产管理</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索资产"
              style="width: 250px"
              clearable
            />
            <el-button type="primary" @click="handleAdd">
              <el-icon><Plus /></el-icon>
              新增资产
            </el-button>
          </div>
        </div>
      </template>

      <!-- 资产统计 -->
      <el-row :gutter="20" class="stat-row">
        <el-col :span="6">
          <el-statistic title="总数据资产" :value="1234" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="已发布" :value="856" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="待审核" :value="45" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="本月新增" :value="128" />
        </el-col>
      </el-row>

      <!-- 资产表格 -->
      <el-table :data="assetList" style="margin-top: 20px">
        <el-table-column prop="assetCode" label="资产编码" width="150" />
        <el-table-column prop="assetName" label="资产名称" width="200" show-overflow-tooltip />
        <el-table-column prop="assetType" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.assetType)">{{ row.assetType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assetStatus" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.assetStatus)">{{ getStatusText(row.assetStatus) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="dataSize" label="数据大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.dataSize) }}
          </template>
        </el-table-column>
        <el-table-column prop="recordCount" label="记录数" width="100" />
        <el-table-column prop="qualityScore" label="质量评分" width="120">
          <template #default="{ row }">
            <el-progress :percentage="row.qualityScore" :color="colors" />
          </template>
        </el-table-column>
        <el-table-column prop="price" label="价格" width="100">
          <template #default="{ row }">
            ¥{{ row.price }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="primary" link @click="handlePublish(row)">发布</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const searchKeyword = ref('')

const assetList = ref([
  { assetCode: 'ASSET-001', assetName: '中医门诊电子病历数据集', assetType: 'DATASET', assetStatus: 'PUBLISHED', dataSize: 1024000000, recordCount: 500000, qualityScore: 95, price: 5000 },
  { assetCode: 'ASSET-002', assetName: '中药饮片质量检验数据', assetType: 'DATASET', assetStatus: 'PUBLISHED', dataSize: 512000000, recordCount: 200000, qualityScore: 92, price: 3000 },
  { assetCode: 'ASSET-003', assetName: '名老中医医案数据集', assetType: 'DATASET', assetStatus: 'DRAFT', dataSize: 256000000, recordCount: 100000, qualityScore: 88, price: 8000 },
  { assetCode: 'ASSET-004', assetName: '中医体质辨识API', assetType: 'API', assetStatus: 'PUBLISHED', dataSize: 0, recordCount: 0, qualityScore: 90, price: 2000 },
])

const colors = [
  { color: '#f56c6c', percentage: 60 },
  { color: '#e6a23c', percentage: 80 },
  { color: '#67c23a', percentage: 100 }
]

const getTypeTag = (type) => {
  const map = { 'DATASET': 'primary', 'API': 'success', 'REPORT': 'warning', 'MODEL': 'danger' }
  return map[type] || ''
}

const getStatusTag = (status) => {
  const map = { 'DRAFT': 'info', 'PUBLISHED': 'success', 'OFFLINE': 'danger' }
  return map[status] || ''
}

const getStatusText = (status) => {
  const map = { 'DRAFT': '草稿', 'PUBLISHED': '已发布', 'OFFLINE': '已下线' }
  return map[status] || status
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const handleAdd = () => {
  ElMessage.info('新增资产')
}

const handleEdit = (row) => {
  ElMessage.info('编辑资产: ' + row.assetName)
}

const handlePublish = (row) => {
  ElMessage.success('发布资产: ' + row.assetName)
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确认删除该资产?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('删除成功')
  })
}
</script>

<style scoped>
.management-page {
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
</style>
