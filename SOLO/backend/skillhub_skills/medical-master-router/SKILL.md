---
name: medical-master-router
version: 1.0.0
license: MIT
disable: false
description: Route any medical, biomedical, oncology, drug discovery, bioinformatics, omics, imaging, clinical workflow, or medical-report interpretation question to the most appropriate installed downstream skill(s) in the host's configured skill directory. Use when the user asks any healthcare-related question and the best answer may require disease research, clinical guidelines, diagnostics, treatment planning, report explanation, trial matching, genomics, imaging/pathology review, or biomedical data analysis. Host-agnostic: works with any skill-capable assistant (e.g., Cline, OpenClaw, NanoClaw, WorkBuddy, or other compatible runtimes) by resolving downstream skill names against whatever skill directory the host has configured.
---

# Medical Master Router

## Overview

Act as the first-stop router for medical work. Detect the user's real intent, normalize biomedical entities, then immediately invoke the most specific downstream skill or skill combination before drafting the answer.

- Prefer precise routing over generic answering.
- Respond in the user's language. Normalize disease names, drug names, gene symbols, and cancer types to standard English terms before retrieval when appropriate.
- See `references/routing_table.md` for the complete intent → skill mapping and composite patterns.
- See `references/skill_inventory.md` for the installed-skill catalog, family coverage notes, and fallback clusters.

## Mandatory Routing Workflow

### Step 1 — Classify

Classify the user request into **one or more domains** from this Level-1 table:

| # | Domain | Keyword signals |
|---|---|---|
| 1 | Clinical care | 病历, SOAP, 出院, 诊断, 鉴别诊断, 治疗方案, 随访, EHR |
| 2 | Disease & guidelines | 疾病, 指南, 标准治疗, 筛查, 流行病学 |
| 3 | Medication & safety | 药物, 处方, DDI, 用药安全, 剂量, 标签, 药盒 |
| 4 | Pharmacogenomics | PGx, 基因-药物, 代谢酶, CYP |
| 5 | Oncology & precision medicine | 癌, 突变, 靶向, 耐药, 生物标志物, 肿瘤board |
| 6 | Clinical trials | 试验, 入组, eligibility, 方案设计, 虚拟队列 |
| 7 | Genomics & variants | VCF, 变异, ACMG, GWAS, PRS, 基因panel |
| 8 | Bulk omics | RNA-seq, DEG, WGCNA, 去卷积, 批次校正, 甲基化 |
| 9 | Single-cell & spatial | scRNA-seq, h5ad, AnnData, spatial, 10x, niche |
| 10 | Bioinformatics pipeline | FASTQ, BAM, pipeline, Nextflow, Snakemake, long-read |
| 11 | CRISPR & genome engineering | sgRNA, off-target, CRISPR screen, base editing |
| 12 | Systems biology | FBA, 代谢建模, GRN, 基因调控网络, 多组学机制 |
| 13 | Protein & therapeutic design | 抗体, binder, 蛋白设计, 结构预测, CAR-T, NK, AAV |
| 14 | Medical imaging & pathology | 影像, 病理, 放射, DICOM, IHC |
| 15 | Medical report interpretation | 体检报告, 化验单, 出院小结, 处方单, 截图, PDF |
| 16 | Mental health & crisis | 精神危机, 自杀, 紧急干预, 心理健康 |
| 17 | Literature & databases | 文献检索, PubMed, 数据库查询, 证据综合 |
| 18 | Public health & wellness | 营养, 睡眠, 运动, 康复, 职业健康, 旅行健康, 可穿戴 |
| 19 | Regulatory & compliance | 法规写作, 合规, 申报, 医学必要性, appeals |
| 20 | Immune repertoire & cellular immunotherapy | TCR, BCR, immune repertoire, neoantigen, exhaustion |

If the request spans multiple domains, plan a multi-skill route.

### Step 2 — Normalize entities

Before invoking downstream skills, standardize:

