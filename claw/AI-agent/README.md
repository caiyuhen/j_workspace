# 医学智能体协同编排系统 - 完整说明

## 1. 系统总览

### 1.1 系统定位

本系统是一个**专业的医学 AI 智能体协同编排平台**，通过智能任务分解、多智能体协作、Skill 集成和自动化调度，实现复杂的医学任务自动化处理。

### 1.2 核心特性

✅ **智能任务分解**: 通过大模型分析，自动将复杂任务分解为可执行的子任务  
✅ **多智能体协同**: 6 个专业医学智能体协作，覆盖诊断、研究、数据分析等  
✅ **Skill 双重兼容**: 同时支持 SkillHub.cn 和 MCP 两种技能协议  
✅ **灵活配置**: 支持提示词和手动配置工作目录、定时任务  
✅ **Token 成本管控**: 实时监控和计算 Token 使用成本  
✅ **自动化调度**: 支持 Cron 表达式，定时任务自动执行  
✅ **完整的监控**: 任务监控、Token 监控、系统健康检查  

---

## 2. 系统架构

### 2.1 架构层次

```
用户层 (UI/API/CLI)
    ↓
编排引擎层 (任务分解/智能体调度/工作流/Skill/定时任务)
    ↓
智能体层 (医学专家/研究者/分析师/药物研究/临床决策/教育)
    ↓
技能层 (SkillHub 适配器/MCP 适配器/本地 Skill)
    ↓
数据层 (工作目录/数据库/缓存/知识库)
```

### 2.2 核心模块

#### 编排引擎
- **任务分解器**: 使用大模型分析任务，生成执行计划
- **智能体调度器**: 根据任务类型分配智能体
- **工作流引擎**: 管理任务执行顺序和依赖关系
- **Skill 管理器**: 统一管理和调用各类技能
- **定时任务调度器**: 基于 Cron 的自动化任务执行
- **Token 监控器**: 实时计算和监控 Token 使用

#### 智能体
1. **Medical Expert (医学专家)**: 诊断建议、病情分析、用药指导
2. **Researcher (研究者)**: 文献检索、分析、综述生成
3. **Data Analyst (数据分析师)**: 统计分析、可视化
4. **Drug Researcher (药物研究员)**: 药物信息、相互作用
5. **Clinical Decision (临床决策)**: 临床路径、治疗方案
6. **Medical Educator (医学教育)**: 知识讲解、培训材料

#### 技能集成
- **SkillHub.cn 适配器**: 对接 skillhub.cn 平台
- **MCP 适配器**: 支持 Model Context Protocol
- **本地 Skill 管理器**: 自定义本地技能

---

## 3. 详细功能说明

### 3.1 任务智能分解

**功能**: 通过自然语言提示词，自动分析任务并生成执行计划

**使用方式**:

#### 提示词方式
```
任务：分析一份患者的用药记录，检查药物相互作用

患者信息：
- 姓名：张三
- 年龄：55 岁
- 病史：高血压、冠心病
- 当前用药：阿司匹林、他汀类、β受体阻滞剂

要求：
1. 检查药物相互作用
2. 评估风险等级
3. 提供调整建议
```

**系统自动执行**:
1. 分解为子任务：信息提取 → 药物检索 → 相互作用分析 → 风险评估 → 建议生成
2. 分配给相应智能体：Data Analyst → Drug Researcher → Medical Expert
3. 生成执行计划和时间表
4. 逐步执行并返回结果

#### 配置文件方式
```yaml
tasks:
  drug_interaction_check:
    description: "药物相互作用检查"
    workflow:
      - step: extract_patient_info
        agent: data_analyst
      - step: retrieve_drug_info
        agent: drug_researcher
      - step: analyze_interactions
        agent: medical_expert
      - step: generate_report
        agent: medical_expert
```

### 3.2 多智能体协同

**协作机制**:

```
用户请求 → AgentsOrchestrator → 任务分解 → 智能体分配 → 并行执行 → 结果汇总
```

**智能体通信协议**:
- **标准接口**: 所有智能体遵循统一的输入输出格式
- **状态传递**: 智能体间共享任务状态和中间结果
- **错误处理**: 智能体失败时自动重试或切换备选方案

**示例协作流程**:

```mermaid
graph TD
    A[用户：药物治疗方案分析] --> B[Orchestrator]
    B --> C[分解：文献检索]
    B --> D[分解：数据分析]
    C --> E[Researcher Agent]
    D --> F[Data Analyst Agent]
    E --> G[汇总文献]
    F --> H[分析数据]
    G --> I[Medical Expert]
    H --> I
    I --> J[生成治疗方案]
    J --> K[返回结果]
```

