<template>
  <div class="catalog-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>资产目录</span>
          <el-input
            v-model="searchKeyword"
            placeholder="搜索资产"
            style="width: 300px"
            clearable
          >
            <template #append>
              <el-button>
                <el-icon><Search /></el-icon>
              </el-button>
            </template>
          </el-input>
        </div>
      </template>

      <el-row :gutter="20">
        <!-- 左侧目录树 -->
        <el-col :span="6">
          <el-tree
            :data="catalogTree"
            :props="{ label: 'catalogName', children: 'children' }"
            @node-click="handleNodeClick"
            highlight-current
            default-expand-all
          />
        </el-col>

        <!-- 右侧资产列表 -->
        <el-col :span="18">
          <el-table :data="assetList">
            <el-table-column prop="assetName" label="资产名称" show-overflow-tooltip />
            <el-table-column prop="assetType" label="类型" width="100">
              <template #default="{ row }">
                <el-tag :type="getTypeTag(row.assetType)">{{ row.assetType }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" show-overflow-tooltip />
            <el-table-column prop="qualityScore" label="质量评分" width="100">
              <template #default="{ row }">
                <el-progress :percentage="row.qualityScore" :color="colors" />
              </template>
            </el-table-column>
            <el-table-column prop="ownerId" label="负责人" width="100" />
            <el-table-column label="操作" width="150">
              <template #default="{ row }">
                <el-button type="primary" link @click="handleView(row)">查看</el-button>
                <el-button type="primary" link @click="handleApply(row)">申请</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const searchKeyword = ref('')

const catalogTree = ref([
  {
    catalogName: '临床诊疗域',
    children: [
      { catalogName: '门诊记录' },
      { catalogName: '住院记录' },
      { catalogName: '四诊信息' },
      { catalogName: '处方医嘱' }
    ]
  },
  {
    catalogName: '药材资源域',
    children: [
      { catalogName: '药材基原' },
      { catalogName: '种植信息' },
      { catalogName: '质量检验' }
    ]
  },
  {
    catalogName: '名医经验域',
    children: [
      { catalogName: '医案文献' },
      { catalogName: '跟师记录' },
      { catalogName: '传承谱系' }
    ]
  }
])

const assetList = ref([
  { assetName: '中医门诊电子病历数据集', assetType: 'DATASET', description: '标准化中医门诊电子病历数据', qualityScore: 95, ownerId: 'admin' },
  { assetName: '中药饮片质量检验数据', assetType: 'DATASET', description: '中药饮片质量检验标准数据', qualityScore: 92, ownerId: 'admin' },
  { assetName: '名老中医医案数据集', assetType: 'DATASET', description: '名老中医经典医案结构化数据', qualityScore: 88, ownerId: 'admin' },
  { assetName: '中医体质辨识API', assetType: 'API', description: '中医体质辨识服务接口', qualityScore: 90, ownerId: 'admin' },
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

const handleNodeClick = (data) => {
  ElMessage.info('选中目录: ' + data.catalogName)
}

const handleView = (row) => {
  ElMessage.info('查看资产: ' + row.assetName)
}

const handleApply = (row) => {
  ElMessage.success('申请使用: ' + row.assetName)
}
</script>

<style scoped>
.catalog-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
