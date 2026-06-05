# CTMS临床试验管理系统 PRD v2.0

> **版本**：v2.0 | **更新日期**：2026-05-06 | **状态**：正式版
> **文档编号**：CTMS-PRD-2026-V2.0
> **适用标准**：ICH GCP E6(R2) | FDA 21 CFR Part 11 | GDPR | HIPAA | ISO 27001

---

## 目录

1. [概述与愿景](#1-概述与愿景)
2. [系统架构](#2-系统架构)
3. [临床试验全流程](#3-临床试验全流程)
4. [角色体系与功能矩阵](#4-角色体系与功能矩阵)
5. [核心功能模块详规](#5-核心功能模块详规)
6. [AI Agent & Skills 设计](#6-ai-agent--skills-设计)
7. [数据库设计](#7-数据库设计)
8. [合规体系设计](#8-合规体系设计)
9. [微信/企微消息通知体系](#9-微信企微消息通知体系)
10. [非功能需求](#10-非功能需求)
11. [版本路线图](#11-版本路线图)

---

## 1. 概述与愿景

### 1.1 产品定位

**CTMS临床试验管理系统（Clinical Trial Management System）** 是一款面向医药企业、CRO公司、研究机构的临床试验全流程管理SaaS平台。系统以**试验项目**为核心载体，整合**AI智能辅助**、**电子签名**、**审计追踪**、**文档合规**四大能力，为申办方、研究者、CRO团队和监管方提供安全、合规、高效的临床试验管理服务。

### 1.2 合规定位

| 合规标准 | 适用条款 | 系统实现 |
|---------|---------|---------|
| **ICH GCP E6(R2)** | 4.2/5.0/8.0 | 试验流程标准化、伦理审查、知情同意管理 |
| **FDA 21 CFR Part 11** | 11.10/11.50 | 电子签名、审计追踪、版本控制 |
| **GDPR** | Art.5/6/17 | 数据最小化、加密存储、数据主体权利 |
| **HIPAA** | Privacy/Security Rule | PHI保护、访问控制、加密传输 |
| **ISO 27001** | A.8/A.14 | 信息安全策略、访问管理、事件响应 |

### 1.3 核心价值主张

| 角色 | 核心价值 |
|------|---------|
| **申办方** | 试验全局可视化、质量管控、成本优化 |
| **中心PI** | 高效的患者管理与数据录入、伦理合规 |
| **Sub-I** | 协作分工、任务追踪、文件管理 |
| **CRO PM** | 项目进度管控、资源调配、风险预警 |
| **CRA** | 远程监查、SDV追踪、问题管理 |
| **CRC** | 患者筛选、访视管理、数据录入 |
| **MM** | 医学监查、方案偏离审核、安全报告 |
| **DM** | 数据管理、质疑追踪、锁库管理 |
| **超管** | 系统配置、权限管理、审计合规 |

### 1.4 设计原则

- **合规优先**：所有功能设计符合GCP要求，支持监管机构检查
- **电子签名不可伪造**：符合21 CFR Part 11的电子签名规范
- **审计追踪全覆盖**：所有数据变更、操作行为留痕
- **AI增强效率**：AI辅助文档审核、数据清理、风险识别
- **数据完整性**：保证数据的准确性、完整性、可归因性（ALCOA+原则）

---

## 2. 系统架构

### 2.1 技术架构分层

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             终端接入层                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   Web端     │  │iOS/Android  │  │ 微信小程序   │  │   REST API  │       │
│  │ 申办方/CRO   │  │ 移动办公    │  │ 研究者访问  │  │ 第三方集成  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             API网关层                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │ Kong API Gateway │ 认证鉴权(SSO/OAuth2) │ 限流熔断 │ 操作路由 │ TLS 1.3 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI接口层 + 业务服务层                               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐              │
│  │   LLM服务        │ │   TTS服务        │ │ 文档解析服务     │              │
│  │  文本推理/审核   │ │  语音合成       │ │ OCR/结构化提取   │              │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘              │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        业务服务层                                       │ │
│  │ 项目管理 │ 伦理管理 │ 受试者管理 │ 访视管理 │ 数据采集 │ 药物管理 │ 安全报告│ │
│  │ 文档管理 │ 流程审批 │ 电子签名 │ 审计追踪 │ 质量管理 │ 工时管理 │ 消息通知│ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        异步任务层                                       │ │
│  │          Kafka消息队列 │ 定时任务 │ 邮件/短信/微信通知 │ 文件处理       │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                               数据层                                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐         │
│  │ MySQL  │ │Postgres│ │Milvus  │ │MinIO   │ │ Redis  │ │Kafka   │         │
│  │ 业务库  │ │ 电子文档│ │向量库   │ │文件对象 │ │ 缓存   │ │消息队列 │         │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                       加密与安全层                                     │   │
│  │    AES-256加密 │ TLS传输 │ 脱敏处理 │ 密钥管理(KMS) │ 电子签名(HSM)     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心AI Agent体系

| Agent名称 | 核心能力 | 调用接口 |
|-----------|---------|---------|
| **DOC_REVIEW** | 文档合规性审核 | LLM |
| **PROTOCOL_CHECK** | 方案偏离检测 | LLM + 规则引擎 |
| **AE_CODING** | 不良事件编码 | LLM + MedDRA |
| **LAB_NORMALIZATION** | 实验室数据标准化 | LLM + 规则引擎 |
| **CONSENT_AUDIT** | 知情同意完整性检查 | LLM + 规则引擎 |
| **SDV_ASSIST** | 源数据核查辅助 | LLM |
| **SAE_ALERT** | SAE快速报告生成 | LLM |
| **DATA_CLEANING** | 数据清理建议 | LLM |
| **QM_REPORT** | 质量报告生成 | LLM |
| **WORK_HOUR_SUGGEST** | 工时合理性建议 | LLM |

### 2.3 技术栈选型

| 层级 | 技术选型 | 说明 |
|------|---------|------|
| 前端Web | React 18 + Ant Design 5 | 企业级中台 |
| 移动端 | Flutter 3.x / React Native | iOS/Android跨平台 |
| 后端 | Spring Boot 3.x + Spring Cloud | 微服务架构 |
| 数据库 | PostgreSQL + MySQL | 业务+电子文档 |
| 文件存储 | MinIO + 对象锁 | 支持版本控制 |
| 缓存 | Redis Cluster | 会话/Token/热点 |
| 消息队列 | Apache Kafka | 异步解耦 |
| AI推理 | vLLM / Ollama | LLM本地部署 |
| 电子签名 | 堡垒机 + HSM | 符合21 CFR Part 11 |
| 加密 | AWS KMS / 自建KMS | 静态加密 |
| 协作文档 | 基于MinIO + Operational Transform | 多人实时编辑 |
| 微信集成 | 企微API / 微信公众号 | 消息通知推送 |

---

## 3. 临床试验全流程

### 3.1 试验阶段划分

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           临床试验全生命周期                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐       │
│  │ 准备阶段 │──▶│ 启动阶段 │──▶│ 执行阶段 │──▶│ 结束阶段 │──▶│ 归档阶段 │       │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘   └─────────┘       │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  准备阶段                                                              │   │
│  │  • 方案设计/审核        • 申办方内部审批    • 利益冲突声明              │   │
│  │  • 中心筛选/评估        • 研究者手册准备    • 实验室参考值收集          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  启动阶段                                                              │   │
│  │  • 伦理委员会(IRB/IEC)审批 • 合同签署         • 中心启动访视           │   │
│  │  • 机构审查委员会批准     • 财务协议          • 研究者培训              │   │
│  │  • 物资配送/药物供应     • IP管理初始化      • EDC系统配置              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  执行阶段                                                              │   │
│  │  • 患者筛选/入组        • 知情同意          • 随机化                  │   │
│  │  • 访视计划执行         • 数据录入(CRF)     • 医学监查                │   │
│  │  • 源数据核查(SDV)      • 方案偏离记录      • 不良事件报告(AE/SAE)    │   │
│  │  • 药物管理             • 样本管理          • 监查访视                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  结束阶段                                                              │   │
│  │  • 最后一位受试者访视   • 数据清理          • 数据库锁定(Database Lock) │   │
│  │  • 数据解锁/再锁定      • 统计编程          • CSR撰写                 │   │
│  │  • 中心关闭访视         • 药物清点/回收     • 物资回收                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  归档阶段                                                              │   │
│  │  • 试验文档归档        • 药物销毁证明       • 财务结算                │   │
│  │  • 受试者补偿发放       • 质量审计          • 监管机构核查支持          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据采集流程（EDC）

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          电子数据采集 (EDC) 流程                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ 数据录入  │───▶│ 保存提交 │───▶│ 自动核查 │───▶│ 数据质疑 │              │
│  │ (CRC)    │    │          │    │ (系统)   │    │ (Query)  │              │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘              │
│                                                        │                    │
│                                                        ▼                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ 数据澄清 │◀───│ 回复质疑 │◀───│ 分发质疑 │◀───│ DM审核   │              │
│  │          │    │ (site)   │    │          │    │          │              │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘              │
│                                                          │                    │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐          │                    │
│  │ 数据库   │◀───│ 数据复核 │◀───│ SDV确认  │◀─────────┘                    │
│  │ 解锁     │    │          │    │ (CRA)    │                               │
│  └──────────┘    └──────────┘    └──────────┘                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         数据库锁定 (Database Lock)                      │   │
│  │  1. 100%数据录入完成    2. 所有质疑已关闭    3. 方案偏离已批准         │   │
│  │  4. 医学编码完成        5. 数据一致性检查    6. 统计部门批准           │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 角色体系与功能矩阵

### 4.1 九大角色定义

| 角色 | 代码 | 描述 | 归属 |
|------|------|------|------|
| **申办方** | SPONSOR | 临床试验发起方，试验责任主体 | 申办方组织 |
| **主要研究者** | PI | 试验中心的主要负责人 | 研究机构 |
| **次要研究者** | SUB_I | PI指派的协助研究者 | 研究机构 |
| **CRO项目经理** | PM | 代表申办方管理试验项目 | CRO公司 |
| **临床监查员** | CRA | 监查试验执行质量 | CRO/申办方 |
| **临床协调员** | CRC | 协助研究者日常事务 | 研究机构/CRO |
| **医学监查员** | MM | 医学方案偏离审核、安全评估 | CRO/申办方 |
| **数据管理员** | DM | 数据管理与数据库锁定 | CRO/申办方 |
| **统计分析人员** | STAT | 统计分析、CSR撰写、SAP设计 | CRO/申办方 |
| **超级管理员** | SUPER_ADMIN | 系统配置与权限管理 | 系统平台 |

### 4.2 角色功能矩阵

| 功能模块 | 申办方 | PI | Sub-I | PM | CRA | CRC | MM | DM | STAT | 超管 |
|---------|-------|-----|-------|-----|------|-----|-----|------|------|------|
| **项目管理** | | | | | | | | | |
| 项目立项/审批 | ✅ | - | - | ✅ | - | - | - | - | - |
| 项目进度查看 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 里程碑管理 | ✅ | - | - | ✅ | - | - | - | - | - |
| **伦理与监管** | | | | | | | | | |
| 伦理申请 | ✅ | ✅ | - | ✅ | ✅ | ✅ | - | - | - |
| 伦理审批跟踪 | ✅ | ✅ | - | ✅ | ✅ | ✅ | - | - | - |
| 监管备案 | ✅ | ✅ | - | ✅ | - | - | - | - | - |
| **受试者管理** | | | | | | | | | |
| 患者入组 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| 知情同意 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| 随机化 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| 受试者列表 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| **访视与数据** | | | | | | | | | |
| 访视安排 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| CRF数据录入 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| 源数据核查(SDV) | - | - | - | - | ✅ | - | - | - | - |
| 数据质疑管理 | - | ✅ | ✅ | - | ✅ | ✅ | - | ✅ | - |
| **安全性管理** | | | | | | | | | |
| AE/SAE报告 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| SAE审核 | ✅ | - | - | ✅ | - | - | ✅ | - | - |
| SUSAR报告 | ✅ | - | - | ✅ | - | - | ✅ | - | - |
| 安全数据审核 | - | - | - | - | - | - | ✅ | - | - |
| **药物管理** | | | | | | | | | |
| 药物分发 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| 药物清点 | - | ✅ | ✅ | - | ✅ | ✅ | - | - | - |
| 药物回收 | - | ✅ | ✅ | - | ✅ | ✅ | - | - | - |
| **文档管理** | | | | | | | | | |
| 文档上传/版本 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 文档审批 | ✅ | ✅ | - | ✅ | - | - | ✅ | - | - |
| 文档协作编辑 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 文档查阅 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **流程审批** | | | | | | | | | |
| 审批流程配置 | ✅ | - | - | ✅ | - | - | - | - | - |
| 发起审批 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 审批操作 | ✅ | ✅ | - | ✅ | - | - | ✅ | ✅ | - |
| **工时管理** | | | | | | | | | |
| 工时填写 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 工时审批 | ✅ | ✅ | - | ✅ | - | - | ✅ | ✅ | - |
| 工时统计/报告 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 项目工时预算 | ✅ | - | - | ✅ | - | - | - | - | - |
| **系统管理** | | | | | | | | | |
| 用户管理 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 角色权限 | - | - | - | - | - | - | - | - | ✅ |
| 审计日志 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 5. 核心功能模块详规

### 5.1 项目管理模块

#### 5.1.1 项目立项

| 功能 | 说明 |
|------|------|
| 项目信息登记 | 项目名称、编号、适应症、试验阶段、试验类型 |
| 方案摘要 | 简要方案、目标入组人数、试验周期 |
| 参与方配置 | 申办方、CRO、研究中心列表 |
| 预算配置 | 项目预算、中心预算、里程碑付款、工时预算 |
| 附件上传 | 方案草案、研究者手册等 |

#### 5.1.2 里程碑管理

| 里程碑 | 触发条件 | 责任人 |
|--------|---------|--------|
| 项目立项 | 审批通过 | 申办方 |
| 首例筛选 | 第一例筛选 | CRC |
| 首例入组 | 第一例入组 | CRC |
| 50%入组 | 入组达50% | PM |
| 100%入组 | 完成入组目标 | PM |
| 最后例出组 | 最后例完成 | CRC |
| 数据库锁定 | Lock批准 | DM |
| 研究总结 | CSR完成 | 医学撰写 |

#### 5.1.3 研究中心管理

| 功能 | 说明 |
|------|------|
| 中心筛选 | 潜在中心评估、立项审批 |
| 中心启动 | 伦理合同完成、启动访视 |
| 中心激活 | 首例入组、正式运营 |
| 中心暂停/终止 | 暂停/终止原因、行动计划 |
| 中心关闭 | 关闭访视、物资回收 |

### 5.2 伦理与监管模块

#### 5.2.1 伦理申请管理

| 功能 | 说明 |
|------|------|
| 伦理申请创建 | 选择伦理会、提交材料清单 |
| 伦理审批跟踪 | 审批状态、意见记录、修正提交 |
| 知情同意书版本 | ICF版本管理、版本切换 |
| 持续审查 | 年度审查、SAE汇总报告 |
| 修正案管理 | 方案修正案申请与跟踪 |

#### 5.2.2 知情同意流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  准备ICF    │────▶│  伦理批准    │────▶│  受试者告知  │────▶│  签署ICF   │
│  版本       │     │  版本       │     │  说明       │     │            │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬─────┘
                                                                     │
                                                                     ▼
                                                             ┌─────────────┐
                                                             │  ICF归档   │
                                                             │ 电子签名   │
                                                             └─────────────┘
```

### 5.3 受试者管理模块

#### 5.3.1 患者入组

| 功能 | 说明 |
|------|------|
| 筛选号分配 | 自动/手动分配筛选号 |
| 入选排除标准 | 电子CRF核对、违规警告 |
| 知情同意确认 | ICF版本、签署时间、电子签名 |
| 随机化 | IWRS对接、药物分配、随机号 |
| 人口学信息 | 姓名(加密)、出生日期、性别等 |

### 5.4 访视与数据采集模块

#### 5.4.1 电子病例报告表(eCRF)

| 功能 | 说明 |
|------|------|
| 表单设计 | 自定义CRF表单、字段配置 |
| 数据录入 | 实时保存、自动计算 |
| 逻辑核查 | 范围检查、一致性检查 |
| 质疑生成 | 自动质疑、人工质疑 |
| 签名确认 | 研究者电子签名 |

#### 5.4.2 源数据核查(SDV)

| 功能 | 说明 |
|------|------|
| SDV计划 | 100% SDV / 抽样SDV |
| SDV执行 | 核对源文件与CRF |
| SDV记录 | SDV完成状态、日期 |
| SDV报告 | 差异报告、质量统计 |

### 5.5 安全性管理模块

#### 5.5.1 不良事件(AE)管理

| 功能 | 说明 |
|------|------|
| AE记录 | 名称、级别、起止日期、相关性 |
| AE编码 | MedDRA编码(AI辅助) |
| AE追踪 | 愈合情况、结局记录 |
| AE报告 | SAE提醒、汇总报告 |

#### 5.5.2 严重不良事件(SAE)处理

| 流程 | 时限 | 责任人 |
|------|------|--------|
| SAE发现→报告申办方 | 24小时 | 研究者 |
| SAE报告→报告伦理 | 24小时(致死) | CRA/PM |
| SUSAR→报告监管 | 7/15天 | MM/申办方 |
| 年度安全报告 | 1年 | MM |

### 5.6 药物管理模块

#### 5.6.1 药物供应

| 功能 | 说明 |
|------|------|
| 药物申请 | 中心药物申请、审批 |
| 药物分发 | 物流追踪、温度监控 |
| 药物接收 | 中心签收、验收记录 |
| 药物储存 | 温湿度监控、报警 |

#### 5.6.2 药物使用

| 功能 | 说明 |
|------|------|
| 药物发放 | 受试者发药、随机号对应 |
| 用药记录 | 剂量、日期、受试者签名 |
| 药物清点 | 库存核对、剩余数量 |
| 药物回收 | 空包装回收、销毁记录 |

### 5.7 文档管理模块（支持多人协作编辑）

#### 5.7.1 TMF (Trial Master File)

文档按ICH E6(R2)要求的TMF结构组织，支持多中心、多版本、多用户协作。

#### 5.7.2 文档版本控制

| 功能 | 说明 |
|------|------|
| 版本号管理 | 主版本.次版本(如1.0,1.1,2.0) |
| 变更记录 | 版本变更原因、变更内容 |
| 审批流程 | 版本发布审批、电子签名 |
| 历史追溯 | 所有历史版本可查阅 |

#### 5.7.3 文档协作编辑（核心新增功能）

**功能说明**：支持多人同时编辑同一份文档，类似Google Docs的实时协作体验。

**技术实现**：

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 协作文档核心 | MinIO + Operational Transform (OT) | 实时冲突解决 |
| 前端编辑器 | CKEditor 5 / Monaco Editor | 支持富文本/代码/表格 |
| 文档锁定机制 | Redis分布式锁 | 防止编辑冲突 |
| 自动保存 | 每30秒自动保存 | 防数据丢失 |
| 历史版本 | 完整操作历史记录 | 可回溯到任意版本 |

**协作功能列表**：

| 功能 | 说明 |
|------|------|
| 多人实时编辑 | 最多10人同时编辑同一文档 |
| 用户在线状态 | 显示当前在线协作者头像 |
| 光标位置同步 | 实时显示其他用户光标位置 |
| 编辑冲突解决 | OT算法自动合并，无冲突丢失 |
| 文档锁定 | 可手动锁定防止干扰，锁定时显示锁定者 |
| 评论与批注 | 协作者可添加批注、@提及 |
| 版本分支 | 可创建版本分支，独立修改后合并 |
| 变更追踪 | 显示每个协作者的修改痕迹 |
| 导出 | 支持导出为Word/PDF/HTML |
| 脱敏预览 | PHI内容自动脱敏显示 |

**文档协作编辑流程**：

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  打开文档   │────▶│  检查锁定    │────▶│  加入协作   │────▶│  实时编辑   │
│  编辑       │     │  状态        │     │  会话       │     │  同步操作   │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                     │
                         ┌────────────────────────────────────────────┤
                         │                                            │
                         ▼                                            ▼
              ┌─────────────┐                             ┌─────────────┐
              │  评论/批注  │                             │  保存版本   │
              │  @提及协作  │                             │  记录变更   │
              └─────────────┘                             └─────────────┘
```

#### 5.7.4 电子签名

| 签名类型 | 适用场景 | 签名要素 |
|---------|---------|---------|
| 作者签名 | 文档创建 | 签名+时间戳 |
| 审核签名 | 方案审核 | 签名+角色+时间戳 |
| 批准签名 | 最终批准 | 签名+角色+时间戳 |
| 确认签名 | 数据确认 | 签名+角色+时间戳 |

### 5.8 流程审批模块

#### 5.8.1 审批流程配置

| 流程类型 | 审批节点 | 审批人 |
|---------|---------|--------|
| 方案审批 | 初审→终审 | 医学总监→申办方 |
| 修正案审批 | IEC审批→执行 | PI→申办方 |
| 方案偏离审批 | 报告→批准 | MM→PI |
| 数据库锁定 | DM申请→批准 | 数据总监→统计 |
| 中心关闭 | 关闭申请→批准 | CRA→PM→申办方 |
| 工时审批 | 提交→审批 | 下级→上级 |
| 文档审批 | 提交→审核→批准 | 多级审批链 |

#### 5.8.2 审批流程图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  发起申请   │────▶│  一级审批   │────▶│  二级审批   │────▶│  审批完成   │
│             │     │             │     │             │     │  执行/归档   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                         │                   │
                         ▼                   ▼
                   ┌─────────────┐     ┌─────────────┐
                   │  驳回       │     │  驳回       │
                   │  退回发起人  │     │  退回一级    │
                   └─────────────┘     └─────────────┘
```

#### 5.8.3 审批消息通知

| 触发场景 | 通知方式 | 接收人 |
|---------|---------|--------|
| 审批任务到达 | 微信/企微+系统内 | 当前审批人 |
| 审批通过 | 微信/企微+邮件 | 发起人 |
| 审批驳回 | 微信/企微+邮件 | 发起人 |
| 审批超时提醒 | 系统内消息 | 审批人 |
| SAE审批加急 | 企微机器人+短信 | 所有审批节点 |

### 5.9 工时管理模块（核心新增功能）

#### 5.9.1 模块概述

工时管理系统覆盖临床试验全流程中所有角色的时间投入记录、审批、统计与成本核算，确保试验资源消耗可追溯、可量化。

#### 5.9.2 工时填写规则

| 角色 | 可填写工时类型 | 填写频率 | 审核人 |
|------|-------------|---------|--------|
| 申办方 | 项目管理、会议、方案审核 | 每周 | 上级主管 |
| PI | 中心管理、受试者管理、伦理、签字 | 每周 | 申办方/PM |
| Sub-I | 受试者管理、访视、医学判断 | 每周 | PI |
| PM | 项目管理、CRO管理、会议、报告 | 每天 | 申办方 |
| CRA | 监查访视、SDV、问题追踪、差旅 | 每天 | PM |
| CRC | 患者管理、数据录入、访视协调 | 每天 | PI/CRA |
| MM | 医学监查、方案偏离审核、安全报告 | 每周 | PM/申办方 |
| DM | 数据管理、数据库锁定、质疑处理 | 每周 | PM |

#### 5.9.3 工时分类体系

| 工时大类 | 工时细类 | 说明 |
|---------|---------|------|
| **项目管理** | 项目立项、会议、合同 | 申办方/PM主导 |
| **监查活动** | 启动访视、期中监查、关闭访视、SDV | CRA |
| **数据管理** | 数据录入、质疑处理、数据库锁定 | CRC/DM |
| **医学活动** | 医学监查、AE/SAE审核、方案偏离 | PI/MM |
| **伦理活动** | 伦理申请、修正案、持续审查 | PI/CRA |
| **药物管理** | 药物盘点、温度记录、药物分发 | CRC |
| **文档活动** | 文档撰写、审核、协作编辑 | 各角色 |
| **培训活动** | GCP培训、项目培训、研究者培训 | 各角色 |
| **差旅时间** | 中心访问差旅（非计费工时） | CRA/PM |
| **其他** | 通讯、行政、其他 | 各角色 |

#### 5.9.4 工时填写流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  每日记录   │────▶│  每周汇总   │────▶│  提交审批   │────▶│  审批确认   │
│  工作内容   │     │  分类工时   │     │  (周一前)   │     │  (PM/PI)   │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                     │
                         ┌────────────────────────────────────────────┤
                         │                                            │
                         ▼                                            ▼
              ┌─────────────┐                             ┌─────────────┐
              │  驳回修改   │                             │  审批通过   │
              │  退回填写   │                             │  计入统计   │
              └─────────────┘                             └─────────────┘
```

#### 5.9.5 工时统计与报表

| 报表类型 | 说明 | 使用角色 |
|---------|------|---------|
| 个人工时报告 | 个人每周/每月工时汇总 | 所有角色 |
| 项目工时总览 | 项目整体、各角色、各中心工时分布 | 申办方、PM |
| 中心工时报告 | 单个研究中心的工时投入 | PI、申办方 |
| 工时vs预算 | 实际工时与预算对比，超支预警 | 申办方、PM |
| 角色工时分析 | 各CRO角色工时分布与效率 | 申办方、PM |
| 工时趋势图 | 工时投入随时间变化趋势 | 所有角色 |
| 成本核算报告 | 工时×单价的成本汇总 | 申办方、财务 |

#### 5.9.6 工时审批规则

| 规则 | 说明 |
|------|------|
| 提交时限 | 每周一前提交上周工时，逾期锁定需申请解锁 |
| 审批层级 | 普通员工→直接上级→项目负责人（可配置） |
| 审批时限 | 审批人需在3个工作日内完成审批 |
| 超时提醒 | 审批超时自动发送企微提醒 |
| 驳回修改 | 被驳回工时可修改后重新提交 |
| 补填规则 | 最多补填前两周工时，需说明原因 |
| 电子签名 | 提交和审批均需电子签名确认 |

---

## 6. AI Agent & Skills 设计

### 6.1 Agent总体架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI Agent调度层                                   │
│                    LangGraph / LangChain Agent Orchestration                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────┬───────────┬───┴───┬───────────┬───────────┐
        ▼           ▼           ▼       ▼           ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│ DOC_REVIEW│ │AE_CODING │ │CONSENT_   │ │ SDV_ASSIST│ │ SAE_ALERT │
│  文档审核  │ │ AE编码   │ │  AUDIT    │ │  SDV辅助  │ │ SAE报告   │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│PROTOCOL_  │ │  LAB_     │ │  DATA_    │ │  QM_      │ │ WORK_HOUR_│
│ CHECK     │ │  NORMAL   │ │  CLEANING │ │  REPORT   │ │  SUGGEST  │
│ 方案偏离  │ │ 实验室标准化│ │ 数据清理  │ │ 质量报告  │ │ 工时建议  │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │        LLM推理引擎            │
                    │  Base URL: 192.168.0.126:8802 │
                    │  /chat (POST)                  │
                    └───────────────────────────────┘
```

### 6.2 Agent Skills详细规格

#### 6.2.1 DOC_REVIEW - 文档合规审核

**Skill Definition (YAML格式)**：

```yaml
skill_name: ctms_doc_review
version: "1.0"
description: |
  对临床试验文档进行GCP合规性审核，检查完整性、一致性和法规符合性。
triggers:
  - document_type: ["protocol", "ICF", "IB", "CSR", "monitoring_report"]
  - event: "document_version_uploaded"
  - manual: true

agent_type: DOC_REVIEW

input_schema:
  document_url: string (required)      # MinIO文件URL
  document_type: enum (required)       # protocol|ICF|IB|CSR|contract|report
  trial_id: string (required)
  document_version: string (required)
  regulatory_standards: array[string]   # ["ICH_GCP", "21CFR_Part11", "NMPA"]
  check_scope: enum                     # full|quick|spot

system_prompt: |
  你是一位专业的ICH GCP E6(R2)合规审核专家，拥有15年临床试验文档审核经验。
  你的职责是对临床试验文档进行严格的GCP合规性检查。

  【审核维度】
  1. **完整性检查**：必需章节/要素是否存在
  2. **GCP合规性**：是否符合ICH E6(R2)要求
  3. **一致性检查**：文档内部逻辑是否一致，交叉引用是否正确
  4. **法规符合性**：是否符合21 CFR Part 11、GDPR、HIPAA要求
  5. **术语规范性**：医学术语、缩略语是否规范
  6. **版本规范性**：版本号、日期是否规范

  【合规标准参考】
  - ICH E6(R2) Section 4 (Investigator), Section 5 (Sponsor), Section 6 (Protocol)
  - 21 CFR Part 11 (Electronic Records)
  - GDPR Art.5 (数据保护原则), Art.6 (处理合法性), Art.17 (删除权)
  - HIPAA Privacy Rule & Security Rule

  【输出要求】
  输出结构化的审核报告，包含：
  - 总体评分 (0-100)
  - 严重问题列表 (Critical)
  - 主要问题列表 (Major)  
  - 一般问题列表 (Minor)
  - 改进建议列表
  - 审核意见摘要 (中文，200字内)

  【重要约束】
  - 如文档包含受试者个人信息(PII/PHI)，自动脱敏处理
  - 不在审核报告中暴露任何可识别受试者信息
  - 所有审核操作均需记录审计日志
  - 引用具体GCP条款编号，说明不符合原因

tools:
  - name: read_document
    description: 读取MinIO中的文档内容
    params: { url: string }
  - name: check_gcp_clause
    description: 核对GCP条款
    params: { clause_id: string }
  - name: log_audit
    description: 记录审核操作到审计日志
    params: { action: string, details: object }

output_schema:
  review_id: string
  overall_score: number (0-100)
  compliance_status: enum  # compliant|conditionally_compliant|non_compliant
  issues:
    critical: array[Issue]
    major: array[Issue]
    minor: array[Issue]
  suggestions: array[string]
  summary: string (Chinese, <200 chars)
  reviewed_at: datetime
  review_duration_seconds: number

Issue:
  issue_id: string
  severity: enum  # critical|major|minor
  gcp_clause_reference: string
  location: string
  description: string
  impact: string
  recommendation: string
```

#### 6.2.2 AE_CODING - AE MedDRA编码辅助

**Skill Definition**：

```yaml
skill_name: ctms_ae_coding
version: "1.0"
description: |
  对不良事件(AE)名称进行MedDRA编码辅助，支持PT/LLT查询和编码一致性检查。
triggers:
  - event: "ae_record_created"
  - event: "ae_name_modified"
  - manual: true

agent_type: AE_CODING

system_prompt: |
  你是一位专业的不良事件编码专家，精通MedDRA（Medical Dictionary for 
  Regulatory Activities）编码系统。

  【编码规则】
  1. 优先使用LLT（Lowest Level Term）编码
  2. 报告PT（Preferred Term）和SOC（System Organ Class）
  3. 多学科AE需选择最相关的SOC分类
  4. 保持同一试验内AE编码的一致性
  5. AI编码结果需人工审核确认

  【MedDRA结构】
  SOC (系统器官分类) → HLGT (高级组术语) → HLT (高级术语) 
  → PT (首选术语) → LLT (最低层级术语)

  【合规要求】
  - 21 CFR Part 312.32 (IND安全报告)
  - ICH E2A (快速安全报告)
  - CIOMS和MedDRA编码指南

  【输出格式】
  {
    "ae_name": "...",
    "llt_code": "...",
    "llt_term": "...",
    "pt_code": "...",
    "pt_term": "...",
    "soc_code": "...",
    "soc_term": "...",
    "confidence": 0.0-1.0,
    "coding_note": "...",
    "alternative_codes": [...]
  }
```

#### 6.2.3 CONSENT_AUDIT - 知情同意完整性检查

**Skill Definition**：

```yaml
skill_name: ctms_consent_audit
version: "1.0"
description: |
  审核知情同意书(ICF)的完整性、合规性和受试者签署规范性。
triggers:
  - event: "consent_signed"
  - event: "consent_version_changed"
  - manual: true

agent_type: CONSENT_AUDIT

system_prompt: |
  你是一位专注于受试者保护和数据隐私的临床试验合规专家。
  
  【知情同意审核清单 - ICH E6(R2) Section 4.8】
  必须包含的要素：
  1. 研究性质和目的说明
  2. 试验治疗措施及随机分配说明
  3. 受试者义务说明
  4. 风险和不便的合理预期
  5. 预期受益说明
  6. 其他可选治疗方案
  7. 保密范围说明
  8. 补偿和损害处理说明
  9. 自愿参与说明
  10. 联系信息（疑问/伤害）
  11. 伦理委员会信息

  【检查项目】
  1. ICF版本与伦理批准版本一致性
  2. 必需要素是否完整
  3. 受试者签名完整性（本人+日期）
  4. 研究者签名完整性
  5. 签署时间逻辑（知情日期 ≤ 签署日期）
  6. 见证人/翻译使用规范性
  7. 撤回同意程序规范性
  8. PHI使用授权声明

  【GDPR/HIPAA特别检查】
  - 数据最小化原则声明
  - 数据主体权利（访问、更正、删除）
  - 数据跨境传输声明（如适用）
  - PHI保护措施说明

  【输出格式】
  {
    "consent_id": "...",
    "audit_status": "pass|conditional|fail",
    "completeness_score": 0-100,
    "required_elements_check": {...},
    "signature_check": {...},
    "timeliness_check": {...},
    "gdpr_hipaa_check": {...},
    "issues": [...],
    "ai_confidence": 0.0-1.0
  }
```

#### 6.2.4 SAE_ALERT - SAE快速报告生成

**Skill Definition**：

```yaml
skill_name: ctms_sae_alert
version: "1.0"
description: |
  当SAE发生时，快速生成标准化的SAE报告草稿，支持SUSAR快速识别。
triggers:
  - event: "sae_reported"
  - urgency: high

agent_type: SAE_ALERT

system_prompt: |
  你是一位药物警戒和临床安全专家，精通SAE报告的国际标准。
  
  【报告标准】
  - ICH E2A: 严重不良事件定义和快速报告
  - ICH E2D: 上市后安全性数据管理
  - CIOMS表格规范
  - FDA 21 CFR 312.32 (IND安全报告)
  - EMA Module VI (PSP)

  【SUSAR识别规则】
  - 死亡或危及生命的SAE
  - 与药物很可能/肯定相关
  - 新发现的重要风险

  【输出内容】
  1. SAE基本信息（受试者编号、SAE名称、发生日期）
  2. SAE详细描述（症状、体征、检查结果）
  3. 因果关系评估（申办方评估）
  4. 合并用药情况
  5. 处理措施和结局
  6. 报告人信息和联系方式
  7. 相关文档清单
  8. SUSAR初步判断
  9. 监管报告时限提醒（7天/15天）
  10. 医学叙述（AI生成草稿）

  【安全约束】
  - 受试者信息脱敏
  - 仅生成结构化报告，不生成诊断结论
  - 所有AI输出需人工审核确认
  - SUSAR判断需MM复核
```

#### 6.2.5 WORK_HOUR_SUGGEST - 工时合理性建议

**Skill Definition**：

```yaml
skill_name: ctms_work_hour_suggest
version: "1.0"
description: |
  分析用户填写的工时记录，提供合理性建议，识别异常工时模式。
triggers:
  - event: "work_hour_submitted"
  - manual: true

agent_type: WORK_HOUR_SUGGEST

system_prompt: |
  你是一位临床试验项目管理和资源分析专家。
  
  【分析维度】
  1. **合理性检查**
     - 工时与活动类型的匹配度
     - 工时与访视/任务的关联性
     - CRA差旅时间合理性（≤4h/天？）
     - 加班频率合理性（>20h/周需预警）
  
  2. **历史对比**
     - 同角色历史平均工时
     - 同中心/项目历史数据
     - 季节性/阶段波动分析
  
  3. **项目阶段对比**
     - 启动阶段 vs 执行阶段 vs 结束阶段 工时分布
     - 里程碑临近时的工时峰值
  
  4. **异常检测**
     - 超出角色基准工时30%标记警告
     - 连续高工时（>50h/周）标记风险
     - 工时与完成任务量不匹配时提醒
     - 节假日/周末工时需说明
  
  5. **成本分析**
     - 按角色单价计算实际成本
     - 与预算对比（%消耗）
     - 完工百分比预测
  
  【输出格式】
  {
    "submission_id": "...",
    "total_hours_submitted": number,
    "analysis_result": {
      "overall_assessment": "reasonable|questionable|abnormal",
      "confidence_score": 0.0-1.0,
      "warnings": [
        {
          "type": "overtime|over_budget|mismatch|unusual_pattern",
          "description": "...",
          "suggestion": "...",
          "severity": "info|warning|critical"
        }
      ],
      "cost_analysis": {
        "estimated_cost": number,
        "budget_utilization_percent": number,
        "forecast_completion_cost": number
      },
      "comparative_analysis": {
        "vs_role_average": "+/-%",
        "vs_project_phase_average": "+/-%",
        "trend_direction": "increasing|decreasing|stable"
      }
    }
  }
```

#### 6.2.6 其他Agent Skills规格一览

| Agent | 触发方式 | 核心LLM Prompt要点 | 输出 | 人工复核 |
|-------|---------|------------------|------|---------|
| **PROTOCOL_CHECK** | SAE报告后自动+手动 | 检测访视偏离、用药偏离、评估偏离，按GCP条款分类 | 偏离类型/级别/影响评估 | 必须(MM) |
| **LAB_NORMALIZATION** | 实验室数据录入后 | 识别异常值、判断临床意义、标准化单位 | 正常化值/临床显著性 | 必须(DM) |
| **SDV_ASSIST** | CRA发起SDV时 | 对比源数据与CRF、识别不一致、建议核查项 | SDV差异列表/核查优先级 | 必须(CRA) |
| **DATA_CLEANING** | 每周数据审核 | 识别缺失值、异常值、逻辑矛盾 | 清理建议清单 | 必须(DM) |
| **QM_REPORT** | 每月+里程碑 | 汇总质量指标、偏离统计、AE概况 | 质量报告草稿 | PM审核 |

### 6.3 Agent合规护栏（Guardrails）

```yaml
guardrails:
  - rule: "pii_phi_protection"
    description: "禁止AI处理包含PII/PHI的原始数据"
    action: "auto_redact"
    applies_to: ["all_agents"]
    
  - rule: "gcp_no_generation"
    description: "禁止AI生成受试者诊断、治疗决策"
    action: "reject_generation"
    applies_to: ["all_agents"]
    
  - rule: "audit_logging"
    description: "所有AI交互必须记录审计日志"
    action: "mandatory_log"
    applies_to: ["all_agents"]
    
  - rule: "human_review_required"
    description: "AI辅助生成的医疗决策文件必须人工审核"
    conditions: ["sae_report", "protocol_deviation_approval", "ae_coding_final"]
    action: "require_human_sign_off"
    
  - rule: "consent_audit_transparency"
    description: "知情同意审核需向用户说明AI审核依据"
    action: "include_gcp_clause_reference"
    
  - rule: "bias_detection"
    description: "检测并标注可能的编码偏见"
    action: "flag_potential_bias"
    applies_to: ["AE_CODING"]
```

---

## 7. 数据库设计

### 7.1 数据库选型

| 数据库 | 用途 | 特点 |
|-------|------|------|
| **PostgreSQL** | 试验数据、电子文档、向量检索 | ACID事务、JSON支持、pgvector |
| **MySQL** | 业务配置、流程数据、工时 | 高并发、成熟稳定 |
| **MinIO** | 文件对象存储、文档协作 | 版本控制、S3兼容、对象锁 |
| **Redis** | 会话、协作文档锁、缓存 | 实时协作支持 |
| **Milvus** | 文档向量检索 | RAG增强 |

### 7.2 MySQL核心表结构（38张表）

> 注：相比v1.0，新增 **工时管理** 相关4张表、**文档协作** 相关2张表、**消息通知** 相关2张表、**企微集成** 相关1张表。

#### 7.2.1 项目与组织表（沿用v1.0表1-7）

> 详见v1.0：trials(表1)、trial_milestones(表2)、sites(表3)、investigators(表4)、sponsors(表5)、cro_companies(表6)、cro_assignments(表7)

#### 7.2.2 受试者管理表（沿用v1.0表8-10）

> 详见v1.0：subjects(表8)、subject_visits(表9)、informed_consents(表10)

#### 7.2.3 安全与药物警戒表（沿用v1.0表11-13）

> 详见v1.0：adverse_events(表11)、serious_adverse_events(表12)、protocol_deviations(表13)

#### 7.2.4 数据采集与管理表（沿用v1.0表14-16）

> 详见v1.0：crf_forms(表14)、crf_entries(表15)、data_queries(表16)

#### 7.2.5 药物管理表（沿用v1.0表17-18）

> 详见v1.0：investigational_products(表17)、ip_dispensations(表18)

#### 7.2.6 文档管理表（扩展，v1.0表19-20 + 新增2张）

**表19（扩展）：trial_documents（试验文档表）**

```sql
CREATE TABLE trial_documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '文档ID',
    doc_code VARCHAR(64) NOT NULL UNIQUE COMMENT '文档编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT COMMENT '中心ID（适用时）',
    doc_type VARCHAR(32) NOT NULL COMMENT '文档类型：protocol方案/ib研究者手册/consent知情/contract合同/regulatory监管/monitoring监查/lab实验室/source源文件/correspondence通讯',
    doc_category VARCHAR(64) COMMENT '文档分类（TMF结构）',
    doc_name VARCHAR(256) NOT NULL COMMENT '文档名称',
    doc_description TEXT COMMENT '文档描述',
    version VARCHAR(16) NOT NULL COMMENT '版本号',
    file_url VARCHAR(512) NOT NULL COMMENT '文件URL',
    file_name VARCHAR(256) COMMENT '原始文件名',
    file_size BIGINT COMMENT '文件大小(字节)',
    file_type VARCHAR(32) COMMENT '文件类型',
    file_hash VARCHAR(64) COMMENT '文件Hash(SHA-256)',
    -- 协作编辑相关字段（新增）
    is_collaborative TINYINT DEFAULT 0 COMMENT '是否支持协作编辑：0否 1是',
    collaborative_session_id VARCHAR(64) COMMENT '当前协作会话ID',
    current_locked_by BIGINT COMMENT '当前锁定人ID',
    current_locked_at DATETIME COMMENT '锁定时间',
    last_auto_save_at DATETIME COMMENT '最后自动保存时间',
    -- 审批与电子签名（沿用）
    approval_required TINYINT DEFAULT 0 COMMENT '是否需要审批',
    approval_status VARCHAR(16) COMMENT '审批状态：not_required/pending/approved/rejected',
    approved_by BIGINT COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    electronic_signature_required TINYINT DEFAULT 0 COMMENT '是否需要电子签名',
    signed_by BIGINT COMMENT '签名人ID',
    signed_at DATETIME COMMENT '签名时间',
    electronic_signature_hash VARCHAR(64) COMMENT '电子签名Hash',
    supersedes_doc_id BIGINT COMMENT '替代的文档ID',
    is_latest_version TINYINT DEFAULT 1 COMMENT '是否为最新版本',
    retention_period_years INT DEFAULT 15 COMMENT '保存年限',
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doc_code (doc_code),
    INDEX idx_trial (trial_id),
    INDEX idx_collaborative (is_collaborative),
    INDEX idx_approval (approval_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试验文档表（含协作编辑）';
```

**表20（扩展）：document_versions（文档版本历史表）**

```sql
CREATE TABLE document_versions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    version_code VARCHAR(64) NOT NULL UNIQUE COMMENT '版本编号',
    doc_id BIGINT NOT NULL COMMENT '文档ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    version VARCHAR(16) NOT NULL COMMENT '版本号',
    change_summary TEXT COMMENT '变更摘要',
    change_details TEXT COMMENT '变更详情',
    file_url VARCHAR(512) NOT NULL COMMENT '文件URL',
    file_hash VARCHAR(64) COMMENT '文件Hash',
    effective_date DATE COMMENT '生效日期',
    approval_status VARCHAR(16) DEFAULT 'pending' COMMENT '审批状态',
    approved_by BIGINT COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    electronic_signature_hash VARCHAR(64) COMMENT '签名Hash',
    is_current_version TINYINT DEFAULT 0 COMMENT '是否为当前版本',
    superseded_at DATETIME COMMENT '被替代时间',
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doc (doc_id),
    INDEX idx_trial (trial_id),
    INDEX idx_current (is_current_version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档版本历史表';
```

**新增-表19A：document_collaborative_sessions（文档协作会话表）**

```sql
CREATE TABLE document_collaborative_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(64) NOT NULL UNIQUE COMMENT '会话ID',
    doc_id BIGINT NOT NULL COMMENT '文档ID',
    doc_version VARCHAR(16) COMMENT '文档版本',
    session_status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '会话状态：active进行中/saved已保存/closed已关闭',
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    created_by_name VARCHAR(64) COMMENT '创建人姓名',
    started_at DATETIME NOT NULL COMMENT '开始时间',
    last_activity_at DATETIME COMMENT '最后活动时间',
    closed_at DATETIME COMMENT '关闭时间',
    total_editing_duration_minutes INT COMMENT '总编辑时长(分钟)',
    auto_save_count INT DEFAULT 0 COMMENT '自动保存次数',
    manual_save_count INT DEFAULT 0 COMMENT '手动保存次数',
    redis_session_key VARCHAR(128) COMMENT 'Redis中的会话键',
    operational_log_url VARCHAR(512) COMMENT '操作日志URL(MinIO)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id),
    INDEX idx_doc (doc_id),
    INDEX idx_status (session_status),
    INDEX idx_user (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档协作会话表';
```

**新增-表19B：document_collaborators（文档协作者表）**

```sql
CREATE TABLE document_collaborators (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(64) NOT NULL COMMENT '会话ID',
    doc_id BIGINT NOT NULL COMMENT '文档ID',
    user_id BIGINT NOT NULL COMMENT '协作者ID',
    user_name VARCHAR(64) NOT NULL COMMENT '协作者姓名',
    user_role VARCHAR(32) NOT NULL COMMENT '协作者角色',
    user_avatar VARCHAR(512) COMMENT '协作者头像',
    cursor_position INT COMMENT '光标位置',
    selection_range JSON COMMENT '选区范围JSON',
    join_at DATETIME NOT NULL COMMENT '加入时间',
    last_active_at DATETIME COMMENT '最后活跃时间',
    is_online TINYINT DEFAULT 0 COMMENT '是否在线',
    permission_level VARCHAR(16) NOT NULL DEFAULT 'editor' COMMENT '权限级别：viewer查看者/editor编辑者/admin管理者',
    can_comment TINYINT DEFAULT 1 COMMENT '是否可以评论',
    can_export TINYINT DEFAULT 0 COMMENT '是否可以导出',
    edits_count INT DEFAULT 0 COMMENT '编辑次数',
    comments_count INT DEFAULT 0 COMMENT '评论次数',
    left_at DATETIME COMMENT '离开时间',
    total_active_minutes INT COMMENT '总活跃时长(分钟)',
    device_info VARCHAR(128) COMMENT '设备信息',
    ip_address VARCHAR(45) COMMENT 'IP地址',
    UNIQUE KEY uk_session_user (session_id, user_id),
    INDEX idx_session (session_id),
    INDEX idx_doc (doc_id),
    INDEX idx_user (user_id),
    INDEX idx_online (is_online)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文档协作者表';
```

#### 7.2.7 流程审批表（沿用v1.0表21-23）

> 详见v1.0：approval_workflows(表21)、approval_requests(表22)、approval_stages(表23)

#### 7.2.8 监查与质量管理表（沿用v1.0表24-25）

> 详见v1.0：monitoring_visits(表24)、audit_logs(表25)

#### 7.2.9 用户与权限表（沿用v1.0表26-29）

> 详见v1.0：users(表26)、user_roles(表27)、permissions(表28)、role_permissions(表29)

#### 7.2.10 实验室与样本表（沿用v1.0表30-31）

> 详见v1.0：lab_tests(表30)、lab_results(表31)

#### 7.2.11 电子签名表（沿用v1.0表32）

> 详见v1.0：electronic_signatures(表32)

#### 7.2.12 数据库锁定表（沿用v1.0表33）

> 详见v1.0：database_lock(表33)

#### 7.2.13 工时管理表（新增表34-37）

**新增-表34：work_hour_categories（工时分类配置表）**

```sql
CREATE TABLE work_hour_categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    category_code VARCHAR(32) NOT NULL UNIQUE COMMENT '分类代码',
    category_name VARCHAR(128) NOT NULL COMMENT '分类名称',
    category_type VARCHAR(16) NOT NULL COMMENT '大类：project_management项目管理/monitoring监查/data_management数据管理/medical_activity医学活动/ethics_activity伦理活动/ip_management药物/document_activity文档/training培训/travel差旅/other其他',
    parent_id BIGINT COMMENT '父分类ID',
    description TEXT COMMENT '分类描述',
    applicable_roles JSON COMMENT '适用角色JSON：["CRA","CRC","PM","PI"]',
    is_billable TINYINT DEFAULT 1 COMMENT '是否可计费',
    hourly_rate DECIMAL(10,2) COMMENT '标准小时费率',
    requires_evidence TINYINT DEFAULT 0 COMMENT '是否需要附件',
    max_hours_per_entry DECIMAL(5,2) DEFAULT 12 COMMENT '每次最大工时',
    min_hours_per_entry DECIMAL(5,2) DEFAULT 0.25 COMMENT '每次最小工时',
    color_code VARCHAR(8) COMMENT '日历显示颜色',
    icon_name VARCHAR(32) COMMENT '图标名称',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    is_active TINYINT DEFAULT 1 COMMENT '是否启用',
    created_by BIGINT COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category_code (category_code),
    INDEX idx_type (category_type),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工时分类配置表';
```

**新增-表35：work_hour_records（工时记录表）**

```sql
CREATE TABLE work_hour_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    record_code VARCHAR(64) NOT NULL UNIQUE COMMENT '记录编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT COMMENT '中心ID（适用时）',
    user_id BIGINT NOT NULL COMMENT '用户ID（工时填写人）',
    user_name VARCHAR(64) NOT NULL COMMENT '用户姓名',
    user_role VARCHAR(32) NOT NULL COMMENT '用户角色',
    organization_id BIGINT COMMENT '组织ID',
    work_date DATE NOT NULL COMMENT '工作日期',
    work_hour_category_id BIGINT COMMENT '工时分类ID',
    work_hour_category_code VARCHAR(32) COMMENT '工时分类代码',
    work_hour_category_name VARCHAR(128) COMMENT '工时分类名称',
    work_description TEXT NOT NULL COMMENT '工作描述',
    related_subject_id BIGINT COMMENT '关联受试者ID（适用时）',
    related_visit_id BIGINT COMMENT '关联访视ID（适用时）',
    related_document_id BIGINT COMMENT '关联文档ID（适用时）',
    related_ae_id BIGINT COMMENT '关联AE ID（适用时）',
    hours_worked DECIMAL(5,2) NOT NULL COMMENT '工时数',
    is_billable TINYINT DEFAULT 1 COMMENT '是否可计费',
    hourly_rate DECIMAL(10,2) COMMENT '小时费率',
    estimated_cost DECIMAL(10,2) COMMENT '估算成本',
    evidence_file_url VARCHAR(512) COMMENT '证据文件URL',
    entry_method VARCHAR(16) DEFAULT 'manual' COMMENT '录入方式：manual手动/import导入/ai_suggested AI建议',
    submission_status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT '提交状态：draft草稿/submitted已提交/approved已审批/rejected已驳回/modified已修改/locked已锁定',
    submission_date DATETIME COMMENT '提交日期',
    submitted_by BIGINT COMMENT '提交人ID',
    approval_workflow_id BIGINT COMMENT '审批流程ID',
    approval_request_id BIGINT COMMENT '审批请求ID',
    current_approver_id BIGINT COMMENT '当前审批人ID',
    current_approver_name VARCHAR(64) COMMENT '当前审批人姓名',
    approval_date DATETIME COMMENT '审批日期',
    approved_by BIGINT COMMENT '审批人ID',
    approved_by_name VARCHAR(64) COMMENT '审批人姓名',
    rejection_reason TEXT COMMENT '驳回原因',
    is_supplement TINYINT DEFAULT 0 COMMENT '是否为补填',
    supplement_reason TEXT COMMENT '补填原因',
    supplement_for_record_id BIGINT COMMENT '补填原记录ID',
    is_locked TINYINT DEFAULT 0 COMMENT '是否已锁定（逾期锁定）',
    locked_reason VARCHAR(256) COMMENT '锁定原因',
    locked_at DATETIME COMMENT '锁定时间',
    locked_by BIGINT COMMENT '锁定人ID',
    ai_suggestion TEXT COMMENT 'AI工时建议内容',
    ai_confidence DECIMAL(5,2) COMMENT 'AI建议置信度',
    ai_flags JSON COMMENT 'AI标记JSON：[{flag_type,description,severity}]',
    electronic_signature_required TINYINT DEFAULT 1 COMMENT '是否需要电子签名',
    submitted_signature_hash VARCHAR(64) COMMENT '提交电子签名Hash',
    approved_signature_hash VARCHAR(64) COMMENT '审批电子签名Hash',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_record_code (record_code),
    INDEX idx_trial (trial_id),
    INDEX idx_user (user_id),
    INDEX idx_work_date (work_date),
    INDEX idx_category (work_hour_category_id),
    INDEX idx_submission (submission_status),
    INDEX idx_trial_user_date (trial_id, user_id, work_date),
    INDEX idx_locked (is_locked)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工时记录表';
```

**新增-表36：work_hour_approvals（工时审批记录表）**

```sql
CREATE TABLE work_hour_approvals (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    approval_code VARCHAR(64) NOT NULL UNIQUE COMMENT '审批编号',
    request_id BIGINT COMMENT '关联审批请求ID（可为空）',
    user_id BIGINT NOT NULL COMMENT '被审批人ID',
    user_name VARCHAR(64) NOT NULL COMMENT '被审批人姓名',
    user_role VARCHAR(32) NOT NULL COMMENT '被审批人角色',
    trial_id BIGINT COMMENT '试验ID',
    approval_period_start DATE NOT NULL COMMENT '审批周期开始',
    approval_period_end DATE NOT NULL COMMENT '审批周期结束',
    total_hours DECIMAL(8,2) COMMENT '总工时',
    total_billable_hours DECIMAL(8,2) COMMENT '总可计费工时',
    total_cost DECIMAL(12,2) COMMENT '总成本',
    record_count INT COMMENT '记录条数',
    approval_status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '审批状态：pending待审批/approved已批准/rejected已驳回/cancelled已取消',
    submitted_at DATETIME NOT NULL COMMENT '提交时间',
    submitted_by BIGINT NOT NULL COMMENT '提交人ID',
    submitted_by_name VARCHAR(64) COMMENT '提交人姓名',
    submitted_signature_hash VARCHAR(64) COMMENT '提交电子签名Hash',
    first_approver_id BIGINT COMMENT '一级审批人ID',
    first_approver_name VARCHAR(64) COMMENT '一级审批人姓名',
    first_approval_status VARCHAR(16) COMMENT '一级审批状态',
    first_approval_at DATETIME COMMENT '一级审批时间',
    first_approval_comments TEXT COMMENT '一级审批意见',
    first_approval_signature_hash VARCHAR(64) COMMENT '一级审批签名Hash',
    second_approver_id BIGINT COMMENT '二级审批人ID（如需）',
    second_approver_name VARCHAR(64) COMMENT '二级审批人姓名',
    second_approval_status VARCHAR(16) COMMENT '二级审批状态',
    second_approval_at DATETIME COMMENT '二级审批时间',
    second_approval_comments TEXT COMMENT '二级审批意见',
    second_approval_signature_hash VARCHAR(64) COMMENT '二级审批签名Hash',
    ai_review_result JSON COMMENT 'AI审核结果JSON',
    ai_flags_count INT DEFAULT 0 COMMENT 'AI标记数量',
    overdue_reminder_sent TINYINT DEFAULT 0 COMMENT '超时提醒是否发送',
    processing_deadline DATETIME COMMENT '审批截止时间',
    actual_processing_hours INT COMMENT '实际处理时长(小时)',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_approval_code (approval_code),
    INDEX idx_user (user_id),
    INDEX idx_trial (trial_id),
    INDEX idx_period (approval_period_start, approval_period_end),
    INDEX idx_status (approval_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工时审批记录表';
```

**新增-表37：work_hour_budgets（工时预算表）**

```sql
CREATE TABLE work_hour_budgets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    budget_code VARCHAR(64) NOT NULL UNIQUE COMMENT '预算编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT COMMENT '中心ID（特定中心时）',
    budget_type VARCHAR(16) NOT NULL COMMENT '预算类型：overall整体/role角色/site中心/phase阶段',
    target_role VARCHAR(32) COMMENT '目标角色（role类型时）',
    budget_period_start DATE NOT NULL COMMENT '预算周期开始',
    budget_period_end DATE COMMENT '预算周期结束',
    total_budget_hours DECIMAL(10,2) NOT NULL COMMENT '总预算工时',
    total_budget_cost DECIMAL(12,2) COMMENT '总预算成本',
    breakdown_json JSON COMMENT '预算分解JSON：[{category_code,category_name,hours,cost}]',
    approval_workflow_id BIGINT COMMENT '审批流程ID',
    approval_status VARCHAR(16) DEFAULT 'approved' COMMENT '审批状态',
    approved_by BIGINT COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    actual_total_hours DECIMAL(10,2) DEFAULT 0 COMMENT '实际总工时',
    actual_total_cost DECIMAL(12,2) DEFAULT 0 COMMENT '实际总成本',
    utilization_rate DECIMAL(5,2) DEFAULT 0 COMMENT '预算使用率%',
    over_budget_alert_threshold DECIMAL(5,2) DEFAULT 80 COMMENT '超预算预警阈值%',
    last_alert_at DATETIME COMMENT '最后预警时间',
    alert_count INT DEFAULT 0 COMMENT '预警次数',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '状态：active有效/closed已关闭/cancelled已取消',
    remarks TEXT COMMENT '备注',
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_budget_code (budget_code),
    INDEX idx_trial (trial_id),
    INDEX idx_site (site_id),
    INDEX idx_type (budget_type),
    INDEX idx_period (budget_period_start, budget_period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='工时预算表';
```

#### 7.2.14 消息通知表（新增表38-39）

**新增-表38：notification_preferences（消息通知偏好表）**

```sql
CREATE TABLE notification_preferences (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    notification_type VARCHAR(32) NOT NULL COMMENT '通知类型：approval_request审批请求/approval_result审批结果/sae_alert SAE警报/document_reminder文档提醒/visit_reminder访视提醒/work_hour_reminder工时提醒/message消息',
    channel VARCHAR(16) NOT NULL COMMENT '通知渠道：wechat微信/enterprise_wechat企微/email邮件/sms短信/system系统',
    enabled TINYINT DEFAULT 1 COMMENT '是否启用',
    quiet_hours_start TIME COMMENT '勿扰开始时间',
    quiet_hours_end TIME COMMENT '勿扰结束时间',
    wechat_openid VARCHAR(64) COMMENT '微信OpenID',
    wechat_unionid VARCHAR(64) COMMENT '微信UnionID',
    enterprise_wechat_userid VARCHAR(64) COMMENT '企微UserID',
    enterprise_wechat_agentid VARCHAR(32) COMMENT '企微应用AgentID',
    mobile_number VARCHAR(32) COMMENT '手机号（短信）',
    email_address VARCHAR(128) COMMENT '邮箱地址',
    priority_filter VARCHAR(32) COMMENT '优先级过滤：all全部/low及以上/normal及以上/high及以上/urgent紧急 only',
    trial_filter JSON COMMENT '试验过滤JSON（指定可接收通知的试验）',
    summary_mode TINYINT DEFAULT 0 COMMENT '是否汇总模式（减少通知频率）',
    summary_frequency VARCHAR(16) DEFAULT 'realtime' COMMENT '汇总频率：realtime实时/hourly每小时/daily每天',
    last_notification_at DATETIME COMMENT '最后通知时间',
    failure_count INT DEFAULT 0 COMMENT '失败次数',
    last_failure_at DATETIME COMMENT '最后失败时间',
    last_failure_reason VARCHAR(256) COMMENT '最后失败原因',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_type_channel (user_id, notification_type, channel),
    INDEX idx_user (user_id),
    INDEX idx_type (notification_type),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息通知偏好表';
```

**新增-表39：notification_records（消息通知记录表）**

```sql
CREATE TABLE notification_records (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    notification_code VARCHAR(64) NOT NULL UNIQUE COMMENT '通知编号',
    user_id BIGINT NOT NULL COMMENT '接收用户ID',
    user_name VARCHAR(64) COMMENT '接收用户姓名',
    notification_type VARCHAR(32) NOT NULL COMMENT '通知类型',
    channel VARCHAR(16) NOT NULL COMMENT '通知渠道',
    title VARCHAR(256) NOT NULL COMMENT '通知标题',
    content TEXT NOT NULL COMMENT '通知内容',
    short_content VARCHAR(128) COMMENT '短内容（微信/企微摘要）',
    priority VARCHAR(16) DEFAULT 'normal' COMMENT '优先级：low/normal/high/urgent',
    trial_id BIGINT COMMENT '关联试验ID',
    related_object_type VARCHAR(64) COMMENT '关联对象类型',
    related_object_id BIGINT COMMENT '关联对象ID',
    related_object_code VARCHAR(64) COMMENT '关联对象编号',
    action_url VARCHAR(512) COMMENT '操作链接URL',
    click_count INT DEFAULT 0 COMMENT '点击次数',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending待发送/sending发送中/sent已发送/delivered已送达/read已读/failed发送失败',
    sent_at DATETIME COMMENT '发送时间',
    delivered_at DATETIME COMMENT '送达时间',
    read_at DATETIME COMMENT '阅读时间',
    failure_reason VARCHAR(256) COMMENT '失败原因',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    max_retry INT DEFAULT 3 COMMENT '最大重试次数',
    external_message_id VARCHAR(128) COMMENT '外部平台消息ID（企微/微信）',
   企微企业ID VARCHAR(64) COMMENT '企微企业ID',
   企微应用ID VARCHAR(32) COMMENT '企微应用AgentID',
   企微响应_code VARCHAR(16) COMMENT '企微API响应码',
   企微响应_msg VARCHAR(256) COMMENT '企微API响应消息',
    audit_log_id BIGINT COMMENT '关联审计日志ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_notification_code (notification_code),
    INDEX idx_user (user_id),
    INDEX idx_type (notification_type),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_trial (trial_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='消息通知记录表';
```

#### 7.2.15 角色功能管理详表（补充）

**各角色工时管理功能对照**：

| 功能 | 申办方 | PI | Sub-I | PM | CRA | CRC | MM | DM |
|------|-------|-----|-------|-----|------|-----|-----|------|
| 工时填写（本人） | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 工时填写（代填下级） | ✅ | ✅ | - | ✅ | - | - | ✅ | ✅ |
| 工时审批（下级） | ✅ | ✅ | - | ✅ | - | - | ✅ | ✅ |
| 工时查看（本人） | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 工时查看（本项目） | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 工时查看（全项目） | ✅ | - | - | - | - | - | - | - |
| 工时预算设置 | ✅ | - | - | ✅ | - | - | - | - |
| 工时报表导出 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 工时系统配置 | - | - | - | - | - | - | - | - | ✅ |

---

## 8. 合规体系设计

### 8.1 ICH GCP E6(R2) 合规映射

| GCP条款 | 系统实现 | 数据表 |
|---------|---------|--------|
| 4.1/4.2 资质 | 研究者资质验证、GCP培训记录 | investigators, users |
| 4.3 资源 | 中心资源配置、工时管理 | sites, work_hour_records |
| 4.4 方案依从 | 方案偏离检测、审批 | protocol_deviations |
| 4.8 受试者保护 | 知情同意管理、ICF版本 | informed_consents |
| 4.9 记录报告 | CRF数据采集、质疑管理 | crf_entries, data_queries |
| 4.11 安全报告 | SAE处理、SUSAR报告 | serious_adverse_events |
| 5.1 质量管控 | 监查计划、SDV、质量报告 | monitoring_visits, audit_logs |
| 5.4 合同 | 合同管理、财务协议 | trial_documents |
| 5.5 试验用药 | 药物管理、温度监控 | investigational_products |
| 8.0 文件 | TMF文档管理、版本控制 | trial_documents |
| 8.3 源文件 | 源数据关联、SDV追踪 | crf_entries |

### 8.2 FDA 21 CFR Part 11 合规实现

| Part 11条款 | 系统实现 |
|------------|---------|
| 11.10(a) 系统验证 | 功能测试、性能测试、IQ/OQ/PQ |
| 11.10(b) 电子签名 | 数字证书+密码+HSM，不可伪造 |
| 11.10(c) 审计追踪 | 全操作留痕，防篡改（区块链Hash链） |
| 11.10(e) 准确可靠 | ALCOA+数据完整性原则 |
| 11.50 电子签名链接 | 签名与电子记录关联 |
| 11.100 电子签名组成 | ID+认证因子，双因素验证 |

### 8.3 GDPR 合规实现

| GDPR条款 | 系统实现 |
|---------|---------|
| Art.5 原则 | 目的限制、最小化、存储限制 |
| Art.6 处理合法性 | 同意+合法利益双基础 |
| Art.12-22 数据主体权利 | 访问、更正、删除、可携带权 |
| Art.25 数据保护设计 | 隐私默认、假名化 |
| Art.32 安全措施 | 加密(AES-256)、访问控制、备份 |
| Art.33/34 违规通知 | 72小时违规通知流程 |

### 8.4 HIPAA 合规实现

| HIPAA规则 | 系统实现 |
|----------|---------|
| Privacy Rule | PHI识别、最小披露原则 |
| Security Rule - Administrative | 访问管理、安全培训 |
| Security Rule - Physical | 数据中心安全、物理防护 |
| Security Rule - Technical | 加密、审计追踪、访问控制 |
| Breach Notification | 违规检测和通知流程 |

### 8.5 ISO 27001 合规实现

| ISO 27001控制域 | 系统实现 |
|---------------|---------|
| A.5 信息安全策略 | 安全策略文档化 |
| A.6 信息安全组织 | 角色权限分离 |
| A.9 访问控制 | RBAC、密码策略、双因素 |
| A.10 密码学 | TLS、AES-256、数字签名 |
| A.12 运营安全 | 审计日志、病毒防护、备份 |
| A.16 信息安全事件 | 事件管理流程 |

---

## 9. 微信/企微消息通知体系

### 9.1 消息通知架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           消息通知触发源                                      │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────┐ ┌────────────┐             │
│  │  流程审批    │ │  SAE警报  │ │  工时提醒    │ │  文档到期  │             │
│  │  (待审批)   │ │  (新SAE) │ │  (待填写)    │ │  (超期)    │             │
│  └──────┬───────┘ └────┬─────┘ └──────┬───────┘ └─────┬──────┘             │
│         │              │              │               │                    │
└─────────┼──────────────┼──────────────┼───────────────┼────────────────────┘
          │              │              │               │
          ▼              ▼              ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Kafka消息总线                                        │
│           统一消息入口 → 消息路由 → 消息队列（按类型/优先级分队列）              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌────────────────────────────┼────────────────────────────┐
        ▼                            ▼                            ▼
┌───────────────────┐   ┌───────────────────┐   ┌───────────────────┐
│   企微通知服务    │   │   微信公众号     │   │   系统内通知     │
│  (WeCom API)      │   │  (WeChat API)    │   │                   │
│  企业内部使用     │   │  患者/外部联系    │   │  所有用户        │
└───────────────────┘   └───────────────────┘   └───────────────────┘
```

### 9.2 企微消息推送配置

| 配置项 | 值 |
|-------|-----|
| 企业ID | 从企微管理后台获取 |
| 应用AgentID | 创建自建应用获取 |
| 应用Secret | 应用凭证Secret |
| Webhook URL | 机器人Webhook（群通知） |
| 消息API | `https://qyapi.weixin.qq.com/cgi-bin/message/send` |

**消息推送请求示例**：

```json
POST https://qyapi.weixin.qq.com/cgi-bin/message/send
Access-Token: {CORP_ACCESS_TOKEN}

{
  "touser": "zhangsan",
  "toparty": "",
  "totag": "",
  "msgtype": "textcard",
  "agentid": "1000001",
  "textcard": {
    "title": "【待审批】新SAE报告需审核",
    "description": "<div class=\"gray\">试验: CTR-2024-001</div><div class=\"normal\">报告编号: SAE-2024-0123</div><div>严重程度: 重度 | 报告人: 张医生</div>",
    "url": "https://ctms.example.com/sae/detail/SAE-2024-0123",
    "btntxt": "立即处理"
  }
}
```

### 9.3 通知场景与模板

| 场景 | 渠道 | 模板类型 | 优先级 | 时效要求 |
|------|------|---------|--------|---------|
| **审批请求** | 企微+系统 | 文本卡片 | high | 即时 |
| **SAE新报告** | 企微机器人 | 文本卡片 | urgent | <5分钟 |
| **SUSAR警报** | 企微+短信 | 文本卡片 | urgent | <5分钟 |
| **工时待填写提醒** | 系统+企微 | 文本 | normal | 每周一09:00 |
| **工时审批通过** | 企微 | 文本 | low | 实时 |
| **访视提醒** | 系统+企微 | 文本卡片 | normal | 访视前24h |
| **文档待签署** | 企微 | 文本卡片 | high | 实时 |
| **文档版本更新** | 企微 | 文本 | normal | 实时 |
| **数据库锁定通知** | 企微+邮件 | 文本卡片 | high | 实时 |
| **系统安全通知** | 企微 | 文本 | urgent | 实时 |

### 9.4 企微机器人通知（群通知场景）

```json
{
  "msgtype": "markdown",
  "agentid": "1000001",
  "markdown": {
    "content": "🚨 **SAE快速警报**\n"
              + "> **试验编号**: CTR-2024-001\n"
              + "> **SAE编号**: SAE-2024-0156\n"
              + "> **严重程度**: 危及生命\n"
              + "> **发生时间**: 2024-03-15 14:30\n"
              + "> **报告人**: PI-张医生\n"
              + "> **当前状态**: 待SUSAR评估\n"
              + "> [立即处理](https://ctms.example.com/sae/detail/SAE-2024-0156)"
  }
}
```

### 9.5 微信公众号消息（外部通知场景）

适用于研究者（PI/Sub-I）非工作时间通知，通过OpenID推送。

| 配置项 | 值 |
|-------|-----|
| AppID | 公众号AppID |
| AppSecret | 公众号AppSecret |
| Template ID | 审批通知模板ID、安全警报模板ID |
| 用户授权 | OAuth2静默授权获取OpenID |

### 9.6 消息通知安全与合规

| 安全措施 | 说明 |
|---------|------|
| 消息内容脱敏 | PHI/PII自动脱敏，不在微信消息中暴露 |
| 传输加密 | TLS 1.3 |
| 企微AccessToken | 2小时自动刷新 |
| 失败重试 | 最多3次，间隔递增 |
| 审计记录 | 所有消息推送记录完整审计 |
| 勿扰模式 | 支持设定勿扰时段 |
| 权限过滤 | 按角色过滤通知类型 |
| 试验权限 | 仅推送用户有权限的试验相关通知 |
| GDPR合规 | 通知记录最小化保存 |

---

## 10. 非功能需求

### 10.1 性能指标

| 指标 | 目标值 | 说明 |
|------|-------|------|
| 系统可用性 | ≥99.9% | 每月停机时间<45分钟 |
| 页面响应时间 | P95 < 2秒 | 核心页面 |
| API响应时间 | P95 < 500ms | 普通接口 |
| AI推理时间 | P95 < 10秒 | LLM接口 |
| 并发用户 | ≥500 | 同时在线 |
| 文件上传 | ≤50MB/文件 | 支持文档 |
| 数据存储 | 15年+ | 监管要求 |

### 10.2 安全指标

| 指标 | 目标值 |
|------|-------|
| 密码强度 | 大小写+数字+特殊字符，≥12位 |
| 会话超时 | 30分钟无操作自动登出 |
| 双因素认证 | 关键操作强制启用 |
| 数据加密 | AES-256静态加密 |
| 传输加密 | TLS 1.3 |
| 审计日志保留 | ≥15年 |
| 备份频率 | 每日增量，每周全量 |

### 10.3 合规保留期

| 数据类型 | 保留期 | 依据 |
|---------|-------|------|
| 试验文档 | 试验结束后≥15年 | ICH GCP E6(R2) 4.9.5 |
| 电子签名记录 | ≥15年 | 21 CFR Part 11 |
| 审计日志 | ≥15年 | 21 CFR Part 11.10(e) |
| AE/SAE报告 | ≥15年 | ICH GCP / NMPA |
| 受试者数据 | 试验结束后≥15年 | GDPR Art.5(1)(e) |
| 工时记录 | ≥7年 | 财务合规 |

---

## 11. 版本路线图

| 版本 | 计划时间 | 主要功能 |
|------|---------|---------|
| **v1.0** | Q1 2026 | 基础框架、项目管理、受试者管理、EDC、安全管理 |
| **v2.0** | Q2 2026 | AI Agent体系、工时管理、文档协作、企微通知 |
| **v3.0** | Q3 2026 | IWRS对接、中心实验室、药物警戒增强 |
| **v4.0** | Q4 2026 | 数据导出(CDISC)、统计分析、CSR自动生成 |

---

> **文档结束**
> 编写：产品通 | 审核：待定 | 批准：待定