### 3.3 Skill 集成

#### SkillHub.cn 集成

**配置**:
```yaml
skillhub:
  enabled: true
  base_url: "https://skillhub.cn/api"
  api_key: "${SKILLHUB_API_KEY}"  # 环境变量
```

**调用示例**:
```
调用 SkillHub 技能：data_analysis_v2
参数：
  - input: data.csv
  - operations: ["clean", "aggregate"]
  - output: result.json
```

**自动同步**:
- 每小时自动同步最新 Skill
- 本地缓存已加载的 Skill
- 支持 Skill 版本管理

#### MCP 集成

**配置**:
```yaml
mcp:
  enabled: true
  servers:
    - name: "filesystem"
      command: "npx -y @modelcontextprotocol/server-filesystem"
      args: ["path/to/workspace"]
      
    - name: "sqlite"
      command: "npx -y @modelcontextprotocol/server-sqlite"
      args: ["database.db"]
```

**工具示例**:
```
调用 MCP 工具：filesystem.read_file
参数：path = "config/model.yaml"
```

**支持的 MCP 服务器**:
- ✅ filesystem - 文件系统操作
- ✅ sqlite - 数据库操作
- ✅ github - GitHub 集成
- ✅ fetch - 网络请求
- ✅ 自定义服务器

#### 本地 Skill

**创建 Skill**:
```json
{
  "name": "medical_data_processor",
  "version": "1.0.0",
  "description": "处理医学数据文件",
  "author": "AI-agent Team",
  "parameters": [
    {
      "name": "input_file",
      "type": "string",
      "required": true,
      "description": "输入数据文件路径"
    },
    {
      "name": "output_format",
      "type": "string",
      "required": false,
      "default": "json",
      "options": ["json", "csv", "xml"]
    }
  ],
  "execution": {
    "type": "script",
    "script": "scripts/process_data.py",
    "dependencies": ["pandas", "numpy"]
  },
  "permissions": {
    "read": ["input_file"],
    "write": ["output_file"]
  }
}
```

**调用**:
```
调用本地技能：medical_data_processor
参数：
  - input_file: patient_data.csv
  - output_format: json
```

### 3.4 工作目录管理

#### 提示词设置

**示例**:
```
工作目录：D:/workspace/claw/AI-agent/projects/medical

任务：分析药物数据
```

**系统自动**:
1. 切换到指定工作目录
2. 验证目录权限
3. 创建必要的子目录
4. 设置环境变量

#### 手动配置

**命令行**:
```bash
# 设置工作目录
mao workspace --set D:/workspace/claw/AI-agent/projects/medical

# 查看当前工作目录
mao workspace --current

# 列出可用工作空间
mao workspace --list
```

**配置文件**:
```yaml
workspace:
  default_path: "D:/workspace/claw/AI-agent"
  
  spaces:
    - name: "medical"
      path: "D:/workspace/claw/AI-agent/projects/medical"
    - name: "research"
      path: "D:/workspace/claw/AI-agent/projects/research"
```

#### 权限控制

```yaml
permissions:
  read: true      # 允许读取
  write: true     # 允许写入
  execute: false  # 禁止执行（安全考虑）
  delete: false   # 禁止删除（安全考虑）
```

### 3.5 定时任务

#### Cron 表达式

**格式**: `秒 分 时 日 月 周`

**示例**:
```
0 8 * * * *    # 每天早上 8 点
0 0 * * 1      # 每周一凌晨 0 点
0 9 1 * *      # 每月 1 号上午 9 点
*/5 * * * * *  # 每 5 分钟
```

#### 提示词设置

**示例**:
```
定时任务：
- 每天早上 8 点汇总医学资讯
- 每周一生成文献综述
- 每月 1 号生成 Token 报告
```

**系统自动**:
1. 解析提示词中的定时信息
2. 生成 Cron 表达式
3. 添加到调度配置
4. 启动定时任务

#### 配置文件

```yaml
schedules:
  daily_news:
    cron: "0 8 * * * *"
    description: "每日医学资讯汇总"
    agent: "researcher"
    prompt: "汇总今日医学最新资讯"
    enabled: true
    
  weekly_review:
    cron: "0 9 * * 1"
    description: "周度文献综述"
    agent: "researcher"
    prompt: "生成周度文献综述报告"
    enabled: true
```

