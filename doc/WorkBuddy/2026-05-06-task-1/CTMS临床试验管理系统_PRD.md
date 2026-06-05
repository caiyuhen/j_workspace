# CTMS临床试验管理系统 PRD v1.0

> **版本**：v1.0 | **更新日期**：2026-05-06 | **状态**：正式版
> **文档编号**：CTMS-PRD-2026-V1.0
> **适用标准**：ICH GCP E6(R2) | FDA 21 CFR Part 11 | GDPR | HIPAA | ISO 27001

---

## 目录

1. [概述与愿景](#1-概述与愿景)
2. [系统架构](#2-系统架构)
3. [临床试验全流程](#3-临床试验全流程)
4. [角色体系与功能矩阵](#4-角色体系与功能矩阵)
5. [核心功能模块详规](#5-核心功能模块详规)
6. [AI接口层规格](#6-ai接口层规格)
7. [数据库设计](#7-数据库设计)
8. [合规体系设计](#8-合规体系设计)
9. [非功能需求](#9-非功能需求)
10. [版本路线图](#10-版本路线图)

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
│  │ 文档管理 │ 流程审批 │ 电子签名 │ 审计追踪 │ 质量管理 │ 财务结算 │         │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        异步任务层                                       │ │
│  │          Kafka消息队列 │ 定时任务 │ 邮件/短信通知 │ 文件处理          │ │
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

### 3.2 核心流程图

#### 3.2.1 项目立项与审批流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  申办方     │     │  方案制定   │     │  内部审核   │     │  方案定稿   │
│  发起立项   │────▶│  (医学部)   │────▶│  (质量部)   │────▶│             │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                     │
                                                                     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  项目启动   │◀────│  合同签署   │◀────│  伦理审批   │◀────│  监管备案   │
│             │     │             │     │  (IEC/IRB)  │     │  (NMPA/FDA) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

#### 3.2.2 受试者入组流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  患者筛选   │────▶│  知情同意   │────▶│  筛选检查   │────▶│  随机入组   │
│  (CRC协助)  │     │  (ICF签名)  │     │             │     │  (IWRS)     │
└─────────────┘     └─────────────┘     └──────┬──────┘     └──────┬──────┘
                                               │                   │
                                               ▼                   ▼
                                        ┌─────────────┐     ┌─────────────┐
                                        │  合格?      │     │  分配受试者  │
                                        │  否→排除    │     │  编码       │
                                        │  是→继续    │     │             │
                                        └─────────────┘     └─────────────┘
```

#### 3.2.3 安全性报告流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  AE/SAE    │────▶│  严重程度   │────▶│  因果关系   │────▶│  上报决策   │
│  发现       │     │  评估       │     │  判断        │     │             │
└─────────────┘     └─────────────┘     └──────┬──────┘     └──────┬──────┘
                                               │                   │
                    ┌──────────────────────────┼───────────────────┤
                    │                          │                   │
                    ▼                          ▼                   ▼
             ┌─────────────┐           ┌─────────────┐     ┌─────────────┐
             │ 非SAE        │           │ SAE         │     │ SUSAR       │
             │ 记录AE       │           │ 立即通知    │     │ 快速报告    │
             │             │           │ 申办方+伦理 │     │ 监管机构    │
             └─────────────┘           └─────────────┘     └─────────────┘
```

### 3.3 数据采集流程（EDC）

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
| **超级管理员** | SUPER_ADMIN | 系统配置与权限管理 | 系统平台 |

### 4.2 角色功能矩阵

| 功能模块 | 申办方 | PI | Sub-I | PM | CRA | CRC | MM | DM | 超管 |
|---------|-------|-----|-------|-----|------|-----|-----|------|------|
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
| 文档查阅 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **流程审批** | | | | | | | | | |
| 审批流程配置 | ✅ | - | - | ✅ | - | - | - | - | - |
| 发起审批 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 审批操作 | ✅ | ✅ | - | ✅ | - | - | ✅ | ✅ | - |
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
| 预算配置 | 项目预算、中心预算、里程碑付款 |
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

#### 5.2.2 监管备案

| 法规 | 适用场景 | 备案要求 |
|------|---------|---------|
| NMPA | 中国临床试验 | 试验登记、备案变更 |
| FDA | 美国临床试验 | IND申请、Annual Report |
| EMA | 欧盟临床试验 | CTA申请、安全报告 |

#### 5.2.3 知情同意流程

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

#### 5.3.2 受试者编号体系

| 编码规则 | 示例 | 说明 |
|---------|------|------|
| 中心编号 | 001 | 研究中心唯一编号 |
| 受试者编号 | 001-001-001 | 中心-随机-访视序号 |
| 随机号 | RCT-2024-00123 | 随机编号 |
| 药物编号 | IP-001-001-LOT01 | 药物号-批号 |

#### 5.3.3 随机化与盲法

| 盲法类型 | 实现方式 |
|---------|---------|
| 双盲 | 药物编盲、紧急破盲程序 |
| 单盲 | 受试者盲态 |
| 开放 | 无盲法要求 |

### 5.4 访视与数据采集模块

#### 5.4.1 访视计划

| 功能 | 说明 |
|------|------|
| 访视窗口 | 窗口期设置、偏离计算 |
| 访视模板 | 标准访视流程配置 |
| 计划调整 | 访视延期、提前的处理 |
| 访视记录 | 实际日期、完成状态 |

#### 5.4.2 电子病例报告表(eCRF)

| 功能 | 说明 |
|------|------|
| 表单设计 | 自定义CRF表单、字段配置 |
| 数据录入 | 实时保存、自动计算 |
| 逻辑核查 | 范围检查、一致性检查 |
| 质疑生成 | 自动质疑、人工质疑 |
| 签名确认 | 研究者电子签名 |

#### 5.4.3 源数据核查(SDV)

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

#### 5.5.3 药物警戒

| 功能 | 说明 |
|------|------|
| 信号检测 | 数据汇总、趋势分析 |
| 风险评估 | 风险获益评估 |
| 安全更新 | DSUR/PSUR生成 |
| 风险最小化 | 沟通、培训计划 |

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

### 5.7 文档管理模块

#### 5.7.1 TMF (Trial Master File)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            试验主文件 (TMF) 结构                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  0. Trial Management (试验管理)                                              │
│     ├── 0.1 试验方案                                                         │
│     ├── 0.2 研究者手册                                                       │
│     ├── 0.3 项目计划                                                        │
│     └── 0.4 培训材料                                                         │
│                                                                              │
│  1. Ethics (伦理)                                                           │
│     ├── 1.1 伦理委员会批件                                                   │
│     ├── 1.2 知情同意书                                                      │
│     ├── 1.3 伦理通讯                                                        │
│     └── 1.4 持续审查记录                                                     │
│                                                                              │
│  2. Regulatory (监管)                                                       │
│     ├── 2.1 监管机构批准文件                                                 │
│     ├── 2.2 备案证明                                                         │
│     └── 2.3 出口许可                                                         │
│                                                                              │
│  3. Investigator & Site (研究者与中心)                                        │
│     ├── 3.1 研究者简历                                                       │
│     ├── 3.2 培训记录                                                         │
│     ├── 3.3 实验室证书                                                       │
│     └── 3.4 利益冲突声明                                                     │
│                                                                              │
│  4. Contract & Finance (合同与财务)                                           │
│     ├── 4.1 试验合同                                                        │
│     ├── 4.2 财务协议                                                        │
│     └── 4.3 受试者补偿                                                       │
│                                                                              │
│  5. Subject Data (受试者数据)                                                │
│     ├── 5.1 筛选记录                                                        │
│     ├── 5.2 随机记录                                                        │
│     ├── 5.3 访视记录                                                        │
│     ├── 5.4 实验室检查                                                      │
│     └── 5.5 样本记录                                                        │
│                                                                              │
│  6. Safety & Pharmacovigilance (安全与药物警戒)                              │
│     ├── 6.1 不良事件报告                                                    │
│     ├── 6.2 SUSAR报告                                                        │
│     └── 6.3 年度安全报告                                                     │
│                                                                              │
│  7. Investigational Product (试验药物)                                       │
│     ├── 7.1 药物发放记录                                                     │
│     ├── 7.2 药物回收记录                                                     │
│     └── 7.3 温度记录                                                         │
│                                                                              │
│  8. Monitoring (监查)                                                       │
│     ├── 8.1 监查访视报告                                                     │
│     ├── 8.2 源数据核查记录                                                   │
│     └── 8.3 偏离报告                                                         │
│                                                                              │
│  9. Statistics (统计)                                                       │
│     ├── 9.1 数据管理计划                                                     │
│     ├── 9.2 统计分析计划                                                     │
│     └── 9.3 CSR                                                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 5.7.2 文档版本控制

| 功能 | 说明 |
|------|------|
| 版本号管理 | 主版本.次版本(如1.0,1.1,2.0) |
| 变更记录 | 版本变更原因、变更内容 |
| 审批流程 | 版本发布审批、电子签名 |
| 历史追溯 | 所有历史版本可查阅 |

#### 5.7.3 电子签名

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

### 5.9 数据管理与统计模块

#### 5.9.1 数据清理

| 阶段 | 活动 | 责任人 |
|------|------|--------|
| 实时核查 | 自动质疑、编辑核查 | 系统/DM |
| 医学编码 | AE/CM MedDRA编码 | MM |
| 数据质疑 | 质疑分发、回复、关闭 | CRA/CRC |
| 数据审核 | 数据审核会、方案偏离 | DM/医学 |
| 锁库前清理 | 最终清理、数据库解锁 | DM |

#### 5.9.2 数据库锁定

| 锁库前检查 | 说明 |
|-----------|------|
| 数据完整性 | 100%数据录入、所有质疑关闭 |
| 方案依从性 | 所有偏离已记录/批准 |
| 医学编码 | AE/CM已完成编码 |
| 一致性 | 跨表数据一致性 |
| 质量审核 | 数据质量报告通过 |

---

## 6. AI接口层规格

### 6.1 LLM接口（文字推理引擎）

#### 6.1.1 接口配置

| 属性 | 值 |
|------|-----|
| **Base URL** | `http://192.168.0.126:8802` |
| **端点** | `/chat` |
| **方法** | `POST` |

#### 6.1.2 请求规格

```json
POST /chat
Content-Type: application/json

{
  "session_id": "ctms_sess_abc123",
  "agent_type": "DOC_REVIEW",
  "messages": [
    {
      "role": "system",
      "content": "你是一位专业的GCP合规审核助手..."
    },
    {
      "role": "user",
      "content": "请审核以下知情同意书文本是否符合GCP要求..."
    }
  ],
  "context": {
    "trial_id": "CTR-2024-001",
    "document_type": "ICF",
    "document_version": "2.0",
    "regulatory_standard": ["ICH_GCP", "21CFR_Part11"]
  },
  "generation_config": {
    "temperature": 0.3,
    "max_tokens": 1000,
    "stream": true
  }
}
```

#### 6.1.3 Agent类型枚举

| agent_type | 说明 | 能力范围 |
|------------|------|---------|
| `DOC_REVIEW` | 文档合规审核 | GCP合规检查、完整性审核 |
| `PROTOCOL_CHECK` | 方案偏离检测 | 偏离识别、分类 |
| `AE_CODING` | AE编码辅助 | MedDRA编码建议 |
| `CONSENT_AUDIT` | 知情同意检查 | ICF完整性、合规性 |
| `SAE_ALERT` | SAE报告辅助 | SAE快速报告生成 |
| `DATA_CLEANING` | 数据清理建议 | 异常数据识别 |
| `QM_REPORT` | 质量报告 | 监查报告、质量汇总 |

#### 6.1.4 医疗合规护栏

| 规则类型 | 描述 | 处理方式 |
|---------|------|---------|
| **数据脱敏** | 禁止暴露PII | 自动脱敏处理 |
| **合规检查** | GCP条款核对 | 标注不符合项 |
| **安全过滤** | 禁止生成受保护信息 | 拒绝生成 |
| **审计记录** | 所有AI交互留痕 | 记录日志 |

---

## 7. 数据库设计

### 7.1 数据库选型

| 数据库 | 用途 | 特点 |
|-------|------|------|
| **PostgreSQL** | 试验数据、电子文档 | ACID事务、JSON支持 |
| **MySQL** | 业务配置、流程数据 | 高并发、成熟稳定 |
| **MinIO** | 文件对象存储 | 版本控制、S3兼容 |

### 7.2 MySQL核心表结构（35张表）

#### 7.2.1 项目与组织表

**表1：trials（试验项目表）**

```sql
CREATE TABLE trials (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '试验ID',
    trial_code VARCHAR(64) NOT NULL UNIQUE COMMENT '试验编号',
    trial_name VARCHAR(256) NOT NULL COMMENT '试验名称',
    protocol_no VARCHAR(64) COMMENT '方案编号',
    indication VARCHAR(256) COMMENT '适应症',
    trial_phase VARCHAR(16) NOT NULL COMMENT '试验阶段：I/II/III/IV',
    trial_type VARCHAR(32) NOT NULL COMMENT '试验类型：interventional/observational',
    design_type VARCHAR(32) COMMENT '设计类型：randomized/blind/parallel/cross_over',
    blinding_method VARCHAR(16) COMMENT '盲法：double_blind/single_blind/open',
    sponsor_id BIGINT COMMENT '申办方ID',
    cro_id BIGINT COMMENT 'CRO公司ID',
    target_enrollment INT COMMENT '目标入组人数',
    actual_enrollment INT DEFAULT 0 COMMENT '实际入组人数',
    enrollment_status VARCHAR(16) DEFAULT 'not_started' COMMENT '入组状态：not_started/not_recruiting/recruiting/closed',
    start_date DATE COMMENT '试验开始日期',
    end_date DATE COMMENT '试验结束日期',
    status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft/approved/active/suspended/terminated/completed',
    therapeutic_area VARCHAR(64) COMMENT '治疗领域',
    study_objective TEXT COMMENT '研究目的',
    primary_endpoint TEXT COMMENT '主要终点',
    secondary_endpoints TEXT COMMENT '次要终点',
    inclusion_criteria TEXT COMMENT '入组标准',
    exclusion_criteria TEXT COMMENT '排除标准',
    regulatory_filing VARCHAR(32) COMMENT '监管备案类型：NMPA/FDA/EMA',
    regulatory_status VARCHAR(16) COMMENT '备案状态',
    approved_by BIGINT COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    locked_at DATETIME COMMENT '锁定时间',
    locked_by BIGINT COMMENT '锁定人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trial_code (trial_code),
    INDEX idx_sponsor (sponsor_id),
    INDEX idx_status (status),
    INDEX idx_phase (trial_phase)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试验项目表';
```

**表2：trial_milestones（试验里程碑表）**

```sql
CREATE TABLE trial_milestones (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    milestone_code VARCHAR(64) NOT NULL UNIQUE COMMENT '里程碑编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    milestone_name VARCHAR(128) NOT NULL COMMENT '里程碑名称',
    milestone_type VARCHAR(32) NOT NULL COMMENT '里程碑类型',
    planned_date DATE COMMENT '计划日期',
    actual_date DATE COMMENT '实际日期',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态：pending/in_progress/completed/delayed/cancelled',
    completion_rate DECIMAL(5,2) DEFAULT 0 COMMENT '完成率',
    responsible_role VARCHAR(32) COMMENT '责任角色',
    responsible_user_id BIGINT COMMENT '责任人ID',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trial (trial_id),
    INDEX idx_status (status),
    INDEX idx_planned_date (planned_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试验里程碑表';
```

**表3：sites（研究中心表）**

```sql
CREATE TABLE sites (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    site_code VARCHAR(32) NOT NULL UNIQUE COMMENT '中心编号',
    site_name VARCHAR(256) NOT NULL COMMENT '中心名称',
    institution_name VARCHAR(256) COMMENT '机构名称',
    institution_type VARCHAR(32) COMMENT '机构类型：hospital/clinic/research_institute',
    address TEXT COMMENT '地址',
    province VARCHAR(32) COMMENT '省份',
    city VARCHAR(32) COMMENT '城市',
    country VARCHAR(32) DEFAULT 'China' COMMENT '国家',
    contact_person VARCHAR(64) COMMENT '联系人',
    contact_phone VARCHAR(32) COMMENT '联系电话',
    contact_email VARCHAR(128) COMMENT '联系邮箱',
    trial_id BIGINT COMMENT '试验ID（关联时）',
    pi_id BIGINT COMMENT '主要研究者ID',
    pi_name VARCHAR(64) COMMENT 'PI姓名',
    pi_credentials TEXT COMMENT 'PI资质证明文件',
    target_enrollment INT COMMENT '目标入组',
    actual_enrollment INT DEFAULT 0 COMMENT '实际入组',
    enrollment_status VARCHAR(16) DEFAULT 'not_started' COMMENT '入组状态',
    site_status VARCHAR(16) NOT NULL DEFAULT 'screening' COMMENT '中心状态：screening筛选/approved批准/activated激活/suspended暂停/closed关闭',
    activation_date DATE COMMENT '启动日期',
    closure_date DATE COMMENT '关闭日期',
    closure_reason VARCHAR(256) COMMENT '关闭原因',
    contract_status VARCHAR(16) COMMENT '合同状态',
    contract_file_url VARCHAR(512) COMMENT '合同文件URL',
    financial_agreement_file_url VARCHAR(512) COMMENT '财务协议URL',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_site_code (site_code),
    INDEX idx_trial (trial_id),
    INDEX idx_pi (pi_id),
    INDEX idx_status (site_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='研究中心表';
```

**表4：investigators（研究者表）**

```sql
CREATE TABLE investigators (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    investigator_code VARCHAR(32) NOT NULL UNIQUE COMMENT '研究者编号',
    real_name VARCHAR(64) NOT NULL COMMENT '姓名',
    gender TINYINT COMMENT '性别：1男 2女',
    birth_date DATE COMMENT '出生日期',
    id_card VARCHAR(18) COMMENT '身份证号（加密）',
    phone VARCHAR(32) COMMENT '电话',
    email VARCHAR(128) COMMENT '邮箱',
    professional_title VARCHAR(64) COMMENT '职称：chief_physician/associate_chief/attending/resident',
    department VARCHAR(64) COMMENT '科室',
    specialty VARCHAR(128) COMMENT '专业领域',
    qualifications TEXT COMMENT '资质证书JSON',
    cv_file_url VARCHAR(512) COMMENT '简历文件URL',
    license_no VARCHAR(64) COMMENT '执业证书号',
    license_file_url VARCHAR(512) COMMENT '执业证书URL',
    gcp_training_file_url VARCHAR(512) COMMENT 'GCP培训证书URL',
    conflict_of_interest_file_url VARCHAR(512) COMMENT '利益冲突声明URL',
    site_id BIGINT COMMENT '所属中心ID',
    role_type VARCHAR(16) NOT NULL COMMENT '角色类型：PI/SUB_I/SUB_INVESTIGATOR',
    is_pi TINYINT DEFAULT 0 COMMENT '是否PI：0否 1是',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '状态：active/inactive/terminated',
    training_records JSON COMMENT '培训记录JSON',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_investigator_code (investigator_code),
    INDEX idx_site (site_id),
    INDEX idx_role (role_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='研究者表';
```

**表5：sponsors（申办方表）**

```sql
CREATE TABLE sponsors (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sponsor_code VARCHAR(32) NOT NULL UNIQUE COMMENT '申办方编号',
    sponsor_name VARCHAR(256) NOT NULL COMMENT '申办方名称',
    sponsor_type VARCHAR(16) COMMENT '类型：pharma/biotech/device/others',
    business_license_no VARCHAR(64) COMMENT '营业执照号',
    business_license_file_url VARCHAR(512) COMMENT '营业执照URL',
    legal_representative VARCHAR(64) COMMENT '法人代表',
    contact_person VARCHAR(64) COMMENT '联系人',
    contact_phone VARCHAR(32) COMMENT '联系电话',
    contact_email VARCHAR(128) COMMENT '联系邮箱',
    address TEXT COMMENT '地址',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '状态：active/inactive',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sponsor_code (sponsor_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='申办方表';
```

**表6：cro_companies（CRO公司表）**

```sql
CREATE TABLE cro_companies (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    cro_code VARCHAR(32) NOT NULL UNIQUE COMMENT 'CRO编号',
    cro_name VARCHAR(256) NOT NULL COMMENT 'CRO公司名称',
    business_license_no VARCHAR(64) COMMENT '营业执照号',
    business_license_file_url VARCHAR(512) COMMENT '营业执照URL',
    contact_person VARCHAR(64) COMMENT '联系人',
    contact_phone VARCHAR(32) COMMENT '联系电话',
    contact_email VARCHAR(128) COMMENT '联系邮箱',
    address TEXT COMMENT '地址',
    service_scope TEXT COMMENT '服务范围',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '状态：active/inactive',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_cro_code (cro_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CRO公司表';
```

**表7：cro_assignments（CRO任务分配表）**

```sql
CREATE TABLE cro_assignments (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    assignment_code VARCHAR(64) NOT NULL UNIQUE COMMENT '分配编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    cro_company_id BIGINT NOT NULL COMMENT 'CRO公司ID',
    role_type VARCHAR(16) NOT NULL COMMENT '角色类型：PM/CRA/CRC/MM/DM',
    user_id BIGINT NOT NULL COMMENT '人员ID',
    user_name VARCHAR(64) COMMENT '人员姓名',
    user_email VARCHAR(128) COMMENT '人员邮箱',
    site_ids JSON COMMENT '负责中心ID列表',
    start_date DATE COMMENT '开始日期',
    end_date DATE COMMENT '结束日期',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '状态：active/inactive/completed',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trial (trial_id),
    INDEX idx_user (user_id),
    INDEX idx_role (role_type),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CRO任务分配表';
```

#### 7.2.2 受试者管理表

**表8：subjects（受试者表）**

```sql
CREATE TABLE subjects (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    subject_code VARCHAR(64) NOT NULL UNIQUE COMMENT '受试者编号',
    subject_id VARCHAR(64) COMMENT '受试者ID（系统内部）',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    screening_no VARCHAR(32) COMMENT '筛选号',
    randomization_no VARCHAR(32) COMMENT '随机号',
    random_group VARCHAR(16) COMMENT '随机分组',
    enrollment_no VARCHAR(32) COMMENT '入组号',
    informed_consent_date DATE COMMENT '知情同意日期',
    consent_version VARCHAR(16) COMMENT '知情同意版本',
    consent_file_url VARCHAR(512) COMMENT '知情同意书URL',
    consent_signed TINYINT DEFAULT 0 COMMENT '是否签署：0否 1是',
    consent_withdrawn TINYINT DEFAULT 0 COMMENT '是否撤回：0否 1是',
    consent_withdrawn_date DATE COMMENT '撤回日期',
    consent_withdrawn_reason TEXT COMMENT '撤回原因',
    first_visit_date DATE COMMENT '首次访视日期',
    last_visit_date DATE COMMENT '末次访视日期',
    enrollment_status VARCHAR(16) NOT NULL DEFAULT 'screening' COMMENT '入组状态：screening筛选/enrolled入组/completed完成/withdrawn撤回/screen_failed筛选失败/lost_to_followup失访/terminated终止',
    exit_reason VARCHAR(256) COMMENT '退出原因',
    exit_date DATE COMMENT '退出日期',
    death_date DATE COMMENT '死亡日期（如适用）',
    death_cause VARCHAR(256) COMMENT '死亡原因（如适用）',
    demographic_data JSON COMMENT '人口学数据（加密）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subject_code (subject_code),
    INDEX idx_trial (trial_id),
    INDEX idx_site (site_id),
    INDEX idx_enrollment_status (enrollment_status),
    INDEX idx_consent (consent_signed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='受试者表';
```

**表9：subject_visits（受试者访视表）**

```sql
CREATE TABLE subject_visits (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    visit_code VARCHAR(64) NOT NULL UNIQUE COMMENT '访视编号',
    subject_id BIGINT NOT NULL COMMENT '受试者ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    visit_name VARCHAR(128) NOT NULL COMMENT '访视名称',
    visit_no INT NOT NULL COMMENT '访视序号',
    visit_window_start_days INT COMMENT '访视窗口开始（天）',
    visit_window_end_days INT COMMENT '访视窗口结束（天）',
    planned_date DATE COMMENT '计划日期',
    actual_date DATE COMMENT '实际日期',
    window_deviation_days INT COMMENT '窗口偏离天数',
    is_window_deviation TINYINT DEFAULT 0 COMMENT '是否超出窗口',
    visit_status VARCHAR(16) NOT NULL DEFAULT 'scheduled' COMMENT '状态：scheduled计划/performed已完成/skipped跳过/not_done未做',
    performed_by BIGINT COMMENT '执行人ID',
    performed_by_name VARCHAR(64) COMMENT '执行人姓名',
    crf_completed TINYINT DEFAULT 0 COMMENT 'CRF完成：0否 1是',
    crf_completed_at DATETIME COMMENT 'CRF完成时间',
    visit_completed_at DATETIME COMMENT '访视完成时间',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subject (subject_id),
    INDEX idx_trial (trial_id),
    INDEX idx_visit_no (visit_no),
    INDEX idx_status (visit_status),
    INDEX idx_planned_date (planned_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='受试者访视表';
```

**表10：informed_consents（知情同意记录表）**

```sql
CREATE TABLE informed_consents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    consent_code VARCHAR(64) NOT NULL UNIQUE COMMENT '知情编号',
    subject_id BIGINT NOT NULL COMMENT '受试者ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    consent_type VARCHAR(32) NOT NULL COMMENT '知情类型：initial初始/resubmit再次/reconsent重签/amendment修正案',
    document_version VARCHAR(16) NOT NULL COMMENT 'ICF版本',
    document_file_url VARCHAR(512) NOT NULL COMMENT 'ICF文件URL',
    document_hash VARCHAR(64) COMMENT '文件Hash（防篡改）',
    consent_date DATE NOT NULL COMMENT '知情日期',
    consent_signed TINYINT DEFAULT 0 COMMENT '是否签署',
    signature_type VARCHAR(16) COMMENT '签名类型：handwritten电子记录/e_consent电子签名',
    electronic_signature_id VARCHAR(64) COMMENT '电子签名ID',
    electronic_signature_hash VARCHAR(64) COMMENT '签名Hash',
    signed_by_subject TINYINT DEFAULT 0 COMMENT '受试者签名：0否 1是',
    subject_signed_at DATETIME COMMENT '受试者签名时间',
    signed_by_investigator TINYINT DEFAULT 0 COMMENT '研究者签名',
    investigator_id BIGINT COMMENT '研究者ID',
    investigator_name VARCHAR(64) COMMENT '研究者姓名',
    investigator_signed_at DATETIME COMMENT '研究者签名时间',
    witnessed TINYINT DEFAULT 0 COMMENT '是否见证',
    witness_name VARCHAR(64) COMMENT '见证人姓名',
    witness_relationship VARCHAR(64) COMMENT '见证关系',
    interpreter_used TINYINT DEFAULT 0 COMMENT '是否使用翻译',
    interpreter_name VARCHAR(64) COMMENT '翻译人员姓名',
    language VARCHAR(16) COMMENT '语言',
    consent_withdrawn TINYINT DEFAULT 0 COMMENT '是否撤回',
    withdrawal_date DATE COMMENT '撤回日期',
    withdrawal_reason TEXT COMMENT '撤回原因',
    withdrawal_signature_hash VARCHAR(64) COMMENT '撤回签名Hash',
    ai_audit_result JSON COMMENT 'AI审核结果',
    audit_status VARCHAR(16) DEFAULT 'pending' COMMENT '审核状态：pending待审核/passed通过/failed不合格',
    audit_completed_at DATETIME COMMENT '审核完成时间',
    audit_completed_by BIGINT COMMENT '审核人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subject (subject_id),
    INDEX idx_trial (trial_id),
    INDEX idx_consent_type (consent_type),
    INDEX idx_consent_signed (consent_signed),
    INDEX idx_withdrawn (consent_withdrawn)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='知情同意记录表';
```

#### 7.2.3 安全与药物警戒表

**表11：adverse_events（不良事件表）**

```sql
CREATE TABLE adverse_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ae_code VARCHAR(64) NOT NULL UNIQUE COMMENT 'AE编号',
    subject_id BIGINT NOT NULL COMMENT '受试者ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    ae_name VARCHAR(256) NOT NULL COMMENT 'AE名称',
    ae_description TEXT COMMENT 'AE描述',
    onset_date DATE NOT NULL COMMENT 'AE开始日期',
    ongoing TINYINT DEFAULT 1 COMMENT '是否持续',
    end_date DATE COMMENT 'AE结束日期',
    outcome VARCHAR(16) COMMENT '结局：resolved缓解/recovering/recovered_with_sequelae/fatal/unknown',
    severity VARCHAR(16) NOT NULL COMMENT '严重程度：mild轻度/moderate中度/severe重度',
    serious TINYINT DEFAULT 0 COMMENT '是否严重',
    serious_reason VARCHAR(256) COMMENT '严重原因（如是SAE）',
    related_to_ip TINYINT DEFAULT 0 COMMENT '与试验药物相关性：0否 1是',
    causality VARCHAR(16) COMMENT '因果关系：not_related无关/unlikely可能无关/possible可能相关/probable很可能相关/definitely相关',
    action_taken VARCHAR(16) COMMENT '采取措施：none无/dose_reduced暂停药物/dose_interrupted中断药物/drug_withdrawn终止药物/other其他',
    outcome_due_to_ae TINYINT DEFAULT 0 COMMENT '是否因AE退出',
    ae_meddra_code VARCHAR(16) COMMENT 'MedDRA编码',
    ae_meddra_term VARCHAR(256) COMMENT 'MedDRA术语',
    ai_coding_confidence DECIMAL(5,2) COMMENT 'AI编码置信度',
    ai_coding_suggestion VARCHAR(256) COMMENT 'AI编码建议',
    coding_confirmed TINYINT DEFAULT 0 COMMENT '编码是否确认',
    coding_confirmed_by BIGINT COMMENT '编码确认人',
    coding_confirmed_at DATETIME COMMENT '编码确认时间',
    reported_as_sae TINYINT DEFAULT 0 COMMENT '是否报告为SAE',
    sdar_code VARCHAR(64) COMMENT '关联SAE编号',
    followup_required TINYINT DEFAULT 0 COMMENT '是否需要随访',
    followup_date DATE COMMENT '随访日期',
    followup_completed TINYINT DEFAULT 0 COMMENT '随访是否完成',
    remarks TEXT COMMENT '备注',
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    created_by_name VARCHAR(64) COMMENT '创建人姓名',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subject (subject_id),
    INDEX idx_trial (trial_id),
    INDEX idx_serious (serious),
    INDEX idx_outcome (outcome),
    INDEX idx_causality (causality),
    INDEX idx_meddra (ae_meddra_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='不良事件表';
```

**表12：serious_adverse_events（严重不良事件表）**

```sql
CREATE TABLE serious_adverse_events (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    sdar_code VARCHAR(64) NOT NULL UNIQUE COMMENT 'SAE编号',
    ae_id BIGINT NOT NULL COMMENT '关联AE ID',
    subject_id BIGINT NOT NULL COMMENT '受试者ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    sae_name VARCHAR(256) NOT NULL COMMENT 'SAE名称',
    sdar_type VARCHAR(16) NOT NULL COMMENT 'SAE类型：death致死/life_threatening危及生命/requires_hospitalization需住院/prolongs_hospitalization延长住院/disability残障/congenital_anomaly先天性畸形/other_other其他重要医学事件',
    onset_date DATE NOT NULL COMMENT '发生日期',
    outcome VARCHAR(16) NOT NULL COMMENT '结局',
    outcome_date DATE COMMENT '结局日期',
    death_cause VARCHAR(256) COMMENT '死亡原因',
    autopsy_performed TINYINT DEFAULT 0 COMMENT '是否尸检',
    autopsy_report_url VARCHAR(512) COMMENT '尸检报告URL',
    ip_relationship VARCHAR(16) NOT NULL COMMENT '与试验药物关系',
    treatment_given TEXT COMMENT '给予的治疗',
    reporter_name VARCHAR(64) NOT NULL COMMENT '报告人姓名',
    reporter_role VARCHAR(32) NOT NULL COMMENT '报告人角色',
    reporter_phone VARCHAR(32) COMMENT '报告人电话',
    pi_acknowledged TINYINT DEFAULT 0 COMMENT 'PI确认',
    pi_acknowledged_at DATETIME COMMENT 'PI确认时间',
    sponsor_notified TINYINT DEFAULT 0 COMMENT '申办方通知',
    sponsor_notified_at DATETIME COMMENT '申办方通知时间',
    irb_notified TINYINT DEFAULT 0 COMMENT '伦理通知',
    irb_notified_at DATETIME COMMENT '伦理通知时间',
    irb_report_deadline DATE COMMENT '伦理报告截止日',
    susar TINYINT DEFAULT 0 COMMENT '是否SUSAR',
    susar_report_id VARCHAR(64) COMMENT 'SUSAR报告ID',
    susar_reported_to_regulator TINYINT DEFAULT 0 COMMENT '是否报告监管',
    susar_report_date DATE COMMENT 'SUSAR报告日期',
    susar_report_deadline DATE COMMENT 'SUSAR报告截止日',
    final_report_url VARCHAR(512) COMMENT '最终报告URL',
    narrative TEXT COMMENT 'SAE叙述',
    ai_narrative TEXT COMMENT 'AI生成叙述草稿',
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ae (ae_id),
    INDEX idx_subject (subject_id),
    INDEX idx_trial (trial_id),
    INDEX idx_susar (susar),
    INDEX idx_sponsor_notified (sponsor_notified),
    INDEX idx_irb_notified (irb_notified)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='严重不良事件表';
```

**表13：protocol_deviations（方案偏离表）**

```sql
CREATE TABLE protocol_deviations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    deviation_code VARCHAR(64) NOT NULL UNIQUE COMMENT '偏离编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    subject_id BIGINT COMMENT '受试者ID（如涉及）',
    visit_id BIGINT COMMENT '访视ID（如涉及）',
    deviation_type VARCHAR(16) NOT NULL COMMENT '偏离类型：inclusion_exclusion入选排除/visit_schedule访视安排/procedure程序/dosing用药/assessment评估/consent知情/documentation文档/ip_management药物',
    deviation_category VARCHAR(16) COMMENT '偏离类别：minor轻微/major重要',
    description TEXT NOT NULL COMMENT '偏离描述',
    identified_date DATE NOT NULL COMMENT '发现日期',
    identified_by VARCHAR(32) COMMENT '发现人',
    identified_by_user_id BIGINT COMMENT '发现人ID',
    occurred_date DATE COMMENT '发生日期',
    occurred_end_date DATE COMMENT '结束日期',
    reason TEXT COMMENT '偏离原因',
    impact_assessment TEXT COMMENT '影响评估',
    corrective_action TEXT COMMENT '纠正措施',
    preventive_action TEXT COMMENT '预防措施',
    requires_irb_report TINYINT DEFAULT 0 COMMENT '是否需报告伦理',
    irb_reported TINYINT DEFAULT 0 COMMENT '是否已报告伦理',
    irb_report_date DATE COMMENT '伦理报告日期',
    requires Sponsor_report TINYINT DEFAULT 0 COMMENT '是否需报告申办方',
    sponsor_reported TINYINT DEFAULT 0 COMMENT '是否已报告申办方',
    sponsor_report_date DATE COMMENT '申办方报告日期',
    resolution_status VARCHAR(16) DEFAULT 'open' COMMENT '解决状态：open待解决/in_progress进行中/resolved已解决/closed关闭',
    resolved_date DATE COMMENT '解决日期',
    resolved_by BIGINT COMMENT '解决人ID',
    waiver_requested TINYINT DEFAULT 0 COMMENT '是否申请豁免',
    waiver_approved TINYINT DEFAULT 0 COMMENT '豁免是否批准',
    waiver_approved_by BIGINT COMMENT '豁免批准人',
    waiver_approved_at DATETIME COMMENT '豁免批准时间',
    ai_analysis TEXT COMMENT 'AI分析',
    remarks TEXT COMMENT '备注',
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trial (trial_id),
    INDEX idx_site (site_id),
    INDEX idx_subject (subject_id),
    INDEX idx_type (deviation_type),
    INDEX idx_category (deviation_category),
    INDEX idx_status (resolution_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='方案偏离表';
```

#### 7.2.4 数据采集与管理表

**表14：crf_forms（CRF表单表）**

```sql
CREATE TABLE crf_forms (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    form_code VARCHAR(64) NOT NULL UNIQUE COMMENT '表单编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    visit_id BIGINT COMMENT '访视ID',
    form_name VARCHAR(128) NOT NULL COMMENT '表单名称',
    form_type VARCHAR(32) NOT NULL COMMENT '表单类型：demographics人口学/visit访视/lab实验室/ecg心电图/ae不良事件/ip_drug药物',
    form_version VARCHAR(16) NOT NULL COMMENT '表单版本',
    form_status VARCHAR(16) NOT NULL DEFAULT 'draft' COMMENT '状态：draft草稿/active激活/archived归档',
    fields_definition JSON NOT NULL COMMENT '字段定义JSON',
    edit_checks JSON COMMENT '编辑核查规则JSON',
    skip_logic JSON COMMENT '跳逻辑规则JSON',
    completion_instructions TEXT COMMENT '填写说明',
    is_required TINYINT DEFAULT 1 COMMENT '是否必填',
    sequence_order INT DEFAULT 0 COMMENT '显示顺序',
    created_by BIGINT COMMENT '创建人ID',
    approved_by BIGINT COMMENT '审批人ID',
    approved_at DATETIME COMMENT '审批时间',
    effective_date DATE COMMENT '生效日期',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trial (trial_id),
    INDEX idx_visit (visit_id),
    INDEX idx_status (form_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CRF表单表';
```

**表15：crf_entries（CRF数据录入表）**

```sql
CREATE TABLE crf_entries (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    entry_code VARCHAR(64) NOT NULL UNIQUE COMMENT '录入编号',
    form_id BIGINT NOT NULL COMMENT '表单ID',
    form_version VARCHAR(16) NOT NULL COMMENT '表单版本',
    subject_id BIGINT NOT NULL COMMENT '受试者ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    visit_id BIGINT COMMENT '访视ID',
    data_values JSON NOT NULL COMMENT '数据值JSON',
    data_status VARCHAR(16) NOT NULL DEFAULT 'data_entry' COMMENT '状态：data_entry数据录入/pending_verification待核实/verified已核实/locked已锁定',
    entry_method VARCHAR(16) COMMENT '录入方式：manual手动/import导入/ai_assisted AI辅助',
    entry_started_at DATETIME COMMENT '开始录入时间',
    entry_completed_at DATETIME COMMENT '录入完成时间',
    entered_by BIGINT COMMENT '录入人ID',
    entered_by_name VARCHAR(64) COMMENT '录入人姓名',
    verified_by BIGINT COMMENT '核实人ID',
    verified_by_name VARCHAR(64) COMMENT '核实人姓名',
    verified_at DATETIME COMMENT '核实时间',
    sdv_required TINYINT DEFAULT 0 COMMENT '是否需要SDV',
    sdv_status VARCHAR(16) COMMENT 'SDV状态：required需要/done完成/not_required不需要',
    sdv_done_by BIGINT COMMENT 'SDV执行人',
    sdv_done_at DATETIME COMMENT 'SDV时间',
    discrepancy_count INT DEFAULT 0 COMMENT '质疑数量',
    discrepancy_status VARCHAR(16) COMMENT '质疑状态：open待解决/closed已关闭',
    signature_required TINYINT DEFAULT 1 COMMENT '是否需要签名',
    signed_by BIGINT COMMENT '签名人ID',
    signed_by_name VARCHAR(64) COMMENT '签名人姓名',
    signed_at DATETIME COMMENT '签名时间',
    electronic_signature_hash VARCHAR(64) COMMENT '电子签名Hash',
    signature_reason VARCHAR(32) COMMENT '签名原因',
    freeze_status VARCHAR(16) DEFAULT 'unfrozen' COMMENT '冻结状态：unfrozen未冻结/frozen已冻结',
    frozen_by BIGINT COMMENT '冻结人ID',
    frozen_at DATETIME COMMENT '冻结时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_form (form_id),
    INDEX idx_subject (subject_id),
    INDEX idx_trial (trial_id),
    INDEX idx_visit (visit_id),
    INDEX idx_status (data_status),
    INDEX idx_sdv (sdv_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CRF数据录入表';
```

**表16：data_queries（数据质疑表）**

```sql
CREATE TABLE data_queries (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    query_code VARCHAR(64) NOT NULL UNIQUE COMMENT '质疑编号',
    entry_id BIGINT NOT NULL COMMENT '关联录入ID',
    subject_id BIGINT NOT NULL COMMENT '受试者ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    field_name VARCHAR(128) NOT NULL COMMENT '质疑字段',
    field_label VARCHAR(256) COMMENT '字段标签',
    query_type VARCHAR(16) NOT NULL COMMENT '质疑类型：system系统/manually人工',
    query_trigger VARCHAR(32) COMMENT '触发规则',
    query_text TEXT NOT NULL COMMENT '质疑内容',
    query_status VARCHAR(16) NOT NULL DEFAULT 'open' COMMENT '状态：open待回复/response_received已回复/closed已关闭/cancelled已取消',
    response_text TEXT COMMENT '回复内容',
    responded_by BIGINT COMMENT '回复人ID',
    responded_by_name VARCHAR(64) COMMENT '回复人姓名',
    responded_at DATETIME COMMENT '回复时间',
    responded_via VARCHAR(16) COMMENT '回复方式：system系统/email邮件/phone电话',
    resolved_by BIGINT COMMENT '解决人ID',
    resolved_by_name VARCHAR(64) COMMENT '解决人姓名',
    resolved_at DATETIME COMMENT '解决时间',
    resolution_type VARCHAR(16) COMMENT '解决类型：data_updated数据更新/query_clarified说明澄清/no_change无需修改',
    updated_value TEXT COMMENT '更新后的值',
    previous_value TEXT COMMENT '修改前的值',
    value_change_reason TEXT COMMENT '值变更原因',
    requires_source_verification TINYINT DEFAULT 0 COMMENT '是否需要源数据验证',
    source_verified TINYINT DEFAULT 0 COMMENT '源数据是否验证',
    source_verified_by BIGINT COMMENT '源数据验证人',
    source_verified_at DATETIME COMMENT '源数据验证时间',
    query_age_days INT COMMENT '质疑开放天数',
    overdue_reminder_sent TINYINT DEFAULT 0 COMMENT '超时提醒是否发送',
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_entry (entry_id),
    INDEX idx_subject (subject_id),
    INDEX idx_trial (trial_id),
    INDEX idx_status (query_status),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据质疑表';
```

#### 7.2.5 药物管理表

**表17：investigational_products（试验药物表）**

```sql
CREATE TABLE investigational_products (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    ip_code VARCHAR(64) NOT NULL UNIQUE COMMENT '药物编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    product_name VARCHAR(256) NOT NULL COMMENT '药物名称',
    product_type VARCHAR(32) COMMENT '药物类型：investigational对照/placebo安慰剂/active_active阳性对照',
    dosage_form VARCHAR(32) COMMENT '剂型：tablet片剂/capsule胶囊/injection注射/cream乳膏',
    strength VARCHAR(64) COMMENT '规格',
    manufacturer VARCHAR(256) COMMENT '生产企业',
    batch_number VARCHAR(64) COMMENT '批号',
    manufacturing_date DATE COMMENT '生产日期',
    expiry_date DATE COMMENT '有效期',
    storage_conditions VARCHAR(64) COMMENT '储存条件',
    temperature_control_required TINYINT DEFAULT 1 COMMENT '是否需要温控',
    temperature_min DECIMAL(5,2) COMMENT '温度下限',
    temperature_max DECIMAL(5,2) COMMENT '温度上限',
    ip_status VARCHAR(16) DEFAULT 'available' COMMENT '状态：available可发放/quarantined隔离/dispatched已分发/used已使用/reclaimed已回收/destroyed已销毁',
    blinding_info VARCHAR(256) COMMENT '盲法信息',
    randomization_group VARCHAR(16) COMMENT '随机分组',
    ip_description TEXT COMMENT '药物描述',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ip_code (ip_code),
    INDEX idx_trial (trial_id),
    INDEX idx_batch (batch_number),
    INDEX idx_status (ip_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试验药物表';
```

**表18：ip_dispensations（药物分发记录表）**

```sql
CREATE TABLE ip_dispensations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    dispensation_code VARCHAR(64) NOT NULL UNIQUE COMMENT '分发编号',
    subject_id BIGINT NOT NULL COMMENT '受试者ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    visit_id BIGINT COMMENT '访视ID',
    ip_id BIGINT NOT NULL COMMENT '药物ID',
    batch_number VARCHAR(64) COMMENT '批号',
    dispensed_date DATE NOT NULL COMMENT '分发日期',
    dispensed_quantity INT COMMENT '分发数量',
    dispensing_pharmacist_id BIGINT COMMENT '药师ID',
    dispensing_pharmacist_name VARCHAR(64) COMMENT '药师姓名',
    randomization_no VARCHAR(32) COMMENT '随机号',
    drug_package_no VARCHAR(32) COMMENT '药物包装号',
    dose_level VARCHAR(64) COMMENT '剂量水平',
    dosage_instructions TEXT COMMENT '用药说明',
    subject_instructed TINYINT DEFAULT 0 COMMENT '受试者是否已指导',
    instruction_date DATE COMMENT '指导日期',
    next_dispensation_date DATE COMMENT '下次分发日期',
    return_expected_date DATE COMMENT '预计回收日期',
    dispensation_status VARCHAR(16) DEFAULT 'dispensed' COMMENT '状态：dispensed已分发/returned已回收/partially_returned部分回收/not_returned未回收',
    return_date DATE COMMENT '回收日期',
    returned_quantity INT COMMENT '回收数量',
    returned_condition VARCHAR(32) COMMENT '回收时状态',
    unused_dispensed_quantity INT COMMENT '未使用分发数量',
    accountability_complete TINYINT DEFAULT 0 COMMENT '药物盘点是否完成',
    accountability_complete_by BIGINT COMMENT '盘点完成人',
    accountability_complete_at DATETIME COMMENT '盘点完成时间',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subject (subject_id),
    INDEX idx_trial (trial_id),
    INDEX idx_visit (visit_id),
    INDEX idx_status (dispensation_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='药物分发记录表';
```

#### 7.2.6 文档管理表

**表19：trial_documents（试验文档表）**

```sql
CREATE TABLE trial_documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
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
    language VARCHAR(16) COMMENT '语言',
    effective_date DATE COMMENT '生效日期',
    expiry_date DATE COMMENT '过期日期',
    applicable_to_all_sites TINYINT DEFAULT 0 COMMENT '是否适用于所有中心',
    applicable_site_ids JSON COMMENT '适用中心ID列表',
    approval_required TINYINT DEFAULT 0 COMMENT '是否需要审批',
    approval_status VARCHAR(16) COMMENT '审批状态：not_required不需要/pending待审批/approved已批准/rejected已拒绝',
    approved_by BIGINT COMMENT '审批人ID',
    approved_by_name VARCHAR(64) COMMENT '审批人姓名',
    approved_at DATETIME COMMENT '审批时间',
    electronic_signature_required TINYINT DEFAULT 0 COMMENT '是否需要电子签名',
    signed_by BIGINT COMMENT '签名人ID',
    signed_by_name VARCHAR(64) COMMENT '签名人姓名',
    signed_by_role VARCHAR(32) COMMENT '签名人角色',
    signed_at DATETIME COMMENT '签名时间',
    electronic_signature_hash VARCHAR(64) COMMENT '电子签名Hash',
    supersedes_doc_id BIGINT COMMENT '替代的文档ID',
    superseded_by_doc_id BIGINT COMMENT '替代文档ID',
    irb_approval_required TINYINT DEFAULT 0 COMMENT '是否需要伦理批准',
    irb_approval_status VARCHAR(16) COMMENT '伦理审批状态',
    irb_approval_date DATE COMMENT '伦理批准日期',
    irb_approval_file_url VARCHAR(512) COMMENT '伦理批准文件URL',
    retention_required TINYINT DEFAULT 1 COMMENT '是否需要归档保存',
    retention_period_years INT DEFAULT 15 COMMENT '保存年限',
    archive_location VARCHAR(256) COMMENT '归档位置',
    is_latest_version TINYINT DEFAULT 1 COMMENT '是否为最新版本',
    created_by BIGINT NOT NULL COMMENT '创建人ID',
    created_by_name VARCHAR(64) COMMENT '创建人姓名',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_doc_code (doc_code),
    INDEX idx_trial (trial_id),
    INDEX idx_site (site_id),
    INDEX idx_type (doc_type),
    INDEX idx_category (doc_category),
    INDEX idx_version (version),
    INDEX idx_approval (approval_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='试验文档表';
```

**表20：document_versions（文档版本历史表）**

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
    file_size BIGINT COMMENT '文件大小',
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

#### 7.2.7 流程审批表

**表21：approval_workflows（审批流程配置表）**

```sql
CREATE TABLE approval_workflows (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    workflow_code VARCHAR(64) NOT NULL UNIQUE COMMENT '流程编号',
    workflow_name VARCHAR(128) NOT NULL COMMENT '流程名称',
    workflow_type VARCHAR(32) NOT NULL COMMENT '流程类型：protocol_approval方案审批/amendment审批/investigator_assignment研究者分配/protocol_deviation方案偏离/site_close中心关闭/db_lock数据库锁定',
    trial_id BIGINT COMMENT '试验ID（特定试验时）',
    is_system_wide TINYINT DEFAULT 0 COMMENT '是否系统级流程',
    stages JSON NOT NULL COMMENT '审批阶段JSON：[{"stage_no":1,"stage_name":"初审","approver_role":"医学监查员","approver_count":1,"timeout_days":5}]',
    is_active TINYINT DEFAULT 1 COMMENT '是否激活',
    effective_date DATE COMMENT '生效日期',
    expiry_date DATE COMMENT '失效日期',
    description TEXT COMMENT '流程描述',
    created_by BIGINT COMMENT '创建人ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_workflow_type (workflow_type),
    INDEX idx_trial (trial_id),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批流程配置表';
```

**表22：approval_requests（审批请求表）**

```sql
CREATE TABLE approval_requests (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    request_code VARCHAR(64) NOT NULL UNIQUE COMMENT '请求编号',
    workflow_id BIGINT NOT NULL COMMENT '流程ID',
    workflow_type VARCHAR(32) NOT NULL COMMENT '流程类型',
    trial_id BIGINT COMMENT '试验ID',
    site_id BIGINT COMMENT '中心ID',
    subject_id BIGINT COMMENT '受试者ID（如适用）',
    request_title VARCHAR(256) NOT NULL COMMENT '请求标题',
    request_description TEXT COMMENT '请求描述',
    request_data JSON COMMENT '请求数据JSON',
    supporting_doc_ids JSON COMMENT '附件文档ID列表',
    current_stage INT DEFAULT 1 COMMENT '当前阶段',
    current_stage_status VARCHAR(16) DEFAULT 'pending' COMMENT '当前状态：pending待审批/approved批准/rejected驳回/cancelled取消',
    request_status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '整体状态：pending/in_progress/approved/rejected/cancelled',
    submitted_by BIGINT NOT NULL COMMENT '提交人ID',
    submitted_by_name VARCHAR(64) COMMENT '提交人姓名',
    submitted_by_role VARCHAR(32) COMMENT '提交人角色',
    submitted_at DATETIME NOT NULL COMMENT '提交时间',
    decided_by BIGINT COMMENT '最终决定人ID',
    decided_by_name VARCHAR(64) COMMENT '最终决定人姓名',
    decided_at DATETIME COMMENT '决定时间',
    decision_comments TEXT COMMENT '决定意见',
    electronic_signature_hash VARCHAR(64) COMMENT '电子签名Hash',
    priority VARCHAR(16) DEFAULT 'normal' COMMENT '优先级：low低/normal普通/high高/urgent紧急',
    due_date DATE COMMENT '截止日期',
    completed_at DATETIME COMMENT '完成时间',
    total_processing_time_hours INT COMMENT '总处理时长(小时)',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_workflow (workflow_id),
    INDEX idx_trial (trial_id),
    INDEX idx_status (request_status),
    INDEX idx_submitted_by (submitted_by),
    INDEX idx_submitted (submitted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批请求表';
```

**表23：approval_stages（审批阶段记录表）**

```sql
CREATE TABLE approval_stages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stage_code VARCHAR(64) NOT NULL UNIQUE COMMENT '阶段编号',
    request_id BIGINT NOT NULL COMMENT '请求ID',
    stage_no INT NOT NULL COMMENT '阶段序号',
    stage_name VARCHAR(128) NOT NULL COMMENT '阶段名称',
    approver_role VARCHAR(32) NOT NULL COMMENT '审批角色',
    required_approvers INT DEFAULT 1 COMMENT '需要审批人数',
    current_approvals INT DEFAULT 0 COMMENT '当前审批人数',
    stage_status VARCHAR(16) DEFAULT 'pending' COMMENT '状态：pending待审批/approved通过/rejected驳回/skipped跳过',
    started_at DATETIME COMMENT '开始时间',
    deadline DATETIME COMMENT '截止时间',
    completed_at DATETIME COMMENT '完成时间',
    stage_processing_time_hours INT COMMENT '阶段处理时长',
    approval_records JSON COMMENT '审批记录JSON：[{approver_id,approver_name,decision,decision_time,comments}]',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_request (request_id),
    INDEX idx_stage_status (stage_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审批阶段记录表';
```

#### 7.2.8 监查与质量管理表

**表24：monitoring_visits（监查访视表）**

```sql
CREATE TABLE monitoring_visits (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    visit_code VARCHAR(64) NOT NULL UNIQUE COMMENT '访视编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    cra_id BIGINT NOT NULL COMMENT 'CRA ID',
    cra_name VARCHAR(64) COMMENT 'CRA姓名',
    visit_type VARCHAR(16) NOT NULL COMMENT '访视类型：initiation启动/interim期中/close_out关闭',
    planned_start_date DATE COMMENT '计划开始日期',
    actual_start_date DATE COMMENT '实际开始日期',
    planned_end_date DATE COMMENT '计划结束日期',
    actual_end_date DATE COMMENT '实际结束日期',
    visit_status VARCHAR(16) NOT NULL DEFAULT 'scheduled' COMMENT '状态：scheduled计划/in_progress进行中/completed完成/cancelled取消',
    visit_purpose TEXT COMMENT '访视目的',
    activities_performed TEXT COMMENT '执行的活动',
    findings TEXT COMMENT '发现',
    issues_identified TEXT COMMENT '识别的问题',
    action_items TEXT COMMENT '待办事项',
    follow_up_required TINYINT DEFAULT 0 COMMENT '是否需要跟进',
    follow_up_due_date DATE COMMENT '跟进截止日期',
    follow_up_completed TINYINT DEFAULT 0 COMMENT '跟进是否完成',
    report_required TINYINT DEFAULT 1 COMMENT '是否需要报告',
    report_file_url VARCHAR(512) COMMENT '报告文件URL',
    report_submitted_at DATETIME COMMENT '报告提交时间',
    report_acknowledged TINYINT DEFAULT 0 COMMENT '报告是否确认',
    acknowledged_by BIGINT COMMENT '确认人ID',
    acknowledged_at DATETIME COMMENT '确认时间',
    site_response TEXT COMMENT '中心回复',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trial (trial_id),
    INDEX idx_site (site_id),
    INDEX idx_cra (cra_id),
    INDEX idx_status (visit_status),
    INDEX idx_planned_date (planned_start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='监查访视表';
```

**表25：audit_logs（审计日志表-完整合规版）**

```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    log_code VARCHAR(64) NOT NULL UNIQUE COMMENT '日志编号',
    log_uuid VARCHAR(64) NOT NULL COMMENT '日志UUID（防篡改）',
    trial_id BIGINT COMMENT '试验ID',
    site_id BIGINT COMMENT '中心ID（适用时）',
    subject_id BIGINT COMMENT '受试者ID（适用时）',
    module VARCHAR(32) NOT NULL COMMENT '模块：user用户/role角色/subject受试者/crf数据/consent知情/ae安全性/document文档/approval审批/workflow流程/system系统',
    action VARCHAR(64) NOT NULL COMMENT '操作类型：create/read/update/delete/login/logout/approve/reject/sign/submit/import/export',
    action_category VARCHAR(16) COMMENT '操作分类：data数据/permission权限/config配置/authentication认证/system系统',
    user_id BIGINT COMMENT '操作用户ID',
    user_name VARCHAR(64) COMMENT '操作用户姓名',
    user_role VARCHAR(32) COMMENT '操作用户角色',
    user_ip_address VARCHAR(45) COMMENT '用户IP地址',
    user_device VARCHAR(128) COMMENT '用户设备信息',
    user_browser VARCHAR(64) COMMENT '用户浏览器',
    target_type VARCHAR(64) COMMENT '操作对象类型',
    target_id BIGINT COMMENT '操作对象ID',
    target_code VARCHAR(64) COMMENT '操作对象编号',
    target_name VARCHAR(256) COMMENT '操作对象名称',
    old_value JSON COMMENT '变更前值（脱敏）',
    new_value JSON COMMENT '变更后值（脱敏）',
    change_summary TEXT COMMENT '变更摘要',
    request_url VARCHAR(512) COMMENT '请求URL',
    request_method VARCHAR(10) COMMENT '请求方法',
    request_id VARCHAR(64) COMMENT '请求追踪ID',
    session_id VARCHAR(128) COMMENT '会话ID',
    response_code VARCHAR(16) COMMENT '响应码',
    execution_time_ms INT COMMENT '执行时长(毫秒)',
    electronic_signature_id VARCHAR(64) COMMENT '电子签名ID（如适用）',
    electronic_signature_hash VARCHAR(64) COMMENT '电子签名Hash',
    signature_reason VARCHAR(32) COMMENT '签名原因',
    regulatory_relevance TINYINT DEFAULT 0 COMMENT '是否与监管相关',
    data_classification VARCHAR(32) COMMENT '数据分类：public公开/normal一般/sensitive敏感/confidential机密/restricted限阅',
    phi_accessed TINYINT DEFAULT 0 COMMENT '是否访问PHI',
    phi_access_type VARCHAR(32) COMMENT 'PHI访问类型',
    consent_status VARCHAR(16) COMMENT '知情状态',
    gcp_compliance_flag TINYINT DEFAULT 0 COMMENT 'GCP合规标记',
    risk_level VARCHAR(16) DEFAULT 'low' COMMENT '风险等级：low低/medium中/high高',
    compliance_tags JSON COMMENT '合规标签JSON',
    retention_required TINYINT DEFAULT 1 COMMENT '是否需要保留',
    retention_period_years INT DEFAULT 15 COMMENT '保留年限',
    immutable TINYINT DEFAULT 1 COMMENT '是否不可修改',
    checksum VARCHAR(64) COMMENT '校验和',
    previous_log_hash VARCHAR(64) COMMENT '前一条日志Hash（区块链式链）',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_trial (trial_id),
    INDEX idx_site (site_id),
    INDEX idx_subject (subject_id),
    INDEX idx_user (user_id),
    INDEX idx_module (module),
    INDEX idx_action (action),
    INDEX idx_target (target_type, target_id),
    INDEX idx_created (created_at),
    INDEX idx_risk (risk_level),
    INDEX idx_phi (phi_accessed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='审计日志表（21 CFR Part 11合规）';
```

#### 7.2.9 用户与权限表

**表26：users（用户表）**

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_code VARCHAR(32) NOT NULL UNIQUE COMMENT '用户编号',
    username VARCHAR(64) NOT NULL UNIQUE COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    email VARCHAR(128) NOT NULL COMMENT '邮箱',
    phone VARCHAR(32) COMMENT '电话',
    real_name VARCHAR(64) NOT NULL COMMENT '真实姓名',
    id_card VARCHAR(18) COMMENT '身份证号（加密）',
    gender TINYINT COMMENT '性别：1男 2女',
    birth_date DATE COMMENT '出生日期',
    avatar_url VARCHAR(512) COMMENT '头像URL',
    user_type VARCHAR(16) NOT NULL COMMENT '用户类型：internal内部/external外部',
    organization_id BIGINT COMMENT '组织ID',
    organization_name VARCHAR(256) COMMENT '组织名称',
    organization_type VARCHAR(16) COMMENT '组织类型：sponsor申办方/cro CRO/site研究中心/platform平台',
    primary_role VARCHAR(32) NOT NULL COMMENT '主角色：SPONSOR/PI/SUB_I/PM/CRA/CRC/MM/DM/SUPER_ADMIN',
    professional_title VARCHAR(64) COMMENT '职称',
    department VARCHAR(64) COMMENT '部门',
    qualifications TEXT COMMENT '资质证书JSON',
    gcp_training_date DATE COMMENT 'GCP培训日期',
    gcp_training_expiry DATE COMMENT 'GCP培训到期',
    sdtm_training TINYINT DEFAULT 0 COMMENT 'SDTM培训',
    electronic_signature_required TINYINT DEFAULT 1 COMMENT '是否需要电子签名',
    electronic_signature_method VARCHAR(32) COMMENT '签名方式：digital_cert数字证书/biometric生物识别/password密码',
    digital_certificate_id VARCHAR(64) COMMENT '数字证书ID',
    two_factor_enabled TINYINT DEFAULT 1 COMMENT '是否启用双因素',
    two_factor_method VARCHAR(16) COMMENT '双因素方式：sms/email/app',
    last_login_at DATETIME COMMENT '最后登录时间',
    last_login_ip VARCHAR(45) COMMENT '最后登录IP',
    login_attempts INT DEFAULT 0 COMMENT '登录尝试次数',
    locked_until DATETIME COMMENT '账户锁定截止',
    status VARCHAR(16) NOT NULL DEFAULT 'active' COMMENT '状态：active/inactive/locked/pending_approval',
    activation_token VARCHAR(64) COMMENT '激活Token',
    activation_expires_at DATETIME COMMENT '激活过期时间',
    password_expires_at DATETIME COMMENT '密码过期时间',
    privacy_policy_accepted TINYINT DEFAULT 0 COMMENT '隐私政策是否接受',
    privacy_accepted_at DATETIME COMMENT '隐私政策接受时间',
    data_processing_consent TINYINT DEFAULT 0 COMMENT '数据处理是否同意',
    consent_timestamp DATETIME COMMENT '同意时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_code (user_code),
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_role (primary_role),
    INDEX idx_organization (organization_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
```

**表27：user_roles（用户角色关联表）**

```sql
CREATE TABLE user_roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL COMMENT '用户ID',
    role_code VARCHAR(32) NOT NULL COMMENT '角色代码：SPONSOR/PI/SUB_I/PM/CRA/CRC/MM/DM/SUPER_ADMIN',
    trial_id BIGINT COMMENT '试验ID（参与特定试验时）',
    site_id BIGINT COMMENT '中心ID（特定中心时）',
    organization_id BIGINT COMMENT '组织ID',
    is_primary TINYINT DEFAULT 0 COMMENT '是否主角色',
    is_active TINYINT DEFAULT 1 COMMENT '是否生效',
    effective_start_date DATE COMMENT '生效开始日期',
    effective_end_date DATE COMMENT '生效结束日期',
    delegation_from_user_id BIGINT COMMENT '委托来源用户ID（如委托签名）',
    delegation_reason VARCHAR(256) COMMENT '委托原因',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by BIGINT COMMENT '创建人ID',
    UNIQUE KEY uk_user_role_trial (user_id, role_code, trial_id),
    INDEX idx_user (user_id),
    INDEX idx_role (role_code),
    INDEX idx_trial (trial_id),
    INDEX idx_site (site_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户角色关联表';
```

**表28：permissions（权限表）**

```sql
CREATE TABLE permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    permission_code VARCHAR(64) NOT NULL UNIQUE COMMENT '权限代码',
    permission_name VARCHAR(128) NOT NULL COMMENT '权限名称',
    permission_category VARCHAR(32) COMMENT '权限分类',
    resource_type VARCHAR(32) COMMENT '资源类型：trial项目/site中心/subject受试者/document文档/ae安全性/crf数据/approval审批',
    action_type VARCHAR(16) COMMENT '操作类型：create/read/update/delete/approve/sign/submit/export',
    scope_level VARCHAR(16) COMMENT '范围级别：platform平台/organization组织/trial试验/site中心',
    description TEXT COMMENT '权限描述',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_code (permission_code),
    INDEX idx_category (permission_category),
    INDEX idx_resource (resource_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='权限表';
```

**表29：role_permissions（角色权限关联表）**

```sql
CREATE TABLE role_permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    role_code VARCHAR(32) NOT NULL COMMENT '角色代码',
    permission_id BIGINT NOT NULL COMMENT '权限ID',
    scope_restrictions JSON COMMENT '范围限制JSON',
    is_granted TINYINT DEFAULT 1 COMMENT '是否授权',
    granted_by BIGINT COMMENT '授权人ID',
    granted_at DATETIME COMMENT '授权时间',
    UNIQUE KEY uk_role_permission (role_code, permission_id),
    INDEX idx_role (role_code),
    INDEX idx_permission (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='角色权限关联表';
```

#### 7.2.10 实验室与样本表

**表30：lab_tests（实验室检查表）**

```sql
CREATE TABLE lab_tests (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    test_code VARCHAR(64) NOT NULL UNIQUE COMMENT '检查编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    test_name VARCHAR(128) NOT NULL COMMENT '检查名称',
    test_category VARCHAR(32) COMMENT '检查类别：hematology血液学/chemistry生化/urinalysis尿液/hormone激素/viral病毒/other其他',
    loinc_code VARCHAR(16) COMMENT 'LOINC编码',
    unit VARCHAR(32) COMMENT '单位',
    normal_range_low DECIMAL(10,2) COMMENT '正常范围下限',
    normal_range_high DECIMAL(10,2) COMMENT '正常范围上限',
    normal_range_text VARCHAR(64) COMMENT '正常范围文本',
    is_required TINYINT DEFAULT 1 COMMENT '是否必做',
    visit_schedule VARCHAR(32) COMMENT '访视安排：baseline基线/each_visit每次访视/specified_visits指定访视',
    collection_method VARCHAR(64) COMMENT '采集方法',
    sample_type VARCHAR(32) COMMENT '样本类型：blood血液/urine尿液/tissue组织/other其他',
    sample_volume DECIMAL(10,2) COMMENT '样本量',
    central_lab_required TINYINT DEFAULT 0 COMMENT '是否需要中心实验室',
    central_lab_id BIGINT COMMENT '中心实验室ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trial (trial_id),
    INDEX idx_category (test_category),
    INDEX idx_loinc (loinc_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实验室检查表';
```

**表31：lab_results（实验室结果表）**

```sql
CREATE TABLE lab_results (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    result_code VARCHAR(64) NOT NULL UNIQUE COMMENT '结果编号',
    subject_id BIGINT NOT NULL COMMENT '受试者ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    visit_id BIGINT COMMENT '访视ID',
    lab_test_id BIGINT NOT NULL COMMENT '检查项目ID',
    specimen_collect_date DATE COMMENT '样本采集日期',
    specimen_receive_date DATE COMMENT '样本接收日期',
    specimen_analyze_date DATE COMMENT '样本分析日期',
    result_value VARCHAR(64) COMMENT '结果值',
    result_numeric DECIMAL(10,2) COMMENT '结果数值',
    result_unit VARCHAR(32) COMMENT '结果单位',
    reference_range_low DECIMAL(10,2) COMMENT '参考范围下限',
    reference_range_high DECIMAL(10,2) COMMENT '参考范围上限',
    reference_range_text VARCHAR(64) COMMENT '参考范围文本',
    abnormal_flag VARCHAR(16) COMMENT '异常标志：normal正常/N低值/H高值/NN正常/HH高-显著/LL低-显著',
    clinically_significant TINYINT DEFAULT 0 COMMENT '是否有临床意义',
    lab_normalization_suggestion TEXT COMMENT '数据标准化建议（AI）',
    lab_normalization_applied TINYINT DEFAULT 0 COMMENT '是否已标准化',
    normalized_value VARCHAR(64) COMMENT '标准化后的值',
    normalized_unit VARCHAR(32) COMMENT '标准化单位',
    method_used VARCHAR(64) COMMENT '检测方法',
    instrument VARCHAR(64) COMMENT '检测仪器',
    lab_normalization_rule_id BIGINT COMMENT '应用的标准化规则ID',
    result_status VARCHAR(16) DEFAULT 'pending' COMMENT '状态：pending待审核/verified已核实/abnormal异常/cancelled取消',
    verified_by BIGINT COMMENT '核实人ID',
    verified_at DATETIME COMMENT '核实时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subject (subject_id),
    INDEX idx_trial (trial_id),
    INDEX idx_visit (visit_id),
    INDEX idx_test (lab_test_id),
    INDEX idx_abnormal (abnormal_flag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='实验室结果表';
```

#### 7.2.11 电子签名表

**表32：electronic_signatures（电子签名记录表）**

```sql
CREATE TABLE electronic_signatures (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    signature_code VARCHAR(64) NOT NULL UNIQUE COMMENT '签名编号',
    signature_uuid VARCHAR(64) NOT NULL COMMENT '签名UUID',
    signer_id BIGINT NOT NULL COMMENT '签名人ID',
    signer_name VARCHAR(64) NOT NULL COMMENT '签名人姓名',
    signer_role VARCHAR(32) NOT NULL COMMENT '签名人角色',
    signer_email VARCHAR(128) NOT NULL COMMENT '签名人邮箱',
    signer_certificate_id VARCHAR(64) COMMENT '数字证书ID',
    signer_certificate_issuer VARCHAR(128) COMMENT '证书颁发机构',
    signer_certificate_expiry DATE COMMENT '证书有效期',
    signature_type VARCHAR(16) NOT NULL COMMENT '签名类型：author作者/reviewer审核/approver批准/contributor贡献/verification核实',
    signature_purpose VARCHAR(64) NOT NULL COMMENT '签名目的',
    document_type VARCHAR(32) COMMENT '文档类型',
    document_id BIGINT COMMENT '文档ID',
    document_code VARCHAR(64) COMMENT '文档编号',
    document_version VARCHAR(16) COMMENT '文档版本',
    document_hash VARCHAR(64) COMMENT '文档Hash',
    signed_content_hash VARCHAR(64) NOT NULL COMMENT '签名内容Hash',
    signature_value VARCHAR(512) COMMENT '签名值',
    signature_algorithm VARCHAR(32) COMMENT '签名算法：RSA-SHA256/ECDSA',
    signature_timestamp DATETIME NOT NULL COMMENT '签名时间戳',
    signature_timestamp_tz VARCHAR(16) COMMENT '时区',
    signature_device VARCHAR(128) COMMENT '签名设备',
    signature_ip_address VARCHAR(45) COMMENT '签名IP地址',
    signature_location VARCHAR(256) COMMENT '签名位置',
    signature_method VARCHAR(16) COMMENT '签名方式：password密码/pin/PIN/biometric生物识别/smart_card智能卡/token令牌的',
    password_verified TINYINT DEFAULT 0 COMMENT '密码是否验证',
    biometric_verified TINYINT DEFAULT 0 COMMENT '生物识别是否验证',
    two_factor_verified TINYINT DEFAULT 0 COMMENT '双因素是否验证',
    additional_authentication JSON COMMENT '额外认证信息',
    certificate_hash VARCHAR(64) COMMENT '证书Hash',
    certificate_chain_verified TINYINT DEFAULT 0 COMMENT '证书链是否验证',
    signature_reason VARCHAR(64) COMMENT '签名原因',
    signature_comments TEXT COMMENT '签名备注',
    irrevocable TINYINT DEFAULT 1 COMMENT '是否不可撤销',
    revoked TINYINT DEFAULT 0 COMMENT '是否被撤销',
    revoked_by BIGINT COMMENT '撤销人ID',
    revoked_at DATETIME COMMENT '撤销时间',
    revocation_reason VARCHAR(256) COMMENT '撤销原因',
    audit_reference VARCHAR(64) COMMENT '审计日志引用',
    gcp_compliant TINYINT DEFAULT 1 COMMENT '是否符合GCP',
    part11_compliant TINYINT DEFAULT 1 COMMENT '是否符合21CFRPart11',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_signature_uuid (signature_uuid),
    INDEX idx_signer (signer_id),
    INDEX idx_document (document_id),
    INDEX idx_timestamp (signature_timestamp),
    INDEX idx_revoked (revoked)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='电子签名记录表（21 CFR Part 11）';
```

#### 7.2.12 数据库锁定表

**表33：database_lock（数据库锁定表）**

```sql
CREATE TABLE database_lock (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    lock_code VARCHAR(64) NOT NULL UNIQUE COMMENT '锁定编号',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    lock_type VARCHAR(16) NOT NULL COMMENT '锁定类型：interim期中/final最终',
    lock_status VARCHAR(16) NOT NULL DEFAULT 'preparation' COMMENT '状态：preparation准备/data_freeze数据冻结/preparation_lock准备锁定/interim_lock期中锁定/final_lock最终锁定/unlocked已解锁',
    planned_lock_date DATE COMMENT '计划锁定日期',
    actual_lock_date DATETIME COMMENT '实际锁定日期',
    unlock_requested TINYINT DEFAULT 0 COMMENT '是否申请解锁',
    unlock_reason TEXT COMMENT '解锁原因',
    unlock_requested_by BIGINT COMMENT '申请解锁人ID',
    unlock_requested_at DATETIME COMMENT '申请解锁时间',
    unlock_approved TINYINT DEFAULT 0 COMMENT '解锁是否批准',
    unlock_approved_by BIGINT COMMENT '解锁批准人ID',
    unlock_approved_at DATETIME COMMENT '解锁批准时间',
    unlock_executed TINYINT DEFAULT 0 COMMENT '解锁是否执行',
    unlocked_at DATETIME COMMENT '解锁时间',
    pre_lock_checklist JSON COMMENT '锁库前检查清单',
    checklist_completion JSON COMMENT '检查完成情况',
    data_freeze_initiated_at DATETIME COMMENT '数据冻结开始时间',
    data_freeze_completed_at DATETIME COMMENT '数据冻结完成时间',
    data_freeze_status VARCHAR(16) COMMENT '冻结状态',
    queries_all_closed TINYINT DEFAULT 0 COMMENT '所有质疑是否关闭',
    deviations_all_closed TINYINT DEFAULT 0 COMMENT '所有偏离是否关闭',
    coding_completed TINYINT DEFAULT 0 COMMENT '编码是否完成',
    sdv_completed TINYINT DEFAULT 0 COMMENT 'SDV是否完成',
    medical_review_completed TINYINT DEFAULT 0 COMMENT '医学审核是否完成',
    statistical_review_completed TINYINT DEFAULT 0 COMMENT '统计审核是否完成',
    requested_by BIGINT COMMENT '锁定申请人人ID',
    requested_by_name VARCHAR(64) COMMENT '锁定申请人姓名',
    requested_at DATETIME COMMENT '锁定申请时间',
    approved_by BIGINT COMMENT '锁定批准人ID',
    approved_by_name VARCHAR(64) COMMENT '锁定批准人姓名',
    approved_at DATETIME COMMENT '锁定批准时间',
    electronic_signature_hash VARCHAR(64) COMMENT '电子签名Hash',
    lock_certificate_url VARCHAR(512) COMMENT '锁定证书URL',
    remarks TEXT COMMENT '备注',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_trial (trial_id),
    INDEX idx_status (lock_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据库锁定表';
```

#### 7.2.13 AI交互记录表

**表34：ai_interactions（AI交互记录表）**

```sql
CREATE TABLE ai_interactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    interaction_code VARCHAR(64) NOT NULL UNIQUE COMMENT '交互编号',
    trial_id BIGINT COMMENT '试验ID',
    session_id VARCHAR(128) NOT NULL COMMENT '会话ID',
    agent_type VARCHAR(32) NOT NULL COMMENT 'Agent类型：DOC_REVIEW/PROTOCOL_CHECK/AE_CODING/CONSENT_AUDIT/SAE_ALERT/DATA_CLEANING/QM_REPORT',
    user_id BIGINT COMMENT '用户ID',
    user_name VARCHAR(64) COMMENT '用户姓名',
    user_role VARCHAR(32) COMMENT '用户角色',
    request_data JSON COMMENT '请求数据（脱敏）',
    request_text TEXT COMMENT '请求文本',
    response_text TEXT COMMENT '响应文本',
    confidence_score DECIMAL(5,2) COMMENT '置信度评分',
    model_used VARCHAR(64) COMMENT '使用的模型',
    model_version VARCHAR(32) COMMENT '模型版本',
    token_usage JSON COMMENT 'Token使用量',
    processing_time_ms INT COMMENT '处理时长(毫秒)',
    input_data_classification VARCHAR(32) COMMENT '输入数据分类',
    contains_phi TINYINT DEFAULT 0 COMMENT '是否包含PHI',
    phi_access_logged TINYINT DEFAULT 0 COMMENT 'PHI访问是否记录',
    gcp_compliance_check JSON COMMENT 'GCP合规检查结果',
    output_validated TINYINT DEFAULT 0 COMMENT '输出是否经过人工验证',
    validated_by BIGINT COMMENT '验证人ID',
    validated_at DATETIME COMMENT '验证时间',
    validation_result VARCHAR(16) COMMENT '验证结果：accepted接受/rejected拒绝/modified修改',
    human_correction TEXT COMMENT '人工修正内容',
    used_in_decision TINYINT DEFAULT 0 COMMENT '是否用于决策',
    decision_impact TEXT COMMENT '决策影响说明',
    audit_reference VARCHAR(64) COMMENT '关联审计日志',
    retention_period_years INT DEFAULT 15 COMMENT '保留年限',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_agent (agent_type),
    INDEX idx_trial (trial_id),
    INDEX idx_user (user_id),
    INDEX idx_phi (contains_phi),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI交互记录表';
```

#### 7.2.14 随机化表

**表35：randomizations（随机化表）**

```sql
CREATE TABLE randomizations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    randomization_code VARCHAR(64) NOT NULL UNIQUE COMMENT '随机编号',
    subject_id BIGINT NOT NULL COMMENT '受试者ID',
    trial_id BIGINT NOT NULL COMMENT '试验ID',
    site_id BIGINT NOT NULL COMMENT '中心ID',
    stratum VARCHAR(64) COMMENT '分层因素',
    stratification_factors JSON COMMENT '分层因素值',
    randomization_number VARCHAR(32) NOT NULL COMMENT '随机号',
    randomization_group VARCHAR(32) COMMENT '随机分组',
    treatment_arm_code VARCHAR(32) COMMENT '治疗组代码',
    treatment_arm_name VARCHAR(128) COMMENT '治疗组名称',
    randomization_date DATETIME NOT NULL COMMENT '随机日期时间',
    randomization_method VARCHAR(32) COMMENT '随机方法：RANDOM/IRV/STRATIFIED',
    allocation_concealment VARCHAR(32) COMMENT '分配隐藏：SEALED_ENVELOPE/IVRS/IWRS/CENTRAL',
    ivrs_iwrs_used TINYINT DEFAULT 0 COMMENT '是否使用IVRS/IWRS',
    ivrs_iwrs_system VARCHAR(64) COMMENT 'IVRS/IWRS系统',
    ip_assignment VARCHAR(32) COMMENT '药物分配',
    ip_kit_numbers JSON COMMENT '药物包编号列表',
    blinding_maintained TINYINT DEFAULT 1 COMMENT '盲态是否维持',
    unblinding_required TINYINT DEFAULT 0 COMMENT '是否需要破盲',
    unblinding_reason TEXT COMMENT '破盲原因',
    unblinding_authorized_by BIGINT COMMENT '破盲授权人ID',
    unblinded_at DATETIME COMMENT '破盲时间',
    emergency_unblinding TINYINT DEFAULT 0 COMMENT '是否紧急破盲',
    subject_informed TINYINT DEFAULT 0 COMMENT '受试者是否被告知',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_subject (subject_id),
    INDEX idx_trial (trial_id),
    INDEX idx_randomization_no (randomization_number),
    INDEX idx_group (randomization_group),
    INDEX idx_randomization_date (randomization_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='随机化表';
```

---

## 8. 合规体系设计

### 8.1 ICH GCP E6(R2) 合规对照

| GCP要求 | 系统实现 |
|---------|---------|
| **4.2 试验用产品的管理** | 药物管理模块：分发、回收、盘点、温控 |
| **4.3 随机化和设盲** | 随机化模块：IWRS对接、盲法维持 |
| **5.0 试验用产品的管理** | 药物追溯、批次管理、过期检查 |
| **5.1 申办者的职责** | 申办方角色：项目管理、质量控制 |
| **5.5 试验用产品的管理** | IP追溯、随机号对应 |
| **6.0 IRB/IEC的职责** | 伦理管理：审批跟踪、版本控制 |
| **8.0 文件** | TMF文档管理、版本控制、归档 |
| **8.2 试验用产品的文件** | IP记录、药物分发记录 |

### 8.2 FDA 21 CFR Part 11 合规

| Part 11要求 | 系统实现 |
|------------|---------|
| **11.10(a) 系统验证** | IQ/OQ/PQ验证文档 |
| **11.10(b) 审计追踪** | 完整审计日志、不可篡改 |
| **11.10(c) 准确性** | 数据完整性检查、校验 |
| **11.10(d) 授权人员** | RBAC权限控制 |
| **11.10(e) 电子签名** | 数字证书、电子签名Hash |
| **11.10(f) 审计追踪可用性** | 日志在线可查 |
| **11.10(g) 保护记录** | 加密存储、备份 |
| **11.50 电子签名关联** | 签名与记录绑定 |

### 8.3 GDPR 合规

| GDPR条款 | 系统实现 |
|---------|---------|
| **Art.5 数据最小化** | 仅采集必要字段 |
| **Art.6 法律基础** | 同意/合法利益/法律义务 |
| **Art.12 透明** | 隐私通知、Cookie政策 |
| **Art.15 数据访问** | 数据主体权利接口 |
| **Art.16 更正** | 数据更正流程 |
| **Art.17 删除权** | 数据删除(匿名化) |
| **Art.32 安全** | 加密、访问控制、审计 |
| **Art.33 通知** | 数据泄露响应流程 |

### 8.4 HIPAA 合规

| HIPAA要求 | 系统实现 |
|----------|---------|
| **Privacy Rule** | PHI定义、受保护信息标识 |
| **Security Rule** | 技术/物理/行政保障 |
| **Safeguards** | 加密传输(AES-256/TLS) |
| **Access Controls** | 唯一标识、角色基访问 |
| **Audit Controls** | PHI访问审计 |
| **Transmission Security** | 安全传输加密 |

### 8.5 ISO 27001 合规

| ISO 27001控制域 | 系统实现 |
|----------------|---------|
| **A.5 信息安全政策** | 安全策略文档 |
| **A.6 信息安全组织** | 安全责任分配 |
| **A.9 访问控制** | RBAC、MFA |
| **A.10 密码学** | 加密、签名 |
| **A.12 操作安全** | 日志、监控 |
| **A.13 通信安全** | TLS、网络隔离 |
| **A.16 事件管理** | 安全事件响应 |
| **A.18 合规** | 法规合规检查 |

### 8.6 电子签名实现

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        电子签名合规实现 (21 CFR Part 11)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  签名要素:                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  1. 签名人身份绑定                                                      │ │
│  │     • 用户账号 + 密码                                                   │ │
│  │     • 数字证书 (X.509)                                                 │ │
│  │     • 生物识别 (指纹/人脸) - 可选                                       │ │
│  │     • 双因素认证 (TOTP/短信)                                           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  2. 签名内容绑定                                                        │ │
│  │     • 文档/记录 Hash (SHA-256)                                         │ │
│  │     • 版本号                                                           │ │
│  │     • 时间戳 (RFC 3161)                                                │ │
│  │     • 操作上下文                                                       │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  3. 签名值生成                                                          │ │
│  │     • RSA-SHA256 / ECDSA                                               │ │
│  │     • HSM硬件安全模块                                                  │ │
│  │     • 私钥保护                                                         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  4. 签名验证                                                            │ │
│  │     • 证书链验证                                                       │ │
│  │     • 签名值验证                                                       │ │
│  │     • 时间戳验证                                                       │ │
│  │     • 内容完整性验证                                                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  签名不可伪造:                                                                │
│  • Hash链式结构 (类似区块链)                                                 │
│  • 审计日志引用                                                             │
│  • 签名唯一编号                                                             │
│  • 不可抵赖、不可篡改                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 8.7 审计追踪实现

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           审计追踪实现 (21 CFR Part 11)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  追踪范围:                                                                    │
│  ✓ 所有数据创建/修改/删除                                                    │
│  ✓ 所有用户登录/登出                                                        │
│  ✓ 所有电子签名                                                             │
│  ✓ 所有权限变更                                                             │
│  ✓ 所有文档访问/下载                                                        │
│  ✓ 所有审批流程                                                             │
│  ✓ 所有系统配置变更                                                         │
│  ✓ 所有数据导入/导出                                                        │
│                                                                              │
│  记录内容:                                                                   │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  • 操作时间 (精确到毫秒)                                               │ │
│  │  • 操作人员 (ID+姓名+角色)                                             │ │
│  │  • 操作终端 (IP+设备+浏览器)                                          │ │
│  │  • 操作对象 (类型+ID+名称)                                             │ │
│  │  • 操作类型 (CREATE/UPDATE/DELETE)                                    │ │
│  │  • 变更前值 (脱敏处理)                                                 │ │
│  │  • 变更后值 (脱敏处理)                                                 │ │
│  │  • 请求追踪 (Request ID)                                               │ │
│  │  • 会话标识 (Session ID)                                               │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  防篡改机制:                                                                  │
│  • UUID唯一标识                                                             │
│  • Hash链式结构 (前一条Hash)                                                 │
│  • 记录不可修改/删除                                                        │
│  • 校验和验证                                                               │
│  • 定期完整性检查                                                           │
│                                                                              │
│  保留要求:                                                                   │
│  • 保留期限 ≥ 2年 (或法规要求)                                               │
│  • 在线可查                                                                │
│  • 可导出供检查                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. 非功能需求

### 9.1 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 系统可用性 | ≥99.9% | 年度停机<8.76小时 |
| API响应时间(P99) | <500ms | 普通接口 |
| 大文件上传 | <60s | ≤100MB文件 |
| 并发用户数 | ≥5,000 | 同时在线 |
| 数据处理 | 支持≥10万受试者 | 单一试验 |

### 9.2 安全指标

| 指标 | 要求 |
|------|------|
| 数据加密 | AES-256 (静态) + TLS 1.3 (传输) |
| 密码策略 | 长度≥8，复杂度，含过期 |
| 会话管理 | 超时30min，强制重新认证 |
| 审计保留 | ≥15年 (GCP要求) |
| 备份 | 每日增量，7天全量，异地容灾 |

### 9.3 备份与恢复

| 策略 | 说明 |
|------|------|
| 在线备份 | 实时复制到灾备中心 |
| 每日全量 | 每日凌晨2:00执行 |
| 增量备份 | 每小时 |
| 恢复测试 | 每月恢复演练 |
| RTO | ≤4小时 |
| RPO | ≤1小时 |

---

## 10. 版本路线图

### 10.1 版本规划

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
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐       │
│  │ 项目管理      │  │ 医学监查     │  │ 高级分析      │  │ 平台化      │       │
│  │ 伦理管理      │  │ 安全管理      │  │ ePRO集成      │  │ 第三方集成  │       │
│  │ 受试者管理    │  │ 药物管理      │  │ 影像评估      │  │ eCTD导出    │       │
│  │ EDC数据采集   │  │ AI辅助编码   │  │ 风险预测      │  │ 监管对接    │       │
│  │ 文档管理      │  │ 电子签名      │  │ 患者招募      │  │ 合作伙伴    │       │
│  │ 监查访视      │  │ 数据质疑      │  │ 远程监查      │  │ 全球部署    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 v1.0 MVP功能清单

| 模块 | 功能点 | 优先级 |
|------|--------|--------|
| 项目 | 项目立项/审批 | P0 |
| 项目 | 里程碑管理 | P0 |
| 项目 | 研究中心管理 | P0 |
| 伦理 | 伦理申请/审批 | P0 |
| 受试者 | 患者入组/知情 | P0 |
| 受试者 | 访视计划/记录 | P0 |
| 数据 | CRF数据录入 | P0 |
| 数据 | 数据质疑管理 | P0 |
| 安全 | AE/SAE报告 | P0 |
| 文档 | TMF文档管理 | P0 |
| 文档 | 版本控制 | P0 |
| 审批 | 流程审批配置 | P0 |
| 系统 | 用户权限管理 | P0 |
| 系统 | 审计日志 | P0 |

---

## 附录

### A. 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| CTMS | Clinical Trial Management System | 临床试验管理系统 |
| GCP | Good Clinical Practice | 药物临床试验质量管理规范 |
| ICH | International Council for Harmonisation | 人用药品注册技术要求国际协调会议 |
| EDC | Electronic Data Capture | 电子数据采集 |
| CRF | Case Report Form | 病例报告表 |
| SAE | Serious Adverse Event | 严重不良事件 |
| SUSAR | Suspected Unexpected Serious Adverse Reaction | 可疑且非预期严重不良反应 |
| PI | Principal Investigator | 主要研究者 |
| Sub-I | Sub-Investigator | 次要研究者 |
| CRA | Clinical Research Associate | 临床监查员 |
| CRC | Clinical Research Coordinator | 临床协调员 |
| SDV | Source Data Verification | 源数据核查 |
| TMF | Trial Master File | 试验主文件 |
| IWRS | Interactive Web Response System | 交互式网络应答系统 |
| IRB/IEC | Institutional Review Board / Independent Ethics Committee | 机构审查委员会/独立伦理委员会 |
| ICF | Informed Consent Form | 知情同意书 |
| MedDRA | Medical Dictionary for Regulatory Activities | 监管活动医学词典 |
| ALCOA+ | - | 数据完整性原则：可归属、清晰、同步、原始、准确+完整/一致/持久/可及 |
| RBAC | Role-Based Access Control | 基于角色的访问控制 |
| HSM | Hardware Security Module | 硬件安全模块 |
| PHI | Protected Health Information | 受保护健康信息 |

### B. 角色权限矩阵

| 权限项 | 申办方 | PI | Sub-I | PM | CRA | CRC | MM | DM | 超管 |
|--------|-------|-----|-------|-----|------|-----|-----|------|------|
| 创建项目 | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 审批方案 | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| 查看所有数据 | ✅ | ❌ | ❌ | ✅ | 授权 | ❌ | ✅ | ✅ | ✅ |
| 录入CRF | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 执行SDV | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| 报告AE/SAE | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 审批SAE | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| 审核数据质疑 | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ |
| 数据库锁定 | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| 电子签名 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 查看审计日志 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 配置权限 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

### C. 数据完整性原则 (ALCOA+)

| 原则 | 说明 | 系统实现 |
|------|------|---------|
| **Attributable** | 可归属 | 用户ID+时间戳+电子签名 |
| **Legible** | 清晰 | 数据格式规范、版本控制 |
| **Contemporaneous** | 同步 | 实时录入、时间戳自动生成 |
| **Original** | 原始 | 源数据记录、不可覆盖 |
| **Accurate** | 准确 | 逻辑核查、自动计算校验 |
| **Complete** | 完整 | 必填校验、质疑追踪 |
| **Consistent** | 一致 | 跨表核查、自动一致性检查 |
| **Enduring** | 持久 | 加密存储、长期归档 |
| **Available** | 可及 | 在线可查、备份恢复 |

---

**文档结束**

*本文档为产品管理内部使用，包含敏感技术信息，请勿外传。*

*© 2026 CTMS临床试验管理系统 - 符合ICH GCP E6(R2)、FDA 21 CFR Part 11、GDPR、HIPAA、ISO 27001*
