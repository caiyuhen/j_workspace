<template>
  <div class="standard-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据标准规范</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            新增标准
          </el-button>
        </div>
      </template>

      <!-- 标准分类 -->
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="全部" name=""></el-tab-pane>
        <el-tab-pane label="术语标准" name="TERMINOLOGY"></el-tab-pane>
        <el-tab-pane label="编码标准" name="CODING"></el-tab-pane>
        <el-tab-pane label="分类标准" name="CLASSIFICATION"></el-tab-pane>
        <el-tab-pane label="元数据标准" name="METADATA"></el-tab-pane>
      </el-tabs>

      <!-- 标准表格 -->
      <el-table :data="standardList" v-loading="loading">
        <el-table-column prop="standardCode" label="标准编码" width="150" />
        <el-table-column prop="standardName" label="标准名称" width="250" show-overflow-tooltip />
        <el-table-column prop="standardType" label="标准类型" width="120" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusTag(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="referenceSource" label="参考来源" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleView(row)">查看</el-button>
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 标准详情弹窗 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="标准编码">
          <el-input v-model="form.standardCode" placeholder="请输入标准编码" />
        </el-form-item>
        <el-form-item label="标准名称">
          <el-input v-model="form.standardName" placeholder="请输入标准名称" />
        </el-form-item>
        <el-form-item label="标准类型">
          <el-select v-model="form.standardType" placeholder="请选择标准类型" style="width: 100%">
            <el-option label="术语标准" value="TERMINOLOGY" />
            <el-option label="编码标准" value="CODING" />
            <el-option label="分类标准" value="CLASSIFICATION" />
            <el-option label="元数据标准" value="METADATA" />
          </el-select>
        </el-form-item>
        <el-form-item label="定义">
          <el-input v-model="form.definition" type="textarea" :rows="3" placeholder="请输入定义" />
        </el-form-item>
        <el-form-item label="数据类型">
          <el-input v-model="form.dataType" placeholder="请输入数据类型" />
        </el-form-item>
        <el-form-item label="允许值">
          <el-input v-model="form.allowedValues" type="textarea" :rows="2" placeholder="请输入允许值列表" />
        </el-form-item>
        <el-form-item label="参考来源">
          <el-input v-model="form.referenceSource" placeholder="请输入参考来源" />
        </el-form-item>
        <el-form-item label="版本">
          <el-input v-model="form.version" placeholder="请输入版本号" />
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
const activeTab = ref('')
const dialogVisible = ref(false)
const dialogTitle = ref('新增标准')
const form = ref({})

const standardList = ref([
  { standardCode: 'TCD-001', standardName: '感冒', standardType: 'CODING', version: '1.0', status: 'PUBLISHED', referenceSource: '中医病证分类与代码' },
  { standardCode: 'TCD-002', standardName: '咳嗽', standardType: 'CODING', version: '1.0', status: 'PUBLISHED', referenceSource: '中医病证分类与代码' },
  { standardCode: 'ICD11-TM-001', standardName: '风寒表证', standardType: 'CODING', version: '1.0', status: 'PUBLISHED', referenceSource: 'ICD-11传统医学章节' },
  { standardCode: 'HERB-001', standardName: '麻黄', standardType: 'CODING', version: '1.0', status: 'PUBLISHED', referenceSource: '中药编码规则及编码' },
  { standardCode: 'TERM-001', standardName: '辨证论治', standardType: 'TERMINOLOGY', version: '1.0', status: 'PUBLISHED', referenceSource: '中医临床诊疗术语' },
  { standardCode: 'TERM-002', standardName: '四诊合参', standardType: 'TERMINOLOGY', version: '1.0', status: 'DRAFT', referenceSource: '中医临床诊疗术语' },
])

const getStatusTag = (status) => {
  const map = { 'DRAFT': 'info', 'PUBLISHED': 'success', 'DEPRECATED': 'danger' }
  return map[status] || ''
}

const getStatusText = (status) => {
  const map = { 'DRAFT': '草稿', 'PUBLISHED': '已发布', 'DEPRECATED': '已废止' }
  return map[status] || status
}

const handleTabChange = () => {
  // 根据分类筛选
}

const handleAdd = () => {
  dialogTitle.value = '新增标准'
  form.value = {}
  dialogVisible.value = true
}

const handleView = (row) => {
  ElMessage.info('查看标准: ' + row.standardName)
}

const handleEdit = (row) => {
  dialogTitle.value = '编辑标准'
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm('确认删除该标准?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    ElMessage.success('删除成功')
  })
}

const handleSubmit = () => {
  dialogVisible.value = false
  ElMessage.success('保存成功')
}
</script>

<style scoped>
.standard-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
