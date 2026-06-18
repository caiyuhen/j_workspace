# Medical Master Router

## 为什么需要路由？

[OpenClaw Medical Skills](https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills) 收录了 **869+ 个医学 AI Skills**，覆盖临床、基因组学、药物研发、生信分析、医学影像等全领域。面对如此庞大的 Skill 库，一个核心挑战是：

> **用户提出一个医学问题时，AI Agent 如何在数百个 Skill 中快速、准确地找到最合适的那一个（或那几个）？**

`medical-master-router` 就是解决这个问题的 **智能路由层** —— 它是所有医学问题的"第一站"，负责理解用户意图，然后将请求精确分发到最匹配的下游 Skill。

```
用户问题 ──▶ medical-master-router ──▶ 精确匹配的 Skill(s) ──▶ 专业回答
                  │
                  ├── 意图分类（20 个医学领域）
                  ├── 实体标准化（疾病/药物/基因/变异）
                  └── 路由决策（单 Skill / 多 Skill 组合）
```

## 核心能力

### 🎯 20 个领域分类

Router 将医学问题分类到 20 个一级领域：

| # | 领域 | 示例关键词 |
|---|------|-----------|
| 1 | 临床诊疗 | 病历、SOAP、诊断、治疗方案 |
| 2 | 疾病与指南 | 疾病、指南、标准治疗、筛查 |
| 3 | 药物与安全 | 药物、处方、DDI、用药安全 |
| 4 | 药物基因组学 | PGx、基因-药物、CYP 代谢酶 |
| 5 | 肿瘤与精准医学 | 癌、突变、靶向、耐药、生物标志物 |
| 6 | 临床试验 | 试验、入组、eligibility、方案设计 |
| 7 | 基因组与变异 | VCF、ACMG、GWAS、PRS |
| 8 | 批量组学 | RNA-seq、DEG、甲基化、去卷积 |
| 9 | 单细胞与空间 | scRNA-seq、h5ad、spatial、10x |
| 10 | 生信流水线 | FASTQ、BAM、Nextflow、Snakemake |
| 11 | CRISPR & 基因编辑 | sgRNA、off-target、base editing |
| 12 | 系统生物学 | FBA、代谢建模、GRN、多组学 |
| 13 | 蛋白与治疗设计 | 抗体、binder、蛋白设计、CAR-T |
| 14 | 医学影像与病理 | 影像、病理、DICOM、IHC |
| 15 | 医学报告解读 | 体检报告、化验单、出院小结 |
| 16 | 心理健康与危机 | 精神危机、自杀、紧急干预 |
| 17 | 文献与数据库 | PubMed、文献检索、证据综合 |
| 18 | 公共卫生与健康 | 营养、运动、康复、可穿戴 |
| 19 | 法规与合规 | FDA 申报、合规、医学必要性 |
| 20 | 免疫组库与细胞治疗 | TCR、BCR、neoantigen、immune repertoire |

### 🔀 路由策略

Router 不是简单的关键词匹配，而是一套完整的路由工作流：

1. **意图分类** — 将用户请求映射到一个或多个领域
2. **实体标准化** — 疾病名、药名、基因符号统一为标准术语
3. **精确路由** — 按领域查询路由表，找到 primary skill + companion skill
4. **报告优先路由** — 识别到报告/截图/附件时，先分类报告类型再路由
5. **Family 回退** — 无精确匹配时，按 Skill 家族前缀（`bio-*`、`tooluniverse-*`、`clinical-*`）回退
6. **组合路由** — 跨领域问题自动组合多个 Skill 协同回答

### 📋 Skill 家族覆盖

| 家族前缀 | 适用场景 | 规模 |
|---------|---------|------|
| `tooluniverse-*` | 检索密集、报告优先、循证查询 | 40+ skills |
| `bio-*` | 分子生物学、测序、组学数据、计算生物学 | 300+ skills |
| `clinical-*` | 病历、推理、临床决策文档 | 10+ skills |
| `medical-*` | 医学研究、实体提取、影像 | 10+ skills |
| `drug-*` / `chem*` / `pharm*` | 化合物、标签、安全性、药化 | 30+ skills |
| `crispr-*` | 向导设计、脱靶、筛选解读 | 10+ skills |
| `*-agent` | 领域专用 AI Agent（肿瘤、抗体设计等） | 20+ skills |

## 项目结构

```
skills/medical-master-router/
├── README.md                          # 本文件
├── SKILL.md                           # 路由核心逻辑（AI Agent 加载的主 Prompt）
├── references/
│   ├── routing_table.md               # 完整的 意图 → Skill 路由映射表
│   └── skill_inventory.md             # 已安装 Skill 目录（按家族分类）
├── scripts/                           # 辅助脚本（预留）
└── assets/                            # 资源文件（预留）
```

### 关键文件说明

