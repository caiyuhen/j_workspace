# 医学智能体编排系统 - 快速开始指南

## 🚀 快速入门

本指南将帮助您快速启动和使用医学智能体编排系统。

### 第一步：环境准备

#### 1.1 系统要求
- Python 3.10+
- Node.js 22+
- 至少 8GB RAM
- 磁盘空间 10GB+

#### 1.2 安装依赖

```bash
# 进入项目目录
cd D:/workspace/claw/AI-agent

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Node.js 依赖
npm install
```

### 第二步：配置系统

#### 2.1 配置大模型

编辑 `config/model.yaml`：

```yaml
model:
  base_url: "http://192.168.0.214:8802/chat/"  # 您的大模型地址
  default_model: "qwen3.5-35b-a3b"
```

#### 2.2 配置工作目录

编辑 `config/workspace.yaml`：

```yaml
workspace:
  default_path: "D:/workspace/claw/AI-agent"
```

#### 2.3 配置智能体

编辑 `config/agents.yaml`，启用需要的智能体。

#### 2.4 配置 Skill

编辑 `config/skills.yaml`，设置 SkillHub 和 MCP 连接。

### 第三步：启动系统

#### 3.1 启动编排引擎

```bash
# 使用 Python 启动
python -m src.orchestrator

# 或者使用启动脚本
./start.sh  # Linux/Mac
start.bat   # Windows
```

#### 3.2 Web 控制台

启动后，打开浏览器访问：
- Web 界面：http://localhost:8080
- API 文档：http://localhost:8080/docs

### 第四步：开始使用

#### 4.1 命令行使用

```bash
# 创建任务
mao create --task "分析高血压患者治疗方案"

# 查看任务状态
mao status --task-id 123

# 查看 Token 使用
mao tokens --today
```

#### 4.2 API 使用

```python
import requests

# 提交任务
response = requests.post(
    "http://localhost:8080/api/tasks",
    json={
        "prompt": "分析某患者的用药风险",
        "workspace": "medical"
    }
)

task_id = response.json()["task_id"]
```

#### 4.3 使用提示词

直接在聊天中输入：

```
任务：我需要分析一份患者的用药记录，检查是否有药物相互作用

工作目录：D:/workspace/claw/AI-agent/projects/medical
Skill 调用：需要调用 drug_researcher 和 medical_expert
定时任务：每天上午 10 点自动检查

执行
```

系统会自动：
1. 分解任务为子任务
2. 选择合适的智能体
3. 调用相应的 Skill
4. 生成执行计划
5. 执行并返回结果

### 第五步：查看结果

#### 5.1 任务结果

```bash
# 查看任务输出
mao output --task-id 123

# 查看日志
mao logs --task-id 123
```

#### 5.2 Token 使用报告

```bash
# 今日 Token 使用
mao tokens --today

# 月度报告
mao tokens --report --month 2026-06
```

---

## 📖 完整功能说明

### 核心功能

#### 1. 智能任务分解

**输入提示词**：
```
我需要完成一个医学研究项目，包括文献检索、数据分析和报告生成
```

**系统输出**：
```
📋 任务分解计划：
├─ 任务 1：文献检索 (Research Agent)
│  ├─ 搜索 PubMed 数据库
│  ├─ 筛选高影响力文献
│  └─ 生成文献清单
├─ 任务 2：数据提取 (Data Analyst)
│  ├─ 提取关键数据
│  ├─ 数据清洗
│  └─ 数据整理
└─ 任务 3：报告生成 (Medical Expert)
   ├─ 分析数据
   ├─ 撰写报告
   └─ 格式调整
```

#### 2. 多智能体协同

智能体自动协作流程：
```
用户输入 → 编排者 → 分解任务 → 分配智能体 → 执行 → 汇总结果
```

支持智能体：
- **Medical Expert**: 医学咨询、诊断建议
- **Researcher**: 文献检索、分析
- **Data Analyst**: 数据分析、可视化
- **Drug Researcher**: 药物信息、相互作用
- **Clinical Decision**: 临床路径建议
- **Medical Educator**: 教学培训

#### 3. Skill 集成

**兼容两种协议**：

- **SkillHub.cn**: 从平台获取技能
- **MCP**: 使用标准协议连接本地技能

**调用示例**：
```
调用 SkillHub 的数据分析技能，输入文件 path/to/data.csv
调用 MCP 的 filesystem 技能，读取文件 config.yaml
```

#### 4. 工作目录管理

**提示词设置**：
```
工作目录：D:/workspace/claw/AI-agent/projects/medical
```

**手动设置**：
```bash
mao workspace --set D:/workspace/claw/AI-agent/projects/medical
```

支持：
- 多工作空间切换
- 权限控制
- 自动备份

#### 5. 定时任务

**提示词设置**：
```
每天上午 8 点自动汇总医学资讯
每周一生成文献综述报告
每月 1 号生成 Token 使用报告
```

