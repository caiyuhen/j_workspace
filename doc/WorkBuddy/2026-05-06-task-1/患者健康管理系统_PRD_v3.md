# 患者健康管理系统 PRD v3.0

> **版本**：v3.0 | **更新日期**：2026-05-06 | **状态**：正式版
> **文档编号**：HCP-PRD-2026-V3.0

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

**患者健康管理系统（Healthcare Patient Management System, HPMS）** 是一款面向企业级客户的智能化健康管理SaaS平台。系统以**患者健康档案**为核心资产，整合**AI大模型**、**数字人交互**、**智能随访**、**疾病风险预测**四大能力，为采购企业、员工、自由患者、代理商、健康管理机构、医生和患者提供全流程、个性化、可持续的健康管理服务。

### 1.2 核心价值主张

| 角色类型 | 角色名称 | 核心价值 |
|---------|---------|---------|
| **企业采购方** | 采购健康管理服务企业 | 员工健康管理、套餐采购、ROI量化分析 |
| **企业员工** | 企业健康管理员工 | 便捷健康服务、企业福利、核销使用 |
| **个人用户** | 自由注册患者 | 自主健康管理、AI数字健管师、随时随地 |
| **代理商** | 健康管理服务代理商企业主 | 拓展客户、服务分成、区域运营 |
| **服务提供方** | 健康管理师 | AI辅助服务、效率提升、数字人分身 |
| **医疗专业** | 医生 | 患者全貌、MDT协作、专业价值 |
| **服务支撑** | 客服 | 全渠道工单、AI辅助、满意度闭环 |
| **平台运营** | 超级管理员 | 统一配置、审计合规、运营监控 |

### 1.3 设计原则

- **隐私优先**：患者档案授权链路全程记录，支持撤回
- **AI增强，非替代**：AI承担重复性工作，人工聚焦复杂决策
- **数据驱动**：所有功能设计基于可量化指标
- **多端协同**：Web/App/小程序/穿戴设备数据实时同步
- **代理商赋能**：支持多级代理商拓展企业客户

---

## 2. 系统架构

### 2.1 技术架构分层

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           终端接入层                                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐ │
│  │ Web端   │  │iOS/Android│ │微信小程序│  │穿戴设备BLE│  │  REST API   │ │
│  │ 企业控制台│  │企业员工App│ │患者小程序 │  │设备同步   │  │ 第三方接入  │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           API网关层                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ Kong/Apisix API Gateway │ 认证鉴权 │ 限流熔断 │ 请求路由 │ 协议转换 ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI接口层 + 业务服务层                              │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐            │
│  │ LLM接口服务       │ │ TTS接口服务      │ │ SadTalker服务   │            │
│  │ 192.168.0.126    │ │ 192.168.0.214   │ │ 192.168.0.214  │            │
│  │ :8802/chat       │ │ :7778/          │ │ :7860/         │            │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘            │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐            │
│  │ 疾病风险预测服务  │ │ 数字孪生医生服务  │ │ AI业务编排服务   │            │
│  │ 192.168.0.126    │ │ 192.168.0.214   │ │ 内部编排引擎    │            │
│  │ :5000/api/predict│ │ :8123/api/v1/  │ │                 │            │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘            │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         业务服务层                                  │  │
│  │ 用户服务 │ 档案服务 │ 随访服务 │ 预警服务 │ 工单服务 │ 支付服务 │ 合同服务│ │
│  └───────────────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                         异步任务层                                  │  │
│  │           Kafka消息队列 │ AI任务队列 │ 定时任务调度 │ 代理商分成结算 │    │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            数据层                                        │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │ MySQL  │ │InfluxDB│ │ Milvus │ │ MinIO  │ │  Redis │ │Kafka   │       │
│  │ 业务库  │ │时序库   │ │向量库   │ │ 文件库  │ │ 缓存库  │ │消息队列│       │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          安全合规层                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ RBAC权限控制   │ │ 数据加密存储   │ │ 审计日志      │ │ 隐私计算      │   │
│  │ 操作留痕       │ │ GDPR/个保法   │ │ 分级授权     │ │ 代理商隔离    │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心AI Agent体系

| Agent名称 | 类型 | 核心能力 | 调用接口 |
|-----------|------|---------|---------|
| **HEALTH_QA** | 对话问答 | 健康知识问答、指标解读、就医建议 | LLM |
| **PLAN_GEN** | 方案生成 | 个性化干预计划生成、任务拆解 | LLM |
| **RISK_ANALYSIS** | 风险分析 | 体征异常识别、疾病风险评估 | LLM + 规则引擎 |
| **RISK_PREDICTION** | 疾病预测 | 心血管/糖尿病/癌症等多病种风险预测 | 疾病风险预测API |
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
| 疾病预测 | 自研/集成ML模型 | 多病种风险预测 |

---

## 3. 角色体系与功能矩阵

### 3.1 八大角色定义

| 角色 | 代码 | 描述 | 归属 |
|------|------|------|------|
| **采购健康管理服务企业** | ORG_BUYER | 采购健康管理服务的企业决策者 | 企业 |
| **企业健康管理员工** | EMPLOYEE | 企业员工，享受企业采购的健康服务 | 企业员工 |
| **自由注册患者** | PATIENT | 个人用户，自主注册使用服务 | 独立用户 |
| **健康管理服务代理商** | AGENT | 健康管理服务代理商，区域拓展 | 代理商企业 |
| **健康管理师** | HEALTH_MANAGER | 一线服务执行者，AI辅助 | 服务机构 |
| **医生** | DOCTOR | 医疗专业决策者 | 服务机构 |
| **客服** | CUSTOMER_SERVICE | 客户问题处理 | 服务机构 |
| **超级管理员** | SUPER_ADMIN | 系统全局配置与审计 | 平台方 |

### 3.2 角色功能矩阵

| 功能模块 | ORG_BUYER | EMPLOYEE | PATIENT | AGENT | 健管师 | 医生 | 客服 | 超管 |
|---------|----------|---------|---------|-------|--------|------|------|------|
| **档案管理** | | | | | | | | |
| 自录健康档案 | - | ✅ | ✅ | - | - | - | - | - |
| 档案授权管理 | - | ✅ | ✅ | - | - | - | - | - |
| **AI交互** | | | | | | | | |
| 数字健管师对话 | - | ✅ | ✅ | - | 辅助对话 | - | - | - |
| AI随访摘要 | - | - | - | - | ✅ | ✅ | - | - |
| 疾病风险预测 | - | ✅ | ✅ | - | ✅ | ✅ | - | - |
| 数字人视频发送 | - | - | - | - | ✅ | ✅ | - | - |
| **体征监测** | | | | | | | | |
| 体征数据录入 | - | ✅ | ✅ | - | - | - | - | - |
| 异常预警查看 | - | ✅ | ✅ | - | ✅ | ✅ | - | - |
| **企业管理** | | | | | | | | |
| 员工管理 | ✅ | - | - | ✅ | - | - | - | - |
| 代理商管理 | - | - | - | - | - | - | - | ✅ |
| 团队管理 | - | - | - | ✅ | - | - | - | - |
| **服务管理** | | | | | | | | |
| 套餐管理 | 采购 | 核销使用 | 自主购买 | 代理销售 | 执行服务 | 专业服务 | - | - |
| 干预计划 | - | - | - | - | 创建/执行 | 审核 | - | - |
| 任务打卡 | - | ✅ | ✅ | - | 追踪 | - | - | - |
| **数据分析** | | | | | | | | |
| 企业健康看板 | ✅ | - | - | ✅ | - | - | - | - |
| 个人健康报告 | - | ✅ | ✅ | - | ✅ | ✅ | - | - |
| **工单服务** | | | | | | | | |
| 发起工单 | - | ✅ | ✅ | - | - | - | - | - |
| 处理工单 | - | - | - | - | - | - | ✅ | - |
| **系统配置** | | | | | | | | |
| AI接口配置 | - | - | - | - | - | - | - | ✅ |
| 权限审计 | - | - | - | - | - | - | - | ✅ |

### 3.3 角色关系图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           超级管理员 (SUPER_ADMIN)                        │
│                    配置 │ 审计 │ 代理商管理 │ 平台运营                    │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ 采购健康管理  │  │ 健康管理服务    │  │ 健康管理服务    │
│ 服务企业       │  │ 代理商企业      │  │ 代理商企业      │
│ ORG_BUYER     │  │ AGENT(一级)     │  │ AGENT(二级)     │
└───────┬───────┘  └────────┬────────┘  └────────┬────────┘
        │                    │                    │
        │ 采购服务            │ 代理拓展           │ 代理拓展
        ▼                    ▼                    ▼
┌───────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ 企业员工       │  │ 服务提供企业    │  │ 服务提供企业    │
│ EMPLOYEE      │  │ (签约服务机构)   │  │ (签约服务机构)   │
└───────────────┘  └────────┬────────┘  └────────┬────────┘
                            │                    │
                            │ 服务执行           │ 服务执行
            ┌───────────────┼───────────────────┼───────────────┐
            │               │                   │               │
            ▼               ▼                   ▼               ▼
      ┌───────────┐  ┌───────────┐      ┌───────────┐  ┌───────────┐
      │健康管理师  │  │   医生    │      │   客服    │  │  医生     │
      │ HEALTH_    │  │  DOCTOR  │      │    CS     │  │  DOCTOR   │
      │ MANAGER    │  └───────────┘      └───────────┘  └───────────┘
      └───────────┘
            │
            │ 服务
            ▼
      ┌───────────┐  ┌───────────┐
      │自由注册患者 │  │ 企业员工   │
      │  PATIENT  │  │ EMPLOYEE  │
      └───────────┘  └───────────┘
