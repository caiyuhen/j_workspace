<template>
  <div class="architecture-page">
    <!-- 架构概览 -->
    <el-card class="overview-card">
      <template #header>
        <div class="card-header">
          <span>系统总体架构</span>
          <el-radio-group v-model="viewMode" size="small">
            <el-radio-button value="layer">分层架构</el-radio-button>
            <el-radio-button value="dataflow">数据流向</el-radio-button>
            <el-radio-button value="deploy">部署架构</el-radio-button>
            <el-radio-button value="tech">技术选型</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 分层架构视图 -->
      <div v-if="viewMode === 'layer'" class="layer-view">
        <div class="arch-layer" v-for="layer in archLayers" :key="layer.id">
          <div class="layer-header" :style="{ background: layer.color }">
            <div class="layer-icon">
              <el-icon :size="20"><component :is="layer.icon" /></el-icon>
            </div>
            <div class="layer-info">
              <h3>{{ layer.name }}</h3>
              <p>{{ layer.desc }}</p>
            </div>
          </div>
          <div class="layer-modules">
            <div
              v-for="mod in layer.modules"
              :key="mod.name"
              class="module-card"
              :style="{ borderColor: layer.color }"
            >
              <div class="module-icon" :style="{ background: layer.color + '15', color: layer.color }">
                <el-icon :size="18"><component :is="mod.icon" /></el-icon>
              </div>
              <div class="module-name">{{ mod.name }}</div>
              <div class="module-tech">{{ mod.tech }}</div>
            </div>
          </div>
          <div class="layer-arrow" v-if="layer.id < archLayers.length">
            <el-icon :size="24" color="#909399"><ArrowDown /></el-icon>
          </div>
        </div>
      </div>

      <!-- 数据流向视图 -->
      <div v-if="viewMode === 'dataflow'" class="dataflow-view">
        <div class="flow-container">
          <div class="flow-stage" v-for="(stage, idx) in dataFlowStages" :key="stage.id">
            <div class="stage-header" :style="{ background: stage.color }">
              <span class="stage-num">{{ idx + 1 }}</span>
              <span class="stage-name">{{ stage.name }}</span>
            </div>
            <div class="stage-content">
              <div class="flow-item" v-for="item in stage.items" :key="item">
                <el-icon :size="14" color="#409EFF"><Right /></el-icon>
                <span>{{ item }}</span>
              </div>
            </div>
            <div class="flow-arrow" v-if="idx < dataFlowStages.length - 1">
              <el-icon :size="28" color="#409EFF"><ArrowRight /></el-icon>
            </div>
          </div>
        </div>
      </div>

      <!-- 部署架构视图 -->
      <div v-if="viewMode === 'deploy'" class="deploy-view">
        <div class="deploy-zone" v-for="zone in deployZones" :key="zone.id">
          <div class="zone-header" :style="{ background: zone.color }">
            <el-icon :size="18"><component :is="zone.icon" /></el-icon>
            <span>{{ zone.name }}</span>
          </div>
          <div class="zone-nodes">
            <div class="node-card" v-for="node in zone.nodes" :key="node.name">
              <div class="node-icon" :style="{ background: zone.color + '15', color: zone.color }">
                <el-icon :size="20"><component :is="node.icon" /></el-icon>
              </div>
              <div class="node-name">{{ node.name }}</div>
              <div class="node-detail">{{ node.detail }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 技术选型视图 -->
      <div v-if="viewMode === 'tech'" class="tech-view">
        <el-table :data="techStack" stripe>
          <el-table-column prop="layer" label="架构层次" width="140">
            <template #default="{ row }">
              <el-tag :type="getLayerTag(row.layer)" effect="plain">{{ row.layer }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="component" label="组件" width="140" />
          <el-table-column prop="tech" label="推荐技术" />
          <el-table-column prop="purpose" label="用途说明" width="200" />
          <el-table-column prop="alternative" label="备选方案" width="200" />
        </el-table>
      </div>
    </el-card>

    <!-- 数据架构 -->
    <el-card class="data-arch-card">
      <template #header>
        <div class="card-header">
          <span>数据分层架构</span>
        </div>
      </template>
      <div class="data-layers">
        <div class="data-layer" v-for="dl in dataLayers" :key="dl.name">
          <div class="dl-header" :style="{ background: dl.color, borderColor: dl.color }">
            <span class="dl-abbr">{{ dl.abbr }}</span>
            <span class="dl-name">{{ dl.name }}</span>
          </div>
          <div class="dl-desc">{{ dl.desc }}</div>
        </div>
        <div class="data-layer-arrow">
          <el-icon :size="20" color="#909399"><ArrowDown /></el-icon>
        </div>
      </div>

      <!-- 主题域 -->
      <div class="theme-domains">
        <h4>中医药主题域</h4>
        <div class="domain-grid">
          <div class="domain-card" v-for="domain in themeDomains" :key="domain.name">
            <div class="domain-icon" :style="{ background: domain.color + '15', color: domain.color }">
              <el-icon :size="22"><component :is="domain.icon" /></el-icon>
            </div>
            <div class="domain-name">{{ domain.name }}</div>
            <div class="domain-items">
              <el-tag v-for="item in domain.items" :key="item" size="small" type="info" effect="plain">{{ item }}</el-tag>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- AI架构 -->
    <el-card class="ai-arch-card">
      <template #header>
        <div class="card-header">
          <span>AI智能应用架构</span>
        </div>
      </template>
      <div class="ai-layers">
        <div class="ai-layer" v-for="aiLayer in aiLayers" :key="aiLayer.name">
          <div class="ai-layer-header" :style="{ background: aiLayer.color }">
            <span>{{ aiLayer.name }}</span>
          </div>
          <div class="ai-layer-modules">
            <div class="ai-module" v-for="mod in aiLayer.modules" :key="mod">
              {{ mod }}
            </div>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const viewMode = ref('layer')

// 分层架构数据
const archLayers = [
  {
    id: 1, name: '应用层 (Application Layer)', desc: '面向用户的业务功能入口',
    color: '#409EFF', icon: 'Monitor',
    modules: [
      { name: '数据治理门户', tech: 'Vue3 + Element Plus', icon: 'DataLine' },
      { name: '数据交易平台', tech: 'Vue3 + ECharts', icon: 'ShoppingCart' },
      { name: 'AI应用中心', tech: 'Vue3 + Canvas', icon: 'Cpu' },
      { name: '统计分析大屏', tech: 'DataV + ECharts', icon: 'TrendCharts' },
      { name: '运营管理后台', tech: 'Vue3 + Element Plus', icon: 'Setting' }
    ]
  },
  {
    id: 2, name: '服务层 (Service Layer)', desc: '核心业务逻辑与微服务',
    color: '#67C23A', icon: 'Grid',
    modules: [
      { name: '元数据服务', tech: 'Spring Boot', icon: 'Document' },
      { name: '数据质量服务', tech: 'Spring Boot', icon: 'CircleCheck' },
      { name: '数据标准服务', tech: 'Spring Boot', icon: 'Stamp' },
      { name: '数据资产服务', tech: 'Spring Boot', icon: 'Coin' },
      { name: '数据安全服务', tech: 'Spring Security', icon: 'Lock' },
      { name: '分类分级服务', tech: 'Spring Boot', icon: 'Sort' },
      { name: '交易流通服务', tech: 'Spring Cloud', icon: 'Exchange' },
      { name: 'AI推理服务', tech: 'Python + FastAPI', icon: 'MagicStick' }
    ]
  },
  {
    id: 3, name: '数据层 (Data Layer)', desc: '数据存储与计算引擎',
    color: '#E6A23C', icon: 'Coin',
    modules: [
      { name: '数据湖 (ODS)', tech: 'Apache Iceberg', icon: 'Files' },
      { name: '数据仓库 (DWD/DWS)', tech: 'Doris / StarRocks', icon: 'House' },
      { name: '数据集市 (ADS)', tech: 'ClickHouse', icon: 'DataBoard' },
      { name: '特征库', tech: 'Redis + Feature Store', icon: 'Box' },
      { name: '知识图谱', tech: 'Neo4j', icon: 'Connection' }
    ]
  },
  {
    id: 4, name: '平台层 (Platform Layer)', desc: '基础技术平台支撑',
    color: '#F56C6C', icon: 'Platform',
    modules: [
      { name: '大数据平台', tech: 'Spark + Flink', icon: 'Cpu' },
      { name: '流计算引擎', tech: 'Apache Flink', icon: 'Timer' },
      { name: '隐私计算平台', tech: 'SecretFlow / FATE', icon: 'Key' },
      { name: 'AI训练平台', tech: 'PyTorch + vLLM', icon: 'Cpu' },
      { name: '区块链存证', tech: 'Hyperledger Fabric', icon: 'Link' }
    ]
  },
  {
    id: 5, name: '接入层 (Integration Layer)', desc: '多源数据统一接入',
    color: '#909399', icon: 'Connection',
    modules: [
      { name: '数据库适配器', tech: 'MySQL/PG/Oracle', icon: 'Database' },
      { name: 'API网关', tech: 'Spring Cloud Gateway', icon: 'Switch' },
      { name: '消息队列', tech: 'Kafka / RocketMQ', icon: 'Message' },
      { name: '文件采集', tech: 'Flume + MinIO', icon: 'Upload' },
      { name: 'ETL引擎', tech: 'DolphinScheduler', icon: 'RefreshRight' }
    ]
  },
  {
    id: 6, name: '基础设施层 (Infrastructure)', desc: '云原生基础设施',
    color: '#606266', icon: 'OfficeBuilding',
    modules: [
      { name: '容器云 (K8s)', tech: 'Kubernetes', icon: 'Box' },
      { name: '分布式数据库', tech: 'TiDB / OceanBase', icon: 'Database' },
      { name: '对象存储', tech: 'MinIO / OSS', icon: 'FolderOpened' },
      { name: '网络与安全', tech: 'Calico + Istio', icon: 'Lock' },
      { name: '监控运维', tech: 'Prometheus + Grafana', icon: 'Odometer' }
    ]
  }
]

// 数据流向
const dataFlowStages = [
  {
    id: 1, name: '数据采集', color: '#909399',
    items: ['HIS系统对接', 'EMR电子病历', 'LIS检验数据', 'PACS舌象影像', '体质辨识系统', '名老中医工作室', '中药溯源系统', '文件/API/消息队列']
  },
  {
    id: 2, name: '数据接入与治理', color: '#409EFF',
    items: ['数据清洗转换', '标准化映射', '分类分级标注', '质量规则校验', '元数据自动采集', '数据血缘追踪', '脱敏与加密']
  },
  {
    id: 3, name: '数据存储与计算', color: '#E6A23C',
    items: ['ODS原始层存储', 'DWD明细层清洗', 'DWS汇总层聚合', 'ADS应用层集市', '知识图谱构建', '向量库索引']
  },
  {
    id: 4, name: '数据资产化', color: '#67C23A',
    items: ['资产编目登记', '质量评分评估', '资产估值定价', '资产入表核算', '产品封装发布', '目录与检索']
  },
  {
    id: 5, name: '数据流通与应用', color: '#F56C6C',
    items: ['数据交易交付', '隐私计算共享', 'AI辅助诊疗', '智能辨证开方', '体质辨识分析', '经验传承挖掘', '统计分析大屏']
  }
]

// 部署架构
const deployZones = [
  {
    id: 1, name: '公有云区域', color: '#409EFF', icon: 'Cloudy',
    nodes: [
      { name: 'Web/APP接入', detail: 'CDN加速 + Nginx', icon: 'Monitor' },
      { name: 'AI推理服务', detail: '大模型API + vLLM', icon: 'Cpu' },
      { name: '非敏感数据存储', detail: '备份/归档', icon: 'FolderOpened' }
    ]
  },
  {
    id: 2, name: '专有云/私有云区域', color: '#67C23A', icon: 'OfficeBuilding',
    nodes: [
      { name: '核心业务系统', detail: 'Spring Cloud微服务', icon: 'Platform' },
      { name: '数据治理平台', detail: 'Spark + Flink', icon: 'DataLine' },
      { name: '隐私计算节点', detail: 'SecretFlow / FATE', icon: 'Key' },
      { name: '敏感数据存储', detail: '加密存储 + 核心资产', icon: 'Lock' }
    ]
  },
  {
    id: 3, name: '边缘节点（医疗机构）', color: '#E6A23C', icon: 'Position',
    nodes: [
      { name: '数据采集网关', detail: '数据预处理', icon: 'Connection' },
      { name: '边缘AI推理', detail: '实时质控', icon: 'Cpu' },
      { name: '本地缓存', detail: '断点续传', icon: 'Files' }
    ]
  }
]

// 技术选型
const techStack = [
  { layer: '前端', component: 'Web应用', tech: 'Vue 3 + TypeScript + Element Plus', purpose: '管理后台与用户界面', alternative: 'React + Ant Design' },
  { layer: '前端', component: '可视化', tech: 'ECharts / AntV / DataV', purpose: '图表与大屏展示', alternative: 'D3.js / Plotly' },
  { layer: '前端', component: '移动端', tech: 'UniApp / Flutter', purpose: '移动端适配', alternative: 'React Native' },
  { layer: '后端', component: '微服务框架', tech: 'Spring Cloud Alibaba', purpose: '服务治理与通信', alternative: 'Go Micro / Kratos' },
  { layer: '后端', component: 'API网关', tech: 'Spring Cloud Gateway', purpose: '路由、限流、鉴权', alternative: 'Kong / APISIX' },
  { layer: '后端', component: '服务注册', tech: 'Nacos', purpose: '服务发现与配置中心', alternative: 'Consul / Eureka' },
  { layer: '存储', component: '关系型数据库', tech: 'PostgreSQL / 达梦数据库', purpose: '核心业务数据存储', alternative: 'MySQL / OceanBase' },
  { layer: '存储', component: '图数据库', tech: 'Neo4j', purpose: '知识图谱存储与查询', alternative: 'JanusGraph / NebulaGraph' },
  { layer: '存储', component: '搜索引擎', tech: 'Elasticsearch', purpose: '全文检索与日志分析', alternative: 'OpenSearch' },
  { layer: '存储', component: '缓存', tech: 'Redis Cluster', purpose: '缓存与会话管理', alternative: 'Memcached' },
  { layer: '大数据', component: '数据湖', tech: 'Apache Iceberg / Hudi', purpose: '海量数据存储与管理', alternative: 'Delta Lake' },
  { layer: '大数据', component: '计算引擎', tech: 'Spark + Flink', purpose: '批处理与流计算', alternative: 'Presto / Trino' },
  { layer: '大数据', component: '数据仓库', tech: 'Doris / StarRocks', purpose: 'OLAP分析查询', alternative: 'ClickHouse' },
  { layer: 'AI', component: '深度学习框架', tech: 'PyTorch / PaddlePaddle', purpose: '模型训练与推理', alternative: 'TensorFlow' },
  { layer: 'AI', component: '大模型推理', tech: 'vLLM / TGI', purpose: '大语言模型高效推理', alternative: 'TensorRT-LLM' },
  { layer: 'AI', component: '向量数据库', tech: 'Milvus / Zilliz', purpose: 'RAG检索增强向量存储', alternative: 'Weaviate / Chroma' },
  { layer: '安全', component: '身份认证', tech: 'OAuth2 + JWT + 国密SM2', purpose: '统一身份认证', alternative: 'Keycloak' },
  { layer: '安全', component: '数据加密', tech: '国密SM4/SM3 + AES-256', purpose: '传输与存储加密', alternative: 'Vault' },
  { layer: 'DevOps', component: '容器编排', tech: 'Kubernetes', purpose: '容器化部署与运维', alternative: 'Docker Swarm' },
  { layer: 'DevOps', component: '监控', tech: 'Prometheus + Grafana + SkyWalking', purpose: '系统监控与链路追踪', alternative: 'Zabbix + Pinpoint' }
]

// 数据分层
const dataLayers = [
  { abbr: 'ODS', name: '操作数据存储', desc: '原始数据接入，保持原貌，按源系统分区', color: '#909399' },
  { abbr: 'DWD', name: '明细数据层', desc: '数据清洗、标准化、脱敏，统一数据标准', color: '#409EFF' },
  { abbr: 'DWS', name: '汇总数据层', desc: '按主题域汇总，构建轻度汇总表', color: '#67C23A' },
  { abbr: 'ADS', name: '应用数据层', desc: '面向具体应用场景的数据集市', color: '#E6A23C' },
  { abbr: 'DIM', name: '维度数据层', desc: '统一维度表（时间、机构、医师、药材等）', color: '#F56C6C' }
]

// 主题域
const themeDomains = [
  { name: '临床诊疗域', color: '#409EFF', icon: 'FirstAidKit', items: ['门诊/住院记录', '四诊信息', '辨证论治', '处方医嘱', '疗效随访'] },
  { name: '药材资源域', color: '#67C23A', icon: 'Sunrise', items: ['药材基原', '种植信息', '采收加工', '质量检验', '流通追溯'] },
  { name: '名医经验域', color: '#E6A23C', icon: 'User', items: ['医案文献', '跟师记录', '学术思想', '传承谱系'] },
  { name: '科研教育域', color: '#F56C6C', icon: 'Reading', items: ['课题项目', '论文专利', '临床试验', '教学资源'] },
  { name: '健康管理域', color: '#909399', icon: 'Heart', items: ['体质辨识', '健康档案', '养生干预', '随访记录'] },
  { name: '产业经济域', color: '#606266', icon: 'TrendCharts', items: ['市场流通', '价格行情', '产业统计', '政策文件'] }
]

// AI架构
const aiLayers = [
  { name: '应用层', color: '#409EFF', modules: ['智能问诊', '辅助开方', '医案分析', '知识问答', '体质辨识', '经验传承'] },
  { name: '能力层', color: '#67C23A', modules: ['辨证推理引擎', '方剂生成引擎', 'NLP理解引擎', '多模态融合', 'RAG检索增强', '思维链推理'] },
  { name: '模型层', color: '#E6A23C', modules: ['基座模型 (Qwen/Baichuan/DeepSeek)', '领域增量预训练', 'SFT监督微调', 'RLHF人类反馈对齐'] },
  { name: '知识层', color: '#F56C6C', modules: ['经典古籍语料库', '名医医案数据库', '诊疗指南知识库', '知识图谱 (Neo4j)', '向量检索库 (Milvus)'] }
]

const getLayerTag = (layer) => {
  const map = { '前端': 'primary', '后端': 'success', '存储': 'warning', '大数据': 'danger', 'AI': '', '安全': 'info', 'DevOps': '' }
  return map[layer] || ''
}
</script>

<style scoped>
.architecture-page {
  padding: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

/* 分层架构 */
.layer-view {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.arch-layer {
  width: 100%;
  max-width: 1100px;
}

.layer-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  border-radius: 10px;
  color: #fff;
  margin-bottom: 12px;
}

.layer-icon {
  width: 40px;
  height: 40px;
  background: rgba(255,255,255,0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.layer-info h3 {
  font-size: 16px;
  margin: 0;
}

.layer-info p {
  font-size: 12px;
  opacity: 0.85;
  margin: 2px 0 0;
}

.layer-modules {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0 8px;
  margin-bottom: 8px;
}

.module-card {
  flex: 1;
  min-width: 140px;
  max-width: 200px;
  border: 1px solid;
  border-radius: 8px;
  padding: 12px;
  text-align: center;
  background: #fff;
  transition: transform 0.2s, box-shadow 0.2s;
}

.module-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}

.module-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 8px;
}

.module-name {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.module-tech {
  font-size: 11px;
  color: #909399;
}

.layer-arrow {
  text-align: center;
  padding: 4px 0;
}

/* 数据流向 */
.dataflow-view {
  overflow-x: auto;
  padding: 10px 0;
}

.flow-container {
  display: flex;
  align-items: flex-start;
  gap: 0;
  min-width: 900px;
}

.flow-stage {
  flex: 1;
  min-width: 160px;
}

.stage-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px 8px 0 0;
  color: #fff;
}

.stage-num {
  width: 22px;
  height: 22px;
  background: rgba(255,255,255,0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.stage-name {
  font-size: 13px;
  font-weight: 600;
}

.stage-content {
  border: 1px solid #ebeef5;
  border-top: none;
  border-radius: 0 0 8px 8px;
  padding: 10px;
}

.flow-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #606266;
  padding: 3px 0;
}

.flow-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  align-self: center;
  margin-top: 20px;
}

/* 部署架构 */
.deploy-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.deploy-zone {
  border: 1px solid #ebeef5;
  border-radius: 10px;
  overflow: hidden;
}

.zone-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
}

.zone-nodes {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px;
}

.node-card {
  flex: 1;
  min-width: 180px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  transition: box-shadow 0.2s;
}

.node-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.node-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 10px;
}

.node-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.node-detail {
  font-size: 12px;
  color: #909399;
}

/* 数据分层 */
.data-arch-card {
  margin-top: 20px;
}

.data-layers {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}

.data-layer {
  width: 100%;
  max-width: 700px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background: #fff;
}

.dl-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: 6px;
  color: #fff;
  white-space: nowrap;
}

