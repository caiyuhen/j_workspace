# CDASH 标准资源索引

## 基本信息

**CDASH** (CDISC Adapted for Clinical Research Health Services) 是 CDISC 组织制定的临床研究报告数据标准，用于规范临床试验数据采集。

### 版本历史
- **CDASH v1.1**: 当前广泛使用的版本
- **CDASHIG v2.0** (开发中): 将替代 v1.1，包含重大更新
- **CDASH Model v1.0** (开发中): 配套的数据模型

### 标准覆盖领域 (16 个域)
1. Demographics (人口统计学)
2. Informed Consent (知情同意)
3. Medical History (病史)
4. Current Medications (当前用药)
5. Intervention Start (干预开始)
6. Intervention End (干预结束)
7. Vital Signs (生命体征)
8. Height/Weight (身高体重)
9. Adverse Events (不良事件)
10. Serious Adverse Events (严重不良事件 - SAE)
11. Laboratory Tests (实验室检测)
12. Questionnaires (问卷)
13. Device Use (设备使用)
14. Pregnancy (妊娠)
15. Device Adverse Events (器械不良事件)
16. Protocol Deviations (方案偏离)

---

## 官方资源下载

### 1. CDASH v1.1 标准文档
- **来源**: CDISC 官方网站 (https://www.cdisc.org/standards/foundational/cdash)
- **内容**: 16 个核心数据域的推荐数据收集字段
- **特点**: 
  - 包含实施指南
  - 最佳实践建议
  - 监管要求参考
  - CDASH 到 SDTM 映射

### 2. CDASH SAE Supplement v1.0
- **用途**: 扩展 AE 域采集严重不良事件信息
- **目的**: 支持生成 E2B 格式的个例安全报告 (ICSR)
- **监管机构**: 用于向监管机构电子报告

### 3. CDASH User Guide v1.0
- **内容**: 
  - 实施示例
  - CDASH 到 SDTM 映射表
  - 实用实现信息
- **使用方式**: 作为 CDASH v1.1 的补充文档

### 4. CDASH ODM-XML
- **类型**: CDISC 操作数据模型 (ODM) 的 XML 实现
- **特点**: 
  - 供应商中立
  - 平台无关
  - 用于数据交换和归档
- **注意**: 可能需要根据具体研究或数据库系统修改

### 5. CDASH CRF Examples Library
- **内容**: 不同数据收集系统中的 CRF 示例
- **格式**: 纸质示例和电子格式
- **用途**: 快速创建符合 CDASH 的 CRF 表单

---

## 下载方式

### 方式 1: CDISC 官方网站 (需要注册/订阅)
CDISC 标准文档主要通过官方网站提供，需要:
1. 注册 CDISC 账户
2. 下载相关标准文档 (部分免费，部分付费)

**官方网站**: https://www.cdisc.org/standards/foundational/cdash

### 方式 2: 通过 NIH 公开资源
NIH 提供部分 CDASH 相关资源:
- 部分实施指南
- 示例 CRF 文档
- 培训材料

### 方式 3: 开源项目
一些开源项目提供 CDASH 参考实现:
- GitHub 上的 CDASH 示例代码
- 开源 eCRF 设计工具

---

## 实施建议

### 对于您的 EDC 系统设计
1. **字段命名规范**: 遵循 CDASH 标准字段名 (如 USUBJID, AESEQ, etc.)
2. **数据类型**: 使用 CDASH 定义的数据类型和格式
3. **验证规则**: 实现 CDASH 规定的数据验证逻辑
4. **映射关系**: 建立 CDASH→SDTM 的自动映射表
5. **审计追踪**: 记录所有数据修改历史

### 关键字段示例

#### Demographics (人口统计学)
```
DOMAIN|LABEL|DATATYPE|REQUIREMENT
DM|Study Identifier|ST|Required
DM|Subject Identifier|ST|Required
DM|Subject Name|NM|Required
DM|Date of Birth|DT|Required
DM|Sex|CA|Required
DM|Race|CA|Conditional
DM|Country|CA|Required
DM|Site Identifier|ST|Required
DM|Date of Screening|DT|Required
DM|Date of Enrollment|DT|Required
```

#### Adverse Events (不良事件)
```
DOMAIN|LABEL|DATATYPE|REQUIREMENT
AE|Subject Identifier|ST|Required
AE|AE Sequence Number|NM|Required
AE|Adverse Event Term|LM|Required
AE|Adverse Event Classification|LM|Required
AE|Date of Onset|DT|Required
AE|End Date|DT|Required
AE|Seriousness|CA|Required
AE|Relationship to Study Intervention|CA|Required
AE|Outcome|CA|Required
AE|Severity|CA|Required
```

---

## 相关标准关系

```
┌─────────────────────────────────────────────────────┐
│                  CDASH (数据采集)                      │
│  - CRF 设计标准 (数据收集字段)                           │
│  - 用于 eCRF 表单设计和数据录入                          │
└─────────────────────────────────────────────────────┘
                        ↓ (CDASH→SDTM 转换引擎)
┌─────────────────────────────────────────────────────┐
│                   SDTM (标准数据模型)                  │
│  - 研究数据交换标准                                   │
│  - 包含 DM, AE, LB, VS, EX 等域                        │
└─────────────────────────────────────────────────────┘
                        ↓ (SDTM→ADaM 转换)
┌─────────────────────────────────────────────────────┐
│                    ADaM (分析数据模型)                   │
│  - 统计分析数据标准                                   │
│  - 用于生成统计报告                                  │
└─────────────────────────────────────────────────────┘
```

---

## 下一步行动

1. **注册 CDISC 账户**: 获取完整标准文档
2. **下载 CDASH v1.1 标准**: 作为 EDC 系统设计的参考
3. **研究 CRF 示例**: 理解字段设计和验证规则
4. **实现 CDASH→SDTM 映射**: 开发转换引擎
5. **建立字段验证库**: 基于 CDASH 标准定义验证规则

---

## 参考资料

- CDISC 官网：https://www.cdisc.org/
- CDASH 标准页：https://www.cdisc.org/standards/foundational/cdash
- CDISC 社区论坛：https://community.cdisc.org/
- CDISC GitHub: https://github.com/cdisc-org

---

**创建时间**: 2026-05-27
**文档版本**: 1.0
**最后更新**: 2026-05-27