```

---

## 4. 核心功能模块详规

### 4.1 采购健康管理服务企业（ORG_BUYER）功能

#### 4.1.1 企业入驻与管理

| 功能 | 说明 |
|------|------|
| 企业信息维护 | 营业执照、法人信息、联系人配置 |
| 管理员账号 | 创建/管理企业管理员账号 |
| 部门组织 | 树形部门结构，支持批量导入员工 |

#### 4.1.2 员工健康管理

| 功能 | 说明 |
|------|------|
| 员工绑定 | 批量导入/邀请员工加入企业 |
| 健康服务分配 | 按部门/岗位分配不同健康服务套餐 |
| 健康档案查看（需授权） | 仅查看脱敏后的健康状态概览 |
| 健康积分配置 | 设置员工健康激励积分规则 |
| 团检安排 | 统一安排年度体检计划 |

#### 4.1.3 套餐采购

| 功能 | 说明 |
|------|------|
| 浏览服务套餐 | 查看平台/代理商发布的服务套餐 |
| 对比选择 | 多套餐对比（价格/内容/服务时长） |
| 在线购买 | 支持企业采购套餐、签署电子合同 |
| 订单管理 | 订单状态跟踪、发票申请 |
| 核销管理 | 查看员工套餐核销记录 |

#### 4.1.4 数据看板

| 指标 | 说明 |
|------|------|
| 员工健康汇总 | 年龄分布、疾病风险分布、高风险人数 |
| 服务使用情况 | 套餐核销率、员工参与度、服务满意度 |
| 健康趋势分析 | 员工健康指标变化趋势 |
| ROI分析 | 健康管理投入产出比估算 |

### 4.2 企业健康管理员工（EMPLOYEE）功能

#### 4.2.1 企业员工身份

| 功能 | 说明 |
|------|------|
| 企业绑定 | 通过企业邀请码/二维码加入 |
| 身份认证 | 企业邮箱/工号认证 |
| 福利查看 | 查看企业分配的免费健康服务 |

#### 4.2.2 健康服务使用

| 功能 | 说明 |
|------|------|
| 企业套餐核销 | 使用企业购买的健康服务（限次/限内容） |
| 健康自评 | 完成企业要求的健康风险评估 |
| 体检预约 | 使用企业团检服务预约 |
| 健康任务打卡 | 完成企业健康活动任务 |

#### 4.2.3 档案与服务

- 与自由注册患者功能一致（见4.4节）
- 额外享有企业付费的高级服务

### 4.3 自由注册患者（PATIENT）功能

#### 4.3.1 自主注册与认证

| 功能 | 说明 |
|------|------|
| 手机号注册 | 快速注册、验证码登录 |
| 实名认证 | 身份证实名，提升服务可信度 |
| 医保绑定 | 绑定医保账户（未来扩展） |

#### 4.3.2 健康档案自录

- 详见本文档第7章

#### 4.3.3 自主健康管理

| 功能 | 说明 |
|------|------|
| AI数字健管师 | 7×24小时AI对话、健康咨询 |
| 疾病风险预测 | 多病种风险评估（心血管/糖尿病等） |
| 自主购买服务 | 直接购买健康服务套餐 |
| 任务打卡 | 干预计划任务完成 |
| 健康报告 | 周报/月报自动生成 |

### 4.4 健康管理服务代理商（AGENT）功能

#### 4.4.1 代理商入驻

| 功能 | 说明 |
|------|------|
| 代理商申请 | 提交资质材料、协议签署 |
| 等级管理 | 一级代理/二级代理等级 |
| 区域划分 | 代理服务区域设定 |
| 押金/预付款 | 保证金管理 |

#### 4.4.2 客户拓展

| 功能 | 说明 |
|------|------|
| 企业客户开发 | 拓展采购健康管理服务的企业 |
| 邀请码管理 | 生成企业邀请码 |
| 客户签约 | 协助企业完成服务签约 |
| 客户管理 | 企业客户列表、状态跟踪 |

#### 4.4.3 服务产品代理

| 功能 | 说明 |
|------|------|
| 套餐代理 | 代理销售平台/服务机构的健康套餐 |
| 价格管理 | 在代理价基础上设置零售价（平台限价） |
| 订单管理 | 代理订单跟踪、佣金结算 |
| 分成结算 | 佣金比例、结算周期、对账 |

#### 4.4.4 代理商看板

| 指标 | 说明 |
|------|------|
| 拓展业绩 | 新增企业数、新增员工数 |
| 销售收入 | 代理销售额、佣金收益 |
| 客户健康 | 代理客户服务健康数据概览 |
| 分成报表 | 佣金明细、提现记录 |

#### 4.4.5 代理商团队管理

| 功能 | 说明 |
|------|------|
| 业务员管理 | 添加/管理销售业务员 |
| 团队业绩 | 团队销售业绩排行 |
| 业务员分成 | 业务员佣金分配规则 |

### 4.5 健康管理师功能

#### 4.5.1 患者工作台

| 功能 | 说明 |
|------|------|
| 患者列表 | 按风险等级/服务状态/分配规则筛选 |
| 患者详情 | 档案概览、最新体征、待办任务 |
| 干预计划管理 | 创建/调整/执行干预计划 |
| 随访管理 | 制定随访计划、执行随访记录 |

#### 4.5.2 AI辅助功能

| 功能 | 说明 |
|------|------|
| 随访摘要 | AI自动总结患者对话要点 |
| 方案推荐 | AI根据患者档案推荐干预方案 |
| 风险预警 | AI识别体征异常并推送提醒 |
| 疾病预测 | 调用疾病风险预测API，评估多病种风险 |
| 报告解读 | AI辅助解读检查报告关键指标 |

#### 4.5.3 数字人服务

| 功能 | 说明 |
|------|------|
| 数字人形象选择 | 预置/定制数字人形象 |
| 话术输入 | 手动输入或AI生成话术 |
| 视频生成 | SadTalker/数字孪生医生生成视频 |
| 视频发送 | 发送给患者（推送/站内信） |

### 4.6 医生功能

#### 4.6.1 患者全貌视图

| 功能 | 说明 |
|------|------|
| 时间线展示 | 就诊历史、检查报告、用药变化 |
| 报告解读 | PDF/影像在线查看、AI辅助结论提取 |
| 批注功能 | 对报告添加个人解读和医嘱 |
| 疾病预测查看 | 查看患者AI疾病风险预测结果 |

#### 4.6.2 专业服务

| 功能 | 说明 |
|------|------|
| MDT协作 | 发起多学科会诊、共享病历资料 |
| 医嘱下达 | 下达专业医嘱、用药建议 |
| 干预计划审核 | 审核/调整健管师制定的干预计划 |
| 数字人视频 | 使用数字孪生医生发送专业解释视频 |

### 4.7 客服功能

#### 4.7.1 全渠道工单

| 功能 | 说明 |
|------|------|
| 渠道接入 | Web/小程序/电话/邮件统一进入工单系统 |
| 智能分类 | AI自动识别工单类型（咨询/投诉/建议/故障） |
| 优先级判定 | 基于紧急程度智能排序 |

#### 4.7.2 AI辅助处理

| 功能 | 说明 |
|------|------|
| 回复建议 | AI生成回复草稿，客服确认/修改后发送 |
| 相似工单推荐 | 历史工单解决方案快速复用 |
| 自动处理 | 简单问题（如密码重置）AI自动处理 |
| 工单转交 | 复杂工单转交专业部门 |

#### 4.7.3 服务质量

| 功能 | 说明 |
|------|------|
| SLA监控 | 工单响应时长、处理时长监控 |
| 满意度回访 | 工单关闭后自动发送满意度调研 |
| 质检管理 | 随机抽检工单、评价服务质量 |

### 4.8 超级管理员功能

#### 4.8.1 AI接口配置

| 功能 | 说明 |
|------|------|
| LLM配置 | 模型选择、API地址、超参配置 |
| TTS配置 | 语音引擎、声音列表、音量/语速 |
| SadTalker配置 | 分辨率、面部增强、回调地址 |
| 疾病预测配置 | 预测模型选择、阈值配置、调用配额 |

#### 4.8.2 代理商管理

| 功能 | 说明 |
|------|------|
| 代理商入驻审核 | 新代理商资质审核 |
| 代理商等级管理 | 等级调整、权限配置 |
| 分成规则管理 | 佣金比例设置、结算周期 |
| 配额管理 | 代理客户数/销售额配额 |

#### 4.8.3 平台运营

| 功能 | 说明 |
|------|------|
| 企业客户管理 | 企业审核、配额管理 |
| 服务套餐审核 | 套餐发布审核、内容合规 |
| 服务机构管理 | 服务机构准入、资质管理 |
| 数据统计 | 平台整体运营数据大盘 |

#### 4.8.4 审计合规

| 功能 | 说明 |
|------|------|
| 操作日志审计 | 所有敏感操作留痕 |
| 数据导出管理 | 敏感数据导出审批 |
| 权限变更记录 | RBAC变更历史追踪 |
| 合规报告 | 数据合规、隐私保护报告 |

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

#### 5.1.3 Agent类型枚举

| agent_type | 说明 | 能力范围 |
|------------|------|---------|
| `HEALTH_QA` | 健康问答 | 健康知识、指标解读、生活建议 |
| `PLAN_GEN` | 方案生成 | 干预计划、任务拆解 |
| `RISK_ANALYSIS` | 风险分析 | 体征异常识别 |
| `REPORT_PARSE` | 报告解析 | OCR后结构化提取 |
| `FOLLOWUP_SUMMARY` | 随访摘要 | 对话摘要、异常标记 |
| `CS_AGENT` | 客服智能 | 工单分类、回复建议 |
| `DIGITAL_MANAGER` | 数字健管师 | 数字人对话编排 |

#### 5.1.4 响应规格

```json
// 流式响应 (stream: true)
data: {"choices": [{"delta": {"content": "根据您提供"}}]}
data: {"choices": [{"delta": {"content": "的血压数据"}}]}
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
  "speed": 1.0
}
```

#### 5.2.3 响应规格

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "audio_url": "https://storage.example.com/tts/2026/05/06/audio_abc123.mp3",
    "audio_id": "tts_abc123",
    "duration_seconds": 8.5
  }
}
```

