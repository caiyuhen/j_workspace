# 临床研究项目全流程测试报告

测试日期：2026-06-13

测试目标：验证项目是否能够围绕“临床试验/临床研究项目”完成一条完整链路：

1. 登录系统
2. 提交临床研究类 Task
3. 由编排代理自动路由到对应 Skill
4. 返回结果并生成交付物文件

## 本次测试结论

结论分两层：

- **Task 与交付物链路：可以**
  - 已成功登录
  - 已成功提交 4 个临床研究相关 Task
  - 已生成结果交付物：`clinical_research_task_results.json`

- **医学后端真实执行：当前未跑通**
  - 所有 Task 都完成了编排与 Skill 选择
  - 但最终执行时返回：`技能执行失败：All connection attempts failed`
  - 说明系统已进入 Skill 执行阶段，但目标医学后端服务当前不可达

## 已生成的交付物

- `clinical_research_task_cases.json`
- `clinical_research_task_runner.py`
- `clinical_research_task_results.json`
- `clinical_research_e2e_test_report.md`

## 测试环境

- 后端 API：`http://127.0.0.1:8000`
- 测试账号：`admin@medical.ai`
- 后端健康检查：通过
- 系统已注册代理：
  - `orchestrator`
  - `diagnosis`
  - `research`
  - `consultation`
  - `knowledge`
  - `tool`
  - `quality`
  - `learning`

## 测试用例与结果

### 用例 1

- 名称：临床试验方案设计
- 期望 Skill：`skill_medical_api_clinical_trial`
- 实际 Skill：`skill_medical_api_clinical_trial`
- Task 状态：`completed`
- 执行结果：`技能执行失败：All connection attempts failed`

结论：**路由正确，后端目标服务不可达**

### 用例 2

- 名称：统计分析计划要点
- 期望 Skill：`skill_medical_api_clinical_trial`
- 实际 Skill：`skill_medical_api_clinical_trial`
- Task 状态：`completed`
- 执行结果：`技能执行失败：All connection attempts failed`

结论：**路由正确，后端目标服务不可达**

### 用例 3

- 名称：纳排标准草案
- 期望 Skill：`skill_medical_api_write`
- 实际 Skill：`skill_medical_api_clinical_trial`
- Task 状态：`completed`
- 执行结果：`技能执行失败：All connection attempts failed`

结论：**Task 可以生成，但规则路由存在偏差**

### 用例 4

- 名称：受试者风险与安全监测
- 期望 Skill：`skill_medical_api_clinical`
- 实际 Skill：`skill_medical_api_clinical_trial`
- Task 状态：`completed`
- 执行结果：`技能执行失败：All connection attempts failed`

结论：**Task 可以生成，但规则路由存在偏差**

## 本次测试发现的问题

### 1. 已修复问题

测试过程中发现 `backend/app/services/skill_registry.py` 中调用了 `uuid.uuid4()`，但未导入 `uuid`，导致 Task 初次执行失败：

- 原错误：`name 'uuid' is not defined`
- 已修复：补充 `import uuid`

修复后，Task 已能正常创建并完成到结果文件输出。

### 2. 当前阻塞问题

#### 医学后端不可达

当前 `medical_api` 类型 Skill 在执行时统一报错：

- `All connection attempts failed`

这表明：

- 编排代理和 ToolAgent 已经工作
- SkillRegistry 已经开始调用 `medical_api`
- 但 `LLM_ENDPOINT` 指向的医学后端服务未启动，或对应接口不可访问

#### 路由规则仍需优化

以下两类请求未命中预期 Skill：

- “纳排标准草案” 应命中 `skill_medical_api_write`，实际命中 `skill_medical_api_clinical_trial`
- “风险与安全监测” 应命中 `skill_medical_api_clinical`，实际命中 `skill_medical_api_clinical_trial`

说明当前 `orchestrator` 的规则优先级/关键词覆盖还需要调整。

## 综合判断

从系统能力角度看：

- **能不能出 Task？能**
- **能不能出交付物？能**
- **能不能证明代理/Skill 已接入主链路？能**

但从“临床研究项目是否已能完整跑通真实业务结果”来看：

- **还不能算完全跑通**

原因不是 Task 机制本身失败，而是：

1. `medical_api` 目标服务不可达
2. 某些临床研究类请求的 Skill 路由不够准确

## 建议下一步

1. 启动或修复 `LLM_ENDPOINT` 指向的医学后端服务
2. 逐条校正临床研究类意图的规则路由：
   - 纳排标准/方案写作 → `skill_medical_api_write`
   - 风险监测/安全建议 → `skill_medical_api_clinical`
   - 试验设计/SAP/样本量 → `skill_medical_api_clinical_trial`
3. 重跑本测试脚本，确认：
   - `actual_skill_id == expect_skill_id`
   - `content_preview` 为真实内容，而非连接失败信息

