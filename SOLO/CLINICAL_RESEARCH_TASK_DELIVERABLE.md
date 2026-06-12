# 临床研究项目：代理/Skill 是否可实现 Task（交付物）

你要做一个临床研究项目时，本系统可以把“研究任务”当成 Task 来处理，并通过 **编排代理** 自动触发 **医学专用 Skill（medical_api）** 来完成关键产出。

本交付物提供一套可复现实验（无需前端），用于验证：

1. 临床研究相关任务能否触发到正确的 Skill（例如临床试验设计、写作、临床建议）
2. 输出是否能稳定回传到 `content`（可直接在聊天/任务结果中展示）
3. 关键医学后端工具（triage/clinical/management_plan）的输出是否会触发质控门禁（若你的后端可用）

## 交付物清单

- `clinical_research_task_cases.json`：验收用例（临床研究任务集）
- `clinical_research_task_runner.py`：验收脚本（提交 Task 并输出结果）
- 运行脚本后生成：`clinical_research_task_results.json`（验收结果，可用于交付留档）

## 涉及到的代理/Skill

### 代理链路

- `OrchestratorAgent`（编排代理）：负责意图识别、任务分解、自动路由到工具代理/医学后端技能
- `ToolAgent`：实际执行 Skill（统一走 `skill_registry`）
- `QualityAgent`：对 `triage/clinical/management_plan` 输出做安全/合规门禁（pass/rewrite/block）

### 医学专用 Skill（medical_api）

以下技能直接对接医学后端接口（由 `LLM_ENDPOINT` 指向的服务提供）：

- `skill_medical_api_clinical_trial` → `POST /clinical_trial`（试验方案/样本量/统计学建议）
- `skill_medical_api_write` → `POST /write`（医学写作：纳排标准/方案章节/科普等）
- `skill_medical_api_clinical` → `POST /clinical`（临床建议：风险、监测、用药注意等）

> 如果医学后端未启动，你仍可验收“是否触发到对应 skill_id”，但执行结果会返回连接失败信息。

## 如何运行验收（无需前端）

### 1. 启动后端 API

确保后端已启动（例如 8000 端口），并可登录：

- `admin@medical.ai` / `admin123`
- `doctor@medical.ai` / `doctor123`

### 2. 运行脚本

```bash
py -3 clinical_research_task_runner.py --api http://127.0.0.1:8000 --email admin@medical.ai --password admin123
```

脚本会执行 `clinical_research_task_cases.json` 中的用例，并输出 `clinical_research_task_results.json`。

结果文件中每个用例包含：

- `expect_skill_id`：期望触发的 skill
- `actual_skill_id`：实际触发的 skill（从 orchestrator 输出中取）
- `quality_gate`：若启用门禁，会记录 pass/rewrite/block
- `content_preview`：输出摘要（用于快速验收）

## 验收通过建议

- 路由正确：`actual_skill_id == expect_skill_id`
- 返回稳定：结果包含 `content_preview`（即 orchestrator 输出的 `content`）
- 若医学后端可用：`triage/clinical/management_plan` 用例应出现 `quality_gate` 字段

