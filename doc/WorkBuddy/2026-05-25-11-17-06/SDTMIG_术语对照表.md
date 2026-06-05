# CDISC SDTM Implementation Guide v3.4 关键术语中英对照表

## 通用术语

| 英文 | 中文 | 说明 |
|------|------|------|
| CDISC | 临床数据交换标准协会 | Clinical Data Interchange Standards Consortium |
| SDTM | 研究数据汇总模型 | Study Data Tabulation Model |
| SDTMIG | SDTM 实施指南 | SDTM Implementation Guide |
| CRF | 病例报告表 | Case Report Form |
| eCRF | 电子病例报告表 | Electronic Case Report Form |
| CTMS | 临床试验管理系统 | Clinical Trial Management System |
| EDC | 电子数据采集 | Electronic Data Capture |
| GCP | 药物临床试验质量管理规范 | Good Clinical Practice |
| FDA | 美国食品药品监督管理局 | Food and Drug Administration |
| PMDA | 日本制药品和医疗器械局 | Pharmaceuticals and Medical Devices Agency |

## SDTM 核心概念

| 英文 | 中文 | 说明 |
|------|------|------|
| Domain | 域 | 数据域,如 AE(不良事件)、DM(受试者人口学) |
| Dataset | 数据集 | 具有相同结构的数据集合 |
| Observation | 观测 | 一次数据记录或测量 |
| Variable | 变量 | 数据集中的列 |
| Record | 记录 | 数据集中的行 |
| Subject | 受试者 | 临床试验参与者 |
| USUBJID | 受试者唯一标识符 | Unique Subject Identifier |
| Study Day | 研究天数 | 相对于研究起点的天数 |
| Visit | 访视 | 受试者参加研究的访视 |
| Episode of Care | 诊疗期 | 连续的治疗或观察期 |

## 数据类别

| 英文 | 中文 | 说明 |
|------|------|------ |
| General Observation Class | 通用观测类别 | SDTM 数据的分类方式 |
| Intervention | 干预 | 如给药、手术等 |
| Findings | 发现/结果 | 如实验室检查、生命体征 |
| Events | 事件 | 如不良事件、医疗史 |
| Exposures | 暴露 | 如药物暴露 |
| Subject Characteristics | 受试者特征 | 如人口学信息 |
| Study Conduct | 研究执行 | 如访视信息 |

## 变量类型

| 英文 | 中文 | 说明 |
|------|------|------|
| Required Variable | 必需变量 | 必须包含的变量 |
| Conditionally Required Variable | 条件必需变量 | 在特定条件下必需的变量 |
| Permitted Variable | 允许变量 | 可选的变量 |
| Core Variable | 核心变量 | 域的核心变量集 |
| Identifier Variable | 标识变量 | 用于标识记录的变量 |
| Grouping Variable | 分组变量 | 用于分组的变量 |
|Qualifier Variable | 限定符变量 | 提供额外信息的变量 |
| Timing Variable | 时间变量 | 记录时间的变量 |
| Result Variable | 结果变量 | 记录测量结果的变量 |

## 时间相关

| 英文 | 中文 | 说明 |
|------|------|------|
| Actual Date | 实际日期 | 事件发生的实际日期 |
| Relative Date | 相对日期 | 相对于研究起点的日期 |
| Study Day | 研究天数 | 从研究起点开始的天数 |
| Duration | 持续时间 | 事件持续的时间 |
| Start Date | 开始日期 | 事件开始日期 |
| End Date | 结束日期 | 事件结束日期 |
| Epoch | 时期 | 研究的特定时期 (如筛选期、治疗期) |

## 编码和术语

| 英文 | 中文 | 说明 |
|------|------|------|
| Controlled Terminology | 受控术语 | CDISC 定义的标准术语集 |
| Codelist | 码表 | 允许值的列表 |
| Code Value | 码值 | 用于存储的代码 |
| Term | 术语 | 码值对应的描述 |
| Low-Level Term | 低层术语 | 最具体的术语 |
| High-Level Term | 高层术语 | 分组术语 |
| Dictionary | 词典 | 术语集合 |
| MedDRA | 医学字典 | Medical Dictionary for Regulatory Activities |
| WHO Drug | 药物词典 | World Health Organization Drug Dictionary |

## 数据提交

| 英文 | 中文 | 说明 |
|------|------|------|
| Regulatory Submission | 监管提交 | 向监管机构提交数据 |
| Dataset Metadata | 数据集元数据 | 描述数据集的信息 |
| Define.xml | Define.xml | 定义数据集结构的 XML 文件 |
| Tabulation Data | 汇总数据 | 用于提交的汇总格式数据 |
| Integration Review Guide | 整合审查指南 | IRG,监管机构的数据审查指南 |

## 技术术语

| 英文 | 中文 | 说明 |
|------|------|------|
| Primary Key | 主键 | 唯一标识记录的键 |
| Natural Key | 自然键 | 基于业务意义的键 |
| Missing Value | 缺失值 | 未填写的值 |
| Text Case | 大小写 | 文本的大小写规范 |
| Variable Length | 变量长度 | 变量的最大长度 |
| Data Type | 数据类型 | 字符型或数值型 |

---

*注*: 本术语表基于 CDISC 官方术语和行业标准译法整理