.dl-abbr {
  font-size: 16px;
  font-weight: 700;
}

.dl-name {
  font-size: 13px;
  font-weight: 500;
}

.dl-desc {
  font-size: 13px;
  color: #606266;
  flex: 1;
}

.data-layer-arrow {
  padding: 4px 0;
}

/* 主题域 */
.theme-domains {
  margin-top: 24px;
}

.theme-domains h4 {
  font-size: 15px;
  color: #303133;
  margin-bottom: 16px;
}

.domain-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

.domain-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  transition: box-shadow 0.2s;
}

.domain-card:hover {
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.domain-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
}

.domain-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.domain-items {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

/* AI架构 */
.ai-arch-card {
  margin-top: 20px;
}

.ai-layers {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.ai-layer {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.ai-layer:first-child {
  border-radius: 8px 8px 0 0;
}

.ai-layer:last-child {
  border-radius: 0 0 8px 8px;
}

.ai-layer:not(:last-child) {
  border-bottom: none;
}

.ai-layer-header {
  padding: 10px 20px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}

.ai-layer-modules {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px 16px;
}

.ai-module {
  padding: 6px 14px;
  background: #f5f7fa;
  border-radius: 16px;
  font-size: 12px;
  color: #606266;
  border: 1px solid #ebeef5;
}

/* 技术选型 */
.tech-view {
  padding: 0;
}

.overview-card {
  margin-bottom: 20px;
}
</style>