**配置文件** (`config/schedules.yaml`)：
```yaml
schedules:
  daily_news:
    cron: "0 8 * * * *"
    agent: "researcher"
    prompt: "汇总每日医学资讯"
```

#### 6. Token 计算

**自动计算**：
```
输入：1500 tokens
输出：2300 tokens
成本：(1500 + 2300) / 1000 * 0.002 = 0.0076 元
```

**查看报告**：
```bash
mao tokens --report --today
mao tokens --report --month 2026-06
```

---

## 🎯 使用场景示例

### 场景 1：医学咨询

**用户输入**：
```
患者，男，45 岁，有高血压、糖尿病史，目前服用：
- 氨氯地平 5mg/天
- 二甲双胍 0.5g/天
- 阿司匹林 100mg/天

请分析：
1. 药物相互作用风险
2. 可能的副作用
3. 调整建议
```

**系统执行**：
1. Medical Expert 分析患者情况
2. Drug Researcher 检查药物相互作用
3. Clinical Decision 生成建议
4. 汇总生成综合报告

**输出结果**：
```markdown
## 药物相互作用分析

### 风险评估
- 氨氯地平 + 阿司匹林：低风险
- 二甲双胍 + 阿司匹林：中度风险（可能增加乳酸酸中毒风险）

### 建议
1. 监测肾功能
2. 定期血糖检测
3. 考虑调整阿司匹林剂量

### 参考来源
- UpToDate: Drug Interactions
- FDA Drug Database
```

### 场景 2：文献研究

**用户输入**：
```
研究主题：新型降压药物疗效比较
时间范围：近 3 年
要求：
- 检索至少 20 篇文献
- 分析研究质量
- 生成综述报告
- 附带引用格式
```

**系统执行**：
1. Researcher 检索 PubMed、Web of Science
2. Data Analyst 评估研究质量
3. Medical Expert 总结关键发现
4. 生成完整综述报告

### 场景 3：数据分析

**用户输入**：
```
数据文件：patient_data.csv
分析需求：
1. 患者特征统计
2. 治疗效果分析
3. 可视化图表
4. 统计检验
```

**系统执行**：
1. Data Analyst 加载数据
2. 执行统计分析
3. 生成可视化图表
4. 输出分析报告

---

## 🔧 高级配置

### 自定义智能体

在 `config/agents.yaml` 中添加：

```yaml
custom_agent:
  name: "CustomMedicalAgent"
  role: "specialist"
  specialties:
    - "cardiology"
    - "neurology"
  model: "qwen3.5-35b-a3b"
```

### 自定义 Skill

在 `skills/` 目录创建：

```json
{
  "name": "medical_data_processor",
  "version": "1.0.0",
  "description": "处理医学数据",
  "parameters": [
    {
      "name": "input_file",
      "type": "string",
      "required": true
    }
  ],
  "execution": "python scripts/process_data.py"
}
```

### 自定义定时任务

编辑 `config/schedules.yaml`：

```yaml
custom_task:
  cron: "0 0 * * 1,3,5"  # 每周一、三、五凌晨 0 点
  agent: "researcher"
  prompt: "执行自定义任务"
```

---

## 📊 监控与日志

### 查看系统状态

```bash
# 系统健康
mao health

# 智能体状态
mao agents --status

# Skill 连接
mao skills --connected

# Token 使用
mao tokens --current
```

### 日志管理

```bash
# 实时日志
mao logs --follow

# 任务日志
mao logs --task 123

# 清理旧日志
mao logs --cleanup --days 30
```

---

## 🐛 故障排查

### 常见问题

#### 1. 无法连接大模型

**症状**: API 请求失败

**解决**:
```bash
# 检查网络连接
ping 192.168.0.214

# 测试 API 连接
curl http://192.168.0.214:8802/chat/

# 检查配置
cat config/model.yaml
```

#### 2. Skill 调用失败

**症状**: 技能无法执行

**解决**:
```bash
# 检查 Skill 连接
mao skills --test

# 查看 Skill 日志
mao logs --skill

# 重新注册 Skill
mao skills --register
```

#### 3. 定时任务未执行

**症状**: 任务未按时执行

**解决**:
```bash
# 检查定时任务状态
mao schedules --list

# 查看任务日志
mao logs --scheduler

# 重启调度器
mao scheduler --restart
```

---

## 📚 更多资源

- [完整文档](docs/)
- [API 文档](docs/api/)
- [智能体开发指南](docs/agents/)
- [Skill 开发指南](docs/skills/)
- [常见问题 FAQ](docs/faq/)

---

## 💡 提示

1. **首次使用**: 建议从示例任务开始
2. **Token 管理**: 定期检查 Token 使用情况
3. **权限安全**: 工作目录权限要谨慎配置
4. **定期备份**: 开启自动备份功能
5. **监控日志**: 养成查看日志的习惯

---

**版本**: 1.0.0  
**更新日期**: 2026-06-02  
**维护团队**: AI-agent 团队