#### 任务管理

**命令行**:
```bash
# 查看定时任务
mao schedules --list

# 启用任务
mao schedules --enable daily_news

# 禁用任务
mao schedules --disable daily_news

# 立即执行
mao schedules --run daily_news

# 查看执行历史
mao schedules --history daily_news
```

### 3.6 Token 计算

#### 自动计算

**计算公式**:
```python
def calculate_cost(input_tokens, output_tokens):
    input_cost = (input_tokens / 1000) * 0.002  # 输入单价
    output_cost = (output_tokens / 1000) * 0.006  # 输出单价
    total = input_cost + output_cost
    return {
        "input": input_tokens,
        "output": output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total
    }
```

#### 实时监控

**日志示例**:
```
[Token Monitor] 任务 123:
  输入：1,500 tokens
  输出：2,300 tokens
  成本：0.0076 CNY
  
[Token Monitor] 智能体 Medical Expert 调用:
  累计输入：15,000 tokens
  累计输出：23,000 tokens
  今日成本：0.076 CNY
```

#### 报告生成

**今日报告**:
```bash
mao tokens --report --today
```

**输出**:
```
========== Token 使用报告 ==========
日期：2026-06-02

总使用情况:
  输入 Token: 50,000
  输出 Token: 75,000
  总成本：0.29 CNY

按智能体统计:
  Medical Expert: 30,000 tokens (0.174 CNY)
  Researcher: 15,000 tokens (0.087 CNY)
  Data Analyst: 10,000 tokens (0.058 CNY)

按任务统计:
  任务 123: 20,000 tokens (0.116 CNY)
  任务 124: 15,000 tokens (0.087 CNY)
  任务 125: 30,000 tokens (0.174 CNY)

⚠️  警告：今日使用量达到预设阈值的 80%
```

**月度报告**:
```bash
mao tokens --report --month 2026-06
```

#### 阈值设置

```yaml
token_monitor:
  thresholds:
    daily_limit: 1000000      # 每日上限
    monthly_limit: 30000000   # 月度上限
    warning_percentage: 80    # 警告阈值
    
  alerts:
    email: admin@example.com
    wechat: true
```

---

## 4. 配置说明

### 4.1 配置文件结构

```
config/
├── config.yaml          # 系统主配置
├── model.yaml           # 大模型配置
├── workspace.yaml       # 工作目录配置
├── agents.yaml          # 智能体配置
├── skills.yaml          # Skill 配置
├── schedules.yaml       # 定时任务配置
└── example.env          # 环境变量示例
```

### 4.2 环境配置

**环境变量**:
```bash
# 在 .env 文件中配置
SKILLHUB_API_KEY=your_api_key_here
GITHUB_TOKEN=your_github_token_here
DATABASE_URL=postgresql://user:pass@localhost/db
```

**加载方式**:
```python
import os
from dotenv import load_dotenv

load_dotenv()  # 自动加载.env 文件
```

### 4.3 配置热重载

系统支持配置热重载，无需重启:

```bash
# 重新加载配置
mao config --reload

# 检查配置有效性
mao config --validate
```

---

## 5. API 参考

### 5.1 任务管理 API

#### 创建任务
```http
POST /api/tasks
Content-Type: application/json

{
  "prompt": "分析高血压患者治疗方案",
  "workspace": "medical",
  "agents": ["medical_expert", "clinical_decision"],
  "skills": ["data_processor"],
  "priority": "high"
}
```

**响应**:
```json
{
  "task_id": "12345",
  "status": "queued",
  "estimated_time": 120
}
```

#### 查询任务状态
```http
GET /api/tasks/{task_id}
```

**响应**:
```json
{
  "task_id": "12345",
  "status": "running",
  "progress": 60,
  "current_step": "数据清洗",
  "estimated_completion": "2026-06-02T10:30:00Z"
}
```

#### 获取任务结果
```http
GET /api/tasks/{task_id}/result
```

### 5.2 智能体管理 API

#### 列出智能体
```http
GET /api/agents
```

#### 获取智能体状态
```http
GET /api/agents/{agent_name}/status
```

### 5.3 Skill 管理 API

#### 列出可用 Skill
```http
GET /api/skills
```

#### 调用 Skill
```http
POST /api/skills/call
Content-Type: application/json

{
  "name": "data_analysis",
  "parameters": {
    "input": "data.csv",
    "operations": ["clean", "aggregate"]
  }
}
```