#### 5.2.4 预置声音列表

| voice_id | 名称 | 性别 | 适用场景 |
|----------|------|------|---------|
| `health_manager_female_01` | 专业女声-小健 | 女 | 健管师标准音 |
| `health_manager_male_01` | 专业男声-小康 | 男 | 健管师标准音 |
| `doctor_female_01` | 医生女声-林医生 | 女 | 医生报告解读 |
| `doctor_male_01` | 医生男声-张医生 | 男 | 医生报告解读 |
| `digital_avatar_female_01` | 数字人女声 | 女 | 数字人唇音同步 |
| `elder_caring_female_01` | 关怀女声 | 女 | 老年患者关怀 |

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
  "audio_url": "https://storage.example.com/tts/audio_abc123.mp3",
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

#### 5.3.3 回调响应规格

```json
// POST {callback_url}
{
  "task_id": "task_sadtalker_abc123",
  "status": "completed",
  "data": {
    "video_url": "https://storage.example.com/sadtalker/video_abc123.mp4",
    "thumbnail_url": "https://storage.example.com/sadtalker/thumb_abc123.jpg",
    "duration_seconds": 8.5
  }
}
```

#### 5.3.4 降级策略

| 故障场景 | 降级方案 |
|---------|---------|
| SadTalker服务不可达 | 发送纯音频 + 静态头像图片 |
| 源图片不合格 | 使用预置默认头像 |
| 生成超时（>60s） | 自动降级为纯音频 |

---

### 5.4 疾病风险预测接口

#### 5.4.1 接口配置

| 属性 | 值 |
|------|-----|
| **Base URL** | `http://192.168.0.126:5000` |
| **端点** | `/api/predict` |
| **方法** | `POST` |
| **协议** | HTTP REST |

#### 5.4.2 请求规格

```json
POST /api/predict
Content-Type: application/json

{
  "patient_id": "p_12345",
  "profile_id": "hp_abc123",
  "prediction_type": "multi_disease",
  "input_data": {
    "demographics": {
      "age": 45,
      "gender": "male",
      "bmi": 26.5,
      "waist_cm": 88
    },
    "vitals": {
      "blood_pressure_systolic": 135,
      "blood_pressure_diastolic": 88,
      "heart_rate": 78,
      "blood_glucose_fasting": 5.8,
      "blood_glucose_hba1c": 5.6,
      "total_cholesterol": 5.2,
      "ldl_cholesterol": 3.1,
      "hdl_cholesterol": 1.2,
      "triglycerides": 1.8
    },
    "lifestyle": {
      "smoking_status": "former",
      "alcohol_consumption": "occasional",
      "exercise_frequency": "moderate",
      "sleep_hours": 7,
      "diet_quality": "fair"
    },
    "medical_history": {
      "family_history": ["diabetes", "hypertension"],
      "personal_history": ["prediabetes"],
      "current_medications": ["metformin"]
    }
  },
  "disease_types": [
    "cardiovascular",
    "diabetes",
    "stroke",
    "copd"
  ],
  "time_horizon_years": 5,
  "callback_url": "http://api.hcms.com/webhook/risk_prediction"
}
```

#### 5.4.3 请求参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `patient_id` | string | ✅ | 患者唯一标识 |
| `profile_id` | string | ✅ | 健康档案ID |
| `prediction_type` | string | ✅ | 预测类型：multi_disease多病种/single_disease单病种/followup跟踪 |
| `input_data.demographics` | object | ✅ | 人口统计学数据 |
| `input_data.vitals` | object | ✅ | 最新体征数据 |
| `input_data.lifestyle` | object | ❌ | 生活方式数据 |
| `input_data.medical_history` | object | ❌ | 病史数据 |
| `disease_types` | array | ❌ | 指定预测病种，默认全部 |
| `time_horizon_years` | int | ❌ | 预测时间范围：1/3/5/10年，默认5年 |
| `callback_url` | string | ❌ | 异步回调地址（复杂预测时使用） |

#### 5.4.4 响应规格

```json
// 同步响应（简单预测）
{
  "code": 0,
  "message": "success",
  "data": {
    "prediction_id": "pred_abc123",
    "patient_id": "p_12345",
    "prediction_time": "2026-05-06T16:00:00Z",
    "model_version": "v2.1.0",
    "prediction_horizon": "5_years",
    "results": {
      "cardiovascular": {
        "disease_name": "心血管疾病",
        "risk_level": "moderate",
        "risk_score": 0.23,
        "risk_percentile": 65,
        "risk_factors": [
          {"factor": "elevated_bp", "contribution": 0.35, "direction": "increase"},
          {"factor": "family_history", "contribution": 0.25, "direction": "increase"},
          {"factor": "bmi_above_normal", "contribution": 0.20, "direction": "increase"}
        ],
        "protective_factors": [
          {"factor": "non_smoker", "contribution": -0.15}
        ],
        "recommendations": [
          "建议进一步心血管检查",
          "控制血压在130/80mmHg以下",
          "每周进行150分钟中等强度运动"
        ]
      },
      "diabetes": {
        "disease_name": "2型糖尿病",
        "risk_level": "high",
        "risk_score": 0.45,
        "risk_percentile": 78,
        "risk_factors": [
          {"factor": "prediabetes", "contribution": 0.40, "direction": "increase"},
          {"factor": "family_history", "contribution": 0.25, "direction": "increase"},
          {"factor": "bmi_above_normal", "contribution": 0.20, "direction": "increase"}
        ],
        "protective_factors": [
          {"factor": "current_treatment", "contribution": -0.10}
        ],
        "recommendations": [
          "建议糖耐量试验",
          "密切监测血糖变化",
          "调整饮食结构，减少精制碳水摄入"
        ]
      },
      "stroke": {
        "disease_name": "脑卒中",
        "risk_level": "low",
        "risk_score": 0.08,
        "risk_percentile": 35,
        "risk_factors": [
          {"factor": "elevated_bp", "contribution": 0.30, "direction": "increase"}
        ],
        "protective_factors": [],
        "recommendations": [
          "继续保持当前生活方式",
          "定期监测血压"
        ]
      }
    },
    "overall_health_risk_score": 0.32,
    "high_priority_conditions": ["diabetes"],
    "confidence_metrics": {
      "cardiovascular": 0.92,
      "diabetes": 0.88,
      "stroke": 0.85
    }
  }
}
```

#### 5.4.5 响应参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| `prediction_id` | string | 预测任务唯一标识 |
| `disease_name` | string | 疾病名称 |
| `risk_level` | string | 风险等级：low低/moderate中/high高/critical极高 |
| `risk_score` | float | 风险评分0-1 |
| `risk_percentile` | int | 风险百分位（相对同龄同性别人群） |
| `risk_factors` | array | 主要风险因素及贡献度 |
| `protective_factors` | array | 保护因素及贡献度 |
| `recommendations` | array | 针对性建议 |
| `confidence_metrics` | object | 各病种预测置信度 |

#### 5.4.6 支持的预测病种

| 疾病代码 | 疾病名称 | 适用人群 |
|---------|---------|---------|
| `cardiovascular` | 心血管疾病 | 全人群 |
| `diabetes` | 2型糖尿病 | 全人群 |
| `stroke` | 脑卒中 | 40岁以上 |
| `copd` | 慢性阻塞性肺疾病 | 吸烟/粉尘暴露人群 |
| `cancer_lung` | 肺癌 | 吸烟/高危人群 |
| `cancer_colorectal` | 结直肠癌 | 50岁以上 |
| `osteoporosis` | 骨质疏松 | 50岁以上女性/60岁以上男性 |
| `depression` | 抑郁症 | 全人群 |
| `kidney_disease` | 慢性肾病 | 糖尿病/高血压人群 |
| `dementia` | 认知障碍/痴呆 | 60岁以上 |

#### 5.4.7 错误响应

```json
{
  "code": 40001,
  "message": "缺少必需字段: demographics.age",
  "error_details": {
    "field": "input_data.demographics.age",
    "error": "required field missing"
  }
}

// 错误码定义
// 40001: 参数缺失
// 40002: 参数格式错误
// 40003: 数据值超出范围
// 40401: 患者档案不存在
// 50001: 预测服务内部错误
// 50002: 预测模型加载失败
```

#### 5.4.8 预测触发时机

