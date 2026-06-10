<template>
  <div class="quality-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>数据质量管理</span>
          <el-button type="primary" @click="handleRunCheck">
            <el-icon><VideoPlay /></el-icon>
            执行检查
          </el-button>
        </div>
      </template>

      <!-- 质量评分卡 -->
      <el-row :gutter="20" class="score-row">
        <el-col :span="4">
          <div class="score-card">
            <el-progress type="dashboard" :percentage="92" :color="colors" />
            <div class="score-label">综合评分</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="score-card">
            <el-progress type="dashboard" :percentage="88" :color="colors" />
            <div class="score-label">完整性</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="score-card">
            <el-progress type="dashboard" :percentage="95" :color="colors" />
            <div class="score-label">准确性</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="score-card">
            <el-progress type="dashboard" :percentage="85" :color="colors" />
            <div class="score-label">一致性</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="score-card">
            <el-progress type="dashboard" :percentage="90" :color="colors" />
            <div class="score-label">及时性</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="score-card">
            <el-progress type="dashboard" :percentage="93" :color="colors" />
            <div class="score-label">唯一性</div>
          </div>
        </el-col>
      </el-row>

      <!-- 质量规则表格 -->
      <el-table :data="ruleList" style="margin-top: 20px">
        <el-table-column prop="ruleCode" label="规则编码" width="120" />
        <el-table-column prop="ruleName" label="规则名称" width="200" />
        <el-table-column prop="ruleType" label="规则类型" width="120">
          <template #default="{ row }">
            <el-tag :type="getRuleTypeTag(row.ruleType)">{{ row.ruleType }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重级别" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityTag(row.severity)">{{ row.severity }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="thresholdValue" label="阈值" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-switch v-model="row.status" :active-value="1" :inactive-value="0" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-button type="primary" link @click="handleRun(row)">执行</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 检查结果 -->
    <el-card style="margin-top: 20px">
      <template #header>
        <div class="card-header">
          <span>最近检查结果</span>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="(result, index) in checkResults"
          :key="index"
          :type="result.status === 'PASS' ? 'success' : 'danger'"
          :timestamp="result.checkTime"
        >
          <h4>{{ result.ruleName }}</h4>
          <p>总记录: {{ result.totalCount }}, 错误: {{ result.errorCount }}, 错误率: {{ result.errorRate }}%</p>
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const colors = [
  { color: '#f56c6c', percentage: 60 },
  { color: '#e6a23c', percentage: 80 },
  { color: '#67c23a', percentage: 100 }
]

const ruleList = ref([
  { ruleCode: 'RULE_001', ruleName: '非空检查', ruleType: 'COMPLETENESS', severity: 'ERROR', thresholdValue: '5%', status: 1 },
  { ruleCode: 'RULE_002', ruleName: '唯一性检查', ruleType: 'UNIQUENESS', severity: 'ERROR', thresholdValue: '0', status: 1 },
  { ruleCode: 'RULE_003', ruleName: '手机号格式检查', ruleType: 'ACCURACY', severity: 'WARNING', thresholdValue: '1%', status: 1 },
  { ruleCode: 'RULE_004', ruleName: '身份证格式检查', ruleType: 'ACCURACY', severity: 'WARNING', thresholdValue: '1%', status: 1 },
  { ruleCode: 'RULE_005', ruleName: '日期范围检查', ruleType: 'ACCURACY', severity: 'ERROR', thresholdValue: '0.5%', status: 1 },
])

const checkResults = ref([
  { ruleName: '非空检查', totalCount: 10000, errorCount: 120, errorRate: 1.2, status: 'PASS', checkTime: '2024-12-10 14:30:00' },
  { ruleName: '唯一性检查', totalCount: 10000, errorCount: 0, errorRate: 0, status: 'PASS', checkTime: '2024-12-10 14:25:00' },
  { ruleName: '手机号格式检查', totalCount: 8000, errorCount: 45, errorRate: 0.56, status: 'PASS', checkTime: '2024-12-10 14:20:00' },
  { ruleName: '日期范围检查', totalCount: 12000, errorCount: 89, errorRate: 0.74, status: 'FAIL', checkTime: '2024-12-10 14:15:00' },
])

const getRuleTypeTag = (type) => {
  const map = { 'COMPLETENESS': 'primary', 'ACCURACY': 'success', 'CONSISTENCY': 'warning', 'TIMELINESS': 'info', 'UNIQUENESS': 'danger' }
  return map[type] || ''
}

const getSeverityTag = (severity) => {
  const map = { 'INFO': 'info', 'WARNING': 'warning', 'ERROR': 'danger', 'CRITICAL': 'danger' }
  return map[severity] || ''
}

const handleRunCheck = () => {
  ElMessage.success('开始执行全量质量检查')
}

const handleEdit = (row) => {
  ElMessage.info('编辑规则: ' + row.ruleName)
}

const handleRun = (row) => {
  ElMessage.success('执行规则: ' + row.ruleName)
}
</script>

<style scoped>
.quality-page {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-row {
  margin-bottom: 20px;
}

.score-card {
  text-align: center;
  padding: 20px;
}

.score-label {
  margin-top: 10px;
  font-size: 14px;
  color: #606266;
}
</style>
