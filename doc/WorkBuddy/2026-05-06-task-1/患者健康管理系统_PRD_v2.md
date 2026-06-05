# 患者健康管理系统 PRD v2.0

> **版本**：v2.0 | **更新日期**：2026-05-06 | **状态**：正式版
> **文档编号**：HCP-PRD-2026-V2.0

---

## 目录

1. [概述与愿景](#1-概述与愿景)
2. [系统架构](#2-系统架构)
3. [角色体系与功能矩阵](#3-角色体系与功能矩阵)
4. [核心功能模块详规](#4-核心功能模块详规)
5. [AI接口层规格](#5-ai接口层规格)
6. [数据库设计](#6-数据库设计)
7. [患者档案自录功能](#7-患者档案自录功能)
8. [非功能需求](#8-非功能需求)
9. [版本路线图](#9-版本路线图)

---

## 1. 概述与愿景

### 1.1 产品定位

**患者健康管理系统（Healthcare Patient Management System, HPMS）** 是一款面向企业级客户的智能化健康管理SaaS平台。系统以**患者健康档案**为核心资产，整合**AI大模型**、**数字人交互**、**智能随访**三大能力，为企业主、健康管理机构、医生和患者提供全流程、个性化、可持续的健康管理服务。

### 1.2 核心价值主张

| 价值维度 | 具体描述 |
|---------|---------|
| **患者端** | 便捷自录健康档案、AI数字健管师7×24小时陪伴、体征异常实时预警、任务打卡养成健康习惯 |
| **企业主（采购方）** | 员工健康脱敏看板、套餐采购管理、ROI量化分析、员工满意度提升 |
| **企业主（供给方）** | 健管师/医生团队管理、套餐发布运营、数字人形象定制、服务质量监控 |
| **健管师** | AI辅助患者管理、智能随访摘要、干预方案生成、数字人视频发送 |
| **医生** | 患者全貌视图、报告解读批注、多学科MDT协作 |
| **客服** | 全渠道统一工单、AI自动处理率≥80%、满意度闭环追踪 |
| **超管** | AI接口统一配置、权限审计、数据合规管理 |

### 1.3 设计原则

- **隐私优先**：患者档案授权链路全程记录，支持撤回
- **AI增强，非替代**：AI承担重复性工作，人工聚焦复杂决策
- **数据驱动**：所有功能设计基于可量化指标
- **多端协同**：Web/App/小程序/穿戴设备数据实时同步

---

## 2. 系统架构

### 2.1 技术架构分层

```
┌─────────────────────────────────────────────────────────────────┐
│                        终端接入层                                 │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Web端   │  │ iOS/Android │ │微信小程序│  │穿戴设备BLE│  │ REST API │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API网关层                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Kong/Apisix API Gateway │ 认证鉴权 │ 限流熔断 │ 请求路由      ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI接口层 + 业务服务层                        │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│  │ LLM接口服务     │ │ TTS接口服务    │ │ SadTalker服务  │          │
│  │ 192.168.0.126  │ │ 192.168.0.214 │ │ 192.168.0.214 │          │
│  │ :8802/chat     │ │ :7778/        │ │ :7860/        │          │
│  └───────────────┘ └───────────────┘ └───────────────┘          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     业务服务层                               │  │
│  │ 用户服务 │ 档案服务 │ 随访服务 │ 预警服务 │ 工单服务 │ 支付服务 │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     异步任务层                               │  │
│  │         Kafka消息队列 │ AI任务队列 │ 定时任务调度            │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据层                                     │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │ MySQL  │ │InfluxDB│ │ Milvus │ │ MinIO  │ │  Redis │        │
│  │ 业务库  │ │时序库   │ │向量库   │ │ 文件库  │ │ 缓存库  │        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      安全合规层                                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ RBAC权限控制   │ │ 数据加密存储   │ │ 审计日志      │            │
│  │ 操作留痕       │ │ GDPR/个保法   │ │ 隐私计算      │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心AI Agent体系

| Agent名称 | 类型 | 核心能力 | 调用接口 |
|-----------|------|---------|---------|
| **HEALTH_QA** | 对话问答 | 健康知识问答、指标解读、就医建议 | LLM |
| **PLAN_GEN** | 方案生成 | 个性化干预计划生成、任务拆解 | LLM |
| **RISK_ANALYSIS** | 风险分析 | 体征异常识别、疾病风险评估 | LLM + 规则引擎 |
| **REPORT_PARSE** | 报告解析 | 检查报告OCR提取、结构化录入 | LLM + OCR |
| **FOLLOWUP_SUMMARY** | 随访摘要 | 对话摘要提取、异常标记、归档 | LLM |
| **CS_AGENT** | 客服智能 | 工单分类、意图识别、回复建议 | LLM |
| **DIGITAL_MANAGER** | 数字健管师 | 数字人形象+语音+对话+情绪感知 | SadTalker + TTS + LLM |

### 2.3 技术栈选型

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端Web | React 18 + Ant Design 5 + UmiJS | 企业级中台 |
| 移动端 | Flutter 3.x / React Native | iOS/Android跨平台 |
| 小程序 | Taro 4.x | 微信/支付宝/抖音小程序 |
| 后端 | Spring Boot 3.x + Spring Cloud Alibaba | 微服务架构 |
| 数据库 | MySQL 8.0 | 业务核心数据 |
| 时序数据库 | InfluxDB 2.x | 体征数据存储 |
| 向量数据库 | Milvus 2.x | 健康知识检索 |
| 文件存储 | MinIO | 影像/文档对象存储 |
| 缓存 | Redis Cluster | 会话/Token/热点数据 |
| 消息队列 | Apache Kafka | 异步解耦、事件驱动 |
| AI推理 | vLLM / Ollama | LLM本地部署 |
| TTS | 腾讯云TTS / Azure / CosyVoice | 语音合成 |
| 数字人 | SadTalker + Wav2Lip | 唇形驱动数字人 |
| 搜索 | Elasticsearch 8.x | 日志/文档检索 |

---

## 3. 角色体系与功能矩阵

### 3.1 七大角色定义

| 角色 | 代码 | 描述 | 归属 |
|------|------|------|------|
| **患者** | PATIENT | 终端用户，健康档案所有者 | 独立/企业绑定 |
| **采购方企业主** | ORG_BUYER | 患者所在企业决策者，套餐采购方 | 企业 |
| **供给方企业主** | ORG_PROVIDER | 健康服务机构决策者，服务提供方 | 企业 |
| **健康管理师** | HEALTH_MANAGER | 一线服务执行者，AI辅助 | 供给方企业 |
| **医生** | DOCTOR | 医疗专业决策者 | 供给方企业 |
| **客服** | CUSTOMER_SERVICE | 客户问题处理 | 供给方企业 |
| **超级管理员** | SUPER_ADMIN | 系统全局配置与审计 | 平台方 |

### 3.2 角色功能矩阵

| 功能模块 | 患者 | ORG_BUYER | ORG_PROVIDER | 健管师 | 医生 | 客服 | 超管 |
|---------|-----|----------|--------------|-------|------|------|------|
| **档案管理** | | | | | | | |
| 自录健康档案 | ✅ | - | - | 查看授权 | 查看授权 | - | 查看 |
| 档案授权管理 | ✅ | - | - | - | - | - | - |
| **AI交互** | | | | | | | |
| 数字健管师对话 | ✅ | - | - | 辅助对话 | - | - | - |
| AI随访摘要 | - | - | - | ✅ | ✅ | - | - |
| 数字人视频发送 | - | - | - | ✅ | ✅ | - | - |
| **体征监测** | | | | | | | |
| 体征数据录入 | ✅ | - | - | - | - | - | - |
| 异常预警查看 | ✅ | - | - | ✅ | ✅ | - | - |
| **服务管理** | | | | | | | |
| 套餐管理 | - | 采购 | 发布/配置 | - | - | - | - |
| 干预计划 | - | - | - | 创建/执行 | 审核 | - | - |
| 任务打卡 | ✅ | - | - | 追踪 | - | - | - |
| **企业管理** | | | | | | | |
| 团队管理 | - | 员工管理 | 健管师/医生 | - | - | - | - |
| 数字人形象定制 | - | - | ✅ | - | - | - | - |
| **数据分析** | | | | | | | |
| 个人健康报告 | ✅ | - | - | 患者报告 | 患者报告 | - | - |
| 企业健康看板 | - | 脱敏看板 | 服务数据 | - | - | - | - |
| **工单服务** | | | | | | | |
| 发起工单 | ✅ | - | - | - | - | - | - |
| 处理工单 | - | - | - | - | - | ✅ | - |
| **系统配置** | | | | | | | |
| AI接口配置 | - | - | - | - | - | - | ✅ |
| 权限审计 | - | - | - | - | - | - | ✅ |

---

## 4. 核心功能模块详规

### 4.1 患者端功能

#### 4.1.1 健康档案自录（重点功能）

患者可通过多方式录入以下7类健康档案：

| 档案类型 | 录入方式 | AI辅助能力 |
|---------|---------|-----------|
| 基础信息 | 表单填写 | 自动校验格式、历史数据复用 |
| 病历/门诊记录 | 文字输入 + PDF上传 | OCR提取关键信息、结构化存储 |
| 检查化验单 | 图片/PDF上传 | OCR提取指标值、异常标注、参考范围对比 |
| 影像报告 | PDF上传 + DICOM存储 | 关键结论提取、影像部位标注 |
| 用药记录 | 扫码/手动录入 | 药品知识关联、禁忌提醒 |
| 手术史 | 表单填写 + 手术记录上传 | 时间线自动生成 |
| 体征监测 | 手动录入/穿戴设备同步 | 趋势图可视化、异常预警 |

#### 4.1.2 数字健管师交互

- **7×24小时AI对话**：基于患者档案上下文，提供个性化健康咨询
- **数字人形象**：支持2D虚拟形象，通过SadTalker驱动唇形动画
- **语音交互**：支持语音输入、TTS语音播报
- **情绪感知**：识别患者情绪状态，必要时转人工健管师

#### 4.1.3 任务打卡

- 健管师/AI生成的干预任务（用药提醒、运动计划等）
- 每日打卡签到
- 连续打卡激励机制（徽章、积分）

#### 4.1.4 健康报告

- 周报/月报自动生成
- 指标趋势分析
- AI健康建议

### 4.2 采购方企业主（ORG_BUYER）功能

#### 4.2.1 员工健康管理

- **员工绑定**：批量导入/邀请员工加入企业
- **健康档案查看**（需员工授权）：仅查看脱敏后的健康状态概览
- **健康积分/激励机制配置**

#### 4.2.2 套餐采购

- **浏览服务套餐**：查看供给方发布的健康管理套餐
- **在线购买**：支持企业采购套餐
- **合同管理**：电子合同签署、服务条款确认

#### 4.2.3 数据看板

- **员工健康汇总**：年龄分布、疾病风险分布、高风险人数
- **服务使用情况**：套餐核销率、员工参与度
- **ROI分析**：健康管理投入产出比估算（ absenteeism reduction 等指标）

### 4.3 供给方企业主（ORG_PROVIDER）功能

#### 4.3.1 团队管理

- **健管师管理**：新增/禁用/角色分配/工作量配置
- **医生管理**：新增/资质审核/专科领域设置
- **客服管理**：工单分配规则设置

#### 4.3.2 服务套餐管理

- **创建套餐**：套餐名称、定价、服务内容、适用人群
- **上下架管理**：套餐状态控制
- **服务合同**：与采购方签署服务协议

#### 4.3.3 数字人形象定制

- **形象选择**：预置数字人模板库
- **个性化定制**：声音选择、问候语配置、虚拟背景
- **品牌标识**：企业Logo嵌入

#### 4.3.4 服务数据监控

- **团队业绩看板**：服务患者数、随访完成率
- **质量监控**：患者满意度、工单响应时长

### 4.4 健康管理师功能

#### 4.4.1 患者工作台

- **患者列表**：按风险等级/服务状态筛选
- **患者详情**：档案概览、最新体征、待办任务
- **干预计划管理**：创建/调整/执行干预计划

#### 4.4.2 AI辅助功能

- **随访摘要**：AI自动总结患者对话要点
- **方案推荐**：AI根据患者档案推荐干预方案
- **风险预警**：AI识别体征异常并推送提醒

#### 4.4.3 数字人视频发送

- 选择预置/定制的数字人形象
- 输入/AI生成话术
- 生成数字人视频并发送给患者

### 4.5 医生功能

#### 4.5.1 患者全貌视图

- **时间线展示**：就诊历史、检查报告、用药变化
- **报告解读**：PDF/影像在线查看、AI辅助结论提取
- **批注功能**：对报告添加个人解读和医嘱

#### 4.5.2 MDT协作

- **发起多学科会诊**：邀请相关科室医生
- **共享病历资料**：加密传输、限时访问
- **会诊记录归档**

### 4.6 客服功能

#### 4.6.1 全渠道工单

- **渠道接入**：Web/小程序/电话/邮件统一进入工单系统
- **智能分类**：AI自动识别工单类型（咨询/投诉/建议/故障）
- **优先级判定**：基于紧急程度智能排序

#### 4.6.2 AI辅助处理

- **回复建议**：AI生成回复草稿，客服确认/修改后发送
- **相似工单推荐**：历史工单解决方案快速复用
- **自动处理**：简单问题（如密码重置）AI自动处理

#### 4.6.3 工单闭环

- **满意度回访**：工单关闭后自动发送满意度调研
- **SLA监控**：工单响应时长、处理时长监控

### 4.7 超级管理员功能

#### 4.7.1 AI接口配置

- **LLM配置**：选择模型（Qwen3-8B-VL）、API地址、超参
- **TTS配置**：语音引擎、声音列表、音量/语速
- **SadTalker配置**：分辨率、面部增强、回调地址
- **数字孪生配置**：数字人视频生成接口地址

#### 4.7.2 企业管理

- **企业入驻审核**：新企业主资质审核
- **企业配额管理**：用户数/存储空间/API调用配额

#### 4.7.3 审计合规

- **操作日志审计**：所有敏感操作留痕
- **数据导出管理**：敏感数据导出审批
- **权限变更记录**：RBAC变更历史追踪

---

## 5. AI接口层规格

### 5.1 LLM接口（文字推理引擎）

#### 5.1.1 接口配置

| 属性 | 值 |
|------|-----|
| **Base URL** | `http://192.168.0.126:8802` |
| **端点** | `/chat` |
| **方法** | `POST` |
| **协议** | HTTP REST |

#### 5.1.2 请求规格

```json
POST /chat
Content-Type: application/json

{
  "session_id": "sess_abc123",
  "agent_type": "HEALTH_QA",
  "messages": [
    {
      "role": "system",
      "content": "你是一位专业的健康管理师助手..."
    },
    {
      "role": "user", 
      "content": "我的血压最近有点高，应该注意什么？"
    }
  ],
  "context": {
    "patient_id": "p_12345",
    "latest_vitals": {
      "blood_pressure_systolic": 145,
      "blood_pressure_diastolic": 92
    },
    "medical_history": ["hypertension_family"]
  },
  "generation_config": {
    "temperature": 0.3,
    "max_tokens": 500,
    "top_p": 0.9,
    "stream": true
  }
}
```

#### 5.1.3 请求参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `session_id` | string | ✅ | 会话唯一标识 |
| `agent_type` | string | ✅ | Agent类型：HEALTH_QA/PLAN_GEN/RISK_ANALYSIS/REPORT_PARSE/FOLLOWUP_SUMMARY/CS_AGENT/DIGITAL_MANAGER |
| `messages` | array | ✅ | 对话历史，格式：[{"role": "user/assistant/system", "content": "..."}] |
| `context` | object | ❌ | 上下文信息，包含患者档案、体征等 |
| `generation_config.temperature` | float | ❌ | 随机性参数，0-1，默认0.3 |
| `generation_config.max_tokens` | int | ❌ | 最大生成长度，默认500 |
| `generation_config.stream` | bool | ❌ | 是否流式返回，默认true |

#### 5.1.4 响应规格

```json
// 流式响应 (stream: true)
data: {"choices": [{"delta": {"content": "根据您提供"}}]}
data: {"choices": [{"delta": {"content": "的血压数据"}}]}
data: {"choices": [{"delta": {"content": "，建议您..."}}]}
data: [DONE]

// 非流式响应 (stream: false)
{
  "id": "chatcmpl_abc123",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "根据您提供的血压数据，建议您..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 150,
    "total_tokens": 250
  }
}
```

#### 5.1.5 医疗护栏规则

| 规则类型 | 描述 | 处理方式 |
|---------|------|---------|
| **禁止确诊** | 禁止AI给出疾病诊断结论 | 回复："建议您就医进行专业检查" |
| **药物指导限制** | 禁止AI指导处方药用法 | 回复："请遵医嘱用药" |
| **情绪危机检测** | 检测到自杀/自伤倾向 | 强制转人工，并推送危机热线 |
| **敏感信息过滤** | 过滤政治/暴力/色情内容 | 拒绝回复并记录 |

#### 5.1.6 Agent提示词模板

```markdown
# HEALTH_QA Agent 提示词
你是一位专业的健康管理师助手，名字叫"小健"。

## 核心原则
1. 只提供健康科普和生活建议，不做疾病诊断
2. 所有建议需标注"仅供参考，请以医生意见为准"
3. 发现异常指标主动提醒就医
4. 语气亲切专业，使用通俗易懂的语言

## 能力范围
- 健康知识问答
- 指标解读与参考范围说明
- 生活方式建议（饮食/运动/睡眠）
- 就医科室推荐

## 禁忌事项
- 不得给出诊断结论（如"你得了XX病"）
- 不得指导处方药用法用量
- 不得替代专业医疗建议
```

---

### 5.2 TTS接口（文字转语音）

#### 5.2.1 接口配置

| 属性 | 值 |
|------|-----|
| **Base URL** | `http://192.168.0.214:7778` |
| **端点** | `/` |
| **方法** | `POST` |
| **协议** | HTTP REST |

#### 5.2.2 请求规格

```json
POST /
Content-Type: application/json

{
  "text": "您好，我是您的数字健康管理师小健。根据您最近的血压记录，我建议您...",
  "voice_id": "health_manager_female_01",
  "emotion": "caring",
  "audio_format": "mp3",
  "sample_rate": 24000,
  "speed": 1.0,
  "pitch": 0
}
```

#### 5.2.3 请求参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `text` | string | ✅ | 待合成文本，最大2000字符 |
| `voice_id` | string | ✅ | 声音ID，预置声音列表见附录 |
| `emotion` | string | ❌ | 情感标签：caring/warm/professional/urgent |
| `audio_format` | string | ❌ | 音频格式：mp3/wav/ogg，默认mp3 |
| `sample_rate` | int | ❌ | 采样率：16000/24000/48000，默认24000 |
| `speed` | float | ❌ | 语速：0.5-2.0，默认1.0 |
| `pitch` | int | ❌ | 音调调整：-10~10，默认0 |

#### 5.2.4 响应规格

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "audio_url": "https://storage.example.com/tts/2026/05/06/audio_abc123.mp3",
    "audio_id": "tts_abc123",
    "duration_seconds": 8.5,
    "file_size_bytes": 136000
  }
}
```

#### 5.2.5 预置声音列表

| voice_id | 名称 | 性别 | 适用场景 |
|----------|------|------|---------|
| `health_manager_female_01` | 专业女声-小健 | 女 | 健管师标准音 |
| `health_manager_male_01` | 专业男声-小康 | 男 | 健管师标准音 |
| `doctor_female_01` | 医生女声-林医生 | 女 | 医生报告解读 |
| `doctor_male_01` | 医生男声-张医生 | 男 | 医生报告解读 |
| `elder_caring_female_01` | 关怀女声 | 女 | 老年患者关怀 |
| `digital_avatar_female_01` | 数字人女声 | 女 | 数字人唇音同步 |

#### 5.2.6 降级策略

| 故障场景 | 降级方案 |
|---------|---------|
| TTS服务不可达 | 返回文本，患者端显示字幕 |
| 指定voice_id不存在 | 使用默认声音 `health_manager_female_01` |
| 文本超长 | 自动截断至2000字符并提示 |

---

### 5.3 SadTalker接口（数字人视频生成）

#### 5.3.1 接口配置

| 属性 | 值 |
|------|-----|
| **Base URL** | `http://192.168.0.214:7860` |
| **端点** | `/` |
| **方法** | `POST` |
| **协议** | HTTP REST |
| **任务模式** | 异步（回调通知） |

#### 5.3.2 请求规格

```json
POST /
Content-Type: application/json

{
  "task_id": "task_sadtalker_abc123",
  "avatar_id": "avatar_female_01",
  "audio_url": "https://storage.example.com/tts/2026/05/06/audio_abc123.mp3",
  "source_image_url": "https://storage.example.com/avatars/face_female_01.png",
  "generation_config": {
    "face_enhancer": true,
    "resolution": "512x512",
    "expression_scale": 1.0,
    "still": false
  },
  "callback_url": "http://api.hcms.com/webhook/sadtalker"
}
```

#### 5.3.3 请求参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | ✅ | 任务唯一标识（客户端生成） |
| `avatar_id` | string | ✅ | 数字人形象ID |
| `audio_url` | string | ✅ | 已生成的TTS音频URL |
| `source_image_url` | string | ✅ | 数字人源图片URL（正脸PNG/JPG） |
| `generation_config.face_enhancer` | bool | ❌ | 面部增强，默认true |
| `generation_config.resolution` | string | ❌ | 输出分辨率：512x512/1024x1024 |
| `generation_config.expression_scale` | float | ❌ | 表情强度0.5-1.5，默认1.0 |
| `generation_config.still` | bool | ❌ | true=头部轻微运动，false=唇形驱动 |
| `callback_url` | string | ✅ | 任务完成回调地址 |

#### 5.3.4 回调响应规格

```json
// POST {callback_url}
{
  "task_id": "task_sadtalker_abc123",
  "status": "completed",
  "data": {
    "video_url": "https://storage.example.com/sadtalker/2026/05/06/video_abc123.mp4",
    "thumbnail_url": "https://storage.example.com/sadtalker/2026/05/06/thumb_abc123.jpg",
    "duration_seconds": 8.5,
    "file_size_bytes": 2450000
  },
  "error": null
}
```

#### 5.3.5 错误响应

```json
{
  "task_id": "task_sadtalker_abc123",
  "status": "failed",
  "data": null,
  "error": {
    "code": "AUDIO_FORMAT_UNSUPPORTED",
    "message": "音频格式不支持，请使用mp3格式"
  }
}
```

#### 5.3.6 数字人形象管理

| avatar_id | 名称 | 类型 | 适用场景 |
|-----------|------|------|---------|
| `avatar_female_01` | 专业女健管师 | 2D虚拟形象 | 日常随访、健康提醒 |
| `avatar_male_01` | 专业男健管师 | 2D虚拟形象 | 日常随访、健康提醒 |
| `avatar_doctor_female` | 女医生形象 | 2D虚拟形象 | 报告解读、医嘱说明 |
| `avatar_doctor_male` | 男医生形象 | 2D虚拟形象 | 报告解读、医嘱说明 |
| `avatar_elder_caring` | 关怀型形象 | 2D虚拟形象 | 老年患者关怀 |
| `avatar_custom_001` | 企业定制形象 | 2D企业定制 | 品牌数字代言人 |

#### 5.3.7 降级策略

| 故障场景 | 降级方案 |
|---------|---------|
| SadTalker服务不可达 | 发送纯音频 + 静态头像图片 |
| 源图片不合格 | 使用预置默认头像 |
| 生成超时（>60s） | 自动降级为纯音频 |
| 视频文件过大（>50MB） | 压缩后重新回调 |

---

### 5.4 数字孪生医生接口（数字人视频生成V2）

#### 5.4.1 接口配置

| 属性 | 值 |
|------|-----|
| **Base URL** | `http://127.0.0.1:8123` |
| **端点** | `/api/v1/generate_video` |
| **方法** | `POST` |
| **协议** | HTTP REST |
| **任务模式** | 异步（轮询查询） |

#### 5.4.2 请求规格

```json
POST /api/v1/generate_video
Content-Type: application/json

{
  "video_id": "video_dt_doctor_abc123",
  "doctor_avatar": {
    "avatar_id": "doctor_zhang",
    "name": "张医生",
    "title": "心内科主任医师",
    "hospital": "北京协和医院"
  },
  "script": {
    "text": "您好，我是张医生。根据您上传的检查报告，您的心电图显示ST段轻度压低，建议您近期来医院进行进一步检查。",
    "language": "zh-CN",
    "emotion": "professional_concerned"
  },
  "reference": {
    "image_url": "https://storage.example.com/doctors/photo_zhang.jpg",
    "audio_url": "https://storage.example.com/tts/doctor_zhang.mp3"
  },
  "output_config": {
    "format": "mp4",
    "resolution": "1080x1920",
    "fps": 30,
    "watermark": true
  },
  "webhook_url": "http://api.hcms.com/webhook/digital_doctor"
}
```

#### 5.4.3 请求参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `video_id` | string | ✅ | 视频任务唯一标识 |
| `doctor_avatar.avatar_id` | string | ✅ | 医生形象ID |
| `doctor_avatar.name` | string | ✅ | 医生姓名（显示在视频中） |
| `doctor_avatar.title` | string | ❌ | 医生职称 |
| `doctor_avatar.hospital` | string | ❌ | 所属医院 |
| `script.text` | string | ✅ | 口播文本（医生语音） |
| `script.language` | string | ❌ | 语言，默认zh-CN |
| `script.emotion` | string | ❌ | 情感：professional/professional_concerned/warm |
| `reference.image_url` | string | ❌ | 医生照片（用于形象驱动） |
| `reference.audio_url` | string | ❌ | 预先录制的医生音频 |
| `output_config.format` | string | ❌ | 输出格式：mp4/webm |
| `output_config.resolution` | string | ❌ | 分辨率：720x1280/1080x1920 |
| `output_config.fps` | int | ❌ | 帧率：24/30 |
| `output_config.watermark` | bool | ❌ | 是否添加水印 |
| `webhook_url` | string | ❌ | 完成回调地址 |

#### 5.4.4 响应规格

```json
// 提交成功
{
  "code": 0,
  "message": "success",
  "data": {
    "video_id": "video_dt_doctor_abc123",
    "status": "queued",
    "estimated_duration": 10,
    "check_status_url": "http://127.0.0.1:8123/api/v1/video_status/video_dt_doctor_abc123"
  }
}

// 查询状态
GET /api/v1/video_status/{video_id}

{
  "code": 0,
  "data": {
    "video_id": "video_dt_doctor_abc123",
    "status": "completed",  // queued/processing/completed/failed
    "progress": 100,
    "result": {
      "video_url": "https://storage.example.com/digital_doctor/video_abc123.mp4",
      "duration_seconds": 12.5,
      "file_size_bytes": 5120000
    }
  }
}
```

#### 5.4.5 与SadTalker对比

| 特性 | SadTalker | 数字孪生医生 |
|------|-----------|-------------|
| **适用场景** | 健管师数字人 | 专业医生形象 |
| **形象定制** | 企业可定制 | 基于真实医生照片 |
| **输出质量** | 基础2D | 高清/超清可选 |
| **医生信息** | 无 | 姓名/职称/医院展示 |
| **情感表达** | 基础情感 | 专业关切情感 |
| **水印** | 可选 | 默认有水印 |

---

### 5.5 数字人视频生成完整流程

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   LLM生成    │────▶│    TTS合成    │────▶│  音频文件    │
│   口播文本   │     │  语音合成     │     │   .mp3      │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   回调通知    │◀────│  数字人视频   │◀────│  音频驱动    │
│  业务系统    │     │  生成完成     │     │ SadTalker/  │
│             │     │              │     │ 数字孪生     │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   视频文件   │
                    │   .mp4      │
                    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  发送给患者   │
                    │  (推送/站内) │
                    └──────────────┘
```

---

## 6. 数据库设计

### 6.1 数据库选型与说明

| 数据库 | 用途 | 特点 |
|-------|------|------|
| **MySQL 8.0** | 业务核心数据 | ACID事务、复杂查询 |
| **InfluxDB** | 体征时序数据 | 高写入、时序聚合 |
| **Milvus** | 健康知识向量 | 相似度检索 |
| **MinIO** | 文件对象存储 | 结构化文件、DICOM |

### 6.2 MySQL核心表结构（26张表）

#### 6.2.1 用户与认证相关表

**表1：users（用户表）**

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    user_code VARCHAR(32) NOT NULL UNIQUE COMMENT '用户编码',
    username VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    real_name VARCHAR(64) COMMENT '真实姓名',
    id_card VARCHAR(18) COMMENT '身份证号（加密存储）',
    phone VARCHAR(20) COMMENT '手机号',
    email VARCHAR(128) COMMENT '邮箱',
    avatar_url VARCHAR(512) COMMENT '头像URL',
    gender TINYINT COMMENT '性别：0未知 1男 2女',
    birth_date DATE COMMENT '出生日期',
    emergency_contact VARCHAR(64) COMMENT '紧急联系人',
    emergency_phone VARCHAR(20) COMMENT '紧急联系电话',
    blood_type VARCHAR(4) COMMENT '血型：A/B/AB/O',
    allergic_history TEXT COMMENT '过敏史（JSON数组）',
    family_history TEXT COMMENT '家族病史（JSON数组）',
    status TINYINT NOT NULL DEFAULT 1 COMMENT '状态：0禁用 1正常 2待激活',
    last_login_at DATETIME COMMENT '最后登录时间',
    last_login_ip VARCHAR(45) COMMENT '最后登录IP',
    privacy_agreement TINYINT NOT NULL DEFAULT 1 COMMENT '隐私协议：0未同意 1已同意',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME COMMENT '软删除时间',
    INDEX idx_phone (phone),
    INDEX idx_user_code (user_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

**表2：user_roles（用户角色关联表）**

```sql
CREATE TABLE user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_code VARCHAR(32) NOT NULL COMMENT '角色代码：PATIENT/ORG_BUYER/ORG_PROVIDER/HEALTH_MANAGER/DOCTOR/CUSTOMER_SERVICE/SUPER_ADMIN',
    enterprise_id BIGINT COMMENT '所属企业ID（ORG_BUYER/ORG_PROVIDER时必填）',
    dept_id BIGINT COMMENT '部门ID',
    position VARCHAR(64) COMMENT '职位',
    is_primary TINYINT NOT NULL DEFAULT 0 COMMENT '是否主角色：0否 1是',
    effective_start_date DATE COMMENT '角色生效开始日期',
    effective_end_date DATE COMMENT '角色生效结束日期',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT COMMENT '创建人ID',
    UNIQUE KEY uk_user_role (user_id, role_code, enterprise_id),
    INDEX idx_role_code (role_code),
    INDEX idx_enterprise_id (enterprise_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';
```

**表3：enterprises（企业表）**

```sql
CREATE TABLE enterprises (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    enterprise_code VARCHAR(32) NOT NULL UNIQUE COMMENT '企业编码',
    enterprise_name VARCHAR(128) NOT NULL COMMENT '企业名称',
    enterprise_type VARCHAR(16) NOT NULL COMMENT '企业类型：ORG_BUYER采购方/ORG_PROVIDER供给方/BOTH双向',
    business_license_url VARCHAR(512) COMMENT '营业执照URL',
    legal_person VARCHAR(64) COMMENT '法人代表',
    contact_person VARCHAR(64) COMMENT '联系人',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    contact_email VARCHAR(128) COMMENT '联系邮箱',
    province VARCHAR(32) COMMENT '省份',
    city VARCHAR(32) COMMENT '城市',
    address VARCHAR(256) COMMENT '详细地址',
    employee_count INT COMMENT '员工人数规模',
    industry VARCHAR(64) COMMENT '所属行业',
    logo_url VARCHAR(512) COMMENT '企业Logo URL',
    description TEXT COMMENT '企业简介',
    status TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0待审核 1审核通过 2审核拒绝 3已禁用',
    audit_remark VARCHAR(512) COMMENT '审核备注',
    audited_by BIGINT COMMENT '审核人ID',
    audited_at DATETIME COMMENT '审核时间',
    contract_start_date DATE COMMENT '合同开始日期',
    contract_end_date DATE COMMENT '合同结束日期',
    max_user_count INT COMMENT '最大用户配额',
    max_storage_gb INT COMMENT '最大存储配额GB',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME COMMENT '软删除时间',
    INDEX idx_enterprise_type (enterprise_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业表';
```

**表4：service_contracts（服务合同表）**

```sql
CREATE TABLE service_contracts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    contract_code VARCHAR(64) NOT NULL UNIQUE COMMENT '合同编号',
    contract_name VARCHAR(256) NOT NULL COMMENT '合同名称',
    buyer_enterprise_id BIGINT NOT NULL COMMENT '采购方企业ID',
    provider_enterprise_id BIGINT NOT NULL COMMENT '供给方企业ID',
    contract_file_url VARCHAR(512) COMMENT '合同文件URL',
    start_date DATE NOT NULL COMMENT '合同开始日期',
    end_date DATE NOT NULL COMMENT '合同结束日期',
    total_amount DECIMAL(12,2) COMMENT '合同总金额',
    payment_status VARCHAR(16) COMMENT '付款状态：unpaid/partially_paid/paid',
    paid_amount DECIMAL(12,2) DEFAULT 0 COMMENT '已付款金额',
    service_type VARCHAR(32) COMMENT '服务类型：health_management/medical_consultation/all',
    included_user_count INT COMMENT '包含用户数量',
    included_services TEXT COMMENT '包含服务列表（JSON）',
    auto_renewal TINYINT DEFAULT 0 COMMENT '是否自动续约：0否 1是',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '状态：pending/active/expired/terminated',
    termination_reason VARCHAR(512) COMMENT '终止原因',
    signed_at DATETIME COMMENT '签署时间',
    signed_by BIGINT COMMENT '签署人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_buyer (buyer_enterprise_id),
    INDEX idx_provider (provider_enterprise_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='服务合同表';
```

**表5：service_packages（服务套餐表）**

```sql
CREATE TABLE service_packages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    package_code VARCHAR(64) NOT NULL UNIQUE COMMENT '套餐编码',
    package_name VARCHAR(128) NOT NULL COMMENT '套餐名称',
    provider_enterprise_id BIGINT NOT NULL COMMENT '供给方企业ID',
    category VARCHAR(32) COMMENT '套餐类别：basic/standard/premium/custom',
    description TEXT COMMENT '套餐描述',
    service_contents TEXT NOT NULL COMMENT '服务内容详情（JSON数组）',
    target_users TEXT COMMENT '适用人群描述',
    duration_days INT COMMENT '服务时长（天）',
    original_price DECIMAL(10,2) COMMENT '原价',
    sale_price DECIMAL(10,2) COMMENT '售价',
    discount_rate DECIMAL(5,2) COMMENT '折扣率',
    max_user_count INT COMMENT '可用人数上限',
    sold_count INT DEFAULT 0 COMMENT '已售数量',
    cover_image_url VARCHAR(512) COMMENT '封面图URL',
    detail_images TEXT COMMENT '详情图URL列表（JSON数组）',
    includes_digital_avatar TINYINT DEFAULT 0 COMMENT '是否包含数字人服务：0否 1是',
    includes_tts_reminder TINYINT DEFAULT 0 COMMENT '是否包含TTS提醒：0否 1是',
    status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft待发布/on_shelf上架/off_shelf下架',
    published_at DATETIME COMMENT '上架时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT COMMENT '创建人ID',
    INDEX idx_provider (provider_enterprise_id),
    INDEX idx_category (category),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='服务套餐表';
```

#### 6.2.2 健康档案相关表

**表6：health_profiles（健康档案主表）**

```sql
CREATE TABLE health_profiles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    profile_code VARCHAR(64) NOT NULL UNIQUE COMMENT '档案编号',
    patient_id BIGINT NOT NULL COMMENT '患者用户ID',
    enterprise_id BIGINT COMMENT '绑定企业ID（ORG_BUYER）',
    basic_info JSON COMMENT '基础信息JSON',
    height_cm DECIMAL(5,1) COMMENT '身高cm',
    weight_kg DECIMAL(5,1) COMMENT '体重kg',
    bmi DECIMAL(4,1) COMMENT 'BMI指数',
    blood_type VARCHAR(4) COMMENT '血型',
    allergic_history JSON COMMENT '过敏史JSON数组',
    family_history JSON COMMENT '家族病史JSON数组',
    surgical_history JSON COMMENT '手术史JSON数组',
    chronic_diseases JSON COMMENT '慢性病史JSON数组',
    current_medications JSON COMMENT '当前用药JSON数组',
    lifestyle JSON COMMENT '生活方式：饮食/运动/睡眠/烟酒',
    health_score INT COMMENT '健康评分0-100',
    risk_level VARCHAR(16) COMMENT '风险等级：low/moderate/high/critical',
    health_goals TEXT COMMENT '健康目标',
    profile_completeness DECIMAL(5,2) DEFAULT 0 COMMENT '档案完整度百分比',
    avatar_url VARCHAR(512) COMMENT '患者头像（用于数字人）',
    consent_file_url VARCHAR(512) COMMENT '知情同意书URL',
    consent_signed_at DATETIME COMMENT '知情同意签署时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient (patient_id),
    INDEX idx_enterprise (enterprise_id),
    INDEX idx_risk_level (risk_level),
    INDEX idx_health_score (health_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康档案主表';
```

**表7：health_profile_authorizations（档案授权记录表）**

```sql
CREATE TABLE health_profile_authorizations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    authorization_code VARCHAR(64) NOT NULL UNIQUE COMMENT '授权编号',
    profile_id BIGINT NOT NULL COMMENT '健康档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    authorized_user_id BIGINT NOT NULL COMMENT '被授权用户ID（如健管师/医生）',
    authorized_role VARCHAR(32) NOT NULL COMMENT '授权角色',
    authorized_enterprise_id BIGINT COMMENT '授权企业ID',
    authorization_scope JSON NOT NULL COMMENT '授权范围：可查看的档案模块',
    authorization_duration JSON COMMENT '授权期限设置',
    authorization_purpose VARCHAR(256) COMMENT '授权用途说明',
    patient_confirmed TINYINT DEFAULT 0 COMMENT '患者是否确认：0待确认 1已确认 2已拒绝',
    patient_confirmed_at DATETIME COMMENT '患者确认时间',
    is_active TINYINT DEFAULT 1 COMMENT '是否生效：0已撤回 1生效中',
    revoked_at DATETIME COMMENT '撤回时间',
    revoke_reason VARCHAR(256) COMMENT '撤回原因',
    expires_at DATETIME COMMENT '授权过期时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_authorized_user (authorized_user_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康档案授权记录表';
```

**表8：medical_records（病历记录表）**

```sql
CREATE TABLE medical_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '记录编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    record_type VARCHAR(32) NOT NULL COMMENT '记录类型：outpatient住院/inpatient门诊/emergency急诊',
    visit_date DATE NOT NULL COMMENT '就诊日期',
    hospital_name VARCHAR(128) COMMENT '就诊医院',
    department VARCHAR(64) COMMENT '就诊科室',
    doctor_name VARCHAR(64) COMMENT '主诊医生',
    chief_complaint TEXT COMMENT '主诉',
    diagnosis TEXT COMMENT '诊断结果',
    treatment_plan TEXT COMMENT '治疗方案',
    medical_advice TEXT COMMENT '医嘱',
    prescription JSON COMMENT '处方明细JSON',
    attachment_urls JSON COMMENT '附件URL列表：病历文档/图片',
    icd_code VARCHAR(16) COMMENT 'ICD疾病编码',
    cost DECIMAL(10,2) COMMENT '费用',
    followup_date DATE COMMENT '复诊日期',
    remarks TEXT COMMENT '备注',
    ai_summary TEXT COMMENT 'AI摘要',
    source VARCHAR(16) DEFAULT 'manual' COMMENT '来源：manual手动/self_report自录/ai_parse AI解析',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_visit_date (visit_date),
    INDEX idx_record_type (record_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='病历记录表';
```

**表9：lab_results（检查化验单表）**

```sql
CREATE TABLE lab_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    result_code VARCHAR(64) NOT NULL UNIQUE COMMENT '结果编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    test_type VARCHAR(64) COMMENT '检验类型：blood尿常规/biochemistry生化/hormone激素/tumor_marker肿瘤标志物',
    test_name VARCHAR(128) NOT NULL COMMENT '检验项目名称',
    test_date DATE NOT NULL COMMENT '检验日期',
    report_date DATE COMMENT '报告日期',
    hospital_name VARCHAR(128) COMMENT '检验机构',
    specimen_type VARCHAR(32) COMMENT '标本类型：blood尿液/tissue组织',
    results JSON NOT NULL COMMENT '检验结果JSON：[{item:项目名,value:值,unit:单位,reference:参考值,flag:异常标志}]',
    ai_interpretation TEXT COMMENT 'AI解读',
    abnormal_count INT DEFAULT 0 COMMENT '异常项数量',
    critical_count INT DEFAULT 0 COMMENT '危急值数量',
    attachment_urls JSON COMMENT '附件URL：报告PDF/图片',
    raw_ocr_text TEXT COMMENT 'OCR原始识别文本',
    confidence DECIMAL(5,2) COMMENT 'OCR识别置信度',
    reviewed_by BIGINT COMMENT '审核医生ID',
    reviewed_at DATETIME COMMENT '审核时间',
    source VARCHAR(16) DEFAULT 'manual' COMMENT '来源：manual手动/self_report自录/upload上传/ai_parse AI解析',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_test_date (test_date),
    INDEX idx_test_type (test_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检查化验单表';
```

**表10：imaging_reports（影像报告表）**

```sql
CREATE TABLE imaging_reports (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_code VARCHAR(64) NOT NULL UNIQUE COMMENT '报告编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    imaging_type VARCHAR(32) NOT NULL COMMENT '影像类型：xray/X线/CT/MRI磁共振/ultrasound超声/PET/CT/钼靶',
    body_part VARCHAR(64) NOT NULL COMMENT '检查部位',
    exam_name VARCHAR(128) NOT NULL COMMENT '检查项目名',
    exam_date DATE NOT NULL COMMENT '检查日期',
    report_date DATE COMMENT '报告日期',
    hospital_name VARCHAR(128) COMMENT '检查机构',
    equipment VARCHAR(64) COMMENT '检查设备',
    clinical_diagnosis TEXT COMMENT '临床诊断',
    examination_findings TEXT COMMENT '影像学表现',
    conclusion TEXT COMMENT '影像学结论',
    ai_finding TEXT COMMENT 'AI辅助发现',
    impression TEXT COMMENT '印象/建议',
    dicom_study_uid VARCHAR(128) COMMENT 'DICOM Study UID',
    dicom_series_uid VARCHAR(128) COMMENT 'DICOM Series UID',
    dicom_instance_uid VARCHAR(128) COMMENT 'DICOM Instance UID',
    dicom_file_urls JSON COMMENT 'DICOM文件URL列表',
    report_file_url VARCHAR(512) COMMENT '报告PDF URL',
    thumbnail_url VARCHAR(512) COMMENT '缩略图URL',
    attachment_urls JSON COMMENT '其他附件URL',
    doctor_name VARCHAR(64) COMMENT '报告医生',
    reviewed_by BIGINT COMMENT '审核医生ID',
    source VARCHAR(16) DEFAULT 'manual' COMMENT '来源：manual手动/self_report自录/upload上传/ai_parse AI解析',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_exam_date (exam_date),
    INDEX idx_imaging_type (imaging_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='影像报告表';
```

**表11：medication_records（用药记录表）**

```sql
CREATE TABLE medication_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '记录编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    drug_name VARCHAR(128) NOT NULL COMMENT '药品名称',
    generic_name VARCHAR(128) COMMENT '通用名',
    drug_category VARCHAR(64) COMMENT '药品类别：western中西药/herbal中药/injection注射',
    specification VARCHAR(64) COMMENT '规格：如100mg/片',
    dosage VARCHAR(64) COMMENT '单次剂量：如1片',
    dosage_unit VARCHAR(16) COMMENT '剂量单位：片/粒/支/ml',
    frequency VARCHAR(32) COMMENT '用药频率：QD每日一次/BID每日两次/TID每日三次/QID每日四次',
    route VARCHAR(32) COMMENT '给药途径：oral口服/injection注射/topical外用',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    is_current TINYINT DEFAULT 1 COMMENT '是否当前用药：0否 1是',
    purpose VARCHAR(256) COMMENT '用药目的',
    prescriber VARCHAR(64) COMMENT '开药医生',
    hospital_name VARCHAR(128) COMMENT '开药医院',
    side_effects TEXT COMMENT '不良反应',
    contraindications TEXT COMMENT '禁忌症',
    instructions TEXT COMMENT '用药指导',
    ai_interaction_warning TEXT COMMENT 'AI药物相互作用警告',
    barcode VARCHAR(64) COMMENT '药品条形码',
    attachment_urls JSON COMMENT '处方/说明书附件',
    remarks TEXT COMMENT '备注',
    source VARCHAR(16) DEFAULT 'manual' COMMENT '来源：manual手动/scan扫码/ai_parse AI解析',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_drug_name (drug_name),
    INDEX idx_current (is_current),
    INDEX idx_start_date (start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用药记录表';
```

**表12：surgery_records（手术记录表）**

```sql
CREATE TABLE surgery_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '记录编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    surgery_name VARCHAR(256) NOT NULL COMMENT '手术名称',
    surgery_code VARCHAR(32) COMMENT '手术编码ICD-9-CM-3',
    surgery_type VARCHAR(32) COMMENT '手术类型：elective择期/emergency急诊/minimally_invasive微创',
    surgery_date DATE NOT NULL COMMENT '手术日期',
    hospital_name VARCHAR(128) NOT NULL COMMENT '手术医院',
    department VARCHAR(64) COMMENT '手术科室',
    surgeon_name VARCHAR(64) COMMENT '主刀医生',
    anesthesiologist VARCHAR(64) COMMENT '麻醉医生',
    anesthesia_type VARCHAR(32) COMMENT '麻醉方式：general全麻/regional局麻/local局麻',
    surgery_duration_minutes INT COMMENT '手术时长（分钟）',
    hospitalization_days INT COMMENT '住院天数',
    surgery_findings TEXT COMMENT '手术所见',
    surgery_procedure TEXT COMMENT '手术经过',
    postoperative_diagnosis TEXT COMMENT '术后诊断',
    complications TEXT COMMENT '并发症',
    recovery_status VARCHAR(32) COMMENT '恢复状态：good良好/stable稳定/complicated有并发症',
    followup_plan TEXT COMMENT '随访计划',
    surgery_report_url VARCHAR(512) COMMENT '手术记录PDF URL',
    incision_type VARCHAR(32) COMMENT '切口类型',
    blood_loss_ml INT COMMENT '术中出血量ml',
    transfusion_ml INT COMMENT '输血量ml',
    remarks TEXT COMMENT '备注',
    source VARCHAR(16) DEFAULT 'manual' COMMENT '来源：manual手动/self_report自录/upload上传',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_surgery_date (surgery_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='手术记录表';
```

#### 6.2.3 体征监测表（InfluxDB）

**表13：vital_records（体征记录表-InfluxDB）**

```sql
-- InfluxDB Measurement: vital_records
-- Tags: patient_id, vital_type, device_type
-- Fields: value, unit, extra(JSON)
-- Timestamp: event_time

-- 血压数据
vital_records,patient_id=p_12345,vital_type=blood_pressure,device_type=ble_monitor value_systolic=145,value_diastolic=92,unit="mmHg",hr=78 1714972800000000000

-- 心率数据
vital_records,patient_id=p_12345,vital_type=heart_rate,device_type=ble_monitor value=72,unit="bpm" 1714972800000000000

-- 血糖数据
vital_records,patient_id=p_12345,vital_type=blood_glucose,device_type=ble_monitor value=5.6,unit="mmol/L",meal_status="fasting" 1714972800000000000

-- 体温数据
vital_records,patient_id=p_12345,vital_type=temperature,device_type=manual value=36.8,unit="℃" 1714972800000000000

-- 血氧数据
vital_records,patient_id=p_12345,vital_type=spo2,device_type=ble_monitor value=97,unit="%" 1714972800000000000

-- 体重数据
vital_records,patient_id=p_12345,vital_type=weight,device_type=smart_scale value=65.5,unit="kg",bmi=22.3 1714972800000000000

-- 步数数据
vital_records,patient_id=p_12345,vital_type=steps,device_type=smart_watch value=8500,unit="steps",distance_km=6.5,calories=280 1714972800000000000
```

#### 6.2.4 风险评估与干预表

**表14：risk_assessments（风险评估表）**

```sql
CREATE TABLE risk_assessments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    assessment_code VARCHAR(64) NOT NULL UNIQUE COMMENT '评估编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    assessment_type VARCHAR(32) NOT NULL COMMENT '评估类型：cardiovascular心血管/diabetes糖尿病/cancer癌症/mental_health心理',
    assessment_name VARCHAR(128) COMMENT '评估量表名称',
    score DECIMAL(5,1) COMMENT '评估得分',
    max_score DECIMAL(5,1) COMMENT '满分',
    risk_level VARCHAR(16) NOT NULL COMMENT '风险等级：low/moderate/high/critical',
    risk_factors JSON COMMENT '风险因素JSON',
    protective_factors JSON COMMENT '保护因素JSON',
    ai_analysis TEXT COMMENT 'AI分析报告',
    recommendations TEXT COMMENT '改善建议',
    assessed_by VARCHAR(32) COMMENT '评估方：ai/doctor/health_manager',
    assessor_id BIGINT COMMENT '评估人ID（人工评估时）',
    assessment_date DATE NOT NULL COMMENT '评估日期',
    next_assessment_date DATE COMMENT '下次评估日期',
    questionnaire_answers JSON COMMENT '问卷答案JSON',
    supporting_data JSON COMMENT '支撑数据（如体征报告引用）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_type (assessment_type),
    INDEX idx_risk_level (risk_level),
    INDEX idx_assessment_date (assessment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风险评估表';
```

**表15：intervention_plans（干预计划表）**

```sql
CREATE TABLE intervention_plans (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plan_code VARCHAR(64) NOT NULL UNIQUE COMMENT '计划编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    plan_name VARCHAR(256) NOT NULL COMMENT '计划名称',
    plan_type VARCHAR(32) COMMENT '计划类型：medication药物/exercise运动/diet饮食/sleep睡眠/stress心理',
    target_disease VARCHAR(128) COMMENT '目标疾病',
    risk_level VARCHAR(16) COMMENT '关联风险等级',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    duration_days INT COMMENT '计划天数',
    overall_goal TEXT COMMENT '总体目标',
    success_metrics JSON COMMENT '成功指标JSON',
    status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft草稿/active进行中/paused暂停/completed已完成/cancelled已取消',
    progress_percent INT DEFAULT 0 COMMENT '完成进度百分比',
    ai_generated TINYINT DEFAULT 0 COMMENT '是否AI生成：0否 1是',
    ai_confidence DECIMAL(5,2) COMMENT 'AI生成置信度',
    approved_by BIGINT COMMENT '审核人ID',
    approved_at DATETIME COMMENT '审核时间',
    cancel_reason VARCHAR(256) COMMENT '取消原因',
    actual_end_date DATE COMMENT '实际结束日期',
    completion_rate DECIMAL(5,2) COMMENT '任务完成率',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT COMMENT '创建人ID',
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_status (status),
    INDEX idx_plan_type (plan_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='干预计划表';
```

**表16：plan_tasks（计划任务表）**

```sql
CREATE TABLE plan_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_code VARCHAR(64) NOT NULL UNIQUE COMMENT '任务编号',
    plan_id BIGINT NOT NULL COMMENT '计划ID',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    task_name VARCHAR(256) NOT NULL COMMENT '任务名称',
    task_type VARCHAR(32) NOT NULL COMMENT '任务类型：medication_reminder用药提醒/exercise运动/diet饮食/measurement测量/checkup检查/survey问卷',
    task_description TEXT COMMENT '任务描述',
    target_value VARCHAR(64) COMMENT '目标值：如"30分钟有氧运动"',
    target_unit VARCHAR(16) COMMENT '目标单位',
    frequency VARCHAR(32) COMMENT '执行频率：daily每天/weekly每周/custom自定义',
    scheduled_time TIME COMMENT '计划执行时间',
    scheduled_days VARCHAR(32) COMMENT '计划执行日期：0101010（周一三五六）',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    reminder_enabled TINYINT DEFAULT 1 COMMENT '是否提醒：0否 1是',
    reminder_times JSON COMMENT '提醒时间点JSON',
    reminder_channel VARCHAR(32) COMMENT '提醒渠道：push_push短信/wechat/in_app',
    ai_reminder_content TEXT COMMENT 'AI生成的提醒内容',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending待执行/active进行中/skipped已跳过/completed已完成/missed已错过',
    difficulty_level TINYINT COMMENT '难度等级：1-5',
    points INT DEFAULT 0 COMMENT '完成后奖励积分',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_plan (plan_id),
    INDEX idx_patient (patient_id),
    INDEX idx_status (status),
    INDEX idx_scheduled (scheduled_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='计划任务表';
```

**表17：task_records（任务执行记录表）**

```sql
CREATE TABLE task_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '记录编号',
    task_id BIGINT NOT NULL COMMENT '任务ID',
    plan_id BIGINT COMMENT '计划ID',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    scheduled_date DATE NOT NULL COMMENT '计划执行日期',
    scheduled_time TIME COMMENT '计划执行时间',
    actual_time DATETIME COMMENT '实际执行时间',
    status VARCHAR(16) NOT NULL COMMENT '执行状态：completed已完成/partially部分完成/skipped已跳过/not_done未完成',
    completion_value VARCHAR(64) COMMENT '实际完成值',
    completion_rate DECIMAL(5,2) COMMENT '完成率百分比',
    evidence_type VARCHAR(32) COMMENT '凭证类型：photo照片/video视频/manual手动确认',
    evidence_urls JSON COMMENT '凭证URL列表',
    self_feeling VARCHAR(32) COMMENT '自我感受：great良好/general一般/tired疲惫',
    side_effects TEXT COMMENT '不良反应',
    notes TEXT COMMENT '患者备注',
    ai_evaluation TEXT COMMENT 'AI评价',
    points_earned INT DEFAULT 0 COMMENT '获得积分',
    check_in_badge JSON COMMENT '打卡徽章',
    notified TINYINT DEFAULT 0 COMMENT '是否已提醒：0否 1是',
    notified_at DATETIME COMMENT '提醒时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task (task_id),
    INDEX idx_patient (patient_id),
    INDEX idx_date (scheduled_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务执行记录表';
```

**表18：followup_records（随访记录表）**

```sql
CREATE TABLE followup_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '随访编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    followup_type VARCHAR(32) NOT NULL COMMENT '随访类型：routine常规/post_visit诊后/acute急性/scheduled计划',
    followup_date DATE NOT NULL COMMENT '随访日期',
    followup_mode VARCHAR(32) COMMENT '随访方式：call电话/video视频/in_person面访/message消息/digital_avatar数字人',
    followup_purpose VARCHAR(256) COMMENT '随访目的',
    respondent_name VARCHAR(64) COMMENT '受访者',
    conversation_summary TEXT COMMENT '对话摘要',
    ai_summary TEXT COMMENT 'AI生成摘要',
    patient_status VARCHAR(32) COMMENT '患者状态：stable稳定/improving好转/worsening恶化',
    chief_complaints TEXT COMMENT '主诉',
    vital_signs_summary JSON COMMENT '体征汇总JSON',
    medication_adherence VARCHAR(16) COMMENT '用药依从性：good良好/partial部分/none无',
    side_effects_reported TEXT COMMENT '报告不良反应',
    adherence_issues TEXT COMMENT '依从性问题',
    ai_suggestions TEXT COMMENT 'AI建议',
    followup_actions JSON COMMENT '后续行动JSON',
    next_followup_date DATE COMMENT '下次随访日期',
    next_followup_type VARCHAR(32) COMMENT '下次随访类型',
    digital_avatar_video_url VARCHAR(512) COMMENT '数字人视频URL（如通过数字人随访）',
    tts_audio_url VARCHAR(512) COMMENT 'TTS音频URL',
    conversation_id VARCHAR(64) COMMENT 'AI对话会话ID',
    duration_seconds INT COMMENT '随访时长（秒）',
    satisfaction INT COMMENT '满意度评分1-5',
    followup_by BIGINT NOT NULL COMMENT '随访执行人ID',
    followup_by_name VARCHAR(64) COMMENT '随访执行人姓名',
    followup_by_role VARCHAR(32) COMMENT '随访执行人角色',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_followup_date (followup_date),
    INDEX idx_followup_by (followup_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='随访记录表';
```

**表19：alert_records（预警记录表）**

```sql
CREATE TABLE alert_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    alert_code VARCHAR(64) NOT NULL UNIQUE COMMENT '预警编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    alert_type VARCHAR(32) NOT NULL COMMENT '预警类型：vital_abnormal体征异常/risk_escalation风险升级/medication_miss用药遗漏/followup_miss随访遗漏/crisis危机',
    alert_level VARCHAR(16) NOT NULL COMMENT '预警级别：info提示/warning警告/critical危急',
    alert_source VARCHAR(32) COMMENT '预警来源：ai_algorithm AI算法/rule_engine规则引擎/manual人工',
    trigger_condition VARCHAR(256) COMMENT '触发条件描述',
    trigger_value VARCHAR(64) COMMENT '触发值',
    reference_value VARCHAR(64) COMMENT '参考值',
    vital_type VARCHAR(32) COMMENT '体征类型（如是体征预警）',
    risk_disease VARCHAR(128) COMMENT '关联疾病风险',
    risk_score DECIMAL(5,2) COMMENT '风险评分',
    ai_analysis TEXT COMMENT 'AI分析',
    recommendations TEXT COMMENT '建议',
    action_required TINYINT DEFAULT 1 COMMENT '是否需要处理：0否 1是',
    action_taken TEXT COMMENT '已采取行动',
    handler_id BIGINT COMMENT '处理人ID',
    handler_name VARCHAR(64) COMMENT '处理人姓名',
    handled_at DATETIME COMMENT '处理时间',
    patient_notified TINYINT DEFAULT 0 COMMENT '是否通知患者：0否 1是',
    patient_notified_at DATETIME COMMENT '患者通知时间',
    notification_channel VARCHAR(32) COMMENT '通知渠道',
    escalated TINYINT DEFAULT 0 COMMENT '是否升级：0否 1是',
    escalated_at DATETIME COMMENT '升级时间',
    escalation_reason VARCHAR(256) COMMENT '升级原因',
    resolution_status VARCHAR(16) DEFAULT 'pending' COMMENT '解决状态：pending待处理/in_progress处理中/resolved已解决/closed已关闭',
    resolved_at DATETIME COMMENT '解决时间',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_type (alert_type),
    INDEX idx_level (alert_level),
    INDEX idx_status (resolution_status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警记录表';
```

#### 6.2.5 服务与工单表

**表20：health_assessments（健康评估表）**

```sql
CREATE TABLE health_assessments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    assessment_code VARCHAR(64) NOT NULL UNIQUE COMMENT '评估编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    assessment_category VARCHAR(32) NOT NULL COMMENT '评估类别：periodic定期/semi_annual半年/annual年度/special专项',
    assessment_period_start DATE COMMENT '评估周期开始',
    assessment_period_end DATE COMMENT '评估周期结束',
    overall_score INT COMMENT '综合评分0-100',
    score_change DECIMAL(5,1) COMMENT '较上次评分变化',
    dimension_scores JSON COMMENT '维度评分JSON：{physical:体能/mental:心理/nutrition:营养/sleep:睡眠/social:社交}',
    health_trends JSON COMMENT '健康趋势JSON',
    achievements JSON COMMENT '成就JSON',
    improvements JSON COMMENT '改善空间JSON',
    ai_report TEXT COMMENT 'AI评估报告',
    ai_insights JSON COMMENT 'AI洞察JSON',
    recommendations JSON COMMENT '建议JSON',
    next_assessment_date DATE COMMENT '下次评估日期',
    report_url VARCHAR(512) COMMENT '报告URL',
    report_generated_at DATETIME COMMENT '报告生成时间',
    shared_with JSON COMMENT '分享对象JSON',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_category (assessment_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康评估表';
```

**表21：work_orders（工单表）**

```sql
CREATE TABLE work_orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_code VARCHAR(64) NOT NULL UNIQUE COMMENT '工单编号',
    order_type VARCHAR(32) NOT NULL COMMENT '工单类型：consult咨询/complaint投诉/suggestion建议/feedback反馈/system系统',
    order_subtype VARCHAR(64) COMMENT '子类型',
    priority VARCHAR(16) NOT NULL DEFAULT 'normal' COMMENT '优先级：low低/normal普通/high高/urgent紧急',
    title VARCHAR(256) NOT NULL COMMENT '工单标题',
    description TEXT NOT NULL COMMENT '工单描述',
    patient_id BIGINT COMMENT '患者ID',
    patient_name VARCHAR(64) COMMENT '患者姓名',
    patient_phone VARCHAR(20) COMMENT '患者电话',
    channel VARCHAR(32) NOT NULL COMMENT '来源渠道：app/web/miniprogram/wechat热线/call电话/email邮件',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending待分配/assigned已分配/processing处理中/pending_reply待回复/resolved已解决/closed已关闭',
    assigned_to BIGINT COMMENT '处理人ID',
    assigned_to_name VARCHAR(64) COMMENT '处理人姓名',
    assigned_at DATETIME COMMENT '分配时间',
    sla_deadline DATETIME COMMENT 'SLA截止时间',
    sla_breached TINYINT DEFAULT 0 COMMENT '是否SLA超时：0否 1是',
    response_time_minutes INT COMMENT '首次响应时长（分钟）',
    resolution_time_hours DECIMAL(8,2) COMMENT '解决时长（小时）',
    customer_rating INT COMMENT '客户评分1-5',
    customer_feedback TEXT COMMENT '客户反馈',
    auto_processed TINYINT DEFAULT 0 COMMENT '是否AI自动处理：0否 1是',
    ai_processing_result TEXT COMMENT 'AI处理结果',
    related_order_id BIGINT COMMENT '关联工单ID',
    attachments JSON COMMENT '附件URL列表',
    tags JSON COMMENT '标签',
    internal_notes TEXT COMMENT '内部备注',
    satisfaction_survey_sent TINYINT DEFAULT 0 COMMENT '满意度调研是否已发送',
    satisfaction_survey_sent_at DATETIME COMMENT '满意度调研发送时间',
    closed_at DATETIME COMMENT '关闭时间',
    close_reason VARCHAR(256) COMMENT '关闭原因',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_type (order_type),
    INDEX idx_priority (priority),
    INDEX idx_status (status),
    INDEX idx_patient (patient_id),
    INDEX idx_assigned (assigned_to),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工单表';
```

#### 6.2.6 AI相关表

**表22：ai_conversations（AI对话记录表）**

```sql
CREATE TABLE ai_conversations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    conversation_code VARCHAR(64) NOT NULL UNIQUE COMMENT '会话编号',
    session_id VARCHAR(128) NOT NULL COMMENT '会话ID',
    profile_id BIGINT COMMENT '档案ID（可选）',
    patient_id BIGINT COMMENT '患者ID',
    agent_type VARCHAR(32) NOT NULL COMMENT 'Agent类型：HEALTH_QA/PLAN_GEN/RISK_ANALYSIS/REPORT_PARSE/FOLLOWUP_SUMMARY/CS_AGENT/DIGITAL_MANAGER',
    interaction_mode VARCHAR(16) COMMENT '交互模式：text文本/voice语音/video数字人',
    messages JSON NOT NULL COMMENT '对话消息JSON',
    context_summary TEXT COMMENT '上下文摘要',
    patient_feedback INT COMMENT '患者满意度1-5',
    escalated TINYINT DEFAULT 0 COMMENT '是否转人工：0否 1是',
    escalated_to BIGINT COMMENT '转人工处理人ID',
    escalation_reason VARCHAR(256) COMMENT '转人工原因',
    emotional_flag VARCHAR(32) COMMENT '情绪标记：normal正常/concerned担忧/anxious焦虑/crisis危机',
    risk_flagged TINYINT DEFAULT 0 COMMENT '是否标记风险：0否 1是',
    llm_model VARCHAR(64) COMMENT '使用的LLM模型',
    token_usage JSON COMMENT 'Token使用量JSON',
    duration_seconds INT COMMENT '会话时长（秒）',
    ended_at DATETIME COMMENT '结束时间',
    end_way VARCHAR(32) COMMENT '结束方式：completed完成/timeout超时/manual_stop手动停止/escalated转人工',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_patient (patient_id),
    INDEX idx_agent (agent_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI对话记录表';
```

**表23：sadtalker_tasks（SadTalker任务表）**

```sql
CREATE TABLE sadtalker_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_code VARCHAR(64) NOT NULL UNIQUE COMMENT '任务编号',
    task_id_external VARCHAR(128) COMMENT '外部任务ID',
    profile_id BIGINT COMMENT '档案ID',
    patient_id BIGINT COMMENT '患者ID',
    task_type VARCHAR(32) NOT NULL COMMENT '任务类型：followup随访/reminder提醒/education教育/greeting问候',
    avatar_id VARCHAR(64) NOT NULL COMMENT '数字人形象ID',
    avatar_url VARCHAR(512) COMMENT '数字人形象URL',
    script_text TEXT COMMENT '口播文本',
    source_image_url VARCHAR(512) COMMENT '源图片URL',
    audio_url VARCHAR(512) COMMENT 'TTS音频URL',
    video_url VARCHAR(512) COMMENT '生成视频URL',
    thumbnail_url VARCHAR(512) COMMENT '视频缩略图URL',
    duration_seconds DECIMAL(5,1) COMMENT '视频时长',
    file_size_bytes BIGINT COMMENT '文件大小',
    generation_config JSON COMMENT '生成配置JSON',
    callback_url VARCHAR(512) COMMENT '回调URL',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending待提交/submitted已提交/processing生成中/completed完成/failed失败',
    error_code VARCHAR(64) COMMENT '错误码',
    error_message TEXT COMMENT '错误信息',
    fallback_used TINYINT DEFAULT 0 COMMENT '是否使用降级策略：0否 1是',
    fallback_type VARCHAR(32) COMMENT '降级类型：audio_only纯音频/static_image静态图',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    sent_to_patient TINYINT DEFAULT 0 COMMENT '是否已发送给患者',
    sent_at DATETIME COMMENT '发送时间',
    sent_channel VARCHAR(32) COMMENT '发送渠道：push/wechat/in_app',
    watched TINYINT DEFAULT 0 COMMENT '患者是否观看',
    watched_at DATETIME COMMENT '观看时间',
    watch_duration_seconds INT COMMENT '观看时长',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient (patient_id),
    INDEX idx_status (status),
    INDEX idx_type (task_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='SadTalker数字人任务表';
```

**表24：tts_tasks（TTS任务表）**

```sql
CREATE TABLE tts_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_code VARCHAR(64) NOT NULL UNIQUE COMMENT '任务编号',
    profile_id BIGINT COMMENT '档案ID',
    patient_id BIGINT COMMENT '患者ID（可选）',
    task_type VARCHAR(32) NOT NULL COMMENT '任务类型：reminder提醒/education教育/announcement通知/custom自定义',
    text_content TEXT NOT NULL COMMENT '待合成文本',
    voice_id VARCHAR(64) NOT NULL COMMENT '声音ID',
    emotion VARCHAR(32) COMMENT '情感标签',
    audio_format VARCHAR(8) DEFAULT 'mp3' COMMENT '音频格式',
    sample_rate INT DEFAULT 24000 COMMENT '采样率',
    speed DECIMAL(3,2) DEFAULT 1.00 COMMENT '语速',
    audio_url VARCHAR(512) COMMENT '生成音频URL',
    duration_seconds DECIMAL(5,1) COMMENT '音频时长',
    file_size_bytes BIGINT COMMENT '文件大小',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending待提交/processing生成中/completed完成/failed失败',
    error_code VARCHAR(64) COMMENT '错误码',
    error_message TEXT COMMENT '错误信息',
    fallback_used TINYINT DEFAULT 0 COMMENT '是否降级：0否 1是',
    related_task_id BIGINT COMMENT '关联任务ID（如用于SadTalker前置音频）',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient (patient_id),
    INDEX idx_status (status),
    INDEX idx_type (task_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='TTS任务表';
```

**表25：avatar_assets（数字人形象资产表）**

```sql
CREATE TABLE avatar_assets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    avatar_code VARCHAR(64) NOT NULL UNIQUE COMMENT '形象编码',
    avatar_name VARCHAR(128) NOT NULL COMMENT '形象名称',
    avatar_type VARCHAR(32) NOT NULL COMMENT '形象类型：preset预置/custom定制/doctor医生',
    enterprise_id BIGINT COMMENT '所属企业ID（定制形象时）',
    owner_type VARCHAR(32) COMMENT '归属类型：platform平台/enterprise企业/individual个人',
    owner_id BIGINT COMMENT '归属者ID',
    base_image_url VARCHAR(512) NOT NULL COMMENT '基础图片URL',
    thumbnail_url VARCHAR(512) COMMENT '缩略图URL',
    gender VARCHAR(8) COMMENT '性别：male/female/unisex',
    age_group VARCHAR(16) COMMENT '年龄段：young青年/middle中年/senior老年',
    style VARCHAR(32) COMMENT '风格：professional专业/caring关怀/friendly友好',
    voice_id VARCHAR(64) COMMENT '关联声音ID',
    role_description VARCHAR(256) COMMENT '角色描述',
    introduction_script TEXT COMMENT '开场白脚本',
    customization_settings JSON COMMENT '定制化设置JSON',
    quality_score DECIMAL(3,1) COMMENT '质量评分',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    is_active TINYINT DEFAULT 1 COMMENT '是否启用：0否 1是',
    is_default TINYINT DEFAULT 0 COMMENT '是否默认形象：0否 1是',
    approved TINYINT DEFAULT 1 COMMENT '审核状态：0待审核 1通过 2拒绝',
    approved_by BIGINT COMMENT '审核人ID',
    approved_at DATETIME COMMENT '审核时间',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_enterprise (enterprise_id),
    INDEX idx_type (avatar_type),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数字人形象资产表';
```

#### 6.2.7 审计日志表

**表26：audit_logs（审计日志表）**

```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    log_code VARCHAR(64) NOT NULL UNIQUE COMMENT '日志编号',
    module VARCHAR(32) NOT NULL COMMENT '模块：user用户/role角色/profile档案/ai_ai/service服务',
    action VARCHAR(64) NOT NULL COMMENT '操作类型：create创建/read读取/update更新/delete删除/login登录/logout登出/export导出/authorize授权/revoke撤回',
    action_type VARCHAR(16) COMMENT '操作分类：data数据/permission权限/config配置/system系统',
    user_id BIGINT COMMENT '操作用户ID',
    user_name VARCHAR(64) COMMENT '操作用户姓名',
    user_role VARCHAR(32) COMMENT '操作用户角色',
    enterprise_id BIGINT COMMENT '操作涉及企业ID',
    target_type VARCHAR(64) COMMENT '操作对象类型',
    target_id BIGINT COMMENT '操作对象ID',
    target_code VARCHAR(64) COMMENT '操作对象编码',
    target_name VARCHAR(256) COMMENT '操作对象名称',
    request_url VARCHAR(512) COMMENT '请求URL',
    request_method VARCHAR(10) COMMENT '请求方法',
    request_params JSON COMMENT '请求参数（脱敏）',
    request_body JSON COMMENT '请求体（脱敏）',
    response_code VARCHAR(16) COMMENT '响应码',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    user_agent TEXT COMMENT 'User-Agent',
    session_id VARCHAR(128) COMMENT '会话ID',
    error_message TEXT COMMENT '错误信息',
    execution_time_ms INT COMMENT '执行时长（毫秒）',
    risk_level VARCHAR(16) COMMENT '风险等级：low低/medium中/high高',
    data_change_summary JSON COMMENT '数据变更摘要',
    consent_granted TINYINT COMMENT '是否涉及知情同意：0否 1是',
    data_classification VARCHAR(32) COMMENT '数据分类：public公开/person一般/sensitive敏感/confidential机密/restricted限阅',
    compliance_tags JSON COMMENT '合规标签：GDPR/个保法/医疗信息分级',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_module (module),
    INDEX idx_action (action),
    INDEX idx_user (user_id),
    INDEX idx_target (target_type, target_id),
    INDEX idx_enterprise (enterprise_id),
    INDEX idx_created (created_at),
    INDEX idx_risk (risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审计日志表';
```

---

## 7. 患者档案自录功能

### 7.1 功能概述

患者档案自录是本系统的核心功能，允许患者自主录入和管理个人健康档案，支持多种录入方式和AI辅助解析。

### 7.2 录入类型与流程

#### 7.2.1 基础信息录入

```
┌─────────────────┐
│  患者发起录入   │
└────────┬────────┘
         ▼
┌─────────────────┐     ┌─────────────────┐
│  表单式录入     │────▶│  历史数据复用   │
│  - 姓名/性别    │     │  (如有记录自动  │
│  - 出生日期    │     │   填充表单)     │
│  - 联系方式    │     └─────────────────┘
│  - 过敏史      │              │
│  - 家族病史    │              ▼
│  - 生活方式    │     ┌─────────────────┐
└─────────────────┘     │  数据格式校验   │
                        │  + 合理性检查   │
                        └────────┬────────┘
                                 ▼
                        ┌─────────────────┐
                        │  档案创建成功   │
                        │  完整度: X%     │
                        └─────────────────┘
```

#### 7.2.2 病历/门诊记录录入

| 步骤 | 操作 | AI辅助 |
|------|------|--------|
| 1 | 文字输入病历内容 | - |
| 2 | 上传病历文档（PDF/图片） | OCR提取文字 |
| 3 | 补充就诊信息（医院/科室/日期） | 自动校验日期格式 |
| 4 | AI解析关键字段 | 结构化提取：诊断/处方/医嘱 |
| 5 | 患者确认修正 | 高亮异常提取供确认 |
| 6 | 存储归档 | 生成时间线视图 |

#### 7.2.3 检查化验单录入

```
┌──────────────────────────────────────────────────────────────┐
│                      检查化验单自录流程                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  拍照/相册    │    │  拍照/相册    │    │  直接输入    │   │
│  │  选择图片     │    │  选择PDF     │    │  手动填表    │   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             ▼                                │
│                    ┌──────────────┐                         │
│                    │   文件上传    │                         │
│                    │  (Max 20MB)  │                         │
│                    └──────┬───────┘                         │
│                             ▼                                │
│                    ┌──────────────┐                         │
│                    │   OCR识别    │                         │
│                    │  + AI解析    │                         │
│                    └──────┬───────┘                         │
│                             ▼                                │
│                    ┌──────────────┐                         │
│                    │  结构化展示   │                         │
│                    │  ┌────────┐  │                         │
│                    │  │指标1   │  │                         │
│                    │  │值:5.6  │  │                         │
│                    │  │参考:3.9│  │  ← 异常标红              │
│                    │  │⚠️偏高  │  │                         │
│                    │  └────────┘  │                         │
│                    └──────┬───────┘                         │
│                             ▼                                │
│                    ┌──────────────┐                         │
│                    │  患者确认    │                         │
│                    │  修正/补充   │                         │
│                    └──────┬───────┘                         │
│                             ▼                                │
│                    ┌──────────────┐                         │
│                    │   存储归档   │                         │
│                    │  生成时间线  │                         │
│                    └──────────────┘                         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

#### 7.2.4 影像报告录入

| 字段 | 说明 | AI辅助 |
|------|------|--------|
| 影像类型 | X线/CT/MRI/超声/PET等 | 自动识别文件内容 |
| 检查部位 | 头部/胸部/腹部等 | 自动识别报告内容 |
| 检查日期 | 日期选择器 | - |
| 检查机构 | 医院名称 | OCR提取 |
| 报告文件 | PDF/图片上传 | - |
| DICOM文件 | DICOM上传 | 存储至MinIO |

#### 7.2.5 用药记录录入

| 方式 | 操作 | AI辅助 |
|------|------|--------|
| 扫码 | 扫描药盒条形码 | 自动匹配药品信息库 |
| 搜索 | 输入药品名称搜索 | 自动填充规格/用法 |
| 手动 | 填写药品详细信息 | 禁忌症/相互作用警告 |

#### 7.2.6 手术史录入

```
┌────────────────────────────────────────────────────────────┐
│                      手术史录入流程                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  方式一：表单录入              方式二：上传手术记录           │
│  ┌──────────────────┐       ┌──────────────────┐         │
│  │ 手术名称          │       │  手术记录PDF/图片 │         │
│  │ 手术日期          │       │       ↓           │         │
│  │ 医院名称          │       │   OCR识别提取     │         │
│  │ 主刀医生          │       │       ↓           │         │
│  │ 手术类型          │       │  关键字段自动填充  │         │
│  │ 麻醉方式          │       │       ↓           │         │
│  │ 术后恢复情况      │       │  患者确认修正     │         │
│  └──────────────────┘       └──────────────────┘         │
│                    │               │                      │
│                    └───────────────┼──────────────────────┘
│                                ▼                           │
│                       ┌──────────────────┐                │
│                       │  AI生成时间线    │                │
│                       │  可视化展示      │                │
│                       └──────────────────┘                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

#### 7.2.7 体征监测数据录入

| 数据来源 | 录入方式 | 说明 |
|---------|---------|------|
| 手动录入 | 表单输入 | 血压/血糖/心率等单次测量 |
| 穿戴设备 | BLE蓝牙同步 | 实时/定时自动上传 |
| 智能设备 | WiFi同步 | 体重秤/血压计等 |
| 导入历史 | CSV/Excel | 批量导入历史数据 |

### 7.3 AI辅助档案识别

#### 7.3.1 OCR识别流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  图片/PDF   │───▶│   图片预处理  │───▶│   OCR识别    │───▶│  文字清洗   │
│  文件上传    │    │ 去噪/旋转    │    │ 文字提取     │    │ 结构化输出   │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                   │
                                                                   ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  患者确认    │◀───│  高亮异常项  │◀───│  AI字段提取  │◀───│  格式规范化  │
│  修正补全    │    │  供确认      │    │  结构化存储   │    │  字段映射    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

#### 7.3.2 AI识别准确率指标

| 文档类型 | OCR准确率 | 结构化准确率 | 异常检测率 |
|---------|----------|-------------|-----------|
| 检查化验单 | ≥95% | ≥90% | ≥85% |
| 影像报告 | ≥90% | ≥85% | ≥80% |
| 门诊病历 | ≥85% | ≥80% | ≥75% |
| 处方单 | ≥95% | ≥92% | ≥90% |

### 7.4 档案完整度计算

```
档案完整度 = Σ(各模块完成度 × 权重) / 总权重 × 100%

模块权重分配：
┌──────────────┬────────┬────────┬─────────────────────────┐
│     模块      │ 权重(%)│ 完成度 │   计算方式              │
├──────────────┼────────┼────────┼─────────────────────────┤
│ 基础信息      │   20   │  X%   │ 必填项/总必填项          │
│ 病历记录      │   15   │  X%   │ 记录数/建议记录数        │
│ 检查化验      │   20   │  X%   │ 最近6个月有记录=100%     │
│ 影像报告      │   10   │  X%   │ 有记录=100%              │
│ 用药记录      │   15   │  X%   │ 当前用药+历史用药完整度  │
│ 手术史        │   10   │  X%   │ 有记录=100%              │
│ 体征数据      │   10   │  X%   │ 最近7天有数据=100%       │
└──────────────┴────────┴────────┴─────────────────────────┘

示例：
基础信息完成80% → 20×0.8 = 16
检查化验完成100% → 20×1.0 = 20
用药记录完成60% → 15×0.6 = 9
...
总完整度 = (16+20+9+...)/100 × 100% = 72%
```

### 7.5 档案授权管理

#### 7.5.1 授权类型

| 授权类型 | 可查看内容 | 有效期 |
|---------|-----------|--------|
| 健管师授权 | 完整档案（限其服务的患者） | 与服务合同绑定 |
| 医生授权 | 完整档案（限就诊相关） | 30天 |
| 企业主授权 | 脱敏健康状态（员工） | 雇佣关系存续 |
| 研究授权 | 脱敏数据（统计分析） | 项目周期 |

#### 7.5.2 授权撤回

患者可随时撤回授权：
- 即时生效
- 记录撤回操作到审计日志
- 通知被授权方授权已失效
- 历史已查看记录不可删除（审计需要）

---

## 8. 非功能需求

### 8.1 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 系统可用性 | ≥99.9% | 年度停机时间<8.76小时 |
| API响应时间(P99) | <500ms | 普通接口 |
| AI对话响应时间(P99) | <3s | 流式输出首字延迟 |
| 数字人视频生成 | <60s | 标准质量 |
| 并发用户数 | ≥10,000 | 同时在线 |
| 数据存储容量 | 支持PB级 | 未来扩展预留 |

### 8.2 安全合规

| 合规要求 | 说明 |
|---------|------|
| **GDPR/个保法** | 个人信息最小化采集、加密存储、用户可撤回同意 |
| **医疗数据** | 分级分类管理、敏感数据脱敏 |
| **等保2.0** | 三级等保认证 |
| **HIPAA** | 如涉及美国用户需符合HIPAA |
| **数据驻留** | 国内用户数据存储于国内服务器 |

### 8.3 可靠性

| 策略 | 说明 |
|------|------|
| **多活部署** | 同城双活 + 异地灾备 |
| **AI服务降级** | 主LLM不可用→备选LLM→纯规则 |
| **TTS降级** | 不可用→字幕展示 |
| **SadTalker降级** | 不可用→静态头像+音频 |
| **数据备份** | 实时同步 + 每日全量 + 7天增量 |

---

## 9. 版本路线图

### 9.1 版本规划

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           版本路线图                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  v1.0 (MVP)        v1.5                  v2.0            v2.5+       │
│  ─────────         ─────                  ─────            ─────        │
│                                                                         │
│  Q1-Q2 2026        Q3-Q4 2026            Q1-Q2 2027       Q3 2027+     │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ 患者端基础功能 │  │ TTS语音合成   │  │ 数字人视频   │  │ 平台化运营  │ │
│  │ 档案自录基础   │  │ 智能随访     │  │ 全流程      │  │ 第三方接入  │ │
│  │ 健管师工作台   │  │ 预警升级     │  │ 企业看板2.0 │  │ 开放API    │ │
│  │ 企业端基础    │  │ 体检对接     │  │ MDT协作     │  │ 开发者生态  │ │
│  │ AI健康问答    │  │ 可穿戴设备   │  │ 数字孪生医生 │  │ 数据市场   │ │
│  │                │  │ 深度集成    │  │ 商业化套餐   │  │            │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ MySQL        │  │ InfluxDB    │  │ 数字人定制   │  │ 国际化      │ │
│  │ Redis        │  │ MinIO       │  │ 企业形象定制 │  │ 多语言支持  │ │
│  │ 基础架构     │  │ 完整数据层   │  │ 多语言       │  │ 海外部署    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 9.2 v1.0 MVP功能清单

| 模块 | 功能点 | 优先级 |
|------|--------|--------|
| 患者端 | 档案自录（表单+图片上传） | P0 |
| 患者端 | AI健康问答（文字） | P0 |
| 患者端 | 任务打卡 | P0 |
| 患者端 | 健康报告 | P1 |
| 健管师端 | 患者工作台 | P0 |
| 健管师端 | 干预计划管理 | P0 |
| 健管师端 | 随访记录 | P0 |
| 企业端 | 员工管理 | P0 |
| 企业端 | 套餐采购 | P1 |
| 企业端 | 健康看板 | P1 |
| 系统端 | 用户认证 | P0 |
| 系统端 | RBAC权限 | P0 |
| 系统端 | 审计日志 | P1 |

### 9.3 v1.5增强功能清单

| 模块 | 功能点 | 优先级 |
|------|--------|--------|
| AI层 | TTS语音合成 | P0 |
| AI层 | 语音提醒推送 | P0 |
| AI层 | 随访摘要AI生成 | P0 |
| 数据层 | 体征时序库(InfluxDB) | P0 |
| 数据层 | 穿戴设备BLE对接 | P1 |
| 数据层 | 体检机构API对接 | P1 |
| 功能 | 预警规则引擎升级 | P0 |
| 功能 | 体检报告解析 | P1 |

### 9.4 v2.0商业化功能清单

| 模块 | 功能点 | 优先级 |
|------|--------|--------|
| AI层 | SadTalker数字人 | P0 |
| AI层 | 数字孪生医生 | P0 |
| AI层 | 数字人视频发送 | P0 |
| 功能 | 企业数字人形象定制 | P0 |
| 功能 | MDT多学科协作 | P1 |
| 功能 | 企业健康看板2.0 | P1 |
| 功能 | ROI分析报告 | P1 |
| 运营 | 商业化套餐定价 | P0 |
| 运营 | 电子合同签署 | P0 |
| 运营 | 发票管理 | P1 |

---

## 附录

### A. 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| 健康档案 | Health Profile | 患者完整的健康信息集合 |
| 数字健管师 | Digital Health Manager | AI驱动的虚拟健康管理师 |
| 干预计划 | Intervention Plan | 针对患者健康目标的改善计划 |
| MDT | Multi-Disciplinary Team | 多学科会诊协作 |
| RBAC | Role-Based Access Control | 基于角色的权限控制 |
| OCR | Optical Character Recognition | 光学字符识别 |
| TTS | Text-to-Speech | 文字转语音 |
| SadTalker | - | 音频驱动的数字人视频生成技术 |

### B. API接口地址汇总

| 接口 | Base URL | 端点 |
|------|----------|------|
| LLM | `http://192.168.0.126:8802` | `/chat` |
| TTS | `http://192.168.0.214:7778` | `/` |
| SadTalker | `http://192.168.0.214:7860` | `/` |
| 数字孪生医生 | `http://127.0.0.1:8123` | `/api/v1/generate_video` |

### C. 角色权限矩阵

| 权限项 | 患者 | ORG_BUYER | ORG_PROVIDER | 健管师 | 医生 | 客服 | 超管 |
|--------|------|----------|--------------|--------|------|------|------|
| 查看自己的档案 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 查看授权的患者档案 | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| 录入/修改自己的档案 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 创建干预计划 | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| 审核干预计划 | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| 查看脱敏企业看板 | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 处理工单 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| 配置AI接口 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 管理企业团队 | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 发布服务套餐 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 采购服务套餐 | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 审计日志查看 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

**文档结束**

*本文档为产品管理内部使用，包含敏感技术信息，请勿外传。*