| 触发场景 | 说明 |
|---------|------|
| 新建档案 | 患者首次录入档案后自动触发 |
| 年度评估 | 每年度健康评估时触发 |
| 重大体征变化 | 体征数据异常变化时触发 |
| 健管师请求 | 健管师手动发起预测请求 |
| 医生请求 | 医生查看患者时触发 |

---

### 5.5 数字孪生医生接口

#### 5.5.1 接口配置

| 属性 | 值 |
|------|-----|
| **Base URL** | `http://192.168.0.214:8123` |
| **端点** | `/api/v1/generate_video` |
| **方法** | `POST` |
| **协议** | HTTP REST |
| **任务模式** | 异步（轮询查询） |

#### 5.5.2 请求规格

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

#### 5.5.3 响应规格

```json
// 提交成功
{
  "code": 0,
  "message": "success",
  "data": {
    "video_id": "video_dt_doctor_abc123",
    "status": "queued",
    "check_status_url": "http://192.168.0.214:8123/api/v1/video_status/video_dt_doctor_abc123"
  }
}

// 查询状态
GET /api/v1/video_status/{video_id}

{
  "code": 0,
  "data": {
    "video_id": "video_dt_doctor_abc123",
    "status": "completed",
    "result": {
      "video_url": "https://storage.example.com/digital_doctor/video_abc123.mp4",
      "duration_seconds": 12.5
    }
  }
}
```

---

### 5.6 数字人视频生成完整流程

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   LLM生成    │────▶│    TTS合成    │────▶│  音频文件    │
│   口播文本   │     │  语音合成     │     │   .mp3      │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                    ┌────────────────────────────┤
                    │                            │
                    ▼                            ▼
           ┌──────────────┐              ┌──────────────┐
           │  SadTalker   │              │ 数字孪生医生 │
           │  数字人视频   │              │  数字人视频   │
           └──────┬───────┘              └──────┬───────┘
                 │                             │
                 └──────────────┬───────────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │  视频文件   │
                        │   .mp4      │
                        └──────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │  发送给患者   │     │  发送给员工   │     │  本地保存    │
    │  (患者端)    │     │  (企业员工)  │     │  档案关联    │
    └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 6. 数据库设计

### 6.1 数据库选型与说明

| 数据库 | 用途 | 特点 |
|-------|------|------|
| **MySQL 8.0** | 业务核心数据 | ACID事务、复杂查询 |
| **InfluxDB** | 体征时序数据 | 高写入、时序聚合 |
| **Milvus** | 健康知识向量 | 相似度检索 |
| **MinIO** | 文件对象存储 | 影像/DICOM存储 |

### 6.2 MySQL核心表结构（30张表）

#### 6.2.1 用户与认证相关表

