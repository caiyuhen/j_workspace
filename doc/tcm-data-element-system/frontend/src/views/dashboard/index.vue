<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #e6f7ff;">
            <el-icon :size="32" color="#1890ff"><Coin /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">1,234</div>
            <div class="stat-label">数据资产</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #f6ffed;">
            <el-icon :size="32" color="#52c41a"><DataLine /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">56,789</div>
            <div class="stat-label">元数据项</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #fff7e6;">
            <el-icon :size="32" color="#fa8c16"><Connection /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">89,012</div>
            <div class="stat-label">知识图谱实体</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: #fff1f0;">
            <el-icon :size="32" color="#f5222d"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">456</div>
            <div class="stat-label">活跃用户</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>数据资产趋势</span>
            </div>
          </template>
          <div ref="assetTrendChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>数据资产类型分布</span>
            </div>
          </template>
          <div ref="assetTypeChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 知识图谱与质量 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>知识图谱实体分布</span>
            </div>
          </template>
          <div ref="kgChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>数据质量评分</span>
            </div>
          </template>
          <div ref="qualityChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-card class="activity-card">
      <template #header>
        <div class="card-header">
          <span>最近活动</span>
        </div>
      </template>
      <el-timeline>
        <el-timeline-item
          v-for="(activity, index) in activities"
          :key="index"
          :type="activity.type"
          :timestamp="activity.time"
        >
          {{ activity.content }}
        </el-timeline-item>
      </el-timeline>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const assetTrendChart = ref(null)
const assetTypeChart = ref(null)
const kgChart = ref(null)
const qualityChart = ref(null)

const activities = [
  { content: '新增数据资产 "中医临床诊疗数据集"', time: '2024-12-10 14:30', type: 'primary' },
  { content: '数据质量检查完成，通过率 98.5%', time: '2024-12-10 12:00', type: 'success' },
  { content: '知识图谱新增实体 1,234 个', time: '2024-12-10 10:15', type: 'warning' },
  { content: '用户 "张医师" 完成体质辨识', time: '2024-12-10 09:30', type: 'info' },
  { content: '数据分类分级策略更新', time: '2024-12-09 16:45', type: 'danger' },
]

onMounted(() => {
  // 资产趋势图
  const trendChart = echarts.init(assetTrendChart.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
    },
    yAxis: { type: 'value' },
    series: [{
      data: [820, 932, 901, 934, 1290, 1330, 1320, 1450, 1520, 1680, 1890, 2100],
      type: 'line',
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(24,144,255,0.3)' },
            { offset: 1, color: 'rgba(24,144,255,0.05)' }
          ]
        }
      },
      itemStyle: { color: '#1890ff' }
    }]
  })

  // 资产类型分布图
  const typeChart = echarts.init(assetTypeChart.value)
  typeChart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: '5%' },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: '#fff',
        borderWidth: 2
      },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 16, fontWeight: 'bold' }
      },
      data: [
        { value: 435, name: '数据集', itemStyle: { color: '#1890ff' } },
        { value: 310, name: 'API接口', itemStyle: { color: '#52c41a' } },
        { value: 234, name: '报告', itemStyle: { color: '#faad14' } },
        { value: 135, name: '模型', itemStyle: { color: '#f5222d' } },
        { value: 120, name: '服务', itemStyle: { color: '#722ed1' } }
      ]
    }]
  })

  // 知识图谱实体分布
  const kgChartInstance = echarts.init(kgChart.value)
  kgChartInstance.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    xAxis: { type: 'category', data: ['疾病', '证型', '症状', '方剂', '中药', '穴位', '经络', '名医'] },
    yAxis: { type: 'value' },
    series: [{
      data: [1200, 980, 1560, 890, 2340, 670, 340, 120],
      type: 'bar',
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: '#52c41a' },
            { offset: 1, color: '#95de64' }
          ]
        },
        borderRadius: [4, 4, 0, 0]
      }
    }]
  })

  // 数据质量评分
  const qualityChartInstance = echarts.init(qualityChart.value)
  qualityChartInstance.setOption({
    tooltip: { trigger: 'axis' },
    radar: {
      indicator: [
        { name: '完整性', max: 100 },
        { name: '准确性', max: 100 },
        { name: '一致性', max: 100 },
        { name: '及时性', max: 100 },
        { name: '唯一性', max: 100 }
      ]
    },
    series: [{
      type: 'radar',
      data: [{
        value: [92, 88, 95, 85, 90],
        name: '数据质量评分',
        areaStyle: { color: 'rgba(250,140,22,0.3)' },
        itemStyle: { color: '#fa8c16' }
      }]
    }]
  })

  window.addEventListener('resize', () => {
    trendChart.resize()
    typeChart.resize()
    kgChartInstance.resize()
    qualityChartInstance.resize()
  })
})
</script>

<style scoped>
.dashboard {
  padding-bottom: 20px;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.chart-row {
  margin-bottom: 20px;
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.activity-card {
  margin-top: 20px;
}
</style>