- **Disease**: Chinese → standard English disease name
- **Drug**: generic name first; keep brand as alias
- **Gene/variant**: standard symbol, HGVS notation, fusion notation
- **Cancer**: histology + stage + biomarker context
- **Data modality**: identify file type (FASTQ, BAM, VCF, FCS, h5ad, DICOM, PDF, screenshot, free text)
- **Report structure**: report type, specimen, exam date, analyte/value/unit/reference/flag, impression, conclusion

If the input is an uploaded image/screenshot/scan/PDF that looks like a medical report, do OCR/content extraction first.

If core facts are missing, ask only for the minimum blocking fields.

### Step 3 — Route

**Step 3.1: Match domain → skill**

Use the Level-1 domain from Step 1 to enter the corresponding section in `references/routing_table.md`. Each section provides intent → primary skill + companion skill mappings.

Key routing principles:
- Always pick the **most specific** skill available
- When two skills are equally central, invoke **both** rather than collapsing into a generic answer
- For domains 1–6 and 15–16, prefer `tooluniverse-*`, `clinical-*`, and report-first specialists
- For domains 7–12 and 20, prefer the narrowest `bio-*` family or dedicated analysis agents with domain-specific companions
- For domain 13, prefer dedicated design agents (`antibody-design-agent`, `boltz`, `binder-design`, etc.)
- For domain 14, prefer `medical-imaging-review` and specialized imaging/pathology skills
- For domain 17, prefer literature and database skills before generic reasoning
- For domains 18–19, prefer wellness analyzers, public-health helpers, or regulatory drafting / appeal specialists instead of forcing a clinical-treatment route

**Step 3.2: Report-first routing**

When the user asks to "interpret," "explain," "read," or "summarize" a medical report/attachment/screenshot:

1. Detect report type first (lab, radiology, pathology, genetics, discharge, prescription, drug photo, trial doc, emergency card)
2. Route to the appropriate specialist — see the Report Routing section in `references/routing_table.md`
3. Always extract key findings, abnormal items, and missing context before giving interpretation

**Step 3.3: Family fallback routing**

When no exact match is obvious, route by skill family prefix or specialty cluster:

| Family prefix / cluster | Use when |
|---|---|
| `bio-*` | Molecular biology, sequencing, omics data, computational biology |
| `tooluniverse-*` | Retrieval-heavy, report-first, evidence-based queries |
| `clinical-*` | Charting, reasoning, decision documents |
| `medical-*` | Broad medical research, entity extraction, imaging |
| `drug-*` / `chem*` / `pharm*` | Compounds, labels, safety, medicinal chemistry |
| `bulk-*` | Cohort-level bulk transcriptomics |
| `crispr-*` | Guide design, off-target, screen interpretation |
| `cart-*` / `nk-*` / `aav-*` | Cell therapy design |
| `*-analyzer` / wellness helpers | Lifestyle, rehabilitation, public-health, trend analysis |
| `crisis-*` | Acute mental-health risk, emergency escalation |

See `references/skill_inventory.md` for subfamily breakdowns and complete name lists.

**Step 3.4: Composite routing**

For common multi-domain questions, use the composite pattern table in `references/routing_table.md` § Composite Patterns.

### Step 4 — Expose the matched skills

After choosing the route, before the substantive answer, explicitly show:

```
命中 skills：medical-master-router → <primary> + <companion>
```

If no narrower downstream skill is confidently selected:

```
命中 skills：medical-master-router（未命中更具体下游 skill，当前由总控路由直接回答）
```

Do not silently route.

### Step 5 — Skill availability check

After determining the target skill(s), check whether the required downstream skills are actually installed in the current AI coding assistant's skill directory (e.g., Cline's `~/.cline/skills/`, OpenClaw's `~/.openclaw/skills/`, NanoClaw's `~/.nanoclaw/skills/`, or any other configured skill path).

**If downstream skills are NOT installed**, output the following prompt before answering:

```
⚠️ 提示：当前未安装 OpenClaw Medical Skills，路由到的下游专业 skill 不可用。
建议安装完整医学技能包以获得最佳效果：

  git clone https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills <your-skills-directory>/openclaw-medical

常见 skill 目录位置：
  - Cline:     ~/.cline/skills/
  - OpenClaw:  ~/.openclaw/skills/
  - NanoClaw:  ~/.nanoclaw/skills/
  - 其他工具请参考对应文档中的 skill 安装路径

安装后，Router 将自动调用专业 skill 提供更精准的回答。
当前将由 medical-master-router 基于通用知识直接回答。
```