### 5.4 Token 监控 API

#### 今日 Token 使用
```http
GET /api/tokens/today
```

#### 获取使用报告
```http
GET /api/tokens/report?period=day&date=2026-06-02
```

---

## 6. 最佳实践

### 6.1 提示词编写

**好的提示词示例**:
```
任务：分析临床数据

**背景**: 
我们有 500 名高血压患者的治疗数据，需要分析不同药物的疗效。

**要求**:
1. 数据文件：data/patient_data.csv
2. 分析维度：年龄、性别、病程、用药方案
3. 统计指标：有效率、副作用发生率
4. 输出格式：Markdown 报告 + Excel 表格

**智能体**: Data Analyst, Medical Expert

**Skill**: data_processor_v2
```

**关键要素**:
- ✅ 明确的任务描述
- ✅ 详细的背景信息
- ✅ 具体的要求
- ✅ 预期的输出格式
- ✅ 指定的智能体

### 6.2 工作目录组织

**推荐结构**:
```
projects/
├── medical/           # 医学项目
│   ├── data/         # 数据文件
│   ├── results/      # 结果文件
│   ├── reports/      # 报告
│   └── configs/      # 配置文件
├── research/         # 研究项目
└── educational/      # 教育项目
```

### 6.3 技能使用

**选择 Skill 的原则**:
1. 优先使用本地 Skill (更快、更安全)
2. SkillHub Skill 用于通用功能
3. MCP Skill 用于系统级操作
4. 避免频繁调用外部 API

### 6.4 定时任务

**设计建议**:
- 避免密集执行 (至少间隔 1 小时)
- 选择低峰时段 (如凌晨)
- 设置合理的超时时间
- 启用执行通知

### 6.5 Token 优化

**降低成本的方法**:
1. 使用合适的温度参数 (医学建议用 0.5-0.7)
2. 限制最大 Token 数
3. 批量处理任务
4. 缓存常用结果
5. 定期审查 Token 使用

---

## 7. 安全与隐私

### 7.1 数据安全

**医疗数据处理**:
- ✅ 所有患者数据自动脱敏
- ✅ 传输过程加密
- ✅ 存储加密
- ✅ 访问日志记录

**权限控制**:
- 工作目录访问权限
- Skill 调用权限
- 智能体访问权限
- API 访问令牌

### 7.2 合规性

**遵循标准**:
- HIPAA (美国健康保险流通与责任法案)
- GDPR (欧盟通用数据保护条例)
- 中国网络安全法

**注意事项**:
- ❌ 不要上传真实患者敏感信息
- ❌ 不要使用未经授权的数据
- ✅ 所有分析仅供研究参考
- ✅ 临床决策必须由专业医生确认

---

## 8. 故障排查

### 8.1 常见问题

#### 无法连接大模型
```bash
# 检查网络
ping 192.168.0.214

# 测试 API
curl http://192.168.0.214:8802/chat/

# 检查日志
tail -f logs/system.log
```

#### Skill 调用失败
```bash
# 检查 Skill 连接
mao skills --test

# 查看 Skill 日志
mao logs --skill

# 重新注册
mao skills --register
```

#### 定时任务未执行
```bash
# 检查调度器状态
mao scheduler --status

# 查看任务日志
mao logs --scheduler

# 重启调度器
mao scheduler --restart
```

### 8.2 获取帮助

**日志文件**:
- `logs/system.log` - 系统日志
- `logs/task_{id}.log` - 任务日志
- `logs/token_usage.log` - Token 使用日志
- `logs/scheduler.log` - 调度器日志

**诊断命令**:
```bash
# 系统健康检查
mao health

# 详细诊断
mao diagnose --all

# 性能分析
mao profile
```

---

## 9. 更新日志

### v1.0.0 (2026-06-02)
- ✨ 初始版本发布
- ✅ 核心功能完成
- ✅ 6 个医学智能体
- ✅ SkillHub 和 MCP 集成
- ✅ Token 计算和监控
- ✅ 定时任务调度
- ✅ Web 控制台
- ✅ CLI 工具
- ✅ RESTful API

---

## 10. 联系方式

- **项目文档**: `docs/`
- **API 文档**: `docs/api/`
- **GitHub**: (待添加)
- **问题反馈**: (待添加)

---

**维护者**: AI-agent 团队  
**版本**: 1.0.0  
**最后更新**: 2026-06-02  
**许可**: MIT
