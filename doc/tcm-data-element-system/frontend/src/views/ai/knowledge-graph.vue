<template>
  <div class="knowledge-graph">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>中医药知识图谱</span>
          <div class="header-actions">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索实体（疾病、证型、方剂、中药等）"
              style="width: 300px"
              clearable
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button @click="handleSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </div>
        </div>
      </template>

      <!-- 实体类型筛选 -->
      <div class="type-filter">
        <el-radio-group v-model="selectedType" @change="handleTypeChange">
          <el-radio-button label="">全部</el-radio-button>
          <el-radio-button label="DISEASE">疾病</el-radio-button>
          <el-radio-button label="SYNDROME">证型</el-radio-button>
          <el-radio-button label="SYMPTOM">症状</el-radio-button>
          <el-radio-button label="FORMULA">方剂</el-radio-button>
          <el-radio-button label="HERB">中药</el-radio-button>
          <el-radio-button label="ACUPOINT">穴位</el-radio-button>
          <el-radio-button label="DOCTOR">名医</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 实体列表 -->
      <el-table :data="entityList" v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="entityId" label="实体ID" width="120" />
        <el-table-column prop="entityName" label="实体名称" width="150">
          <template #default="{ row }">
            <el-tag :type="getEntityTypeTag(row.entityType)">{{ row.entityName }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="entityType" label="实体类型" width="100">
          <template #default="{ row }">
            {{ getEntityTypeName(row.entityType) }}
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" show-overflow-tooltip />
        <el-table-column prop="confidence" label="置信度" width="100">
          <template #default="{ row }">
            <el-progress :percentage="row.confidence * 100" :show-text="false" />
          </template>
        </el-table-column>
        <el-table-column prop="source" label="来源" width="120" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
            <el-button type="primary" link @click="viewRelations(row)">关系</el-button>
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
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </el-card>

    <!-- 实体详情弹窗 -->
    <el-dialog v-model="detailVisible" title="实体详情" width="600px">
      <el-descriptions :column="2" border v-if="currentEntity">
        <el-descriptions-item label="实体ID">{{ currentEntity.entityId }}</el-descriptions-item>
        <el-descriptions-item label="实体名称">{{ currentEntity.entityName }}</el-descriptions-item>
        <el-descriptions-item label="实体类型">
          <el-tag>{{ getEntityTypeName(currentEntity.entityType) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="置信度">{{ currentEntity.confidence }}</el-descriptions-item>
        <el-descriptions-item label="来源">{{ currentEntity.source }}</el-descriptions-item>
        <el-descriptions-item label="别名">{{ currentEntity.aliases }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ currentEntity.description }}</el-descriptions-item>
        <el-descriptions-item label="属性" :span="2">
          <pre>{{ currentEntity.properties }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const searchKeyword = ref('')
const selectedType = ref('')
const entityList = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const detailVisible = ref(false)
const currentEntity = ref(null)

// 模拟数据
const mockEntities = [
  { entityId: 'D001', entityName: '感冒', entityType: 'DISEASE', description: '感受触冒风邪，邪犯卫表而导致的常见外感疾病', aliases: '伤风,冒寒', confidence: 0.95, source: '中医病证分类与代码', properties: '{"category":"外感病","onset":"急性"}' },
  { entityId: 'S001', entityName: '风寒感冒', entityType: 'SYNDROME', description: '风寒之邪外袭、肺气失宣所致', aliases: '', confidence: 0.92, source: '中医临床诊疗术语', properties: '{"category":"表证","nature":"寒"}' },
  { entityId: 'F001', entityName: '麻黄汤', entityType: 'FORMULA', description: '发汗解表，宣肺平喘', aliases: '', confidence: 0.98, source: '伤寒论', properties: '{"source":"伤寒论","category":"解表剂"}' },
  { entityId: 'H001', entityName: '麻黄', entityType: 'HERB', description: '发汗解表，宣肺平喘，利水消肿', aliases: '龙沙,卑相', confidence: 0.97, source: '中国药典', properties: '{"nature":"温","taste":"辛、微苦","meridian":"肺、膀胱"}' },
  { entityId: 'A001', entityName: '合谷', entityType: 'ACUPOINT', description: '疏风解表，行气活血，通络止痛', aliases: '虎口', confidence: 0.96, source: '针灸甲乙经', properties: '{"meridian":"手阳明大肠经","location":"手背第一、二掌骨间"}' },
  { entityId: 'D002', entityName: '咳嗽', entityType: 'DISEASE', description: '肺失宣降，肺气上逆作声，咳吐痰液', aliases: '', confidence: 0.94, source: '中医病证分类与代码', properties: '{"category":"肺病","onset":"急性/慢性"}' },
  { entityId: 'S002', entityName: '风热感冒', entityType: 'SYNDROME', description: '风热之邪犯表、肺气失和所致', aliases: '', confidence: 0.91, source: '中医临床诊疗术语', properties: '{"category":"表证","nature":"热"}' },
  { entityId: 'F002', entityName: '银翘散', entityType: 'FORMULA', description: '辛凉透表，清热解毒', aliases: '', confidence: 0.97, source: '温病条辨', properties: '{"source":"温病条辨","category":"解表剂"}' },
  { entityId: 'H002', entityName: '桂枝', entityType: 'HERB', description: '发汗解肌，温通经脉，助阳化气', aliases: '柳桂', confidence: 0.96, source: '中国药典', properties: '{"nature":"温","taste":"辛、甘","meridian":"心、肺、膀胱"}' },
  { entityId: 'A002', entityName: '足三里', entityType: 'ACUPOINT', description: '健脾和胃，扶正培元，通经活络', aliases: '下陵', confidence: 0.98, source: '针灸甲乙经', properties: '{"meridian":"足阳明胃经","location":"小腿外侧，犊鼻下3寸"}' },
]

const getEntityTypeTag = (type) => {
  const map = {
    'DISEASE': 'danger',
    'SYNDROME': 'warning',
    'SYMPTOM': 'info',
    'FORMULA': 'success',
    'HERB': 'success',
    'ACUPOINT': 'primary',
    'DOCTOR': ''
  }
  return map[type] || ''
}

const getEntityTypeName = (type) => {
  const map = {
    'DISEASE': '疾病',
    'SYNDROME': '证型',
    'SYMPTOM': '症状',
    'FORMULA': '方剂',
    'HERB': '中药',
    'ACUPOINT': '穴位',
    'MERIDIAN': '经络',
    'DOCTOR': '名医'
  }
  return map[type] || type
}

const loadData = () => {
  loading.value = true
  // 模拟API调用
  setTimeout(() => {
    let filtered = mockEntities
    if (selectedType.value) {
      filtered = filtered.filter(item => item.entityType === selectedType.value)
    }
    if (searchKeyword.value) {
      filtered = filtered.filter(item => 
        item.entityName.includes(searchKeyword.value) || 
        item.aliases.includes(searchKeyword.value)
      )
    }
    entityList.value = filtered
    total.value = filtered.length
    loading.value = false
  }, 500)
}

const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

const handleTypeChange = () => {
  currentPage.value = 1
  loadData()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  loadData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadData()
}

const viewDetail = (row) => {
  currentEntity.value = row
  detailVisible.value = true
}

const viewRelations = (row) => {
  ElMessage.info(`查看 ${row.entityName} 的关系图谱`)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.knowledge-graph {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-filter {
  margin-bottom: 20px;
}

pre {
  background: #f5f7fa;
  padding: 10px;
  border-radius: 4px;
  margin: 0;
}
</style>
