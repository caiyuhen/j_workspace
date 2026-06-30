# MedAIagents 项目结构

```
MedAIagents/
├── src/
│   └── medai/                          # 主包目录
│       ├── __init__.py                 # 包入口
│       ├── agent.py                    # 医学AI代理核心类
│       ├── config.py                   # 配置管理
│       ├── cli.py                      # 命令行接口
│       │
│       ├── llm/                        # LLM 模块
│       │   ├── __init__.py
│       │   └── routing.py              # LLM 路由和集成
│       │
│       ├── memory/                     # 记忆系统模块
│       │   ├── __init__.py
│       │   └── system.py              # 会话记忆和长期记忆
│       │
│       ├── knowledge/                  # 医学知识库模块
│       │   ├── __init__.py
│       │   └── base.py                # 知识库搜索和向量数据库
│       │
│       ├── cdss/                       # 临床决策支持模块
│       │   ├── __init__.py
│       │   └── diagnosis.py           # 诊断推理和用药安全
│       │
│       ├── emr/                        # 电子病历自动化模块
│       │   ├── __init__.py
│       │   └── automation.py          # 病历生成和ICD编码
│       │
│       └── security/                   # 安全与合规模块
│           ├── __init__.py
│           └── compliance.py          # 加密、去标识化、审计、RBAC
│
├── examples/                           # 示例代码
│   └── basic_usage.py                 # 基本使用示例
│
├── data/                               # 数据目录 (运行时创建)
│   ├── knowledge/                      # 知识库数据
│   ├── memory/                         # 记忆系统数据
│   └── audit/                          # 审计日志
│
├── logs/                               # 日志目录
│
├── config.yaml                         # 主配置文件
├── .env.example                        # 环境变量示例
├── pyproject.toml                      # Python 包配置
├── requirements.txt                    # Python 依赖
├── package.json                        # Node.js 配置
├── README.md                           # 项目说明文档
└── PROJECT_STRUCTURE.md                # 本文件
```

## 模块说明

### 1. 核心模块 (`medai/`)

#### agent.py
- **MedicalAgent**: 医学AI代理主类
- 集成所有子系统功能
- 提供统一的API接口

#### config.py
- **Config**: 配置管理类
- 支持 YAML 配置文件
- 支持环境变量覆盖

#### cli.py
- 命令行接口
- 交互式聊天模式
- 诊断、用药检查、文书生成等功能

### 2. LLM 模块 (`llm/`)

#### routing.py
- **LLMRouter**: LLM 路由管理器
- **BaseLLMProvider**: LLM 提供商基类
- **OpenAIProvider**: OpenAI GPT 集成
- **AnthropicProvider**: Anthropic Claude 集成
- **DeepSeekProvider**: DeepSeek 集成
- 支持动态切换提供商

### 3. 记忆系统模块 (`memory/`)

#### system.py
- **MemorySystem**: 记忆系统
- 会话历史管理
- 上下文压缩
- 用户偏好记忆
- SQLite 持久化存储

### 4. 医学知识库模块 (`knowledge/`)

#### base.py
- **MedicalKnowledgeBase**: 医学知识库主类
- **PubMedSearcher**: PubMed 文献搜索
- **SimpleVectorDB**: 简单向量数据库实现
- 内置医学指南和疾病知识
- 支持语义搜索

### 5. 临床决策支持模块 (`cdss/`)

#### diagnosis.py
- **DiagnosticReasoner**: 诊断推理引擎
- 基于症状的疾病匹配
- 置信度计算
- **MedicationSafetyChecker**: 用药安全检查
- 药物相互作用检测
- 剂量合理性验证
- 过敏检查
- **ClinicalDecisionSupport**: CDSS 主类

### 6. 电子病历模块 (`emr/`)

#### automation.py
- **MedicalNoteTemplate**: 病历模板类
- 支持入院记录、病程记录、出院记录、手术记录
- **EMRInformationExtractor**: 信息提取器
- 从自由文本中提取患者信息、症状、检查结果
- **EMRNoteGenerator**: 病历生成器
- **ICD10Coder**: ICD-10 编码助手

### 7. 安全与合规模块 (`security/`)

#### compliance.py
- **DataEncryptor**: 数据加密器
- AES 加密/解密
- **DataDeidentifier**: 数据去标识化处理器
- 移除敏感字段
- 匿名化处理
- **RBACManager**: 基于角色的访问控制
- 用户角色管理
- 权限检查
- **AuditLogger**: 审计日志记录器
- 操作跟踪
- 日志查询和导出
- **HIPAAComplianceChecker**: HIPAA 合规检查
- PHI 字段检测
- 合规报告生成
- **SecurityManager**: 安全管理器主类

## 核心功能

### 1. 临床决策支持
- 症状到诊断的推理
- 鉴别诊断列表
- 建议的进一步检查
- ICD-10 编码匹配

### 2. 用药安全检查
- 药物相互作用检测
- 剂量合理性验证
- 过敏史检查
- 用药建议

### 3. 医学知识检索
- 内置医学指南知识库
- PubMed 文献搜索
- 向量语义搜索
- 相关文献推荐

### 4. 电子病历自动化
- 入院记录生成
- 病程记录生成
- 出院记录生成
- 手术记录生成
- ICD-10 编码查询

### 5. 安全与合规
- 数据加密存储
- 患者信息去标识化
- RBAC 权限管理
- 完整审计日志
- HIPAA 合规检查

### 6. 多模型支持
- OpenAI GPT-4 / GPT-3.5
- Anthropic Claude
- DeepSeek
- 可扩展架构

## 数据流程

```
用户输入 → 医疗代理 → 知识库检索 → LLM 处理 → 安全检查 → 输出结果
                          ↓
                    记忆系统更新
                          ↓
                    审计日志记录
```

## 扩展开发

### 添加新的 LLM 提供商
1. 继承 `BaseLLMProvider` 类
2. 实现 `chat_completion()` 和 `chat_completion_stream()` 方法
3. 在 `LLMRouter` 中注册新提供商

### 扩展医学知识库
1. 使用 `MedicalKnowledgeBase.add_document()` 添加新文档
2. 或扩展 `_load_builtin_knowledge()` 方法添加内置知识

### 自定义病历模板
1. 在 `EMRNoteGenerator` 中添加新的模板类型
2. 创建对应的模板内容和变量

### 添加安全规则
1. 扩展 `HIPAAComplianceChecker` 的 PHI 字段列表
2. 在 `RBACManager` 中添加新角色和权限
