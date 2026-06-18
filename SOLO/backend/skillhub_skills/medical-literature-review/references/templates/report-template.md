# [研究主题] 系统文献综述

> **生成日期**: {{date}}
> **检索截止日期**: {{search_date}}
> **报告类型**: 系统文献综述

---

## 摘要

**背景**: {{background_summary}}

**方法**: 检索 {{databases}} 数据库（{{date_range}}），纳入 {{inclusion_criteria}}。

**结果**: 共纳入 {{total_included}} 项研究（n={{total_sample}}）。{{main_finding}}。

**结论**: {{conclusion}}（GRADE {{grade_level}}）。推荐强度：{{recommendation_strength}}。

---

## 1. 背景与目的

{{background_detail}}

**研究目的**: {{objective}}

---

## 2. 方法

### 2.1 检索策略

**检索日期**: {{search_date}}

**检索数据库**:

| 数据库 | 检索方式 | 检索结果数 |
|--------|----------|-----------|
{{#databases_detail}}
| {{name}} | {{method}} | {{count}} |
{{/databases_detail}}

**检索式** (`{{primary_database}}`):
```
{{search_syntax}}
```

### 2.2 纳入与排除标准

| 标准类型 | 纳入 | 排除 |
|----------|------|------|
| 研究设计 | {{include_design}} | {{exclude_design}} |
| 人群 | {{include_population}} | {{exclude_population}} |
| 干预 | {{include_intervention}} | {{exclude_intervention}} |
| 对照 | {{include_comparison}} | {{exclude_comparison}} |
| 结局 | {{include_outcome}} | {{exclude_outcome}} |
| 语言 | {{include_language}} | {{exclude_language}} |
| 发表时间 | {{include_time}} | {{exclude_time}} |

### 2.3 文献筛选流程

{{prisma_flowchart}}

### 2.4 数据提取与质量评价

**数据提取**: {{extraction_method}}

**质量评价工具**:
- RCT: {{rct_quality_tool}}
- 观察性研究: {{obs_quality_tool}}
- 系统评价: {{sr_quality_tool}}

---

## 3. 结果

### 3.1 文献筛选结果

{{screening_results_summary}}

### 3.2 纳入研究特征表

| # | 研究(年份) | 设计 | 样本量 | 干预 | 对照 | 主要结局 | 效应量(95%CI) | GRADE |
|---|------------|------|--------|------|------|----------|---------------|-------|
{{#studies}}
| {{index}} | {{author}} ({{year}}) | {{design}} | N={{sample_size}} | {{intervention}} | {{comparison}} | {{outcome}} | {{effect_size}} | {{grade}} |
{{/studies}}

### 3.3 主要结局分析

{{#outcomes}}
#### {{outcome_name}}

- **汇总效应量**: {{pooled_effect}}
- **异质性**: I² = {{i2}}%（{{heterogeneity_level}}）
- **绝对风险差异**: {{absolute_risk_diff}}
- **亚组分析**: {{subgroup_results}}

**GRADE评定**: {{grade_assessment}}

{{/outcomes}}

### 3.4 偏倚风险评估

| 研究 | 随机化 | 偏离干预 | 缺失数据 | 结局测量 | 选择性报告 | 总体 |
|------|--------|----------|----------|----------|------------|------|
{{#rob_assessment}}
| {{study}} | {{domain1}} | {{domain2}} | {{domain3}} | {{domain4}} | {{domain5}} | {{overall}} |
{{/rob_assessment}}

**发表偏倚**: {{publication_bias_assessment}}

---

## 4. 讨论

### 4.1 主要发现

{{main_findings_list}}

### 4.2 与现有证据的比较

{{comparison_with_existing}}

### 4.3 局限性

{{#limitations}}
{{index}}. {{limitation}}
{{/limitations}}

### 4.4 临床意义

{{clinical_implications}}

---

## 5. 结论与建议

{{conclusion_detail}}

**证据概况**:

| 结局 | GRADE证据等级 | 推荐强度 |
|------|--------------|----------|
{{#evidence_summary}}
| {{outcome}} | {{grade}} | {{strength}} |
{{/evidence_summary}}

---

## 参考文献

{{#references}}
{{index}}. {{citation}}
{{/references}}

---

**利益冲突声明**: {{conflict_of_interest}}

**检索截止日期**: {{search_date}}

---

> *本报告由循证医学文献综述系统自动生成，基于检索到的文献数据和既定的GRADE/PRISMA评估标准。具体临床决策应结合患者个体情况和临床经验。*
