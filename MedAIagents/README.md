# 🏥 MedAIagents - 专业级医学 AI 智能体框架

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Version](https://img.shields.io/badge/Version-0.1.0-green.svg?style=flat-square)](setup.py)

面向医疗健康领域的专业级 AI Agent 框架，专注于临床决策支持、医学知识检索、电子病历处理、临床科研和医学写作五大核心场景。

---

## 📑 目录

- [核心功能](#核心功能)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [功能演示](#功能演示)
- [模块详解](#模块详解)
- [配置说明](#配置说明)
- [开发指南](#开发指南)
- [Roadmap](#roadmap)
- [贡献指南](#贡献指南)
- [许可证](#许可证)

---

## 🎯 核心功能

### 1. 🧠 临床决策支持系统 (CDSS)

| 功能 | 描述 | 状态 |
|------|------|------|
| 智能诊断引擎 | 基于患者信息的辅助诊断建议 | ✅ |
| 鉴别诊断分析 | 多维度鉴别诊断和概率排序 | ✅ |
| 用药安全检查 | 药物相互作用、禁忌症、剂量验证 | ✅ |
| 临床指南引擎 | 内置 50+ 常见疾病诊疗规范 | ✅ |
| 检验检查解读 | 智能解读检验报告和影像报告 | ✅ |

### 2. 📋 电子病历智能处理 (EMR)

| 功能 | 描述 | 状态 |
|------|------|------|
| 病历信息提取 | 智能抽取关键临床信息 | ✅ |
| 结构化处理 | 非结构化病历转结构化数据 | ✅ |
| ICD-10 编码助手 | 诊断和手术操作智能编码 | ✅ |
| 病历质量审查 | 自动检测病历完整性问题 | ✅ |
| 医疗术语标准化 | 支持 ICD-10、SNOMED-CT 等 | ✅ |

### 3. 🔒 安全与合规引擎

| 功能 | 描述 | 状态 |
|------|------|------|
| 数据加密 | AES-256 数据加密存储 | ✅ |
| 隐私保护 | 患者信息自动脱敏和匿名化 | ✅ |
| 访问控制 | RBAC 细粒度权限管理 | ✅ |
| 审计追踪 | 完整操作日志记录 | ✅ |
| HIPAA 合规 | 符合医疗数据隐私规范 | ✅ |

### 4. 📊 临床科研自动化 (NEW!)

| 功能 | 描述 | 状态 |
|------|------|------|
| **样本量计算** | 率比较、均数比较、生存分析样本量 | ✅ |
| **RCT 方案生成** | 随机对照试验完整方案自动生成 | ✅ |
| **RWE 研究设计** | 真实世界研究方案设计 | ✅ |
| **报告规范** | CONSORT、STROBE 等报告清单 | ✅ |
| **统计模板** | 常用统计分析方法模板 | ✅ |

### 5. ✍️ 医学写作助手 (NEW!)

| 功能 | 描述 | 状态 |
|------|------|------|
| **论文结构生成** | IMRaD 标准论文结构自动生成 | ✅ |
| **参考文献管理** | 温哥华、APA、GB7714 格式 | ✅ |
| **图表模板** | 表格、流程图、森林图等模板 | ✅ |
| **CONSORT 流程图** | 临床试验受试者流程图自动生成 | ✅ |
| **投稿信生成** | 智能 Cover Letter 生成 | ✅ |
| **写作规范检查** | 医学论文写作指导与提示 | ✅ |

---

## 📁 项目结构

```
MedAIagents/
├── src/
│   └── medai/
│       ├── __init__.py              # 包入口和版本信息
│       ├── config.py                # 配置管理
│       ├── data/                    # 内置数据和知识库
│       ├── cdss/                    # 临床决策支持
│       │   ├── __init__.py
│       │   ├── diagnosis.py         # 诊断引擎
│       │   ├── drug_safety.py       # 用药安全
│       │   └── guideline_engine.py  # 指南引擎
│       ├── emr/                     # 电子病历处理
│       │   ├── __init__.py
│       │   ├── extractor.py         # 信息提取
│       │   └── icd10.py            # ICD-10 编码
│       ├── knowledge/               # 医学知识库
│       │   ├── __init__.py
│       │   └── retriever.py        # 知识检索
│       ├── llm/                     # 大模型集成
│       │   ├── __init__.py
│       │   └── base.py             # LLM 基类
│       ├── memory/                  # 记忆管理
│       │   ├── __init__.py
│       │   └── memory.py           # 对话记忆
│       ├── security/                # 安全与合规
│       │   ├── __init__.py
│       │   └── compliance.py       # 合规检查
│       ├── research/               # 临床科研自动化 ✨ NEW
│       │   ├── __init__.py
│       │   └── rct.py             # RCT 方案生成、样本量计算
│       ├── writing/                # 医学写作助手 ✨ NEW
│       │   ├── __init__.py
│       │   └── medical_writing.py  # 论文生成、参考文献管理
│       └── desktop/                # 桌面应用
│           ├── __init__.py
│           └── app.py              # PyWebView 应用
├── examples/                       # 示例代码
│   ├── basic_usage.py             # 基础功能演示
│   └── research_writing_demo.py   # 科研与写作演示
├── config/                        # 配置文件
├── tests/                         # 单元测试
├── README.md                      # 本文档
└── setup.py                       # 安装配置
```

---

## 🚀 快速开始

### 环境要求

- Python 3.9+
- pip / conda

### 安装

```bash
# 克隆项目
git clone https://github.com/your-org/MedAIagents.git
cd MedAIagents

# 安装依赖
pip install -r requirements.txt

# 开发模式安装
pip install -e .
```

### 基础使用

```python
from medai import ClinicalDecisionSupportSystem
from medai.research import SampleSizeCalculator, RCTProtocolGenerator
from medai.writing import MedicalWritingAssistant

# 1. 临床决策支持
cdss = ClinicalDecisionSupportSystem()
diagnosis = cdss.diagnose({
    'age': 55,
    'gender': 'male',
    'symptoms': ['多饮', '多尿', '体重下降'],
    'lab_results': {'空腹血糖': '9.8 mmol/L'}
})

# 2. 科研样本量计算
calc = SampleSizeCalculator()
result = calc.calculate_proportion(
    p1=0.30,  # 对照组有效率
    p2=0.45,  # 试验组有效率
    alpha=0.05,
    power=0.8
)
print(f"所需样本量: {result['sample_size']['total']} 例")

# 3. 医学论文写作
writer = MedicalWritingAssistant()
manuscript = writer.create_manuscript(
    title='新型口服降糖药治疗2型糖尿病的III期临床研究',
    study_type='临床试验'
)
```

### 桌面应用启动

```bash
# 方式一：直接运行桌面应用
python -m medai.desktop.app

# 方式二：使用命令行工具
medai-desktop
```

---

## 🎬 功能演示

### 临床科研模块演示

运行完整的科研功能演示：

```bash
python examples/research_writing_demo.py
```

**样本量计算示例：**

```python
from medai.research import SampleSizeCalculator

calc = SampleSizeCalculator()

# 率比较（有效率差异）
result = calc.calculate_proportion(
    p1=0.30,  # 对照组 30%
    p2=0.45,  # 试验组 45%
    alpha=0.05,
    power=0.8
)
# 总样本量: 406 例 (含20%失访率)

# 生存分析样本量
survival = calc.calculate_survival(
    median_survival_control=12,  # 对照组中位生存12月
    median_survival_treatment=18,  # 试验组18月
    hazard_ratio=0.67,
    alpha=0.05,
    power=0.8
)
```

**RCT 方案生成：**

```python
from medai.research import RCTProtocolGenerator

generator = RCTProtocolGenerator()
protocol = generator.generate_protocol(
    study_title='新型口服降糖药治疗2型糖尿病的多中心III期研究',
    indication='2 型糖尿病',
    phase='III期',
    primary_endpoint='治疗24周后HbA1c较基线变化',
    intervention='新药100mg qd',
    control='安慰剂'
)
```

### 医学写作模块演示

**论文结构生成：**

```python
from medai.writing import MedicalWritingAssistant

writer = MedicalWritingAssistant()

# 创建完整论文手稿
manuscript = writer.create_manuscript(
    title='新型口服降糖药XXX的III期临床研究',
    study_type='临床试验'
)

# 生成投稿信
cover_letter = writer.generate_cover_letter(
    journal_name='The Lancet Diabetes & Endocrinology',
    manuscript_title='新型口服降糖药XXX的III期研究',
    key_findings='''1. HbA1c降低1.5%，显著优于对照组
2. 安全性良好，低血糖<2%
3. 具有心血管获益趋势''',
    significance='本研究为新药提供关键III期临床证据'
)
```

**参考文献管理：**

```python
from medai.writing import ReferenceManager

ref_manager = ReferenceManager()
ref_manager.add_citation(
    citation_id='1',
    authors=['Smith A', 'Johnson B'],
    title='新药治疗糖尿病的系统评价',
    journal='New England Journal of Medicine',
    year=2023,
    volume='388',
    pages='1089-1100',
    doi='10.1056/NEJMoa2215026'
)

# 温哥华格式
print(ref_manager.format_citation('1', style='vancouver'))

# GB7714 中国国家标准格式
print(ref_manager.format_citation('1', style='gb7714'))
```

---

## 📦 模块详解

### 1. 临床科研 (`medai.research`)

**核心类：**
- `SampleSizeCalculator`: 样本量计算器
  - `calculate_proportion()`: 率比较样本量
  - `calculate_mean()`: 均数比较样本量
  - `calculate_survival()`: 生存分析样本量

- `RCTProtocolGenerator`: RCT 试验方案生成器
  - `generate_protocol()`: 生成完整试验方案
  - 包含研究设计、入排标准、干预措施、统计计划等

- `RWEAnalyzer`: 真实世界研究分析
  - `generate_rwe_protocol()`: RWE 研究方案生成
  - 变量集、结局定义、混杂控制方法

- `StudyReportGenerator`: 报告规范生成
  - `generate_consort_checklist()`: CONSORT 2010 清单
  - `generate_strobe_checklist()`: STROBE 观察性研究清单

### 2. 医学写作 (`medai.writing`)

**核心类：**
- `PaperGenerator`: 论文结构生成器
  - `generate_paper_structure()`: IMRaD 标准结构
  - 标题页、摘要、引言、方法、结果、讨论、参考文献

- `ReferenceManager`: 参考文献管理器
  - `add_citation()`: 添加文献条目
  - `format_citation()`: 多种格式输出
  - 支持温哥华、APA、GB7714 格式

- `FigureTableGenerator`: 图表模板生成
  - `generate_table_template()`: 科研表格模板
  - `generate_figure_template()`: 各类图形模板
  - `generate_consort_flowchart()`: CONSORT 流程图

- `MedicalWritingAssistant`: 完整写作助手
  - `create_manuscript()`: 完整手稿生成
  - `generate_cover_letter()`: 投稿信生成
  - 内置写作规范和投稿检查清单

---

## ⚙️ 配置说明

项目使用 YAML 配置文件，默认位于 `config/default.yaml`：

```yaml
# 科研模块配置
research:
  default_alpha: 0.05
  default_power: 0.8
  dropout_rate: 0.20
  randomization_ratio: 1.0

# 医学写作配置
writing:
  default_journal: "default"
  reference_style: "vancouver"  # vancouver / apa / gb7714
  paper_structure: "IMRAD"

# ICD-10 编码
icd10:
  version: "2024"
  language: "zh-CN"

# 安全配置
security:
  encryption: true
  anonymization_level: "standard"  # none, standard, strict
  audit_log: true
```

---

## 🧪 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定模块测试
pytest tests/test_research.py -v
pytest tests/test_writing.py -v

# 覆盖率测试
pytest --cov=medai --cov-report=html
```

---

## 🗺️ Roadmap

### v0.2.0 (Q1 2025)
- [ ] 临床研究数据管理系统 (EDC)
- [ ] Meta 分析自动化工具
- [ ] 系统评价自动生成
- [ ] 统计分析报告自动生成

### v0.3.0 (Q2 2025)
- [ ] 医学文献智能检索
- [ ] 论文自动摘要生成
- [ ] 文献综述 AI 助手
- [ ] 期刊选择推荐系统

### v0.4.0 (Q3 2025)
- [ ] 基金申请书撰写助手
- [ ] 伦理审查材料生成
- [ ] 多语言医学翻译
- [ ] 同行评审意见智能回复

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

提交代码前请确保：
- 代码风格符合 PEP 8
- 添加相应的单元测试
- 更新相关文档

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## ⚠️ 免责声明

> **重要提示**：本软件仅供医学研究和教育目的使用，**不能替代专业医生的临床判断和诊疗建议**。所有医疗决策必须由合格的医疗专业人员做出。使用本软件产生的任何后果，开发者不承担任何责任。

---

## 📞 联系方式

- 项目主页：[GitHub Repo](https://github.com/your-org/MedAIagents)
- 问题反馈：[Issues](https://github.com/your-org/MedAIagents/issues)
- 邮箱：contact@medaiagents.com

---

<div align="center">
  <p>
    Made with ❤️ for Healthcare Professionals
  </p>
  <p>
    🏥 助力医学科研，守护人类健康 🏥
  </p>
</div>
