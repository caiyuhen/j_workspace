<template>
  <div class="diagnosis">
    <el-row :gutter="20">
      <!-- 左侧：症状输入 -->
      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-header">
              <el-icon><FirstAidKit /></el-icon>
              <span>智能辨证</span>
            </div>
          </template>

          <el-form :model="form" label-position="top">
            <!-- 四诊信息采集 -->
            <el-divider content-position="left">望诊</el-divider>
            <el-form-item label="舌象">
              <el-select v-model="form.tongue" placeholder="请选择舌象" style="width: 100%">
                <el-option label="淡红舌" value="淡红" />
                <el-option label="淡白舌" value="淡白" />
                <el-option label="红舌" value="红" />
                <el-option label="绛舌" value="绛" />
                <el-option label="紫舌" value="紫" />
              </el-select>
            </el-form-item>
            <el-form-item label="舌苔">
              <el-select v-model="form.coating" placeholder="请选择舌苔" style="width: 100%">
                <el-option label="薄白" value="薄白" />
                <el-option label="薄黄" value="薄黄" />
                <el-option label="厚白" value="厚白" />
                <el-option label="厚黄" value="厚黄" />
                <el-option label="腻苔" value="腻" />
              </el-select>
            </el-form-item>

            <el-divider content-position="left">闻诊</el-divider>
            <el-form-item label="声音">
              <el-input v-model="form.voice" placeholder="描述声音特点" />
            </el-form-item>
            <el-form-item label="气味">
              <el-input v-model="form.odor" placeholder="描述气味特点" />
            </el-form-item>

            <el-divider content-position="left">问诊</el-divider>
            <el-form-item label="主诉">
              <el-input
                v-model="form.chiefComplaint"
                type="textarea"
                :rows="3"
                placeholder="请输入患者主诉症状"
              />
            </el-form-item>
            <el-form-item label="伴随症状">
              <el-checkbox-group v-model="form.symptoms">
                <el-checkbox label="发热" />
                <el-checkbox label="恶寒" />
                <el-checkbox label="头痛" />
                <el-checkbox label="咳嗽" />
                <el-checkbox label="咽痛" />
                <el-checkbox label="流涕" />
                <el-checkbox label="身痛" />
                <el-checkbox label="汗出" />
              </el-checkbox-group>
            </el-form-item>

            <el-divider content-position="left">切诊</el-divider>
            <el-form-item label="脉象">
              <el-select v-model="form.pulse" placeholder="请选择脉象" style="width: 100%">
                <el-option label="浮脉" value="浮" />
                <el-option label="沉脉" value="沉" />
                <el-option label="迟脉" value="迟" />
                <el-option label="数脉" value="数" />
                <el-option label="滑脉" value="滑" />
                <el-option label="涩脉" value="涩" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" size="large" style="width: 100%" @click="handleDiagnosis" :loading="loading">
                <el-icon><MagicStick /></el-icon>
                AI智能辨证
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：诊断结果 -->
      <el-col :span="14">
        <el-card v-if="!result" class="empty-result">
          <el-empty description="请输入症状信息，点击AI智能辨证按钮获取诊断结果">
            <template #image>
              <el-icon :size="80" color="#dcdfe6"><FirstAidKit /></el-icon>
            </template>
          </el-empty>
        </el-card>

        <template v-else>
          <!-- 辨证结果 -->
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span>辨证结果</span>
                <el-tag type="success" effect="dark">AI推荐</el-tag>
              </div>
            </template>
            
            <div class="syndrome-result">
              <h3>{{ result.syndrome }}</h3>
              <el-progress :percentage="result.confidence" :color="progressColors" />
              <p class="confidence-text">置信度: {{ result.confidence }}%</p>
            </div>

            <el-divider />

            <div class="analysis-section">
              <h4>辨证分析</h4>
              <p>{{ result.analysis }}</p>
            </div>
          </el-card>

          <!-- 方剂推荐 -->
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span>方剂推荐</span>
              </div>
            </template>
            
            <el-table :data="result.formulas" style="width: 100%">
              <el-table-column prop="name" label="方剂名称" width="120" />
              <el-table-column prop="source" label="来源" width="120" />
              <el-table-column prop="composition" label="组成" show-overflow-tooltip />
              <el-table-column prop="effects" label="功效" show-overflow-tooltip />
              <el-table-column label="匹配度" width="100">
                <template #default="{ row }">
                  <el-progress :percentage="row.matchRate" />
                </template>
              </el-table-column>
            </el-table>
          </el-card>

          <!-- 用药禁忌提醒 -->
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span>用药禁忌提醒</span>
                <el-tag type="danger">重要</el-tag>
              </div>
            </template>
            
            <el-alert
              v-for="(warning, index) in result.warnings"
              :key="index"
              :title="warning.title"
              :type="warning.type"
              :description="warning.description"
              show-icon
              :closable="false"
              style="margin-bottom: 10px"
            />
          </el-card>

          <!-- 调养建议 -->
          <el-card class="result-card">
            <template #header>
              <div class="card-header">
                <span>调养建议</span>
              </div>
            </template>
            
            <el-timeline>
              <el-timeline-item
                v-for="(advice, index) in result.advices"
                :key="index"
                :type="advice.type"
              >
                <h4>{{ advice.title }}</h4>
                <p>{{ advice.content }}</p>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </template>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const result = ref(null)

