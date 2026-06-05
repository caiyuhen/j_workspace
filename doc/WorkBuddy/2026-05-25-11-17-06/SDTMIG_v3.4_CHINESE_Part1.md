# CDISC 研究数据汇总模型实施指南：人体临床试验

## 版本 3.4 (最终版)

**由 CDISC 提交数据标准团队开发**

---

## 修订历史

| 日期 | 版本 | 变更摘要 |
|------|------|----------|
| 2022-07-21 | 3.4 Final | 重新发布 PDF，更新图片以提高清晰度 |
| 2021-11-29 | 3.4 Final | 参见附录 E |
| 2018-02-20 | 3.3 Final | 参见附录 E |
| 2013-11-26 | 3.2 Final | 参见附录 E |
| 2012-07-16 | 3.1.3 Final | 参见 SDTMIG v3.2 |
| 2008-11-12 | 3.1.2 Final | 参见 SDTMIG v3.2 |
| 2005-08-26 | 3.1.1 Final | 参见 SDTMIG v3.2 |
| 2004-07-14 | 3.1 | 参见 SDTMIG v3.2 |

> 参见附录 F 了解陈述和保证、责任限制及免责声明。

---

## 读者须知

- 本实施指南对应 CDISC 研究数据汇总模型 (SDTM) 第 2.0 版的人体临床试验实施指南。

---

## 目录

### 1 引言 (Introduction)
- 1.1 目的 (Purpose)
- 1.2 本文档的组织结构 (Organization of this Document)
- 1.3 与之前 CDISC 文档的关系 (Relationship to Prior CDISC Documents)
- 1.4 如何阅读本实施指南 (How to Read this Implementation Guide)
  - 1.4.1 如何阅读域规范 (How to Read a Domain Specification)
- 1.5 已知问题 (Known Issues)

### 2 SDTM 基础 (Fundamentals of the SDTM)
- 2.1 观测与变量 (Observations and Variables)
- 2.2 数据集与域 (Datasets and Domains)
- 2.3 通用观测类别 (The General Observation Classes)
- 2.4 非通用观测类别域的数据集 (Datasets Other than General Observation Class Domains)
- 2.5 SDTM 标准域模型 (The SDTM Standard Domain Models)
- 2.6 创建新域 (Creating a New Domain)
- 2.7 SDTMIG 中不允许的 SDTM 变量 (SDTM Variables Not Allowed in the SDTMIG)

### 3 以标准格式提交数据 (Submitting Data in Standard Format)
- 3.1 数据集内容和属性的标准元数据 (Standard Metadata for Dataset Contents and Attributes)
- 3.2 在监管提交中使用 CDISC 域模型 - 数据集元数据 (Using the CDISC Domain Models in Regulatory Submissions – Dataset Metadata)
  - 3.2.1 数据集级元数据 (Dataset-level Metadata)
    - 3.2.1.1 主键 (Primary Keys)
    - 3.2.1.2 CDISC 提交值级元数据 (CDISC Submission Value-level Metadata)
  - 3.2.2 一致性 (Conformance)

### 4 域模型的假设 (Assumptions for Domain Models)
- 4.1 通用域假设 (General Domain Assumptions)
- 4.2 通用变量假设 (General Variable Assumptions)
- 4.3 编码和控制术语假设 (Coding and Controlled Terminology Assumptions)
- 4.4 实际和相对时间假设 (Actual and Relative Time Assumptions)
- 4.5 其他假设 (Other Assumptions)

---

## 第 1 章 引言

### 1.1 目的

本实施指南为人体临床试验提供了 CDISC 研究数据汇总模型 (Study Data Tabulation Model, SDTM) 的具体实现指导。SDTM 定义了用于向监管机构 (如美国 FDA 和日本 PMDA) 提交临床试验数据时的标准数据集结构。

### 1.2 本文档的组织结构

本文档包含以下主要部分:

1. **引言** - 介绍 SDTM 的背景、目的和使用方法
2. **SDTM 基础** - 解释 SDTM 的核心概念和原理
3. **以标准格式提交数据** - 说明如何准备和提交符合标准的数据
4. **域模型的假设** - 定义应用 SDTM 时的基本假设和规则
5. **标准域规格说明** - 详细定义每个标准域的结构和要求
6. **附录** - 补充信息和参考材料

### 1.3 与之前 CDISC 文档的关系

SDTM 是 CDISC 数据标准体系的重要组成部分，与其他 CDISC 标准的关系如下:

- **CDASH (Clinical Data Acquisition Standards Harmonization)**: 定义病例报告表 (CRF) 的设计标准
- **SDTM (Study Data Tabulation Model)**: 定义汇总数据的标准格式 (即本指南涵盖的内容)
- **ADaM (Analysis Data Model)**: 定义分析数据集的标准
- **CDISC Controlled Terminology**: 定义受控术语集

这些标准共同构成了从数据收集到分析提交的完整数据流。

### 1.4 如何阅读本实施指南

本指南为每个 SDTM 域提供了详细的规格说明。阅读时应注意以下几点:

1. **理解基本假设**: 第 4 章定义了对所有域适用的通用假设和规则
2. **参考域模型**: 每个域的规格说明都包含域模型图示
3. **注意变量要求**: 变量分为必需 (Required)、条件必需 (Conditionally Required) 和允许 (Permitted)
4. **遵循编码规则**: 使用 CDISC 受控术语集进行编码

#### 1.4.1 如何阅读域规格说明

每个域规格说明包含以下部分:

- **域概述**: 描述该域的用途和适用范围
- **域模型**: 图示展示域的结构和变量关系
- **变量定义表**: 列出所有变量的详细信息，包括:
  - 变量名 (Variable Name)
  - 标签 (Label)
  - 类型 (Type): 字符 (Character) 或数值 (Numeric)
  - 长度 (Length)
  - 必需性 (Requiredness): 必需/条件必需/允许
  - 控制格式/码表 (Controlled Format/Codelist)
  - 描述 (Description)
- **示例数据**: 展示该域的实际数据示例
- **特殊规则**: 该域特定的业务规则和要求

### 1.5 已知问题

本节列出当前版本中已知的限制和问题:

- 某些复杂研究设计可能需要创建自定义域
- 某些治疗领域的特殊数据可能需要扩展标准域
- 与某些监管机构的特定要求可能存在差异

---

*翻译说明*:
- 本翻译基于 SDTMIG v3.4 Final (2022-07-21 版本)
- 专业术语采用 CDISC 官方中文术语或行业通用译法
- 原文档页码标注在对应内容的开头

---

**下一步**: 继续翻译第 2 章"SDTM 基础"和后续章节...
