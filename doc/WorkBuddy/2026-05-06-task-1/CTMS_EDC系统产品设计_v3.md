# CTMS+EDC临床试验管理系统 产品设计规格书

> **版本**：v3.0 | **更新日期**：2026-05-06 | **状态**：正式版
> **文档编号**：CTMS-EDC-PRD-2026-V3.0
> **适用标准**：RCT | RWE | ICH GCP E6(R2) | FDA 21 CFR Part 11 | GDPR | HIPAA | ISO 27001

---

## 目录

1. [产品概述与愿景](#1-产品概述与愿景)
2. [系统架构设计](#2-系统架构设计)
3. [临床试验全流程管理](#3-临床试验全流程管理)
4. [角色体系与功能矩阵](#4-角色体系与功能矩阵)
5. [核心功能模块详规](#5-核心功能模块详规)
6. [工时管理系统](#6-工时管理系统)
7. [项目收支管理](#7-项目收支管理)
8. [AI Agent & Skills 设计](#8-ai-agent--skills-设计)
9. [数据库设计](#9-数据库设计)
10. [文档管理与协作](#10-文档管理与协作)
11. [流程审批管理](#11-流程审批管理)
12. [合规体系设计](#12-合规体系设计)
13. [消息通知体系](#13-消息通知体系)
14. [非功能需求](#14-非功能需求)
15. [版本路线图](#15-版本路线图)

---

## 1. 产品概述与愿景

### 1.1 产品定位

**CTMS+EDC临床试验管理系统** 是一款面向医药企业、CRO公司、研究机构的**一体化临床试验管理平台**。系统整合了：

| 子系统 | 功能范围 |
|--------|----------|
| **CTMS** | 项目管理、监查管理、药物管理、中心管理、供应商管理 |
| **EDC** | 电子数据采集、随机化(IWRS)、数据质疑、数据库锁定 |

**核心优势**：
- ✅ 一体化设计，数据互通，避免信息孤岛
- ✅ AI智能辅助，提升数据质量与效率
- ✅ 全流程合规支持，符合国际GCP标准
- ✅ 支持RCT（随机对照试验）和RWE（真实世界研究）两种模式

### 1.2 合规矩阵

| 合规标准 | 适用条款 | 系统实现方式 |
|---------|---------|-------------|
| **RCT** | 随机对照试验设计 | IWRS随机化、盲法管理、随机分配隐藏 |
| **RWE** | 真实世界证据 | 观察性研究设计、回顾性数据采集、倾向性评分 |
| **ICH GCP E6(R2)** | 4.2/5.0/8.0 | 试验流程标准化、伦理审查、知情同意管理 |
| **FDA 21 CFR Part 11** | 11.10/11.50/11.70 | 电子签名、数字证书、审计追踪、版本控制 |
| **GDPR** | Art.5/6/17/32 | 数据加密、访问控制、数据主体权利、数据删除 |
| **HIPAA** | Privacy/Security Rule | PHI保护、脱敏处理、加密传输、BAA协议 |
| **ISO 27001** | A.8/A.14/A.18 | 信息安全策略、访问管理、事件响应、安全审计 |

### 1.3 核心价值主张

| 角色 | 核心价值 |
|------|---------|
| **申办方** | 试验全局可视化、质量管控、成本优化、投资回报分析 |
| **中心PI** | 高效的患者管理和数据录入、伦理合规、研究中心绩效 |
| **Sub-I** | 协作分工、任务追踪、文件管理、诊疗效率提升 |
| **CRO PM** | 项目进度管控、资源调配、风险预警、财务追踪 |
| **CRA** | 远程监查、SDV追踪、问题管理、访视报告自动生成 |
| **CRC** | 患者筛选、访视管理、数据录入、AE/SAE上报 |
| **MM** | 医学监查、方案偏离审核、安全性评估、DSMB支持 |
| **DM** | 数据管理、质疑追踪、数据库锁定、统计准备 |
| **超管** | 系统配置、权限管理、审计合规、租户管理 |

---

## 2. 系统架构设计

### 2.1 技术架构

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           CTMS+EDC 系统架构                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        1. 表现层 (Presentation Layer)                  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │  │
│  │  │ Web端   │ │ 移动端  │ │ 微信端  │ │企微端   │ │ API接口 │        │  │
│  │  │(React)  │ │(RN)     │ │(小程序) │ │(企微应用)│ │(REST)   │        │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        2. 网关层 (Gateway Layer)                        │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │  │
│  │  │ 负载均衡    │ │ API网关     │ │ 认证授权    │ │ 限流熔断    │     │  │
│  │  │ (Nginx)    │ │ (Kong)      │ │ (OAuth2)    │ │ (Sentinel)  │     │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘     │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        3. 业务服务层 (Business Layer)                   │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │  │
│  │  │ CTMS服务  │ │ EDC服务   │ │ AI服务    │ │ 文档服务  │ │ 审批服务  │    │  │
│  │  │ (Java)   │ │ (Java)   │ │ (Python) │ │ (Python) │ │ (Java)   │    │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                  │  │
│  │  │ 通知服务  │ │ 工时服务  │ │ 财务服务  │ │ 日志服务  │                  │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘                  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        4. AI能力层 (AI Layer)                           │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐  │  │
│  │  │                     LLM 大模型服务                                │  │  │
│  │  │            Base URL: http://192.168.0.126:8802/write/              │  │  │
│  │  │                         (POST /chat)                              │  │  │
│  │  └──────────────────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │  │
│  │  │DocReview│ │AE_Coding│ │Consent  │ │SDV_     │ │SAE_     │           │  │
│  │  │Agent    │ │Agent    │ │Audit    │ │Assist   │ │Alert    │           │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘           │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                      │  │
│  │  │Protocol │ │Lab_     │ │Data_    │ │QM_      │                      │  │
│  │  │Check    │ │Normalize│ │Clean    │ │Report   │                      │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘                      │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                        5. 数据层 (Data Layer)                           │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │  │
│  │  │ PostgreSQL  │ │   MySQL     │ │  MongoDB    │ │  Redis      │       │  │
│  │  │ (主业务库)  │ │ (历史归档)  │ │ (文档存储)  │ │ (缓存/会话) │       │  │
│  │  │  localhost  │ │  localhost  │ │             │ │             │       │  │
│  │  │  :5432      │ │  :3306     │ │             │ │             │       │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘       │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 CTMS与EDC数据流关系

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          CTMS ↔ EDC 数据流图                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐             │
│  │    CTMS       │     │     EDC       │     │     IWRS      │             │
│  │  (项目管理)   │◄───►│  (数据采集)   │◄───►│  (随机化)    │             │
│  └───────┬───────┘     └───────┬───────┘     └───────┬───────┘             │
│          │                     │                     │                       │
│          │ 同步                 │ 同步                │ 同步                  │
│          ▼                     ▼                     ▼                       │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                        统一数据中心                                   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │   │
│  │  │试验信息 │ │受试者   │ │访视数据 │ │安全性   │ │药物分配 │       │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘       │   │
│  └────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. 临床试验全流程管理

### 3.1 试验类型支持

| 试验类型 | 描述 | 系统支持 |
|---------|------|----------|
| **RCT** | 随机对照试验 | IWRS随机化、盲法管理、随机分配隐藏、盲态维护 |
| **RWE** | 真实世界研究 | 观察性设计、回顾性数据采集、外部对照、倾向性评分 |
| **IIT** | 研究者发起的试验 | 简化立项流程、学术发表支持 |
| **BE/BA** | 生物等效性研究 | 生物样本管理、PK参数计算 |

### 3.2 试验生命周期（5阶段16里程碑）

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          临床试验生命周期                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  1.准备阶段  │───▶│  2.启动阶段  │───▶│  3.执行阶段  │───▶│  4.结束阶段  │───▶│ 5.归档阶段 │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│                                                                              │
│  里程碑: M1立项 → M2方案 → M3伦理 → M4合同 → M5启动 → M6首入组 →           │
│         M7末入组 → M8末访视 → M9锁库 → M10统计 → M11 CSR → M12归档         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 各阶段核心活动

| 阶段 | 阶段名称 | 核心活动 | 主要角色 | EDC关联 |
|------|---------|---------|---------|---------|
| **Phase 1** | 准备阶段 | 项目立项、方案制定、IND/NDA申请、研究中心筛选 | Sponsor, PM | 创建研究 |
| **Phase 2** | 启动阶段 | 伦理审批、合同签署、物资准备、启动培训、授权配置 | PI, CRA, CRC | 创建CRF |
| **Phase 3** | 执行阶段 | 受试者筛选、入组、随访、监查、数据清理 | PI, Sub-I, CRA, CRC | 数据录入 |
| **Phase 4** | 结束阶段 | 数据库锁定、统计解锁、CSR生成、揭盲(如适用) | DM, MM, STAT | 数据导出 |
| **Phase 5** | 归档阶段 | 文档归档、物资回收、项目关闭、经验总结 | PM, 文档管理员 | 归档完成 |

---

## 4. 角色体系与功能矩阵

### 4.1 九大角色定义

| 角色 | 代码 | 英文全称 | 归属 | 主要职责 |
|------|------|---------|------|---------|
| **申办方** | SPONSOR | Sponsor | 医药企业 | 试验发起、资金投入、最终责任 |
| **主要研究者** | PI | Principal Investigator | 研究机构 | 试验执行、医疗决策、团队领导 |
| **次要研究者** | SUB_I | Sub-Investigator | 研究机构 | 患者诊治、数据记录、AE处理 |
| **项目经理** | PM | Project Manager | CRO | 项目整体管理、进度控制、风险管理 |
| **临床监查员** | CRA | Clinical Research Associate | CRO/申办方 | 中心监查、质量保证、问题追踪 |
| **临床协调员** | CRC | Clinical Research Coordinator | 研究机构/CRO | 患者协调、文件管理、数据录入 |
| **医学监查员** | MM | Medical Monitor | CRO/申办方 | 医学审核、安全评估、方案偏离 |
| **数据管理员** | DM | Data Manager | CRO/申办方 | 数据库设计、数据审核、锁库管理 |
| **超级管理员** | SUPER_ADMIN | System Administrator | 平台 | 系统配置、权限管理、审计合规 |

### 4.2 角色功能矩阵

| 功能模块 | 申办方 | PI | Sub-I | PM | CRA | CRC | MM | DM | 超管 |
|---------|:------:|:--:|:------:|:--:|:----:|:--:|:--:|:--:|:----:|
| **项目管理** |
| 项目立项/审批 | ✅ | - | - | ✅ | - | - | - | - | - |
| 项目进度查看 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 里程碑管理 | ✅ | - | - | ✅ | - | - | - | - | - |
| **伦理与监管** |
| 伦理申请 | ✅ | ✅ | - | ✅ | ✅ | ✅ | - | - | - |
| 伦理审批跟踪 | ✅ | ✅ | - | ✅ | ✅ | ✅ | - | - | - |
| **受试者管理(EDC)** |
| 患者筛选/入组 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| 知情同意 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| 随机化(IWRS) | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| CRF数据录入 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| **源数据核查** |
| SDV执行 | - | - | - | - | ✅ | - | - | - | - |
| SDV报告生成 | - | - | - | ✅ | ✅ | - | - | - | - |
| **数据质疑** |
| 发起质疑 | - | - | - | - | ✅ | - | - | ✅ | - |
| 质疑回复 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| **安全性管理** |
| AE/SAE报告 | - | ✅ | ✅ | - | - | ✅ | - | - | - |
| SAE审核 | ✅ | - | - | ✅ | - | - | ✅ | - | - |
| **文档管理(TM)** |
| 文档上传/版本 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 文档协作编辑 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| **流程审批** |
| 审批流程配置 | ✅ | - | - | ✅ | - | - | - | - | ✅ |
| 发起审批 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| **工时管理** |
| 工时填写 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 工时审批 | ✅ | ✅ | - | ✅ | - | - | ✅ | ✅ | ✅ |
| **收支管理** |
| 收入项目管理 | ✅ | - | - | ✅ | - | - | - | - | ✅ |
| 支出项目管理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |
| 财务报表 | ✅ | - | - | ✅ | - | - | - | - | ✅ |
| **系统管理** |
| 用户管理 | ✅ | ✅ | - | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 角色权限配置 | - | - | - | - | - | - | - | - | ✅ |
| 审计日志查看 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## 5. 核心功能模块详规

### 5.1 CTMS项目管理模块

#### 5.1.1 项目立项流程

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           项目立项流程 (RFI→FID→启动)                        │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐   │
│  │ RFI     │───▶│ 方案设计 │───▶│ 项目估算 │───▶│ FID     │───▶│ 项目启动 │   │
│  │ 询价函  │    │ Protocol│    │ Budget  │    │ 正式立项 │    │ Kickoff │   │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘   │
│                                                                              │
│  角色: Sponsor    Sponsor/PM    Sponsor/PM    Sponsor    Sponsor/PM         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 EDC电子数据采集模块

#### 5.2.1 CRF设计器

```json
{
  "crf_id": "CRF-2026-001",
  "form_groups": [
    {
      "group_name": "筛选期",
      "forms": [
        {"form_id": "FRM-SCR-001", "form_name": "知情同意书", "repeatable": false},
        {"form_id": "FRM-SCR-002", "form_name": "人口学资料", "repeatable": false},
        {"form_id": "FRM-SCR-003", "form_name": "入选/排除标准", "repeatable": false}
      ]
    },
    {
      "group_name": "治疗期",
      "forms": [
        {"form_id": "FRM-TRT-001", "form_name": "研究药物分发", "repeatable": true},
        {"form_id": "FRM-TRT-002", "form_name": "生命体征", "repeatable": true},
        {"form_id": "FRM-AE-001", "form_name": "不良事件", "repeatable": true}
      ]
    }
  ]
}
```

#### 5.2.2 IWRS随机化系统

```json
{
  "iwrs_module": {
    "randomization_method": "区组随机|分层随机|动态随机",
    "blinding": "开放|单盲|双盲|三盲",
    "strata": ["中心", "疾病分期"],
    "allocation_ratio": [1, 1],
    "emergency_unblinding": {
      "enabled": true,
      "approval_required": true
    }
  }
}
```

---

## 6. 工时管理系统

### 6.1 工时填写规则

```json
{
  "work_hour_rules": {
    "填写的角色": ["Sponsor", "PI", "Sub-I", "PM", "CRA", "CRC", "MM", "DM"],
    "工时类型": {
      "TRV": {"name": "临床监查", "desc": "现场/远程监查访视", "默认审批人": "PM"},
      "PMO": {"name": "项目管理", "desc": "项目管理活动", "默认审批人": "Sponsor"},
      "DMO": {"name": "数据管理", "desc": "数据管理活动", "默认审批人": "PM"},
      "MEO": {"name": "医学监查", "desc": "医学审核活动", "默认审批人": "Sponsor"},
      "STA": {"name": "数据分析", "desc": "统计分析活动", "默认审批人": "PM"},
      "DOC": {"name": "文档工作", "desc": "文档编写审阅", "默认审批人": "PM"},
      "TRN": {"name": "培训会议", "desc": "培训和会议", "默认审批人": "PM"},
      "TRF": {"name": "差旅时间", "desc": "差旅途时间", "默认审批人": "PM"},
      "OTH": {"name": "其他", "desc": "其他活动", "默认审批人": "PM"}
    },
    "填写频率": "每周一次(每周五前填写本周工时)",
    "补填规则": "可补填最近30天工时，超出需申请特批",
    "锁定规则": "已审批工时不得自行修改，需申请变更"
  }
}
```

### 6.2 工时审批流程

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              工时审批流程                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  员工填写 ──▶ 直线上级审批 ──▶ PM审核(项目工时) ──▶ 财务复核 ──▶ 完成       │
│  ┌───────┐      ┌─────────┐        ┌─────────┐        ┌─────────┐          │
│  │ Draft │ ───▶ │ Pending │ ─────▶ │ Pending │ ─────▶ │Approved │          │
│  └───────┘      └─────────┘        └─────────┘        └─────────┘          │
│                                                                              │
│  审批规则:                                                                   │
│  - 普通员工: 直线上级审批 → PM复核                                           │
│  - PM自己: Sponsor审批                                                        │
│  - Sponsor: 无需审批(直接计入)                                                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 项目收支管理

### 7.1 收入项目管理

```json
{
  "income_categories": [
    {"code": "INC-001", "name": "固定服务费", "desc": "按项目整体报价", "billing_rule": "里程碑触发"},
    {"code": "INC-002", "name": "人员工时费", "desc": "按实际工时计费", "billing_rule": "月度结算"},
    {"code": "INC-003", "name": "中心费用", "desc": "各中心服务费", "billing_rule": "中心启动触发"},
    {"code": "INC-004", "name": "里程碑奖金", "desc": "提前完成奖励", "billing_rule": "里程碑触发"},
    {"code": "INC-005", "name": "变更订单", "desc": "范围变更增加费用", "billing_rule": "变更审批通过"}
  ]
}
```

### 7.2 支出项目管理

```json
{
  "expense_categories": [
    {"code": "EXP-001", "name": "人员成本", "type": "直接成本", "approval_required": true},
    {"code": "EXP-002", "name": "中心费用", "type": "直接成本", "approval_required": true},
    {"code": "EXP-003", "name": "检测费用", "type": "直接成本", "approval_required": true},
    {"code": "EXP-004", "name": "药物费用", "type": "直接成本", "approval_required": true},
    {"code": "EXP-005", "name": "第三方服务", "type": "直接成本", "approval_required": true},
    {"code": "EXP-006", "name": "差旅费用", "type": "直接成本", "approval_required": true},
    {"code": "EXP-007", "name": "办公费用", "type": "间接成本", "approval_required": false},
    {"code": "EXP-008", "name": "系统使用费", "type": "间接成本", "approval_required": false}
  ]
}
```

### 7.3 收支审批流程

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                              项目收支审批流程                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  【收入类】                           【支出类】                              │
│  ┌─────────┐                        ┌─────────┐                              │
│  │发票开具  │──▶Sponsor审批 ──▶完成  │费用申请  │──▶PM审批 ──┬──▶≤10000:完成 │
│  └─────────┘                        └─────────┘            │                │
│                                                              └──▶>10000: ──┬─▶Sponsor审 │
│                                                                             │ 批 ──▶完成 │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. AI Agent & Skills 设计

### 8.1 AI能力架构

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           AI Agent 架构图                                    │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        LLM 大模型服务                                 │  │
│  │              Base URL: http://192.168.0.126:8802/write/                │  │
│  │                       Endpoint: POST /chat                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                     │                                      │
│                                     ▼                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      AI Orchestration Layer                           │  │
│  │                    (LangGraph / LangChain)                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                     │                                      │
│     ┌───────────┬───────────┬───────────┬───────────┬───────────┐          │
│     │           │           │           │           │           │          │
│     ▼           ▼           ▼           ▼           ▼           ▼          │
│  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐         │
│  │Doc  │    │AE   │    │Cons │    │SDV  │    │SAE  │    │Prot │         │
│  │Review│   │Coding│   │Audit│   │Assist│   │Alert│   │Check│         │
│  └─────┘    └─────┘    └─────┘    └─────┘    └─────┘    └─────┘         │
│     │           │           │           │           │           │          │
│     ▼           ▼           ▼           ▼           ▼           ▼          │
│  ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐    ┌─────┐         │
│  │Lab  │    │Data │    │QM   │    │Work │    │Chat │    │Trans│         │
│  │Norm │    │Clean│    │Report│   │Hour │    │Bot  │    │late │         │
│  └─────┘    └─────┘    └─────┘    └─────┘    └─────┘    └─────┘         │
│                                                                             │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Agent Skill YAML 定义

#### 8.2.1 DOC_REVIEW Agent (文档审核)

```yaml
skill_name: ctms_doc_review
version: "1.0"
agent_type: DOC_REVIEW
category: compliance
description: 自动审核临床试验文档的GCP合规性

system_prompt: |
  你是一位专业的ICH GCP E6(R2)合规审核专家。
  审核标准：ICH GCP E6(R2)、FDA 21 CFR Part 11、HIPAA
  问题分类：严重(Critical)、主要(Major)、次要(Minor)

input_schema:
  document_url:
    type: string
    required: true
    description: 文档存储URL
  document_type:
    type: enum
    required: true
    enum: ["protocol", "icf", "crf", "sap", "csr", "lab_manual", "ib", "other"]
    description: 文档类型
  trial_id:
    type: string
    required: true
    description: 试验ID

output_schema:
  review_id:
    type: string
  overall_score:
    type: number
    minimum: 0
    maximum: 100
  compliance_status:
    type: enum
    enum: ["pass", "pass_with_comments", "needs_revision", "fail"]
  issues:
    type: object
    properties:
      critical: {type: array}
      major: {type: array}
      minor: {type: array}
```

#### 8.2.2 AE_CODING Agent (不良事件编码)

```yaml
skill_name: ctms_ae_coding
version: "1.0"
agent_type: AE_CODING
category: safety
description: 使用MedDRA术语对不良事件进行标准化编码

system_prompt: |
  你是一位专业的不良事件编码专家，精通MedDRA编码规则。
  编码原则：优先选择最精确的PT（首选术语）
  遵循"字面意思"编码原则
  考虑LLT到PT的层级关系

input_schema:
  ae_description:
    type: string
    required: true
    description: AE原始描述
  seriousness:
    type: enum
    required: true
    enum: ["SAE", "non_SAE"]
  relatedness:
    type: enum
    required: true
    enum: ["definitely", "probably", "possibly", "unlikely", "not_related"]

output_schema:
  coding_id:
    type: string
  coded_term:
    type: object
    properties:
      pt_code: {type: string}
      pt_name: {type: string}
      hlt_code: {type: string}
      hlt_name: {type: string}
      soc_code: {type: string}
      soc_name: {type: string}
  confidence:
    type: number
    minimum: 0
    maximum: 1
  requires_review:
    type: boolean
```

#### 8.2.3 CONSENT_AUDIT Agent (知情同意审核)

```yaml
skill_name: ctms_consent_audit
version: "1.0"
agent_type: CONSENT_AUDIT
category: compliance
description: 审核知情同意过程的完整性和合规性

system_prompt: |
  你是一位临床试验知情同意审核专家。
  审核要点：
  - 知情同意版本是否为伦理批准的最新版本
  - 知情同意日期是否在入组日期之前
  - 签名是否完整（受试者、研究者）
  - 电子签名是否符合21 CFR Part 11要求

input_schema:
  subject_id:
    type: string
    required: true
  trial_id:
    type: string
    required: true
  site_id:
    type: string
    required: true

output_schema:
  audit_id:
    type: string
  consent_status:
    type: enum
    enum: ["valid", "requires_followup", "invalid", "partial"]
  checklist:
    type: object
  findings:
    type: array
  action_required:
    type: array
```

#### 8.2.4 SDV_ASSIST Agent (源数据核查辅助)

```yaml
skill_name: ctms_sdv_assist
version: "1.0"
agent_type: SDV_ASSIST
category: quality
description: 辅助CRA进行源数据核查

system_prompt: |
  你是一位经验丰富的临床监查专家。
  SDV关注点：
  - 数据一致性：CRF与源文件的一致性
  - 逻辑核查：日期逻辑、数值范围、异常值
  - 方案违背：入选/排除标准偏离

input_schema:
  subject_id:
    type: string
    required: true
  visit_id:
    type: string
    required: true
  form_id:
    type: string
    required: true
  crf_data:
    type: object
    required: true
  source_documents:
    type: array
    required: true

output_schema:
  sdv_result_id:
    type: string
  match_status:
    type: enum
    enum: ["match", "mismatch", "partial", "unverified"]
  discrepancies:
    type: array
  sdv_completeness:
    type: number
  recommendation:
    type: string
```

#### 8.2.5 SAE_ALERT Agent (SAE预警)

```yaml
skill_name: ctms_sae_alert
version: "1.0"
agent_type: SAE_ALERT
category: safety
description: 实时监控SAE报告，触发监管报告和预警

system_prompt: |
  你是一位药物警戒专家。
  报告时限：
  - 致死或危及生命的SUSAR：24小时内
  - 其他SUSAR：7/15天内
  - 中国：严重不良反应24小时快速报告

input_schema:
  ae_id:
    type: string
    required: true
  ae_data:
    type: object
    required: true
  subject_data:
    type: object
    required: true

output_schema:
  alert_id:
    type: string
  alert_type:
    type: enum
    enum: ["susar_fatal", "susar_life_threatening", "susar_other", "sar"]
  reporting_requirements:
    type: array
  notifications:
    type: array
  actions_required:
    type: array
```

#### 8.2.6 PROTOCOL_CHECK Agent (方案违背检测)

```yaml
skill_name: ctms_protocol_check
version: "1.0"
agent_type: PROTOCOL_CHECK
category: compliance
description: 自动检测和分类方案偏离/违背

system_prompt: |
  你是一位临床试验方案违背审核专家。
  偏离分类：
  - 重要偏离(Important PD)：可能影响受试者安全性或数据完整性
  - 一般偏离(Minor PD)：不影响安全性或数据完整性的偏离

input_schema:
  subject_id:
    type: string
    required: true
  deviation_type:
    type: enum
    required: true
    enum: ["inclusion_criteria", "exclusion_criteria", "icf_issue", "visit_window", "drug_dosing"]
  deviation_details:
    type: object
    required: true

output_schema:
  pd_id:
    type: string
  classification:
    type: enum
    enum: ["important", "minor"]
  severity:
    type: enum
    enum: ["critical", "major", "minor"]
  impact_assessment:
    type: object
  corrective_action:
    type: string
  preventive_action:
    type: string
  reporting_required:
    type: boolean
```

#### 8.2.7 LAB_NORMALIZATION Agent (实验室数据标准化)

```yaml
skill_name: ctms_lab_normalize
version: "1.0"
agent_type: LAB_NORMALIZATION
category: data_management
description: 标准化实验室检测数据

system_prompt: |
  你是一位实验室数据标准化专家。
  任务：
  1. 单位转换：将不同单位的检测值统一
  2. 参考范围应用：判断异常
  3. CTCAE分级：不良事件分级

input_schema:
  lab_data:
    type: array
    required: true
  subject_info:
    type: object
    required: true

output_schema:
  normalized_data:
    type: array
  conversion_notes:
    type: array
  data_quality_issues:
    type: array
```

#### 8.2.8 DATA_CLEANING Agent (数据清理)

```yaml
skill_name: ctms_data_cleaning
version: "1.0"
agent_type: DATA_CLEANING
category: data_management
description: 自动执行数据清理逻辑

system_prompt: |
  你是一位数据管理专家。
  清理规则类别：
  1. 编辑核查：数值范围、日期逻辑
  2. 一致性核查：跨表单数据一致性
  3. 完整性核查：必填字段、访视完成
  质疑类型：N(需确认)、Q(需澄清)、CL(需更正)

input_schema:
  trial_id:
    type: string
    required: true
  cleaning_scope:
    type: enum
    required: true
    enum: ["all", "subject", "visit", "form"]

output_schema:
  cleaning_report_id:
    type: string
  queries_generated:
    type: array
  summary:
    type: object
  recommendations:
    type: array
```

#### 8.2.9 QM_REPORT Agent (质量报告生成)

```yaml
skill_name: ctms_qm_report
version: "1.0"
agent_type: QM_REPORT
category: quality_management
description: 生成临床试验质量报告

system_prompt: |
  你是一位临床试验质量管理专家。
  报告类型：
  1. 试验层面质量报告
  2. 中心层面质量报告
  3. CRA绩效报告
  4. 数据质量趋势报告

input_schema:
  report_type:
    type: enum
    required: true
    enum: ["trial_overall", "site_performance", "cra_metrics", "data_quality"]
  trial_id:
    type: string
    required: true
  date_range:
    type: object

output_schema:
  report_id:
    type: string
  executive_summary:
    type: string
  kpis:
    type: array
  findings:
    type: array
  charts:
    type: array
```

#### 8.2.10 WORK_HOUR_SUGGEST Agent (工时智能建议)

```yaml
skill_name: ctms_workhour_suggest
version: "1.0"
agent_type: WORK_HOUR_SUGGEST
category: resource_management
description: 智能估算和优化工时分配

system_prompt: |
  你是一位临床试验资源管理专家。
  任务：
  1. 基于历史数据估算项目所需工时
  2. 识别工时异常和风险
  3. 提供工时优化建议

input_schema:
  project_id:
    type: string
    required: true
  current_phase:
    type: enum
    required: true
    enum: ["preparation", "startup", "execution", "closeout"]
  work_hours_actual:
    type: object
    required: true
  enrollment_progress:
    type: number

output_schema:
  analysis_id:
    type: string
  utilization_rate:
    type: number
  variance_analysis:
    type: array
  forecast:
    type: object
  risk_alerts:
    type: array
  optimization_suggestions:
    type: array
```

---

## 9. 数据库设计

### 9.1 数据库连接信息

```yaml
# PostgreSQL 配置 (主业务库)
postgresql:
  host: localhost
  port: 5432
  database: ctms_edc
  username: postgres
  password: root@123
  schema: public

# MySQL 配置 (历史归档库)
mysql:
  host: localhost
  port: 3306
  database: ctms_archive
  username: root
  password: root@123
  charset: utf8mb4
```

### 9.2 PostgreSQL 核心表设计

#### 表1: 组织机构表

```sql
CREATE TABLE organizations (
    org_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    org_code VARCHAR(50) UNIQUE NOT NULL,
    org_name VARCHAR(200) NOT NULL,
    org_type VARCHAR(20) NOT NULL CHECK (org_type IN ('sponsor', 'cro', 'site', 'vendor')),
    parent_org_id VARCHAR(36),
    contact_person VARCHAR(100),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(100),
    address TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_org_parent FOREIGN KEY (parent_org_id) REFERENCES organizations(org_id)
);
```

#### 表2: 用户表

```sql
CREATE TABLE users (
    user_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(50),
    employee_id VARCHAR(50),
    full_name VARCHAR(100) NOT NULL,
    title VARCHAR(100),
    department VARCHAR(100),
    org_id VARCHAR(36) NOT NULL,
    user_type VARCHAR(20) NOT NULL CHECK (user_type IN ('internal', 'external')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'locked')),
    mfa_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_user_org FOREIGN KEY (org_id) REFERENCES organizations(org_id)
);
```

#### 表3: 角色表

```sql
CREATE TABLE roles (
    role_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    role_code VARCHAR(50) UNIQUE NOT NULL,
    role_name VARCHAR(100) NOT NULL,
    role_name_en VARCHAR(100),
    description TEXT,
    role_level VARCHAR(20) DEFAULT 'project' CHECK (role_level IN ('system', 'org', 'project', 'site')),
    is_system_role BOOLEAN DEFAULT FALSE,
    permissions JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE
);

-- 预定义角色
INSERT INTO roles (role_id, role_code, role_name, role_name_en, description, role_level, is_system_role) VALUES
('role-sponsor', 'SPONSOR', '申办方', 'Sponsor', '临床试验发起方', 'org', TRUE),
('role-pi', 'PI', '主要研究者', 'Principal Investigator', '试验中心负责人', 'site', TRUE),
('role-sub-i', 'SUB_I', '次要研究者', 'Sub-Investigator', '协助PI的研究者', 'site', TRUE),
('role-pm', 'PM', '项目经理', 'Project Manager', 'CRO项目负责人', 'project', TRUE),
('role-cra', 'CRA', '临床监查员', 'Clinical Research Associate', '负责监查的研究人员', 'project', TRUE),
('role-crc', 'CRC', '临床协调员', 'Clinical Research Coordinator', '协助研究者日常事务', 'site', TRUE),
('role-mm', 'MM', '医学监查员', 'Medical Monitor', '医学审核人员', 'project', TRUE),
('role-dm', 'DM', '数据管理员', 'Data Manager', '数据管理人员', 'project', TRUE),
('role-super-admin', 'SUPER_ADMIN', '超级管理员', 'System Administrator', '系统管理员', 'system', TRUE);
```

#### 表4: 用户角色关系表

```sql
CREATE TABLE user_roles (
    user_role_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    role_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36),
    site_id VARCHAR(36),
    org_id VARCHAR(36),
    effective_start_date DATE,
    effective_end_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'expired')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36),
    CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_ur_role FOREIGN KEY (role_id) REFERENCES roles(role_id),
    UNIQUE (user_id, role_id, project_id, site_id)
);
```

#### 表5: 临床试验项目表

```sql
CREATE TABLE projects (
    project_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(500) NOT NULL,
    project_type VARCHAR(20) NOT NULL CHECK (project_type IN ('RCT', 'RWE', 'IIT', 'BE')),
    therapeutic_area VARCHAR(100),
    indication VARCHAR(200),
    trial_phase VARCHAR(10) CHECK (trial_phase IN ('I', 'II', 'III', 'IV')),
    blinding_method VARCHAR(20) CHECK (blinding_method IN ('open', 'single', 'double', 'triple')),
    sponsor_org_id VARCHAR(36) NOT NULL,
    cro_org_id VARCHAR(36),
    pm_user_id VARCHAR(36),
    planned_start_date DATE,
    planned_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    target_enrollment INTEGER,
    number_of_sites INTEGER,
    project_status VARCHAR(20) DEFAULT 'draft' CHECK (project_status IN ('draft', 'submitted', 'approved', 'in_progress', 'suspended', 'completed', 'archived')),
    protocol_version VARCHAR(20),
    total_budget DECIMAL(15,2),
    budget_currency VARCHAR(10) DEFAULT 'CNY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(36),
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_project_sponsor FOREIGN KEY (sponsor_org_id) REFERENCES organizations(org_id)
);
```

#### 表6: 项目里程碑表

```sql
CREATE TABLE project_milestones (
    milestone_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    milestone_code VARCHAR(20) NOT NULL,
    milestone_name VARCHAR(200) NOT NULL,
    milestone_type VARCHAR(20) CHECK (milestone_type IN ('regulatory', 'operational', 'financial', 'quality')),
    planned_date DATE,
    actual_date DATE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'delayed', 'cancelled')),
    responsible_user_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ms_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表7: 研究中心表

```sql
CREATE TABLE trial_sites (
    site_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    site_code VARCHAR(50) NOT NULL,
    site_name VARCHAR(200) NOT NULL,
    pi_name VARCHAR(100),
    pi_user_id VARCHAR(36),
    address TEXT,
    city VARCHAR(100),
    province VARCHAR(100),
    country VARCHAR(50) DEFAULT '中国',
    target_enrollment INTEGER,
    actual_enrollment INTEGER DEFAULT 0,
    site_status VARCHAR(20) DEFAULT 'pending' CHECK (site_status IN ('pending', 'approved', 'initiated', 'in_progress', 'suspended', 'closed')),
    approval_date DATE,
    site_initiation_date DATE,
    site_fee DECIMAL(15,2),
    per_subject_fee DECIMAL(15,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_site_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表8: 受试者表

```sql
CREATE TABLE subjects (
    subject_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    site_id VARCHAR(36) NOT NULL,
    subject_code VARCHAR(50) NOT NULL,
    randomization_number VARCHAR(50),
    treatment_group VARCHAR(50),
    sex VARCHAR(10) CHECK (sex IN ('male', 'female')),
    birth_date DATE,
    age_at_enrollment INTEGER,
    icf_version VARCHAR(20),
    icf_signed_date DATE,
    enrollment_status VARCHAR(20) DEFAULT 'screened' CHECK (enrollment_status IN ('screened', 'randomized', 'in_treatment', 'completed', 'withdrawn', 'screen_failed')),
    randomization_date DATE,
    first_dose_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_subject_project FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CONSTRAINT fk_subject_site FOREIGN KEY (site_id) REFERENCES trial_sites(site_id),
    UNIQUE (project_id, site_id, subject_code)
);
```

#### 表9: 访视表

```sql
CREATE TABLE subject_visits (
    visit_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    subject_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    visit_code VARCHAR(20) NOT NULL,
    visit_name VARCHAR(100) NOT NULL,
    visit_window_start INTEGER,
    visit_window_end INTEGER,
    target_date DATE,
    actual_date DATE,
    visit_status VARCHAR(20) DEFAULT 'scheduled' CHECK (visit_status IN ('scheduled', 'not_done', 'completed', 'partial', 'early_termination')),
    sdv_required BOOLEAN DEFAULT TRUE,
    sdv_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_visit_subject FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);
```

#### 表10: CRF表单定义表

```sql
CREATE TABLE crf_forms (
    form_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    form_code VARCHAR(50) NOT NULL,
    form_name VARCHAR(200) NOT NULL,
    form_group VARCHAR(100),
    is_repeatable BOOLEAN DEFAULT FALSE,
    version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'approved', 'locked')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_form_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表11: CRF字段定义表

```sql
CREATE TABLE crf_fields (
    field_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    form_id VARCHAR(36) NOT NULL,
    field_code VARCHAR(100) NOT NULL,
    field_name VARCHAR(200) NOT NULL,
    field_type VARCHAR(30) NOT NULL CHECK (field_type IN ('text', 'number', 'date', 'datetime', 'select', 'radio', 'checkbox', 'textarea', 'esig', 'file')),
    required BOOLEAN DEFAULT FALSE,
    min_value DECIMAL,
    max_value DECIMAL,
    options JSONB,
    default_value VARCHAR(200),
    sdv_required BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_field_form FOREIGN KEY (form_id) REFERENCES crf_forms(form_id)
);
```

#### 表12: CRF数据表

```sql
CREATE TABLE crf_data (
    data_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    subject_id VARCHAR(36) NOT NULL,
    visit_id VARCHAR(36),
    form_id VARCHAR(36) NOT NULL,
    field_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    value_text TEXT,
    value_number DECIMAL,
    value_date DATE,
    value_coded VARCHAR(50),
    status VARCHAR(20) DEFAULT 'entered' CHECK (status IN ('entered', 'verified', 'locked', 'frozen')),
    entered_by VARCHAR(36) NOT NULL,
    entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(36),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_data_subject FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    CONSTRAINT fk_data_form FOREIGN KEY (form_id) REFERENCES crf_forms(form_id),
    UNIQUE (subject_id, visit_id, field_id)
);
```

#### 表13: 数据质疑表

```sql
CREATE TABLE data_queries (
    query_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    subject_id VARCHAR(36),
    visit_id VARCHAR(36),
    data_id VARCHAR(36),
    query_number VARCHAR(50),
    query_type VARCHAR(10) CHECK (query_type IN ('N', 'Q', 'CL')),
    query_text TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'answered', 'closed', 'cancelled')),
    response_text TEXT,
    response_by VARCHAR(36),
    response_at TIMESTAMP,
    raised_by VARCHAR(36) NOT NULL,
    raised_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_by VARCHAR(36),
    closed_at TIMESTAMP,
    CONSTRAINT fk_query_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表14: 不良事件表

```sql
CREATE TABLE adverse_events (
    ae_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    subject_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    ae_number INTEGER,
    ae_description TEXT,
    onset_date DATE NOT NULL,
    ongoing BOOLEAN DEFAULT TRUE,
    end_date DATE,
    is_serious BOOLEAN DEFAULT FALSE,
    meddra_version VARCHAR(20),
    pt_code VARCHAR(20),
    pt_name VARCHAR(200),
    outcome VARCHAR(30) CHECK (outcome IN ('recovered', 'recovering', 'not_recovered', 'fatal')),
    relatedness VARCHAR(20) CHECK (relatedness IN ('definitely', 'probably', 'possibly', 'unlikely', 'not_related')),
    severity VARCHAR(10) CHECK (severity IN ('mild', 'moderate', 'severe')),
    ctcae_grade INTEGER CHECK (ctcae_grade BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ae_subject FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);
```

#### 表15: SAE严重不良事件表

```sql
CREATE TABLE sae_reports (
    sae_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    ae_id VARCHAR(36) NOT NULL,
    subject_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36) NOT NULL,
    sae_number VARCHAR(50) UNIQUE,
    initial_report_date DATE NOT NULL,
    reporter_name VARCHAR(100),
    sae_description TEXT,
    outcome VARCHAR(30),
    causality VARCHAR(20),
    report_status VARCHAR(20) DEFAULT 'initial' CHECK (report_status IN ('initial', 'followup', 'final', 'closed')),
    susar BOOLEAN DEFAULT FALSE,
    susar_report_date DATE,
    medical_review_by VARCHAR(36),
    medical_review_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36),
    CONSTRAINT fk_sae_ae FOREIGN KEY (ae_id) REFERENCES adverse_events(ae_id)
);
```

#### 表16: 文档表

```sql
CREATE TABLE documents (
    doc_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36),
    doc_code VARCHAR(100),
    doc_name VARCHAR(500) NOT NULL,
    doc_type VARCHAR(50) CHECK (doc_type IN ('protocol', 'icf', 'crf', 'sap', 'csr', 'ib', 'correspondence', 'approval_letter', 'contract')),
    version VARCHAR(20) NOT NULL,
    version_status VARCHAR(20) DEFAULT 'draft' CHECK (version_status IN ('draft', 'in_review', 'approved', 'effective', 'superseded')),
    file_name VARCHAR(255),
    file_path VARCHAR(500),
    file_hash VARCHAR(64),
    tmf_category VARCHAR(100),
    tmf_section VARCHAR(100),
    access_level VARCHAR(20) DEFAULT 'project',
    esig_required BOOLEAN DEFAULT FALSE,
    esigned BOOLEAN DEFAULT FALSE,
    esig_records JSONB DEFAULT '[]',
    ai_review_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_doc_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表17: 审批流程定义表

```sql
CREATE TABLE approval_workflows (
    workflow_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workflow_code VARCHAR(50) UNIQUE NOT NULL,
    workflow_name VARCHAR(200) NOT NULL,
    workflow_type VARCHAR(50) NOT NULL CHECK (workflow_type IN ('document', 'contract', 'expense', 'work_hour', 'database_lock', 'deviation')),
    project_id VARCHAR(36),
    is_template BOOLEAN DEFAULT FALSE,
    stages JSONB NOT NULL DEFAULT '[]',
    allow_delegate BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 表18: 审批实例表

```sql
CREATE TABLE approval_instances (
    instance_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    workflow_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36),
    business_type VARCHAR(50) NOT NULL,
    business_id VARCHAR(36) NOT NULL,
    business_summary VARCHAR(500),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('draft', 'pending', 'approved', 'rejected', 'cancelled')),
    initiated_by VARCHAR(36) NOT NULL,
    initiated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_by VARCHAR(36),
    completed_at TIMESTAMP,
    priority VARCHAR(10) DEFAULT 'normal',
    CONSTRAINT fk_inst_wf FOREIGN KEY (workflow_id) REFERENCES approval_workflows(workflow_id)
);
```

#### 表19: 工时分类表

```sql
CREATE TABLE work_hour_categories (
    category_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    category_code VARCHAR(20) UNIQUE NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    default_approver_type VARCHAR(20) CHECK (approver_type IN ('user', 'role', 'auto')),
    default_approver_id VARCHAR(36),
    is_billable BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active',
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO work_hour_categories (category_code, category_name, description, default_approver_type, is_billable) VALUES
('TRV', '临床监查', '现场/远程监查访视', 'role-pm', TRUE),
('PMO', '项目管理', '项目管理活动', 'role-sponsor', TRUE),
('DMO', '数据管理', '数据管理活动', 'role-pm', TRUE),
('MEO', '医学监查', '医学审核活动', 'role-sponsor', TRUE),
('STA', '统计分析', '统计分析活动', 'role-pm', TRUE),
('DOC', '文档工作', '文档编写审阅', 'role-pm', TRUE),
('TRN', '培训会议', '培训和会议', 'role-pm', FALSE),
('TRF', '差旅时间', '差旅途时间', 'role-pm', FALSE),
('OTH', '其他', '其他活动', 'role-pm', FALSE);
```

#### 表20: 工时记录表

```sql
CREATE TABLE work_hour_records (
    record_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    site_id VARCHAR(36),
    user_id VARCHAR(36) NOT NULL,
    org_id VARCHAR(36) NOT NULL,
    work_date DATE NOT NULL,
    hours DECIMAL(5,2) NOT NULL CHECK (hours > 0 AND hours <= 24),
    category_id VARCHAR(36) NOT NULL,
    category_code VARCHAR(20),
    work_description TEXT,
    location VARCHAR(100),
    is_travel BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'submitted', 'approved', 'rejected', 'locked')),
    approval_instance_id VARCHAR(36),
    approver_id VARCHAR(36),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(36),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_whr_project FOREIGN KEY (project_id) REFERENCES projects(project_id),
    CONSTRAINT fk_whr_user FOREIGN KEY (user_id) REFERENCES users(user_id),
    CONSTRAINT fk_whr_category FOREIGN KEY (category_id) REFERENCES work_hour_categories(category_id)
);
```

#### 表21: 工时预算表

```sql
CREATE TABLE work_hour_budgets (
    budget_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    role_code VARCHAR(50),
    planned_hours DECIMAL(10,2) NOT NULL,
    planned_rate DECIMAL(10,2),
    planned_amount DECIMAL(15,2),
    actual_hours DECIMAL(10,2) DEFAULT 0,
    actual_amount DECIMAL(15,2) DEFAULT 0,
    budget_status VARCHAR(20) DEFAULT 'approved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_whb_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表22: 收入项目表

```sql
CREATE TABLE income_items (
    income_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    income_code VARCHAR(50) NOT NULL,
    income_name VARCHAR(200) NOT NULL,
    income_type VARCHAR(30) CHECK (income_type IN ('fixed_service', 'hourly', 'per_subject', 'milestone', 'change_order')),
    billing_rule VARCHAR(30),
    amount DECIMAL(15,2),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_income_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表23: 支出项目表

```sql
CREATE TABLE expense_items (
    expense_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    expense_code VARCHAR(50) NOT NULL,
    expense_name VARCHAR(200) NOT NULL,
    expense_type VARCHAR(30) CHECK (expense_type IN ('personnel', 'site_fee', 'lab', 'drug', 'third_party', 'travel', 'office')),
    cost_type VARCHAR(20) CHECK (cost_type IN ('direct', 'indirect')),
    budget_amount DECIMAL(15,2),
    spent_amount DECIMAL(15,2) DEFAULT 0,
    approval_required BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_expense_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表24: 支出记录表

```sql
CREATE TABLE expense_records (
    expense_record_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    record_number VARCHAR(50) UNIQUE NOT NULL,
    record_date DATE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    expense_type VARCHAR(30),
    description TEXT,
    vendor_name VARCHAR(200),
    invoice_number VARCHAR(100),
    approval_instance_id VARCHAR(36),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'approved', 'rejected', 'paid')),
    payment_date DATE,
    created_by VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_er_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表25: 发票表

```sql
CREATE TABLE invoices (
    invoice_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36) NOT NULL,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    invoice_type VARCHAR(20) CHECK (invoice_type IN ('income', 'expense')),
    amount DECIMAL(15,2) NOT NULL,
    tax_amount DECIMAL(15,2),
    total_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    issuer_name VARCHAR(200),
    recipient_name VARCHAR(200),
    invoice_date DATE NOT NULL,
    due_date DATE,
    paid_date DATE,
    status VARCHAR(20) DEFAULT 'issued' CHECK (status IN ('draft', 'issued', 'sent', 'paid', 'overdue', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 表26: 审计日志表 (符合21 CFR Part 11)

```sql
CREATE TABLE audit_logs (
    log_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    project_id VARCHAR(36),
    event_type VARCHAR(50) NOT NULL,
    event_category VARCHAR(30) CHECK (event_category IN ('create', 'update', 'delete', 'view', 'login', 'logout', 'esig', 'approval')),
    table_name VARCHAR(100),
    record_id VARCHAR(36),
    record_identifier VARCHAR(200),
    action VARCHAR(100) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    changed_fields JSONB DEFAULT '[]',
    user_id VARCHAR(36),
    username VARCHAR(100),
    user_role VARCHAR(50),
    ip_address VARCHAR(50),
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    previous_log_hash VARCHAR(64),
    current_log_hash VARCHAR(64),
    session_id VARCHAR(50),
    regulatory_requirement VARCHAR(100),
    CONSTRAINT fk_audit_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE INDEX idx_audit_project ON audit_logs(project_id);
CREATE INDEX idx_audit_table ON audit_logs(table_name, record_id);
CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(event_timestamp);
```

#### 表27: 电子签名记录表

```sql
CREATE TABLE electronic_signatures (
    esig_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    signature_type VARCHAR(20) CHECK (signature_type IN ('approve', 'reject', 'verify', 'submit', 'confirm')),
    signer_id VARCHAR(36) NOT NULL,
    signer_name VARCHAR(100) NOT NULL,
    signer_role VARCHAR(50),
    meaning VARCHAR(200) NOT NULL,
    reason VARCHAR(500),
    signature_hash VARCHAR(64) NOT NULL,
    signature_algorithm VARCHAR(20) DEFAULT 'SHA256withRSA',
    certificate_id VARCHAR(100),
    signature_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    project_id VARCHAR(36),
    document_id VARCHAR(36),
    data_record_id VARCHAR(36),
    verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    CONSTRAINT fk_esig_project FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
```

#### 表28: 消息模板表

```sql
CREATE TABLE notification_templates (
    template_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    template_code VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    channel VARCHAR(20) CHECK (channel IN ('system', 'email', 'sms', 'wechat', 'wecom')),
    title_template VARCHAR(500),
    content_template TEXT,
    variables JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    priority VARCHAR(10) DEFAULT 'normal',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 表29: 消息通知记录表

```sql
CREATE TABLE notification_records (
    notification_id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    template_id VARCHAR(36),
    recipient_user_id VARCHAR(36) NOT NULL,
    recipient_name VARCHAR(100),
    recipient_email VARCHAR(100),
    recipient_phone VARCHAR(50),
    wechat_openid VARCHAR(100),
    wecom_userid VARCHAR(100),
    channel VARCHAR(20) NOT NULL,
    title VARCHAR(500),
    content TEXT,
    variables JSONB DEFAULT '[]',
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'read', 'failed')),
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    read_at TIMESTAMP,
    error_code VARCHAR(50),
    error_message VARCHAR(500),
    business_type VARCHAR(50),
    business_id VARCHAR(36),
    project_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 9.3 MySQL 归档表设计

```sql
-- MySQL: 历史数据归档表

CREATE TABLE archive_subjects (
    archive_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(36) NOT NULL,
    site_id VARCHAR(36) NOT NULL,
    subject_code VARCHAR(50) NOT NULL,
    archive_date DATE NOT NULL,
    archive_reason VARCHAR(50) NOT NULL,
    subject_data JSON NOT NULL,
    visit_data JSON,
    ae_data JSON,
    archived_by VARCHAR(36) NOT NULL,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_archive_project (project_id),
    INDEX idx_archive_date (archive_date),
    UNIQUE KEY uk_archive_subject (project_id, site_id, subject_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE archive_projects (
    archive_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    project_id VARCHAR(36) UNIQUE NOT NULL,
    project_code VARCHAR(50) NOT NULL,
    archive_date DATE NOT NULL,
    project_summary JSON NOT NULL,
    financial_summary JSON,
    archived_by VARCHAR(36) NOT NULL,
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_archive_date (archive_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE archive_audit_logs (
    archive_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    archive_batch_id VARCHAR(36) NOT NULL,
    log_id VARCHAR(36) NOT NULL,
    project_id VARCHAR(36),
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(36),
    event_timestamp TIMESTAMP NOT NULL,
    action VARCHAR(100) NOT NULL,
    current_log_hash VARCHAR(64),
    archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_archive_batch (archive_batch_id),
    INDEX idx_archive_timestamp (event_timestamp),
    UNIQUE KEY uk_archive_log (log_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 10. 文档管理与协作

### 10.1 TMF文档结构

```json
{
  "tmf_structure": {
    "section_1": {"name": "试验主文件管理", "subsections": {"1.01": "试验方案和修正案", "1.02": "知情同意书模板", "1.03": "研究者手册"}},
    "section_2": {"name": "伦理审批", "subsections": {"2.01": "伦理委员会批件", "2.02": "研究者资质文件"}},
    "section_3": {"name": "研究者文件", "subsections": {"3.01": "研究者简历", "3.02": "实验室资质", "3.03": "中心授权表"}},
    "section_4": {"name": "合同与财务", "subsections": {"4.01": "试验合同", "4.02": "财务披露"}},
    "section_5": {"name": "监查与质量", "subsections": {"5.01": "监查访视报告", "5.02": "审计报告"}}
  }
}
```

### 10.2 协作编辑架构 (OT算法)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         实时协作编辑架构 (Operational Transform)              │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  用户A          用户B          用户C                                          │
│    │              │              │                                           │
│    ▼              ▼              ▼                                           │
│  ┌─────┐       ┌─────┐       ┌─────┐                                        │
│  │编辑 │       │编辑 │       │编辑 │                                        │
│  │器   │       │器   │       │器   │                                        │
│  └──┬──┘       └──┬──┘       └──┬──┘                                        │
│     └──────────────┼──────────────┘                                           │
│                    │                                                          │
│                    ▼                                                          │
│  ┌────────────────────────────────────────┐                                 │
│  │           OT Server (协作服务器)        │                                 │
│  │  操作转换 | 版本控制 | 冲突解决          │                                 │
│  └────────────────────────────────────────┘                                 │
│                                                                              │
│  操作类型: insert(position, text) | delete(position) | retain(count)        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. 流程审批管理

### 11.1 审批流程类型

| 流程类型 | 描述 | 审批节点 |
|---------|------|---------|
| **文档审批** | 方案、ICF、CRF等文档审核 | 拟定→医学审核→合规审核→批准 |
| **合同审批** | 试验合同、变更合同审批 | 拟定→法务→财务→Sponsor批准 |
| **费用审批** | 费用报销、预付款审批 | 申请人→PM→财务→Sponsor |
| **工时审批** | 工时记录审核 | 员工→直线经理→PM |
| **数据库锁定** | 数据库锁定申请审批 | DM→MM→Sponsor批准 |
| **方案违背** | 重要方案违背审批 | CRA→MM→Sponsor |
| **SAE报告** | SAE/SUSAR报告审批 | CRC→PI→MM→Sponsor |
| **解盲审批** | 紧急解盲申请审批 | CRA→MM→Sponsor→批准 |

---

## 12. 合规体系设计

### 12.1 合规检查清单

| 合规要求 | 实现方式 | 检查点 |
|---------|---------|--------|
| **RCT设计** | IWRS随机化 | 随机分配隐藏、盲法维护 |
| **RWE研究** | 数据来源标注 | 回顾性数据标记、数据质量说明 |
| **ICH GCP E6(R2)** | 流程标准化 | 试验流程、伦理审查、知情同意 |
| **FDA 21 CFR Part 11** | 电子签名/审计 | 数字证书、审计追踪、版本控制 |
| **GDPR** | 数据保护 | 加密存储、访问控制、数据删除权 |
| **HIPAA** | PHI保护 | 脱敏处理、加密传输、BAA |
| **ISO 27001** | 信息安全 | 访问管理、日志审计、事件响应 |

### 12.2 ALCOA+数据完整性原则

| 原则 | 说明 | 系统实现 |
|-----|------|---------|
| **Attributable** 可归因 | 数据可追溯到操作者 | 用户ID强制关联、ESig |
| **Legible** 易读 | 数据清晰可读 | 标准化格式、字符编码 |
| **Contemporaneous** 同步 | 操作即时记录 | 时间戳服务器同步 |
| **Original** 原始 | 保留原始数据 | 审计日志、版本控制 |
| **Accurate** 准确 | 数据真实准确 | 编辑核查、自动验证 |
| **Complete** 完整 | 无数据遗漏 | 必填字段、完整性检查 |
| **Consistent** 一致 | 数据逻辑一致 | 跨表单核查、逻辑规则 |
| **Enduring** 持久 | 数据长期可读 | 标准化格式、备份恢复 |
| **Available** 可用 | 审计时可供查阅 | 快速检索、电子归档 |

---

## 13. 消息通知体系

### 13.1 微信/企微集成配置

```yaml
wechat_integration:
  # 企业微信
  enterprise_wechat:
    corp_id: ww_xxx
    agent_id: 1000001
    secret: xxx
    api_base: https://qyapi.weixin.qq.com
    
    features:
      - 消息推送
      - 应用免登
      - 部门同步
      - 审批回调
    
    message_templates:
      sae_alert:
        title: "【紧急】SAE预警"
        content: "受试者{subject_code}发生{ae_description}，请立即处理"
        urgency: immediate
      
      sdv_reminder:
        title: "【监查提醒】"
        content: "中心{site_name}有{visit_count}个待核查访视"
        urgency: normal
      
      approval_request:
        title: "【待审批】{workflow_name}"
        content: "{business_summary}"
        urgency: normal
```

### 13.2 通知触发规则

```json
{
  "notification_rules": [
    {"trigger": "SAE报告创建", "channels": ["wechat", "wecom", "sms"], "recipients": ["PI", "MM", "Sponsor_Medical"], "urgency": "immediate"},
    {"trigger": "数据质疑生成", "channels": ["wechat", "system"], "recipients": ["CRC", "PI"], "urgency": "normal"},
    {"trigger": "访视待SDV", "channels": ["wecom", "system"], "recipients": ["CRA"], "urgency": "normal"},
    {"trigger": "审批请求", "channels": ["wechat", "email"], "recipients": ["Approver"], "urgency": "normal"},
    {"trigger": "审批超时提醒", "channels": ["system"], "recipients": ["Approver"], "urgency": "high"},
    {"trigger": "里程碑完成", "channels": ["wechat", "system"], "recipients": ["Sponsor", "PM"], "urgency": "normal"}
  ]
}
```

---

## 14. 非功能需求

### 14.1 性能指标

| 指标 | 要求 |
|-----|------|
| 系统响应时间 | P95 < 2秒 |
| 并发用户数 | 支持500+同时在线 |
| 数据处理能力 | 支持10000+受试者/项目 |
| 可用性 | 99.9% (每月停机 < 8.7小时) |
| 数据备份 | 每日增量备份，每周全量备份 |

### 14.2 安全要求

| 要求 | 实现 |
|-----|------|
| 传输加密 | TLS 1.3 |
| 存储加密 | AES-256 |
| 访问控制 | RBAC + ABAC |
| 审计日志 | 完整记录，不可篡改 |
| 会话管理 | JWT + Refresh Token |
| 密码策略 | 复杂度要求，定期更换 |

---

## 15. 版本路线图

### 15.1 产品路线图

| 阶段 | 时间 | 功能范围 |
|------|------|---------|
| **MVP** | Q1 2026 | CTMS基础 + EDC基础 + 用户管理 |
| **V1.0** | Q2 2026 | IWRS + 工时管理 + 收支管理 |
| **V2.0** | Q3 2026 | AI Agent集成 + 协作编辑 + 企微集成 |
| **V3.0** | Q4 2026 | 高级分析 + 移动端 + API开放平台 |

### 15.2 AI功能路线图

| 功能 | 上线时间 | Agent |
|------|---------|-------|
| 文档GCP审核 | V2.0 | DOC_REVIEW |
| AE MedDRA编码 | V1.0 | AE_CODING |
| 知情同意审核 | V2.0 | CONSENT_AUDIT |
| SDV辅助 | V2.0 | SDV_ASSIST |
| SAE预警 | V1.0 | SAE_ALERT |
| 方案违背检测 | V2.0 | PROTOCOL_CHECK |
| 实验室标准化 | V1.0 | LAB_NORMALIZATION |
| 数据清理 | V1.0 | DATA_CLEANING |
| 质量报告 | V2.0 | QM_REPORT |
| 工时建议 | V2.0 | WORK_HOUR_SUGGEST |

---

**文档结束**

*本文档为CTMS+EDC临床试验管理系统完整产品设计规格书 v3.0*
*最后更新：2026-05-06*
