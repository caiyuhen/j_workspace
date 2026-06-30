# MedAIagents 快速启动指南

## 🚀 5分钟快速开始

### 方式一：桌面应用（推荐）

```bash
# 1. 进入项目目录
cd MedAIagents

# 2. 设置环境变量（Windows PowerShell）
$env:PYTHONPATH="d:\workspace\MedAIagents\src"

# 3. 启动桌面应用
python -m medai.desktop.app

# 4. 浏览器自动打开，或访问 http://127.0.0.1:8228
```

**Windows 一键启动（批处理文件）：**
```bash
# 直接双击运行
start_desktop.bat
```

**Linux/Mac 启动：**
```bash
chmod +x start_desktop.sh
./start_desktop.sh
```

### 方式二：命令行使用

```python
# 1. 设置 PYTHONPATH
import sys
sys.path.insert(0, 'd:\\workspace\\MedAIagents\\src')

# 2. 导入模块
from medai import ClinicalDecisionSupport, MedicalKnowledgeBase
from medai.emr.automation import EMRNoteGenerator, ICD10Coder

# 3. 开始使用
cdss = ClinicalDecisionSupport()
result = cdss.diagnose(symptoms=['头痛', '头晕', '血压升高'])
print(result)
```

## 📋 功能演示

### 1. 临床决策支持 (CDSS)

```python
from medai.cdss.diagnosis import ClinicalDecisionSupport

cdss = ClinicalDecisionSupport()

# 诊断辅助
diagnosis = cdss.diagnose(
    symptoms=['多饮', '多食', '多尿', '体重下降'],
    lab_results={'空腹血糖': '8.5 mmol/L', 'HbA1c': '7.8%'}
)
print(diagnosis['primary_diagnosis'])

# 用药安全检查
safety = cdss.check_medication_safety(
    medications=['华法林', '阿司匹林'],
    allergies=['青霉素']
)
print(safety['recommendations'])
```

### 2. 医学知识库检索

```python
from medai.knowledge.base import MedicalKnowledgeBase

kb = MedicalKnowledgeBase()

# 搜索医学知识
results = kb.search('高血压 治疗', limit=3)
for result in results:
    print(f"标题: {result['title']}")
    print(f"内容: {result['content'][:100]}...")

# 获取统计信息
print(kb.get_statistics())
```

### 3. 电子病历 (EMR) 生成

```python
from medai.emr.automation import EMRNoteGenerator

emr = EMRNoteGenerator()

# 生成入院记录
note = emr.generate_admission_note(
    patient_name='张三',
    gender='男',
    age=55,
    chief_complaint='多饮多食多尿伴体重下降1月',
    diagnosis='2型糖尿病'
)
print(note)

# 生成病程记录
progress_note = emr.generate_progress_note(
    subjective='患者今日精神可，无特殊不适',
    temperature=36.5,
    pulse=72,
    respiration=18,
    blood_pressure='135/85 mmHg'
)
print(progress_note)
```

### 4. ICD-10 编码查询

```python
from medai.emr.automation import ICD10Coder

coder = ICD10Coder()

# 查询编码
code = coder.get_icd10_code('2型糖尿病')
print(f"ICD-10 编码: {code}")  # E11

# 搜索相关编码
results = coder.search_icd10('高血压')
for r in results:
    print(f"{r['diagnosis']}: {r['icd10_code']}")
```

### 5. 数据安全与脱敏

```python
from medai.security.compliance import DataDeidentifier

deidentifier = DataDeidentifier()

patient_data = {
    'name': '张三',
    'age': 55,
    'gender': '男',
    'phone': '13800138000',
    'diagnosis': '高血压'
}

# 数据去标识化
deidentified_data = deidentifier.deidentify(patient_data)
print(deidentified_data)
# {'age': 55, 'gender': '男', 'diagnosis': '高血压'} - 姓名、电话被移除
```

## 🌐 桌面应用功能

### 功能菜单

1. **智能问答** - 基于 LLM 的医学知识问答
2. **诊断辅助** - 输入症状，获取诊断建议
3. **用药安全** - 药物相互作用、剂量检查
4. **病历文书** - 自动生成入院/病程/出院记录
5. **ICD-10** - 诊断编码快速查询
6. **知识库** - 医学文献和指南检索
7. **审计日志** - 操作记录追溯

### 截图预览

```
┌─────────────────────────────────────────────────────┐
│ 🏥 MedAIagents                             [菜单]   │
├─────────────────────────────────────────────────────┤
│ 🔍 诊断辅助                                         │
│                                                     │
│ 症状: [头痛, 头晕, 血压升高____________________]  │
│                                                     │
│ [开始诊断]                                          │
│                                                     │
│ 诊断结果:                                           │
│ ▶ 主要诊断: 原发性高血压 (I10)                       │
│ ▶ 建议检查: 心电图、心脏超声、肌钙蛋白...              │
└─────────────────────────────────────────────────────┘
```

## ⚙️ 配置说明

### 环境变量 (.env)

复制 `.env.example` 为 `.env` 并配置：

```env
# OpenAI API（推荐）
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 或 Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx

# 或 DeepSeek
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
```

### 配置文件 (config.yaml)

详细配置请参考 `config.yaml`，包括：
- LLM 模型配置
- 知识库配置
- 安全与合规设置
- 日志配置

## 🔌 API 接口

启动 Web 服务后，可通过 REST API 访问：

```bash
# 启动服务
python -m medai.desktop.server

# API 文档
open http://127.0.0.1:8228/docs
```

### 主要 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | 智能问答 |
| `/api/diagnosis` | POST | 诊断辅助 |
| `/api/medication-safety` | POST | 用药安全检查 |
| `/api/generate-note` | POST | 生成病历 |
| `/api/icd10` | POST | ICD-10 编码查询 |
| `/api/search` | POST | 知识库检索 |

## 🧪 测试验证

### 验证安装

```bash
# 检查导入
$env:PYTHONPATH="d:\workspace\MedAIagents\src"
python -c "import medai; medai.print_feature_status()"
```

### 运行所有测试

```bash
# 测试知识库
python examples/basic_usage.py
```

## 📱 支持的平台

- ✅ Windows 10/11
- ✅ Linux (Ubuntu 20.04+)
- ✅ macOS 10.15+
- ✅ Web 浏览器（任意现代浏览器）

## 🆘 常见问题

### Q1: ModuleNotFoundError: No module named 'medai'

**A:** 确保设置了正确的 PYTHONPATH：
```bash
$env:PYTHONPATH="d:\workspace\MedAIagents\src"  # Windows
export PYTHONPATH="/path/to/MedAIagents/src"    # Linux/Mac
```

### Q2: 如何启用 AI 问答功能？

**A:** 安装 LLM 依赖并配置 API Key：
```bash
pip install openai anthropic
# 然后在 .env 中设置你的 API Key
```

### Q3: 桌面应用无法打开？

**A:** 检查是否安装了 `pywebview`：
```bash
pip install pywebview
# 或直接在浏览器访问 http://127.0.0.1:8228
```

### Q4: 数据存储在哪里？

**A:** 默认在项目目录的 `data/` 文件夹下：
- `data/knowledge/` - 知识库数据
- `data/memory/` - 会话和记忆数据
- `logs/` - 日志文件

## 📞 获取帮助

- 提交 Issue: [GitHub Issues]
- 查看文档: `README.md`
- 代码示例: `examples/` 目录

---

祝您使用愉快！🏥✨