**表1：users（用户表）**

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    user_code VARCHAR(32) NOT NULL UNIQUE COMMENT '用户编码',
    username VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    user_type VARCHAR(16) NOT NULL COMMENT '用户类型：PERSON个人/ENTERPRISE企业',
    real_name VARCHAR(64) COMMENT '真实姓名/企业名',
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
    INDEX idx_status (status),
    INDEX idx_user_type (user_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

**表2：user_roles（用户角色关联表）**

```sql
CREATE TABLE user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_code VARCHAR(32) NOT NULL COMMENT '角色代码：ORG_BUYER采购企业/EMPLOYEE企业员工/PATIENT个人患者/AGENT代理商/HEALTH_MANAGER健管师/DOCTOR医生/CUSTOMER_SERVICE客服/SUPER_ADMIN超管',
    enterprise_id BIGINT COMMENT '所属企业ID（ORG_BUYER/AGENT/ORG_PROVIDER时）',
    employee_enterprise_id BIGINT COMMENT '员工所属企业ID（EMPLOYEE时）',
    dept_id BIGINT COMMENT '部门ID',
    position VARCHAR(64) COMMENT '职位',
    is_primary TINYINT NOT NULL DEFAULT 0 COMMENT '是否主角色：0否 1是',
    agent_level VARCHAR(16) COMMENT '代理商等级：level1一级/level2二级',
    agent_region VARCHAR(128) COMMENT '代理商区域',
    effective_start_date DATE COMMENT '角色生效开始日期',
    effective_end_date DATE COMMENT '角色生效结束日期',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT COMMENT '创建人ID',
    UNIQUE KEY uk_user_role (user_id, role_code, enterprise_id),
    INDEX idx_role_code (role_code),
    INDEX idx_enterprise_id (enterprise_id),
    INDEX idx_employee_enterprise (employee_enterprise_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';
```

**表3：enterprises（企业表）**

```sql
CREATE TABLE enterprises (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    enterprise_code VARCHAR(32) NOT NULL UNIQUE COMMENT '企业编码',
    enterprise_name VARCHAR(128) NOT NULL COMMENT '企业名称',
    enterprise_type VARCHAR(16) NOT NULL COMMENT '企业类型：ORG_BUYER采购方/ORG_PROVIDER供给方/AGENT代理商/BOTH双向',
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
    agent_level VARCHAR(16) COMMENT '代理商等级：level1一级/level2二级',
    parent_agent_id BIGINT COMMENT '上级代理商ID（二级代理时）',
    commission_rate DECIMAL(5,2) COMMENT '佣金比例',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME COMMENT '软删除时间',
    INDEX idx_enterprise_type (enterprise_type),
    INDEX idx_status (status),
    INDEX idx_agent_level (agent_level),
    INDEX idx_parent_agent (parent_agent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业表';
```

**表4：service_contracts（服务合同表）**

```sql
CREATE TABLE service_contracts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    contract_code VARCHAR(64) NOT NULL UNIQUE COMMENT '合同编号',
    contract_name VARCHAR(256) NOT NULL COMMENT '合同名称',
    contract_type VARCHAR(16) NOT NULL COMMENT '合同类型：direct直签/agent代理',
    buyer_enterprise_id BIGINT COMMENT '采购方企业ID（直签时）',
    buyer_employee_id BIGINT COMMENT '采购员工ID（个人购买时）',
    agent_enterprise_id BIGINT COMMENT '代理商企业ID（代理时）',
    provider_enterprise_id BIGINT NOT NULL COMMENT '服务提供方企业ID',
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
    signed_at DATETIME COMMENT '签署时间',
    signed_by BIGINT COMMENT '签署人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_buyer (buyer_enterprise_id),
    INDEX idx_buyer_employee (buyer_employee_id),
    INDEX idx_agent (agent_enterprise_id),
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
    package_type VARCHAR(16) NOT NULL COMMENT '套餐类型：enterprise企业包/personal个人包',
    provider_enterprise_id BIGINT NOT NULL COMMENT '供给方企业ID',
    agent_enterprise_id BIGINT COMMENT '代理商企业ID（代理销售时）',
    category VARCHAR(32) COMMENT '套餐类别：basic基础/standard标准/premium高级/custom定制',
    description TEXT COMMENT '套餐描述',
    service_contents TEXT NOT NULL COMMENT '服务内容详情（JSON数组）',
    target_users TEXT COMMENT '适用人群描述',
    duration_days INT COMMENT '服务时长（天）',
    original_price DECIMAL(10,2) COMMENT '原价',
    sale_price DECIMAL(10,2) COMMENT '售价',
    agent_price DECIMAL(10,2) COMMENT '代理商拿货价',
    discount_rate DECIMAL(5,2) COMMENT '折扣率',
    max_user_count INT COMMENT '可用人数上限',
    sold_count INT DEFAULT 0 COMMENT '已售数量',
    cover_image_url VARCHAR(512) COMMENT '封面图URL',
    detail_images TEXT COMMENT '详情图URL列表（JSON数组）',
    includes_digital_avatar TINYINT DEFAULT 0 COMMENT '是否包含数字人服务：0否 1是',
    includes_tts_reminder TINYINT DEFAULT 0 COMMENT '是否包含TTS提醒：0否 1是',
    includes_risk_prediction TINYINT DEFAULT 0 COMMENT '是否包含疾病预测：0否 1是',
    status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft待发布/on_shelf上架/off_shelf下架',
    published_at DATETIME COMMENT '上架时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT COMMENT '创建人ID',
    INDEX idx_provider (provider_enterprise_id),
    INDEX idx_agent (agent_enterprise_id),
    INDEX idx_category (category),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='服务套餐表';
```

**表6：orders（订单表）**

```sql
CREATE TABLE orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_code VARCHAR(64) NOT NULL UNIQUE COMMENT '订单编号',
    order_type VARCHAR(16) NOT NULL COMMENT '订单类型：enterprise企业订单/personal个人订单/agent代理订单',
    buyer_type VARCHAR(16) NOT NULL COMMENT '采购方类型：enterprise企业/employee员工/patient患者/agent代理商',
    buyer_id BIGINT NOT NULL COMMENT '采购方ID',
    buyer_enterprise_id BIGINT COMMENT '采购方企业ID',
    agent_id BIGINT COMMENT '代理商ID',
    provider_enterprise_id BIGINT COMMENT '服务提供方ID',
    package_id BIGINT COMMENT '套餐ID',
    package_name VARCHAR(128) COMMENT '套餐名称快照',
    quantity INT DEFAULT 1 COMMENT '购买数量',
    unit_price DECIMAL(10,2) COMMENT '单价',
    total_amount DECIMAL(12,2) NOT NULL COMMENT '订单总金额',
    paid_amount DECIMAL(12,2) DEFAULT 0 COMMENT '已支付金额',
    discount_amount DECIMAL(12,2) DEFAULT 0 COMMENT '优惠金额',
    coupon_id BIGINT COMMENT '使用优惠券ID',
    payment_method VARCHAR(32) COMMENT '支付方式：wechat/alipay/bank/enterprise',
    payment_status VARCHAR(16) NOT NULL DEFAULT 'unpaid' COMMENT '支付状态：unpaid待支付/paid已支付/refunded已退款/partially_refunded部分退款',
    payment_time DATETIME COMMENT '支付时间',
    transaction_id VARCHAR(64) COMMENT '支付流水号',
    invoice_status VARCHAR(16) DEFAULT 'none' COMMENT '发票状态：none未开/requested已申请/issued已开',
    invoice_id BIGINT COMMENT '发票ID',
    settlement_status VARCHAR(16) DEFAULT 'unsettled' COMMENT '结算状态：unsettled未结算/settling结算中/settled已结算',
    commission_amount DECIMAL(12,2) COMMENT '佣金金额（代理订单）',
    commission_settled TINYINT DEFAULT 0 COMMENT '佣金是否已结算',
    effective_start_date DATE COMMENT '服务生效开始日期',
    effective_end_date DATE COMMENT '服务生效结束日期',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '状态：active有效/completed已完成/cancelled已取消/expired已过期',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_buyer (buyer_id),
    INDEX idx_buyer_enterprise (buyer_enterprise_id),
    INDEX idx_agent (agent_id),
    INDEX idx_provider (provider_enterprise_id),
    INDEX idx_package (package_id),
    INDEX idx_payment_status (payment_status),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='订单表';
```

**表7：employee_bindings（企业员工绑定表）**

```sql
CREATE TABLE employee_bindings (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    binding_code VARCHAR(64) NOT NULL UNIQUE COMMENT '绑定编号',
    employee_user_id BIGINT NOT NULL COMMENT '员工用户ID',
    employee_enterprise_id BIGINT NOT NULL COMMENT '员工所属企业ID',
    employee_no VARCHAR(64) COMMENT '员工工号',
    department VARCHAR(128) COMMENT '所属部门',
    position VARCHAR(64) COMMENT '职位',
    binding_type VARCHAR(16) NOT NULL COMMENT '绑定类型：invite邀请/registe注册/transfer调岗',
    invite_code VARCHAR(32) COMMENT '邀请码',
    inviter_id BIGINT COMMENT '邀请人ID',
    service_package_id BIGINT COMMENT '分配的服务套餐ID',
    service_start_date DATE COMMENT '服务开始日期',
    service_end_date DATE COMMENT '服务结束日期',
    binding_status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '绑定状态：active生效/resigned已离职/suspended已停用/transferred已调岗',
    resignation_date DATE COMMENT '离职日期',
    transfer_to_enterprise_id BIGINT COMMENT '调往企业ID',
    activated_at DATETIME COMMENT '激活时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_employee_enterprise (employee_user_id, employee_enterprise_id),
    INDEX idx_enterprise (employee_enterprise_id),
    INDEX idx_status (binding_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='企业员工绑定表';
```

#### 6.2.2 健康档案相关表

**表8：health_profiles（健康档案主表）**

```sql
CREATE TABLE health_profiles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    profile_code VARCHAR(64) NOT NULL UNIQUE COMMENT '档案编号',
    patient_id BIGINT NOT NULL COMMENT '患者用户ID',
    user_type VARCHAR(16) NOT NULL COMMENT '用户类型：EMPLOYEE企业员工/PATIENT个人患者',
    enterprise_id BIGINT COMMENT '绑定企业ID（企业员工时）',
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
    INDEX idx_user_type (user_type),
    INDEX idx_enterprise (enterprise_id),
    INDEX idx_risk_level (risk_level),
    INDEX idx_health_score (health_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健康档案主表';
```

**表9：health_profile_authorizations（档案授权记录表）**

```sql
CREATE TABLE health_profile_authorizations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    authorization_code VARCHAR(64) NOT NULL UNIQUE COMMENT '授权编号',
    profile_id BIGINT NOT NULL COMMENT '健康档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    authorized_user_id BIGINT NOT NULL COMMENT '被授权用户ID',
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

**表10：medical_records（病历记录表）**

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
    attachment_urls JSON COMMENT '附件URL列表',
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

**表11：lab_results（检查化验单表）**

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
    specimen_type VARCHAR(32) COMMENT '标本类型',
    results JSON NOT NULL COMMENT '检验结果JSON：[{item:项目名,value:值,unit:单位,reference:参考值,flag:异常标志}]',
    ai_interpretation TEXT COMMENT 'AI解读',
    abnormal_count INT DEFAULT 0 COMMENT '异常项数量',
    critical_count INT DEFAULT 0 COMMENT '危急值数量',
    attachment_urls JSON COMMENT '附件URL',
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

**表12：imaging_reports（影像报告表）**

```sql
CREATE TABLE imaging_reports (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_code VARCHAR(64) NOT NULL UNIQUE COMMENT '报告编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    imaging_type VARCHAR(32) NOT NULL COMMENT '影像类型：xray/CT/MRI/ultrasound/PET/CT',
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
    dicom_file_urls JSON COMMENT 'DICOM文件URL列表',
    report_file_url VARCHAR(512) COMMENT '报告PDF URL',
    thumbnail_url VARCHAR(512) COMMENT '缩略图URL',
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

**表13：medication_records（用药记录表）**

```sql
CREATE TABLE medication_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '记录编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    drug_name VARCHAR(128) NOT NULL COMMENT '药品名称',
    generic_name VARCHAR(128) COMMENT '通用名',
    drug_category VARCHAR(64) COMMENT '药品类别',
    specification VARCHAR(64) COMMENT '规格',
    dosage VARCHAR(64) COMMENT '单次剂量',
    dosage_unit VARCHAR(16) COMMENT '剂量单位',
    frequency VARCHAR(32) COMMENT '用药频率：QD/BID/TID/QID',
    route VARCHAR(32) COMMENT '给药途径',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    is_current TINYINT DEFAULT 1 COMMENT '是否当前用药：0否 1是',
    purpose VARCHAR(256) COMMENT '用药目的',
    prescriber VARCHAR(64) COMMENT '开药医生',
    hospital_name VARCHAR(128) COMMENT '开药医院',
    side_effects TEXT COMMENT '不良反应',
    contraindications TEXT COMMENT '禁忌症',
    ai_interaction_warning TEXT COMMENT 'AI药物相互作用警告',
    barcode VARCHAR(64) COMMENT '药品条形码',
    attachment_urls JSON COMMENT '处方/说明书附件',
    source VARCHAR(16) DEFAULT 'manual' COMMENT '来源：manual手动/scan扫码/ai_parse AI解析',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_drug_name (drug_name),
    INDEX idx_current (is_current)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用药记录表';
```

**表14：surgery_records（手术记录表）**

```sql
CREATE TABLE surgery_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '记录编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    surgery_name VARCHAR(256) NOT NULL COMMENT '手术名称',
    surgery_code VARCHAR(32) COMMENT '手术编码',
    surgery_type VARCHAR(32) COMMENT '手术类型',
    surgery_date DATE NOT NULL COMMENT '手术日期',
    hospital_name VARCHAR(128) NOT NULL COMMENT '手术医院',
    department VARCHAR(64) COMMENT '手术科室',
    surgeon_name VARCHAR(64) COMMENT '主刀医生',
    anesthesia_type VARCHAR(32) COMMENT '麻醉方式',
    surgery_duration_minutes INT COMMENT '手术时长（分钟）',
    hospitalization_days INT COMMENT '住院天数',
    surgery_findings TEXT COMMENT '手术所见',
    surgery_procedure TEXT COMMENT '手术经过',
    postoperative_diagnosis TEXT COMMENT '术后诊断',
    complications TEXT COMMENT '并发症',
    recovery_status VARCHAR(32) COMMENT '恢复状态',
    followup_plan TEXT COMMENT '随访计划',
    surgery_report_url VARCHAR(512) COMMENT '手术记录PDF URL',
    remarks TEXT COMMENT '备注',
    source VARCHAR(16) DEFAULT 'manual' COMMENT '来源：manual手动/self_report自录/upload上传',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_surgery_date (surgery_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='手术记录表';
```

#### 6.2.3 体征监测表

**表15：vital_records（体征记录表-InfluxDB）**

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

-- 体重数据
vital_records,patient_id=p_12345,vital_type=weight,device_type=smart_scale value=65.5,unit="kg",bmi=22.3 1714972800000000000
```

#### 6.2.4 风险评估与干预表

**表16：risk_assessments（风险评估表）**

```sql
CREATE TABLE risk_assessments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    assessment_code VARCHAR(64) NOT NULL UNIQUE COMMENT '评估编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    assessment_type VARCHAR(32) NOT NULL COMMENT '评估类型：cardiovascular/diabetes/cancer/mental_health/risk_prediction',
    assessment_name VARCHAR(128) COMMENT '评估量表名称',
    score DECIMAL(5,1) COMMENT '评估得分',
    max_score DECIMAL(5,1) COMMENT '满分',
    risk_level VARCHAR(16) NOT NULL COMMENT '风险等级：low/moderate/high/critical',
    risk_factors JSON COMMENT '风险因素JSON',
    protective_factors JSON COMMENT '保护因素JSON',
    ai_analysis TEXT COMMENT 'AI分析报告',
    ai_recommendations TEXT COMMENT '改善建议',
    prediction_source VARCHAR(32) COMMENT '预测来源：ai_algorithm/rule_engine/manual/risk_prediction_api',
    prediction_id VARCHAR(64) COMMENT '关联疾病预测任务ID',
    assessed_by VARCHAR(32) COMMENT '评估方：ai/doctor/health_manager/risk_api',
    assessor_id BIGINT COMMENT '评估人ID',
    assessment_date DATE NOT NULL COMMENT '评估日期',
    next_assessment_date DATE COMMENT '下次评估日期',
    supporting_data JSON COMMENT '支撑数据JSON',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_type (assessment_type),
    INDEX idx_risk_level (risk_level),
    INDEX idx_assessment_date (assessment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风险评估表';
```

**表17：disease_risk_predictions（疾病风险预测记录表）**

```sql
CREATE TABLE disease_risk_predictions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    prediction_code VARCHAR(64) NOT NULL UNIQUE COMMENT '预测编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    prediction_type VARCHAR(32) NOT NULL COMMENT '预测类型：multi_disease/single_disease/followup',
    time_horizon_years INT DEFAULT 5 COMMENT '预测时间范围（年）',
    model_version VARCHAR(32) COMMENT '模型版本',
    results JSON NOT NULL COMMENT '预测结果JSON',
    overall_health_risk_score DECIMAL(5,3) COMMENT '综合健康风险评分',
    high_priority_conditions JSON COMMENT '高优先级病种JSON数组',
    confidence_metrics JSON COMMENT '置信度指标JSON',
    input_data_snapshot JSON COMMENT '输入数据快照',
    trigger_type VARCHAR(32) COMMENT '触发类型：auto_new_profile自动新建档案/auto_annual自动年度/auto_vital_change体征变化/manual_manager手动健管师/manual_doctor手动医生',
    triggered_by BIGINT COMMENT '触发人ID（手动时）',
    predicted_at DATETIME NOT NULL COMMENT '预测时间',
    expires_at DATETIME COMMENT '预测结果过期时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_prediction_type (prediction_type),
    INDEX idx_predicted_at (predicted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='疾病风险预测记录表';
```

**表18：intervention_plans（干预计划表）**

```sql
CREATE TABLE intervention_plans (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    plan_code VARCHAR(64) NOT NULL UNIQUE COMMENT '计划编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    plan_name VARCHAR(256) NOT NULL COMMENT '计划名称',
    plan_type VARCHAR(32) COMMENT '计划类型：medication/exercise/diet/sleep/stress/comprehensive',
    target_disease VARCHAR(128) COMMENT '目标疾病',
    risk_level VARCHAR(16) COMMENT '关联风险等级',
    related_prediction_id BIGINT COMMENT '关联疾病预测ID',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    duration_days INT COMMENT '计划天数',
    overall_goal TEXT COMMENT '总体目标',
    success_metrics JSON COMMENT '成功指标JSON',
    status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft草稿/active进行中/paused暂停/completed已完成/cancelled已取消',
    progress_percent INT DEFAULT 0 COMMENT '完成进度百分比',
    ai_generated TINYINT DEFAULT 0 COMMENT '是否AI生成：0否 1是',
    approved_by BIGINT COMMENT '审核人ID',
    approved_at DATETIME COMMENT '审核时间',
    completion_rate DECIMAL(5,2) COMMENT '任务完成率',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT COMMENT '创建人ID',
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_status (status),
    INDEX idx_plan_type (plan_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='干预计划表';
```

**表19：plan_tasks（计划任务表）**

```sql
CREATE TABLE plan_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_code VARCHAR(64) NOT NULL UNIQUE COMMENT '任务编号',
    plan_id BIGINT NOT NULL COMMENT '计划ID',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    task_name VARCHAR(256) NOT NULL COMMENT '任务名称',
    task_type VARCHAR(32) NOT NULL COMMENT '任务类型：medication_reminder/exercise/diet/measurement/checkup/survey',
    target_value VARCHAR(64) COMMENT '目标值',
    target_unit VARCHAR(16) COMMENT '目标单位',
    frequency VARCHAR(32) COMMENT '执行频率：daily/weekly/custom',
    scheduled_time TIME COMMENT '计划执行时间',
    start_date DATE NOT NULL COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    reminder_enabled TINYINT DEFAULT 1 COMMENT '是否提醒：0否 1是',
    reminder_times JSON COMMENT '提醒时间点JSON',
    reminder_channel VARCHAR(32) COMMENT '提醒渠道：push/短信/wechat/in_app',
    ai_reminder_content TEXT COMMENT 'AI生成的提醒内容',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending待执行/active进行中/skipped已跳过/completed已完成/missed已错过',
    difficulty_level TINYINT COMMENT '难度等级：1-5',
    points INT DEFAULT 0 COMMENT '完成后奖励积分',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_plan (plan_id),
    INDEX idx_patient (patient_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='计划任务表';
```

**表20：task_records（任务执行记录表）**

```sql
CREATE TABLE task_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '记录编号',
    task_id BIGINT NOT NULL COMMENT '任务ID',
    plan_id BIGINT COMMENT '计划ID',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    scheduled_date DATE NOT NULL COMMENT '计划执行日期',
    actual_time DATETIME COMMENT '实际执行时间',
    status VARCHAR(16) NOT NULL COMMENT '执行状态：completed/partially/skipped/not_done',
    completion_value VARCHAR(64) COMMENT '实际完成值',
    completion_rate DECIMAL(5,2) COMMENT '完成率百分比',
    evidence_type VARCHAR(32) COMMENT '凭证类型：photo/video/manual',
    evidence_urls JSON COMMENT '凭证URL列表',
    self_feeling VARCHAR(32) COMMENT '自我感受：great/general/tired',
    notes TEXT COMMENT '患者备注',
    ai_evaluation TEXT COMMENT 'AI评价',
    points_earned INT DEFAULT 0 COMMENT '获得积分',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task (task_id),
    INDEX idx_patient (patient_id),
    INDEX idx_date (scheduled_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务执行记录表';
```

**表21：followup_records（随访记录表）**

```sql
CREATE TABLE followup_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '随访编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    followup_type VARCHAR(32) NOT NULL COMMENT '随访类型：routine/post_visit/acute/scheduled',
    followup_date DATE NOT NULL COMMENT '随访日期',
    followup_mode VARCHAR(32) COMMENT '随访方式：call/video/in_person/message/digital_avatar',
    conversation_summary TEXT COMMENT '对话摘要',
    ai_summary TEXT COMMENT 'AI生成摘要',
    patient_status VARCHAR(32) COMMENT '患者状态：stable/improving/worsening',
    medication_adherence VARCHAR(16) COMMENT '用药依从性',
    ai_suggestions TEXT COMMENT 'AI建议',
    next_followup_date DATE COMMENT '下次随访日期',
    digital_avatar_video_url VARCHAR(512) COMMENT '数字人视频URL',
    conversation_id VARCHAR(64) COMMENT 'AI对话会话ID',
    duration_seconds INT COMMENT '随访时长（秒）',
    satisfaction INT COMMENT '满意度评分1-5',
    followup_by BIGINT NOT NULL COMMENT '随访执行人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_followup_date (followup_date),
    INDEX idx_followup_by (followup_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='随访记录表';
```

**表22：alert_records（预警记录表）**

```sql
CREATE TABLE alert_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    alert_code VARCHAR(64) NOT NULL UNIQUE COMMENT '预警编号',
    profile_id BIGINT NOT NULL COMMENT '档案ID',
    patient_id BIGINT NOT NULL COMMENT '患者ID',
    alert_type VARCHAR(32) NOT NULL COMMENT '预警类型：vital_abnormal/risk_escalation/medication_miss/followup_miss/crisis/risk_prediction',
    alert_level VARCHAR(16) NOT NULL COMMENT '预警级别：info/warning/critical',
    alert_source VARCHAR(32) COMMENT '预警来源：ai_algorithm/rule_engine/manual/risk_prediction_api',
    trigger_condition VARCHAR(256) COMMENT '触发条件描述',
    trigger_value VARCHAR(64) COMMENT '触发值',
    reference_value VARCHAR(64) COMMENT '参考值',
    ai_analysis TEXT COMMENT 'AI分析',
    recommendations TEXT COMMENT '建议',
    action_required TINYINT DEFAULT 1 COMMENT '是否需要处理',
    action_taken TEXT COMMENT '已采取行动',
    handler_id BIGINT COMMENT '处理人ID',
    handled_at DATETIME COMMENT '处理时间',
    patient_notified TINYINT DEFAULT 0 COMMENT '是否通知患者',
    escalated TINYINT DEFAULT 0 COMMENT '是否升级',
    resolution_status VARCHAR(16) DEFAULT 'pending' COMMENT '解决状态',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_profile (profile_id),
    INDEX idx_patient (patient_id),
    INDEX idx_type (alert_type),
    INDEX idx_level (alert_level),
    INDEX idx_status (resolution_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='预警记录表';
```

#### 6.2.5 服务与工单表

**表23：work_orders（工单表）**

```sql
CREATE TABLE work_orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_code VARCHAR(64) NOT NULL UNIQUE COMMENT '工单编号',
    order_type VARCHAR(32) NOT NULL COMMENT '工单类型：consult/complaint/suggestion/feedback/system',
    priority VARCHAR(16) NOT NULL DEFAULT 'normal' COMMENT '优先级：low/normal/high/urgent',
    title VARCHAR(256) NOT NULL COMMENT '工单标题',
    description TEXT NOT NULL COMMENT '工单描述',
    patient_id BIGINT COMMENT '患者ID',
    patient_name VARCHAR(64) COMMENT '患者姓名',
    patient_enterprise_id BIGINT COMMENT '患者所属企业ID',
    channel VARCHAR(32) NOT NULL COMMENT '来源渠道：app/web/miniprogram/wechat热线/call/email',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/assigned/processing/pending_reply/resolved/closed',
    assigned_to BIGINT COMMENT '处理人ID',
    assigned_to_name VARCHAR(64) COMMENT '处理人姓名',
    assigned_at DATETIME COMMENT '分配时间',
    sla_deadline DATETIME COMMENT 'SLA截止时间',
    auto_processed TINYINT DEFAULT 0 COMMENT '是否AI自动处理',
    customer_rating INT COMMENT '客户评分1-5',
    related_order_id BIGINT COMMENT '关联工单ID',
    attachments JSON COMMENT '附件URL列表',
    internal_notes TEXT COMMENT '内部备注',
    closed_at DATETIME COMMENT '关闭时间',
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

**表24：ai_conversations（AI对话记录表）**

```sql
CREATE TABLE ai_conversations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    conversation_code VARCHAR(64) NOT NULL UNIQUE COMMENT '会话编号',
    session_id VARCHAR(128) NOT NULL COMMENT '会话ID',
    profile_id BIGINT COMMENT '档案ID',
    patient_id BIGINT COMMENT '患者ID',
    agent_type VARCHAR(32) NOT NULL COMMENT 'Agent类型',
    interaction_mode VARCHAR(16) COMMENT '交互模式：text/voice/video',
    messages JSON NOT NULL COMMENT '对话消息JSON',
    patient_feedback INT COMMENT '患者满意度1-5',
    escalated TINYINT DEFAULT 0 COMMENT '是否转人工',
    emotional_flag VARCHAR(32) COMMENT '情绪标记',
    llm_model VARCHAR(64) COMMENT '使用的LLM模型',
    token_usage JSON COMMENT 'Token使用量JSON',
    duration_seconds INT COMMENT '会话时长（秒）',
    ended_at DATETIME COMMENT '结束时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_patient (patient_id),
    INDEX idx_agent (agent_type),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI对话记录表';
```

**表25：sadtalker_tasks（SadTalker任务表）**

```sql
CREATE TABLE sadtalker_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_code VARCHAR(64) NOT NULL UNIQUE COMMENT '任务编号',
    profile_id BIGINT COMMENT '档案ID',
    patient_id BIGINT COMMENT '患者ID',
    task_type VARCHAR(32) NOT NULL COMMENT '任务类型：followup/reminder/education/greeting',
    avatar_id VARCHAR(64) NOT NULL COMMENT '数字人形象ID',
    script_text TEXT COMMENT '口播文本',
    audio_url VARCHAR(512) COMMENT 'TTS音频URL',
    video_url VARCHAR(512) COMMENT '生成视频URL',
    duration_seconds DECIMAL(5,1) COMMENT '视频时长',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/submitted/processing/completed/failed',
    error_message TEXT COMMENT '错误信息',
    fallback_used TINYINT DEFAULT 0 COMMENT '是否使用降级策略',
    sent_to_patient TINYINT DEFAULT 0 COMMENT '是否已发送患者',
    watched TINYINT DEFAULT 0 COMMENT '患者是否观看',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient (patient_id),
    INDEX idx_status (status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='SadTalker数字人任务表';
```

**表26：tts_tasks（TTS任务表）**

```sql
CREATE TABLE tts_tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_code VARCHAR(64) NOT NULL UNIQUE COMMENT '任务编号',
    profile_id BIGINT COMMENT '档案ID',
    patient_id BIGINT COMMENT '患者ID',
    task_type VARCHAR(32) NOT NULL COMMENT '任务类型：reminder/education/announcement/custom',
    text_content TEXT NOT NULL COMMENT '待合成文本',
    voice_id VARCHAR(64) NOT NULL COMMENT '声音ID',
    emotion VARCHAR(32) COMMENT '情感标签',
    audio_url VARCHAR(512) COMMENT '生成音频URL',
    duration_seconds DECIMAL(5,1) COMMENT '音频时长',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/processing/completed/failed',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_patient (patient_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='TTS任务表';
```

**表27：avatar_assets（数字人形象资产表）**

```sql
CREATE TABLE avatar_assets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    avatar_code VARCHAR(64) NOT NULL UNIQUE COMMENT '形象编码',
    avatar_name VARCHAR(128) NOT NULL COMMENT '形象名称',
    avatar_type VARCHAR(32) NOT NULL COMMENT '形象类型：preset预置/custom定制/doctor医生',
    enterprise_id BIGINT COMMENT '所属企业ID（定制形象时）',
    base_image_url VARCHAR(512) NOT NULL COMMENT '基础图片URL',
    thumbnail_url VARCHAR(512) COMMENT '缩略图URL',
    gender VARCHAR(8) COMMENT '性别',
    style VARCHAR(32) COMMENT '风格：professional/caring/friendly',
    voice_id VARCHAR(64) COMMENT '关联声音ID',
    role_description VARCHAR(256) COMMENT '角色描述',
    is_active TINYINT DEFAULT 1 COMMENT '是否启用',
    is_default TINYINT DEFAULT 0 COMMENT '是否默认形象',
    usage_count INT DEFAULT 0 COMMENT '使用次数',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_enterprise (enterprise_id),
    INDEX idx_type (avatar_type),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数字人形象资产表';
```

#### 6.2.7 代理商与结算表

**表28：agent_commissions（代理商佣金表）**

```sql
CREATE TABLE agent_commissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    commission_code VARCHAR(64) NOT NULL UNIQUE COMMENT '佣金编号',
    agent_enterprise_id BIGINT NOT NULL COMMENT '代理商企业ID',
    agent_level VARCHAR(16) NOT NULL COMMENT '代理商等级',
    parent_agent_id BIGINT COMMENT '上级代理商ID（二级代理时）',
    order_id BIGINT NOT NULL COMMENT '关联订单ID',
    order_code VARCHAR(64) COMMENT '订单编号快照',
    order_amount DECIMAL(12,2) NOT NULL COMMENT '订单金额',
    commission_rate DECIMAL(5,2) NOT NULL COMMENT '佣金比例',
    commission_amount DECIMAL(12,2) NOT NULL COMMENT '佣金金额',
    parent_commission_amount DECIMAL(12,2) COMMENT '上级代理商佣金（二级时）',
    commission_type VARCHAR(16) NOT NULL COMMENT '佣金类型：direct直接/salesperson业务员',
    salesperson_id BIGINT COMMENT '业务员ID（团队佣金时）',
    salesperson_commission DECIMAL(12,2) COMMENT '业务员佣金',
    settlement_status VARCHAR(16) NOT NULL DEFAULT 'unsettled' COMMENT '结算状态：unsettled未结算/settling结算中/settled已结算',
    settlement_period VARCHAR(16) COMMENT '结算周期：monthly月度/quarterly季度',
    settlement_batch VARCHAR(32) COMMENT '结算批次号',
    settled_at DATETIME COMMENT '结算时间',
    settled_by BIGINT COMMENT '结算人ID',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '状态：active有效/reversed已冲正/cancelled已取消',
    reversed_reason VARCHAR(256) COMMENT '冲正原因',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_agent (agent_enterprise_id),
    INDEX idx_order (order_id),
    INDEX idx_settlement (settlement_status),
    INDEX idx_settlement_period (settlement_period),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代理商佣金表';
```

**表29：agent_settlements（代理商结算表）**

```sql
CREATE TABLE agent_settlements (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    settlement_code VARCHAR(64) NOT NULL UNIQUE COMMENT '结算单编号',
    agent_enterprise_id BIGINT NOT NULL COMMENT '代理商企业ID',
    settlement_period VARCHAR(16) NOT NULL COMMENT '结算周期：monthly月度/quarterly季度',
    period_start_date DATE NOT NULL COMMENT '周期开始日期',
    period_end_date DATE NOT NULL COMMENT '周期结束日期',
    total_orders INT DEFAULT 0 COMMENT '订单总数',
    total_order_amount DECIMAL(12,2) DEFAULT 0 COMMENT '订单总金额',
    total_commission DECIMAL(12,2) DEFAULT 0 COMMENT '佣金总额',
    total_parent_commission DECIMAL(12,2) DEFAULT 0 COMMENT '上级佣金总额',
    net_commission DECIMAL(12,2) DEFAULT 0 COMMENT '净佣金（扣除上级后）',
    tax_amount DECIMAL(12,2) DEFAULT 0 COMMENT '代扣税额',
    actual_payment DECIMAL(12,2) DEFAULT 0 COMMENT '实际支付金额',
    payment_method VARCHAR(32) COMMENT '支付方式',
    payment_account VARCHAR(128) COMMENT '收款账户',
    payment_status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '支付状态：pending待确认/confirmed已确认/paid已支付/rejected已拒绝',
    payment_time DATETIME COMMENT '支付时间',
    payment_proof_url VARCHAR(512) COMMENT '支付凭证URL',
    confirmed_at DATETIME COMMENT '确认时间',
    confirmed_by BIGINT COMMENT '确认人ID',
    reject_reason VARCHAR(256) COMMENT '拒绝原因',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_agent (agent_enterprise_id),
    INDEX idx_period (settlement_period),
    INDEX idx_payment_status (payment_status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代理商结算表';
```

#### 6.2.8 审计日志表

**表30：audit_logs（审计日志表）**

```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    log_code VARCHAR(64) NOT NULL UNIQUE COMMENT '日志编号',
    module VARCHAR(32) NOT NULL COMMENT '模块：user/role/profile/ai/service/agent/order',
    action VARCHAR(64) NOT NULL COMMENT '操作类型',
    action_type VARCHAR(16) COMMENT '操作分类：data/permission/config/system',
    user_id BIGINT COMMENT '操作用户ID',
    user_name VARCHAR(64) COMMENT '操作用户姓名',
    user_role VARCHAR(32) COMMENT '操作用户角色',
    enterprise_id BIGINT COMMENT '操作涉及企业ID',
    target_type VARCHAR(64) COMMENT '操作对象类型',
    target_id BIGINT COMMENT '操作对象ID',
    target_code VARCHAR(64) COMMENT '操作对象编码',
    request_url VARCHAR(512) COMMENT '请求URL',
    request_params JSON COMMENT '请求参数（脱敏）',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    risk_level VARCHAR(16) COMMENT '风险等级：low/medium/high',
    data_classification VARCHAR(32) COMMENT '数据分类：public/person/sensitive/confidential/restricted',
    compliance_tags JSON COMMENT '合规标签：GDPR/个保法/医疗信息分级',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_module (module),
    INDEX idx_action (action),
    INDEX idx_user (user_id),
    INDEX idx_target (target_type, target_id),
    INDEX idx_created (created_at),
    INDEX idx_risk (risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审计日志表';
```

---

## 7. 患者档案自录功能

### 7.1 功能概述

患者档案自录是本系统的核心功能，支持企业员工和个人患者自主录入和管理个人健康档案。

### 7.2 录入类型与流程

| 档案类型 | 录入方式 | AI辅助能力 |
|---------|---------|-----------|
| 基础信息 | 表单填写 | 自动校验、历史数据复用 |
| 病历/门诊记录 | 文字输入 + PDF上传 | OCR提取关键信息 |
| 检查化验单 | 图片/PDF上传 | OCR提取指标值、异常标注 |
| 影像报告 | PDF上传 + DICOM存储 | 关键结论提取 |
| 用药记录 | 扫码/手动录入 | 药品知识关联、禁忌提醒 |
| 手术史 | 表单填写 + 手术记录上传 | 时间线自动生成 |
| 体征监测 | 手动录入/穿戴设备同步 | 趋势图可视化、异常预警 |

### 7.3 AI辅助档案识别

| 文档类型 | OCR准确率 | 结构化准确率 | 异常检测率 |
|---------|----------|-------------|-----------|
| 检查化验单 | ≥95% | ≥90% | ≥85% |
| 影像报告 | ≥90% | ≥85% | ≥80% |
| 门诊病历 | ≥85% | ≥80% | ≥75% |
| 处方单 | ≥95% | ≥92% | ≥90% |

### 7.4 档案授权管理

| 授权类型 | 可查看内容 | 有效期 |
|---------|-----------|--------|
| 健管师授权 | 完整档案 | 与服务合同绑定 |
| 医生授权 | 完整档案（限就诊相关） | 30天 |
| 企业主授权（员工） | 脱敏健康状态 | 雇佣关系存续 |
| 研究授权 | 脱敏数据 | 项目周期 |

---

## 8. 非功能需求

### 8.1 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 系统可用性 | ≥99.9% | 年度停机时间<8.76小时 |
| API响应时间(P99) | <500ms | 普通接口 |
| AI对话响应时间(P99) | <3s | 流式输出首字延迟 |
| 疾病预测响应时间 | <5s | 单病种预测 |
| 数字人视频生成 | <60s | 标准质量 |
| 并发用户数 | ≥10,000 | 同时在线 |

### 8.2 安全合规

| 合规要求 | 说明 |
|---------|------|
| **GDPR/个保法** | 个人信息最小化采集、加密存储、用户可撤回同意 |
| **医疗数据** | 分级分类管理、敏感数据脱敏 |
| **代理商隔离** | 代理商数据与平台数据隔离 |
| **等保2.0** | 三级等保认证 |
| **数据驻留** | 国内用户数据存储于国内服务器 |

### 8.3 AI服务降级策略

| 服务 | 故障场景 | 降级方案 |
|------|---------|---------|
| LLM | 服务不可达 | 备选LLM → 纯规则引擎 |
| TTS | 服务不可达 | 返回文本，患者端显示字幕 |
| SadTalker | 服务不可达 | 发送纯音频 + 静态头像图片 |
| 疾病预测 | 服务不可达 | 使用简化规则引擎评估，返回低置信度结果 |

---

## 9. 版本路线图

### 9.1 版本规划

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              版本路线图                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  v1.0 (MVP)        v1.5                  v2.0            v2.5+               │
│  ─────────         ─────                  ─────            ─────            │
│                                                                              │
│  Q1-Q2 2026        Q3-Q4 2026            Q1-Q2 2027       Q3 2027+           │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐     │
│  │ 员工/患者基础 │  │ TTS语音合成   │  │ 数字人视频   │  │ 平台化运营  │     │
│  │ 档案自录     │  │ 智能随访     │  │ 全流程      │  │ 代理商体系  │     │
│  │ 健管师工作台  │  │ 预警升级     │  │ 企业看板2.0 │  │ 开放API    │     │
│  │ 代理商基础   │  │ 疾病预测API  │  │ MDT协作     │  │ 开发者生态  │     │
│  │ 企业端基础   │  │ 可穿戴设备   │  │ 数字孪生医生 │  │ 数据市场   │     │
│  │ AI健康问答   │  │ 深度集成    │  │ 商业化套餐   │  │ 国际化     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.2 v1.0 MVP功能清单

| 模块 | 功能点 | 优先级 |
|------|--------|--------|
| 用户端 | 员工/患者注册认证 | P0 |
| 患者端 | 档案自录（表单+图片上传） | P0 |
| 患者端 | AI健康问答（文字） | P0 |
| 患者端 | 任务打卡 | P0 |
| 代理商 | 代理商入驻管理 | P0 |
| 代理商 | 企业客户拓展 | P0 |
| 健管师端 | 患者工作台 | P0 |
| 健管师端 | 干预计划管理 | P0 |
| 企业端 | 员工管理、套餐采购 | P0 |
| 系统端 | 用户认证、RBAC权限 | P0 |

### 9.3 v1.5增强功能清单

| 模块 | 功能点 | 优先级 |
|------|--------|--------|
| AI层 | TTS语音合成 | P0 |
| AI层 | 随访摘要AI生成 | P0 |
| AI层 | 疾病风险预测API集成 | P0 |
| 数据层 | 体征时序库(InfluxDB) | P0 |
| 功能 | 预警规则引擎升级 | P0 |
| 功能 | 代理商佣金结算 | P0 |
| 功能 | 体检报告解析 | P1 |

### 9.4 v2.0商业化功能清单

| 模块 | 功能点 | 优先级 |
|------|--------|--------|
| AI层 | SadTalker数字人 | P0 |
| AI层 | 数字孪生医生 | P0 |
| AI层 | 疾病风险预测全面上线 | P0 |
| 功能 | 企业数字人形象定制 | P0 |
| 功能 | MDT多学科协作 | P1 |
| 运营 | 商业化套餐定价 | P0 |
| 运营 | 电子合同签署 | P0 |
| 运营 | 代理商分成结算自动化 | P0 |

---

## 附录

### A. 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| ORG_BUYER | - | 采购健康管理服务的企业 |
| EMPLOYEE | - | 企业健康管理员工 |
| AGENT | - | 健康管理服务代理商 |
| 健康档案 | Health Profile | 患者完整的健康信息集合 |
| 数字健管师 | Digital Health Manager | AI驱动的虚拟健康管理师 |
| 疾病风险预测 | Disease Risk Prediction | 基于ML的多病种风险评估 |
| MDT | Multi-Disciplinary Team | 多学科会诊协作 |
| RBAC | Role-Based Access Control | 基于角色的权限控制 |
| TTS | Text-to-Speech | 文字转语音 |
| SadTalker | - | 音频驱动的数字人视频生成技术 |

### B. API接口地址汇总

| 接口 | Base URL | 端点 |
|------|----------|------|
| LLM | `http://192.168.0.126:8802` | `/chat` |
| TTS | `http://192.168.0.214:7778` | `/` |
| SadTalker | `http://192.168.0.214:7860` | `/` |
| 疾病风险预测 | `http://192.168.0.126:5000` | `/api/predict` |
| 数字孪生医生 | `http://192.168.0.214:8123` | `/api/v1/generate_video` |

### C. 角色权限矩阵

| 权限项 | EMPLOYEE | PATIENT | AGENT | 健管师 | 医生 | 超管 |
|--------|----------|---------|-------|--------|------|------|
| 录入自己的档案 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 查看授权的患者档案 | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| 创建干预计划 | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ |
| 审核干预计划 | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| 查看脱敏企业看板 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 处理工单 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 配置AI接口 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 管理企业团队 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 发布服务套餐 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 采购服务套餐 | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 代理销售套餐 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 审计日志查看 | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

**文档结束**

*本文档为产品管理内部使用，包含敏感技术信息，请勿外传。*