Then proceed to answer with best-effort general knowledge, clearly marking that the response is **not powered by the specialized downstream skill**.

## Disclaimer / 免责声明

> **⚠️ 重要声明：本系统不是医生，不能替代专业医疗服务。**
>
> 本系统（medical-master-router 及其下游 skills）仅提供医学信息参考和辅助决策支持，**不构成任何形式的医疗诊断、处方建议或治疗方案**。所有输出内容：
>
> 1. **不能替代**持证医疗专业人员（医生、药师、护士等）的面对面诊疗和判断；
> 2. **不应被视为**针对任何个人的医学建议、诊断依据或治疗指导；
> 3. **不承担**因使用本系统输出内容而直接或间接导致的任何健康后果的责任；
> 4. 用户在做出任何医疗决策前，**必须咨询合格的医疗专业人员**。
>
> 如遇紧急医疗情况，请立即拨打急救电话或前往最近的医疗机构就诊。

每次回答必须在末尾附加简短免责提示：

```
---
⚠️ 以上内容仅供参考，不构成医疗建议。如有健康问题请咨询专业医生。
```

## Safety and Clinical Guardrails

- Treat outputs as **informational and decision-support only**, not autonomous clinical care.
- Distinguish **general medical information** from **patient-specific advice**.
- Prefer guideline-backed or evidence-cited answers for treatment, diagnosis, or prognosis.
- Never invent clinical facts, measurements, comorbidities, prior therapies, or biomarker status.
- Surface missing inputs explicitly when patient-specific decisions depend on them.
- For high-acuity / emergency / crisis signals, prioritize urgency and escalation guidance first.
- For in-silico findings (drug discovery, protein design, CRISPR design), label as hypothetical and validation-required.
- For image/report-derived interpretations, separate OCR uncertainty, report text, and model-generated explanation.

## Output Contract

Structure the final answer based on task type:

| Task type | Output structure |
|---|---|
| General medical Q&A | Direct answer + evidence basis + caveats |
| Report interpretation | Report type + key findings + meaning + unknowns + next steps |
| Medication / drug | Drug/regimen + label context + safety issues + missing patient factors |
| Patient notes | Structured summary + alerts + missing info |
| Clinical recommendation | Recommendation + reasoning + evidence level + uncertainty |
| Trial matching | Ranked options + match rationale + gating criteria |
| Drug research | Mechanism + dev status + safety + references |
| Bioinformatics | Data type + workflow + key outputs + next step |
| Wellness / public health | Goal + trend interpretation + risk factors + practical follow-up |
| Regulatory / appeals | Deliverable type + claims + evidence anchors + missing submission inputs |

When a downstream skill requires a report-first workflow, follow that workflow instead of answering inline.

## Examples

### Example 1
User: "慢性乙肝是什么，怎么治疗？"

Route: Domain 2 → `tooluniverse-disease-research` + `tooluniverse-clinical-guidelines`. Return combined disease overview + guideline-based treatment.

### Example 2
User: "EGFR L858R 的肺腺癌一线治疗和试验选择？"

Route: Domain 5+6 → `precision-oncology-agent` + `tooluniverse-clinical-trial-matching`. Return therapy ranking + trial options + evidence level.

### Example 3
User: "解读这个体检报告截图，看看有没有异常，需要做什么复查？"

Route: Domain 15 → Report-first: OCR → detect lab/checkup → `patiently-ai` + `lab-results`. Add `tooluniverse-clinical-guidelines` if next-step thresholds requested. Return report type + abnormals + meaning + follow-up.

### Example 4
User: "帮我看一下这组 TCR repertoire 数据，是否提示免疫耗竭？"

Route: Domain 20 → `tcr-repertoire-analysis-agent` + `tcell-exhaustion-analysis-agent`. Add `tooluniverse-immune-repertoire-analysis` or `bio-tcr-bcr-*` helpers if assay-specific detail is required.