const form = ref({
  tongue: '',
  coating: '',
  voice: '',
  odor: '',
  chiefComplaint: '',
  symptoms: [],
  pulse: ''
})

const progressColors = [
  { color: '#f56c6c', percentage: 60 },
  { color: '#e6a23c', percentage: 80 },
  { color: '#67c23a', percentage: 100 }
]

const handleDiagnosis = async () => {
  if (!form.value.chiefComplaint) {
    ElMessage.warning('请输入主诉症状')
    return
  }

  loading.value = true
  
  // 模拟AI诊断API调用
  setTimeout(() => {
    result.value = {
      syndrome: '风寒表证',
      confidence: 92,
      analysis: '患者表现为恶寒重、发热轻、无汗、头痛身痛、鼻塞流清涕、咳嗽吐稀白痰、口不渴或渴喜热饮、苔薄白。脉象浮紧，符合风寒表证的辨证要点。风寒之邪外袭，肺气失宣所致。',
      formulas: [
        {
          name: '麻黄汤',
          source: '《伤寒论》',
          composition: '麻黄9g、桂枝6g、杏仁9g、甘草3g',
          effects: '发汗解表，宣肺平喘',
          matchRate: 95
        },
        {
          name: '桂枝汤',
          source: '《伤寒论》',
          composition: '桂枝9g、芍药9g、生姜9g、大枣3枚、甘草6g',
          effects: '解肌发表，调和营卫',
          matchRate: 85
        },
        {
          name: '荆防败毒散',
          source: '《摄生众妙方》',
          composition: '荆芥、防风、羌活、独活等',
          effects: '发汗解表，散风祛湿',
          matchRate: 78
        }
      ],
      warnings: [
        {
          title: '十八反禁忌',
          type: 'error',
          description: '处方中不可使用"半蒌贝蔹及攻乌"等相反药物组合'
        },
        {
          title: '妊娠禁忌',
          type: 'warning',
          description: '孕妇慎用麻黄、桂枝等发汗力强的药物'
        },
        {
          title: '体虚慎用',
          type: 'warning',
          description: '体虚多汗者慎用麻黄汤，可考虑桂枝汤'
        }
      ],
      advices: [
        {
          title: '饮食调养',
          type: 'primary',
          content: '宜食温热性食物，如生姜、葱白、红糖水等。忌食生冷寒凉食物，如西瓜、冷饮等。'
        },
        {
          title: '起居调养',
          type: 'success',
          content: '注意保暖，避免受凉。适当休息，保证充足睡眠。室内保持空气流通但避免直接吹风。'
        },
        {
          title: '情志调养',
          type: 'warning',
          content: '保持心情舒畅，避免过度紧张焦虑。可适当进行轻度活动，如散步等。'
        }
      ]
    }
    loading.value = false
    ElMessage.success('辨证完成')
  }, 2000)
}
</script>

<style scoped>
.diagnosis {
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.empty-result {
  height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.result-card {
  margin-bottom: 20px;
}

.syndrome-result {
  text-align: center;
  padding: 20px 0;
}

.syndrome-result h3 {
  font-size: 24px;
  color: #303133;
  margin-bottom: 16px;
}

.confidence-text {
  color: #909399;
  margin-top: 8px;
}

.analysis-section h4 {
  color: #303133;
  margin-bottom: 12px;
}

.analysis-section p {
  color: #606266;
  line-height: 1.8;
}
</style>
