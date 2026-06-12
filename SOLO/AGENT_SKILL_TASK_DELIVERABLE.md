# 代理/Skill 是否可用于实现 Task（验收交付物）

本项目已经具备用“代理 + 技能（Skill）”实现 Task 的完整链路，并提供了可运行的验收脚本 `agent_skill_task_runner.py`，用于输出可留存的结果文件 `agent_skill_task_results.json`。

## 核心能力覆盖

以下场景能通过编排代理自动路由到对应 Skill（tool agent）执行，并返回可直接展示的 `content`：

- 化验单/检验结果解读 → `skill_lab_interpretation`
- 分诊/挂科/是否急诊 → `skill_medical_api_triage`（走医学后端 `/triage`）
- 临床建议/治疗方案 → `skill_medical_api_clinical`（走医学后端 `/clinical`）
- 个案管理计划/每日任务 → `skill_medical_api_management_plan`（走医学后端 `/management_plan`）

并且对 `triage/clinical/management_plan` 的输出已经加了 **强制质控门禁**：

- 调用 `QualityAgent` 执行 `safety_check` 与 `compliance_verification`
- 命中高危信号（胸痛/呼吸困难/意识障碍/大出血/剧烈头痛等）时会降级/拦截并强化就医提示
- 检测到高风险或不合规时会自动改写为更安全合规版本（避免确定性诊断与处方剂量）

## 交付物清单

- `agent_skill_task_runner.py`：验收脚本（无需前端）
- `AGENT_SKILL_TASK_DELIVERABLE.md`：本说明文件
- 运行脚本后生成：`agent_skill_task_results.json`（验收结果）

## 如何运行验收（推荐环境）

由于部分 Python 版本（例如 3.14）可能缺少依赖库的预编译 wheel，建议使用 Python 3.10~3.12 来启动后端并运行脚本。

### 1. 启动后端 API

在 `backend/` 目录中安装依赖并启动：

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 配置医学后端（可选但推荐）

若希望 `medical_api` 的 `triage/clinical/management_plan` 真正执行成功，需要医疗大模型后端服务可访问：

- `LLM_ENDPOINT` 指向医学后端基础地址（例如 `http://127.0.0.1:8802`）
- 该服务需提供：`/health`、`/chat`、`/triage`、`/clinical`、`/management_plan` 等接口

如果医学后端未启动，验收脚本仍可验证“路由是否触发到对应 skill_id”，但执行结果可能包含连接失败信息。

### 3. 运行验收脚本

```bash
py -3 agent_skill_task_runner.py --api http://127.0.0.1:8000 --email admin@medical.ai --password admin123
```

脚本会输出一个 `agent_skill_task_results.json`，每个测试用例会包含：

- `expect_skill_id`：期望触发的 skill
- `actual_skill_id`：实际触发的 skill（从 orchestrator 输出中取）
- `quality_gate`：若经过质控门禁，会记录 pass/rewrite/block
- `content_preview`：返回内容片段（用于快速验收）

## 验收通过标准（建议）

- 每个用例 `status` 为 `completed` 或（后端不可用时）至少能看到 `actual_skill_id == expect_skill_id`
- 化验单用例能看到 `actual_skill_id == skill_lab_interpretation`
- 分诊/临床建议/管理计划能看到对应 `skill_medical_api_*`，且 `quality_gate` 字段存在（pass/rewrite/block）

