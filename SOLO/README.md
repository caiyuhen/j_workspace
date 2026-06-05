# 医学智能体协同系统

一个基于多代理架构的医学AI协同平台，支持临床诊断辅助、医学研究分析、健康咨询问答等场景。

## 核心特性

- **8个专业代理协同工作**: 编排、诊断、研究、咨询、知识、工具、质控、学习
- **内置RAG的大模型服务**: 192.168.0.214:8802/chat/ 已集成医学知识向量库
- **双协议Skill集成**: 支持 skillhub.cn 和 MCP 协议
- **智能任务编排**: 自动分解任务、调度代理、整合结果

## 项目结构

```
backend/
├── app/
│   ├── api/v1/              # API接口
│   │   ├── conversations.py # 对话管理
│   │   ├── agents.py        # 代理管理
│   │   └── skills.py        # Skill管理
│   ├── agents/              # 代理实现
│   │   ├── base.py          # 代理基类
│   │   ├── orchestrator.py  # 编排代理
│   │   ├── diagnosis.py     # 诊断代理
│   │   ├── research.py      # 研究代理
│   │   ├── consultation.py  # 咨询代理
│   │   ├── knowledge.py     # 知识代理
│   │   ├── tool.py          # 工具代理
│   │   ├── quality.py       # 质控代理
│   │   ├── learning.py      # 学习代理
│   │   └── registry.py      # 代理注册中心
│   ├── services/            # 服务层
│   │   ├── llm_service.py   # LLM服务(内置RAG)
│   │   └── skill_service.py # Skill服务
│   ├── config.py            # 配置管理
│   └── main.py              # FastAPI入口
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 已实现的代理

| 代理 | 功能 | 能力 |
|-----|-----|-----|
| **OrchestratorAgent** | 任务编排 | 意图解析、任务分解、代理调度、结果整合 |
| **DiagnosisAgent** | 临床诊断辅助 | 病历分析、诊断建议、鉴别诊断、用药建议、风险评估 |
| **ResearchAgent** | 医学研究助手 | 文献检索、文献摘要、数据分析、论文辅助、趋势分析 |
| **ConsultationAgent** | 健康咨询顾问 | 健康咨询、症状自查、就医指导、用药指导、健康教育 |
| **KnowledgeAgent** | 医学知识查询 | 知识查询、术语解释、药物查询、疾病百科、指南检索 |
| **ToolAgent** | 工具集成专家 | Skill发现、Skill调用、MCP适配、结果转换 |
| **QualityAgent** | 质量与安全守护 | 结果审核、安全检查、合规验证、偏见检测、引用验证 |
| **LearningAgent** | 系统进化引擎 | 反馈学习、知识更新、效果评估、趋势分析 |

## 已实现的Skill

| Skill | 类别 | 协议 | 功能 |
|-------|-----|-----|-----|
| symptom_analyzer | diagnosis | skillhub | 症状分析 |
| lab_interpretation | diagnosis | skillhub | 检验结果解读 |
| imaging_analysis | diagnosis | skillhub | 影像辅助分析 |
| drug_interaction | pharmacy | mcp | 药物相互作用检查 |
| dosage_calculator | pharmacy | local | 药物剂量计算 |
| clinical_trial_search | research | mcp | 临床试验检索 |
| guideline_search | knowledge | mcp | 临床指南检索 |
| risk_score | calculation | local | 风险评分计算 |

## API端点

### 对话管理
| 方法 | 端点 | 描述 |
|-----|-----|-----|
| POST | /api/v1/conversations | 创建对话 |
| POST | /api/v1/conversations/{id}/messages | 发送消息 |
| GET | /api/v1/conversations/{id}/messages | 获取消息列表 |

### 代理管理
| 方法 | 端点 | 描述 |
|-----|-----|-----|
| GET | /api/v1/agents | 列出所有代理 |
| GET | /api/v1/agents/{name} | 获取代理详情 |
| POST | /api/v1/agents/tasks | 提交任务 |

### Skill管理
| 方法 | 端点 | 描述 |
|-----|-----|-----|
| GET | /api/v1/skills | 列出所有Skill |
| GET | /api/v1/skills/{id} | 获取Skill详情 |
| POST | /api/v1/skills/{id}/invoke | 调用Skill |

## 快速开始

### 1. 启动数据库
```bash
docker-compose up -d postgres redis
```

### 2. 安装依赖
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. 配置环境变量
```bash
copy .env.example .env
# 编辑 .env 文件
```

### 4. 启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 测试示例

### 发送消息
```bash
curl -X POST http://localhost:8000/api/v1/conversations/conv_001/messages ^
  -H "Content-Type: application/json" ^
  -d "{\"content\": \"患者主诉头痛3天，伴有发热，请给出诊断建议\"}"
```

### 调用Skill
```bash
curl -X POST http://localhost:8000/api/v1/skills/symptom_analyzer/invoke ^
  -H "Content-Type: application/json" ^
  -d "{\"input\": {\"text\": \"头痛发热3天\"}}"
```

## 大模型服务

系统使用内置RAG的大模型服务：

- **地址**: http://192.168.0.214:8802/chat/
- **特性**: 自动检索医学知识增强生成效果
- **知识库**: 疾病、药物、指南、文献等

## 文档

- [项目实施指南](./项目实施指南.md)
- [系统设计方案](./医学专业智能体协同系统设计方案.md)

## License

MIT