| 文件 | 作用 |
|------|------|
| `SKILL.md` | Router 的核心——AI Agent 加载后成为"医学分诊台"，包含完整的分类表、路由工作流、安全护栏和输出规范 |
| `references/routing_table.md` | 20 个领域的详细路由表，每个意图对应 primary skill 和 companion skill，以及跨域组合模式 |
| `references/skill_inventory.md` | 所有已安装 Skill 的分类目录，按家族前缀组织，支撑 Router 的精确匹配和回退路由 |

## 路由示例

### 示例 1：疾病查询
```
用户: "慢性乙肝是什么，怎么治疗？"

命中 skills：medical-master-router → tooluniverse-disease-research + tooluniverse-clinical-guidelines
```

### 示例 2：精准肿瘤学 + 试验匹配
```
用户: "EGFR L858R 的肺腺癌一线治疗和试验选择？"

命中 skills：medical-master-router → precision-oncology-agent + tooluniverse-clinical-trial-matching
```

### 示例 3：报告解读
```
用户: "解读这个体检报告截图，看看有没有异常"

命中 skills：medical-master-router → patiently-ai + lab-results
       (先 OCR 提取 → 识别报告类型 → 路由到报告解读专家)
```

### 示例 4：免疫组库分析
```
用户: "帮我看一下这组 TCR repertoire 数据，是否提示免疫耗竭？"

命中 skills：medical-master-router → tcr-repertoire-analysis-agent + tcell-exhaustion-analysis-agent
```

### 示例 5：跨域组合查询
```
用户: "这个患者携带 BRCA1 突变，帮我查一下靶向药和在招的临床试验"

命中 skills：medical-master-router 
  → tooluniverse-cancer-variant-interpretation (变异解读)
  + tooluniverse-precision-oncology (靶向治疗)
  + tooluniverse-clinical-trial-matching (试验匹配)
```

## 设计理念

### 为什么不让用户自己选 Skill？

869 个 Skill 的命名和覆盖范围对普通用户来说是不透明的。一个"肺癌靶向治疗"的问题，可能涉及 `precision-oncology-agent`、`tooluniverse-precision-oncology`、`tooluniverse-cancer-variant-interpretation` 等多个 Skill。Router 的价值在于：

- **降低认知负荷** — 用户只需用自然语言描述问题
- **提升路由精度** — 实体标准化 + 多级路由逻辑，优于简单关键词匹配
- **支持多 Skill 协同** — 自动组合 primary + companion skills，覆盖复杂查询
- **透明可追溯** — 每次路由结果会显示 `命中 skills：...`，用户知道 AI 用了什么

### 安全护栏

- 所有输出标注为 **决策支持信息**，非自主临床诊疗
- 区分通用医学信息与患者特异性建议
- 优先引用指南和证据来源
- 不编造临床事实、检验结果或治疗史
- 高紧迫/危机信号时优先升级处理

## 如何使用

### 作为 OpenClaw / NanoClaw 用户

安装了 OpenClaw Medical Skills 后，`medical-master-router` 会**自动作为医学问题的入口 Skill 被加载**。你只需要直接用自然语言提问：

```
"帮我查一下二甲双胍和华法林有没有相互作用"
"这个 VCF 文件里的 BRCA2 变异是致病的吗？"
"解读一下这张血常规报告"
```

Router 会自动完成分类 → 标准化 → 路由 → 调用下游 Skill → 返回结构化回答。

### 作为开发者

如果你要新增 Skill 并希望 Router 能路由到它：

1. 在 `references/skill_inventory.md` 中注册新 Skill
2. 在 `references/routing_table.md` 中添加对应的 intent → skill 映射
3. 如果属于新领域，在 `SKILL.md` 的 Level-1 分类表中增加条目

## ⚠️ 免责声明

> **本系统不是医生，不能替代专业医疗服务。**
>
> `medical-master-router` 及其路由的所有下游 Skills 仅提供医学信息参考和辅助决策支持，**不构成任何形式的医疗诊断、处方建议或治疗方案**。
>
> - 本系统的输出**不能替代**持证医疗专业人员（医生、药师、护士等）的面对面诊疗和判断；
> - 本系统的输出**不应被视为**针对任何个人的医学建议、诊断依据或治疗指导；
> - 使用者在做出任何医疗决策前，**必须咨询合格的医疗专业人员**；
> - 本系统**不承担**因使用输出内容而直接或间接导致的任何健康后果的责任。
>
> **如遇紧急医疗情况，请立即拨打急救电话或前往最近的医疗机构就诊。**

## 相关链接

- [OpenClaw Medical Skills 主仓库](https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills)
- [Skill 开发文档](../../doc/README.md)
- [OpenClaw 框架](https://github.com/openclaw/openclaw)
- [NanoClaw 框架](https://github.com/qwibitai/nanoclaw)
