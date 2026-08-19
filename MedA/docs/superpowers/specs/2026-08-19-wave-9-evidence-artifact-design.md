# PRD 9 Spec · Wave 9 Evidence Artifact 共享引擎 + 三模块（Screening Dual-Phase / ROB-2 QA / Abstractor Auto-Triager）
> 日期：2026-08-19 | 架构：方案 2（Evidence Artifact 共享引擎）| 实施顺序：9a → 9b → 9c

---

## §0 NOTOUCH 约束（Wave 9 版 · 4 条硬约束）
| # | 不触碰条款 | 验证方式 |
|---|---|---|
| N1 | Wave 8.x 序列化/模型/REST 响应字段 **0 变动** | git diff `apps/agent-core/app/services/report_engine.py` `report_generator` wrapper 不变；`workspace.py` 旧 POST `/report/generate` 签名保留 |
| N2 | Wave 5 GRADE 引擎 **0 变动**（只有追加读取 evidence_artifact 的只读 SQL，不改已有 GRADE 字段签名） | `apps/agent-core/app/services/grade_engine.py` 不删除/重命名任何函数 |
| N3 | Meta Analysis 引擎内部 **0 变动**（只有 SELECT * FROM evidence_artifact WHERE decision='include' 的只读追加） | `meta_analysis` 包函数签名 0 变动 |
| N4 | shared-sdk / shared-ui 导出 **append-only**（禁止删除/重命名任何已有 export） | 全部修改用 `export { newComponent }` 追加，T9 无修改 export |

---

## §1 · 架构 & 12 文件清单 & shared-sdk 追加类型

### 1.1 五节点数据流（单向不可逆）
```
LiteratureRecords(N1-N4 8 步去重 + 10 步漏斗)
  → Screening Dual-Phase (9a)
      ├ evidence_artifact (stage=screening_ta | screening_fulltext)
  → Abstractor Auto-Triager (9c)
      └ evidence_artifact (stage=data_abstractor, confidence 0-1.0)
  → ROB-2 & ROBINS-I QA (9b)
      ├ evidence_artifact (stage=quality_ro | quality_nrsi)
      └ 直接被 Wave 5 GRADE 引用（只读 SQL 计算降级）
  → Wave 6 Meta Analysis / Wave 8.4 Output（已有模块，不改）
```

### 1.2 12 文件清单（每 Wave 4 新增）
```
● 4 NEW (backend，非 UI，9a + 9b + 9c)
  1. apps/agent-core/app/models.py + EvidenceArtifact (append-only 新类)
  2. apps/agent-core/app/services/screening_engine.py   (9a funnel 10 步 + 9 exclude reasons)
  3. apps/agent-core/app/services/rob2_engine.py        (9b ROB-2 5域 + ROBINS-I 7域 + 信号灯规则)
  4. apps/agent-core/app/services/simhash.py            (9c 64-bit SimHash + Jaccard 0 依赖)

● 4 NEW (shared-ui 组件 + 1 Hook，9a + 9b + 9c)
  5. packages/shared-ui/src/hooks/useEvidenceArtifact.ts  (统一 Injectable fetchClient Hook)
  6. packages/shared-ui/src/components/FunnelProgressBar.tsx  (9a 10 步漏斗组件)
  7. packages/shared-ui/src/components/RoB2Matrix.tsx + TrafficLightCell.tsx  (9b 信号灯矩阵)
  8. packages/shared-ui/src/components/AbstractorCard.tsx + ConfidenceBar.tsx  (9c 三档卡片)

● 2 NEW (backend REST：workspace.py 追加 6 路由；0 修改旧签名)
  9. apps/agent-core/app/routers/workspace.py · 追加：
      POST /evidence-artifact/list          GET  /evidence-artifact/{id}
      POST /evidence-artifact/decide        POST /screening/funnel-stats
      POST /rob2/evaluate-study             POST /abstractor/run-pipeline (9c)

● 2 MOD (append-only，shared-sdk 类型 + shared-ui barrel 导出)
  10. packages/shared-sdk/src/index.ts       (证据引擎 + 三模块 类型)
  11. packages/shared-ui/src/index.ts        (9 append-only barrel 导出)
```

### 1.3 shared-sdk 追加类型（append-only 8 个）
```ts
// === Evidence Artifact 核心表 ===
export type EvidenceStage =
  | 'screening_ta' | 'screening_fulltext'
  | 'quality_ro'   | 'quality_nrsi'
  | 'data_abstractor';
export type EvidenceDecision = 'include' | 'exclude' | 'review';
export interface EvidenceArtifact {
  id: string;
  literature_record_id: string;
  stage: EvidenceStage;
  decision: EvidenceDecision;
  confidence?: number;          // 0~1.0，9c Abstractor 必带
  exclude_reason_ids?: number[]; // 9 项排除原因 2-9，9a 用
  meta_json?: Record<string, unknown>; // PICO / RoB2 域评级 / 流水线日志
  created_by?: string;
  override_by_user_id?: string; // 9c 改推荐时填
  created_at: string;
}

// === 9a Screening ===
export type ExcludeReasonId = 2|3|4|5|6|7|8|9;  // 1=Duplicate 自动禁用
export interface FunnelStepStat {
  key: 'N1'|'N2'|'N3'|'N4'|'E1'|'E2'|'E3'|'E4'|'E5'|'E6';
  label: string;
  count: number;
  locked: boolean;
}

// === 9b ROB-2 / ROBINS-I ===
export type TrafficLightRating = 'low' | 'some_concerns' | 'high' | 'critical' | 'ni';
export interface RoB2DomainRating {
  domain: 'D1_randomization'|'D2_deviations'|'D3_missing'|'D4_measurement'|'D5_reporting';
  rating: TrafficLightRating;
  signal_answers: Record<string, 'Y'|'N'|'NA'>; // 5 个 Signalling
  rationale: string;
}
export interface RoB2Overall {
  study_id: string;
  study_type: 'RCT';
  domains: RoB2DomainRating[];
  overall: TrafficLightRating;
}
export type RobinsIDomain =
  | 'D1_confounding'|'D2_selection'|'D3_classification'
  | 'D4_deviations' |'D5_missing'  |'D6_measurement'|'D7_reporting';

// === 9c Abstractor ===
export type TriageDecision = 'include' | 'exclude' | 'review';
export interface StructuredPICO {
  p: { text: string; n?: number; condition?: string; age_min?:number; age_max?:number };
  i: { drug?: string; dose?: string; duration?: string; n?: number };
  c: { comparator: string; type?: 'active'|'placebo'|'other' };
  o: Array<{ name: string; mean_diff?: number; rr?: number; ci_low?:number; ci_high?:number; p_value?: number }>;
}
export interface TriageResult {
  record_id: string;
  pico?: StructuredPICO;
  decision: TriageDecision;
  confidence: number;     // 0~1.0
  reasons: string[];      // 可解释理由
  exclude_reason_ids?: ExcludeReasonId[];   // #2-#9
  failed_steps?: string[]; // LLM 解析失败时降级
}
```

---

## §2 · Wave 9a · Screening Dual-Phase（Funnel 10 步 + TA/Fulltext 双阶段）

### 2.1 FunnelProgressBar Props 契约
```ts
interface FunnelProgressBarProps {
  stats: FunnelStepStat[];              // 10 步
  studyType: 'RCT' | 'NRSI' | 'ALL';
  onStepClick?: (step: FunnelStepStat) => void;   // 点击跳表格
  "data-testid"?: string;               // fpb-step-{N1..E6}
}
```
- **硬锁**：step 前一步 count > 0 才解锁下一步；否则置灰不可点
- **颜色**：N1-N4 紫粉系，E1-E3 蓝系，E4-E5 绿/红系，E6 最终纳入绿底白边

### 2.2 9 项排除原因常量
```ts
export const EXCLUDE_REASONS_9A: Record<ExcludeReasonId, {
  label_cn: string; ta_allowed: boolean; ft_allowed: boolean;
}> = {
  2: { label_cn: '错误研究类型（非 RCT/NRSI）',  ta_allowed: true,  ft_allowed: true  },
  3: { label_cn: '错误人群（偏离 PICO P）',     ta_allowed: true,  ft_allowed: true  },
  4: { label_cn: '错误干预（偏离 PICO I）',     ta_allowed: true,  ft_allowed: true  },
  5: { label_cn: '错误对照（偏离 PICO C）',     ta_allowed: true,  ft_allowed: true  },
  6: { label_cn: '错误结局（偏离 PICO O）',     ta_allowed: false, ft_allowed: true  },
  7: { label_cn: '重叠数据（同一试验多报告）',  ta_allowed: false, ft_allowed: true  },
  8: { label_cn: '无全文（联系作者 2 次无回复）',ta_allowed: false, ft_allowed: true  },
  9: { label_cn: '其他（必填备注）',            ta_allowed: true,  ft_allowed: true  },
};
```
- **NOTOUCH-N1 保障**：`decision=exclude AND len(exclude_reason_ids)==0 → 后端拒绝写入`
- **Fulltext 证据链**：`meta_json.evidence_quotes = [{page,line,quote_text}]` 至少 1 条才允许 6-8

### 2.3 9a pytest 矩阵（S1~S10 共 15 个）
| ID | 名称 | 断言 |
|---|---|---|
| S1 | test_funnel_n4_after_dupe_is_less_than_n3 | N4 < N3（严格去重）|
| S2 | test_funnel_step_E1_equals_N4 | E1 = N4（所有去重后进入 TA）|
| S3 | test_exclude_reason_6_not_allowed_in_TA_stage | 后端拒绝 POST { stage=screening_ta, exclude_ids=[6] } 422 |
| S4 | test_exclude_reason_8_required_contact_log | stage=screening_fulltext + exclude_ids=[8] → meta_json.contact_attempts ≥ 2 |
| S5 | test_exclude_reason_9_required_rationale | exclude 9 → len(rationale) ≥ 20 chars |
| S6 | test_included_E6_equals_E4_minus_E5 | E6 = E4 - E5（最终纳入一致性）|
| S7 | test_funnel_step_locked_until_prev_step_gt0 | step 前一步 count=0 → GET /funnel 返回 locked=true |
| S8 | test_TA_include_400_records_screening_stats_integrity | 统计校验：screened = included_TA + excluded_TA |
| S9 | test_fulltext_exclude_evidence_quote_required | 6-8 排除需要 evidence_quotes ≥ 1 |
| S10 | test_evidence_artifact_screening_to_meta_query | meta 引擎 WHERE decision='include' AND stage IN('screening_fulltext','data_abstractor') → 返回 E6 |

### 2.4 9a vitest 矩阵（E1~E20 共 22 个）
| ID | 测试 | 断言 |
|---|---|---|
| E1-E10 | FunnelProgressBar 10 步颜色 & locked | snapshot |
| E11-E13 | EXCLUDE_REASONS_9A ta_allowed/ft_allowed 三档 | 6/7/8 → ta_allowed=false |
| E14-E16 | 双表格批量 Include/Exclude 按钮 (TA/FT) | onClick dispatch 正确 action |
| E17-E18 | ExcludeReasonDialog TA 阶段禁用 6-8 灰显 | disabled=true |
| E19 | Fulltext evidence quote Dialog page+line 输入 | 必填校验 |
| E20 | 10 步 step 前一步 locked → pointer-events none | CSS class |

---

## §3 · Wave 9b · ROB-2 & ROBINS-I（信号灯矩阵 + GRADE 联动）

### 3.1 RoB2Matrix Props 契约
```ts
interface RoB2MatrixProps {
  studies: (RoB2Overall | RobinsIOverall)[];
  editable?: boolean;
  onCellChange?: (studyId: string, domain: string, rating: TrafficLightRating) => void;
  "data-testid"?: string;          // rob2-cell-{studyId}-{domain}
}
```

### 3.2 TrafficLightCell 常量 3 色
```ts
export const TRAFFIC_LIGHT_COLORS: Record<TrafficLightRating, { bg: string; text: string; emoji: string }> = {
  low:           { bg: '#10b981', text: 'white',        emoji: '🟢' },
  some_concerns: { bg: '#fbbf24', text: '#78350f',      emoji: '🟡' },
  high:          { bg: '#ef4444', text: 'white',        emoji: '🔴' },
  critical:      { bg: '#dc2626', text: 'white',        emoji: '🔥' },  // ROBINS-I
  ni:            { bg: '#f1f5f9', text: '#64748b',      emoji: '➖' },
};
```

### 3.3 ROB-2 Overall 上卷规则（硬编码）
```python
# rob2_engine.py · 4 条规则
def calc_rob2_overall(domains: list[RoB2DomainRating]) -> TrafficLightRating:
  # R1: ANY 域 = high           → overall = high
  if any(d['rating']=='high' for d in domains): return 'high'
  # R2: ≥2 域 = some_concerns   → overall = some_concerns
  if sum(1 for d in domains if d['rating']=='some_concerns') >= 2: return 'some_concerns'
  # R3: EXACT 1 域 = some_concerns → overall = some_concerns
  if sum(1 for d in domains if d['rating']=='some_concerns') == 1: return 'some_concerns'
  # R4: ALL low                 → overall = low
  return 'low'
```
- **ROBINS-I 特例**：ANY D = `critical` → Overall = `critical`（最高上卷）

### 3.4 → GRADE 联动规则（只读 SQL 追加；NOTOUCH-N2 GRADE 引擎不变）
```sql
-- grade_engine.py ADDITIVE ONLY（追加一个 helper）
SELECT stage, decision, overall
FROM evidence_artifact
WHERE stage IN ('quality_ro','quality_nrsi') AND literature_record_id = ANY(%(study_ids)s)
```
| Overall 占比 | GRADE RoB 域降级 |
|---|---|
| Low ≥ 75% studies | 0 级（不降级）|
| Some Concerns ≥ 25% | -1 级 |
| High ≥ 25% **OR** ≥ 1 Critical | -2 级 |

### 3.5 9b pytest（R1~R16 共 16 个）
| ID | 测试 | 断言 |
|---|---|---|
| R1-R4 | ROB-2 4 条上卷规则逐用例 | 全部等价 calc_rob2_overall |
| R5-R6 | ROBINS-I critical 上卷 | 1 critical → Overall critical |
| R7 | calc_rob2 ALL low → low | |
| R8 | 1 some_concerns + rest low → some_concerns | |
| R9 | 2 some_concerns → some_concerns | |
| R10 | D1 high → overall high | |
| R11 | 5 signal Y→N→Y→Y→Y → D1=some (开放标签 HbA1c 规则) | |
| R12 | 3 signal 盲法未使用 + 主观结局 pain → D1=high | |
| R13-G1 | GRADE 联动：4 studies, 1 high(25%) → RoB 降级 -1 | |
| R14-G2 | 1 critical → GRADE RoB 降级 -2 | |
| R15-G3 | 全 Low → GRADE 0 降级 | |
| R16 | evidence_artifact stage=quality_ro 保存 → load 还原 | roundtrip 100% |

### 3.6 9b vitest（Q1~Q14 共 15 个）
Q1-Q5: TrafficLightCell 5 档 TrafficLightRating 颜色匹配 snapshot
Q6-Q10: RoB2Matrix 5 域 × 5 study 矩阵渲染
Q11: editable=false → pointer-events none
Q12: Overall column 重边框 (border 3px)
Q13: NRSI 研究 → ROBINS-I button（↪️ 跳转）
Q14: GRADE 联动 badge（显示 "RoB -1" / "-2"）
Q15: R3 单域 deep-dive card 5 signal 题 Y/N/NA

---

## §4 · Wave 9c · Abstractor Auto-Triager（SimHash + LLM + 3 档）

### 4.1 SimHash 算法（0 第三方依赖，64-bit）
```python
# simhash.py · 四个 helper
def tokenize_to_2shingles(text: str) -> list[str]: ...        # 2-shingle
def hash_64bit(token: str) -> int: ...                        # 内置 hashlib
def simhash(doc: str) -> int: ...                             # 权重 1
def hamming_distance(h1: int, h2: int) -> int: ...            # bin(x^y).count('1')
def jaccard(a: set[str], b: set[str]) -> float: ...           # len(inter)/len(union)
THRESHOLDS = { 'hamming_bits_max': 7, 'jaccard_min': 0.92 }
```

### 4.2 3 档 Triage 规则
```python
# abstractor.py
def triage(pico: StructuredPICO) -> tuple[TriageDecision, list[str], float]:
  # C1: 研究类型错误 → Exclude 0.2
  # C2: P 人群错 (e.g. T1DM for T2DM protocol) → Exclude 0.25
  # C3: P∩I∩C∩O 全匹配 & 结局有显著意义 → Include ≥ 0.85
  # C4: Any 缺失 / 模糊描述 → Review 0.45-0.85
  # C5: FALLBACK: LLM 解析失败 2 次 → Review, confidence = 0.5 + reasons
  confidence = 0.7 * PICO_match + 0.2 * study_type_ok + 0.1 * outcome_quality
```

### 4.3 Triage Result 3 档降级保护
```python
LLM_FALLBACK_ON = True      # LLM 不可用 → 只做标题 PICO 关键词匹配 → decision='review'
NEVER_AUTO_EXCLUDE_STUDY_TYPES = {'RCT','registry'}   # 高危不自动 Exclude
FALSE_NEGATIVE_TOLERANCE = 0.003   # < 0.3%（Gold Test 480 篇 ≤ 1 篇假阴）
```

### 4.4 9c pytest（A1~A18 共 18 个）
| ID | 测试 | 断言 |
|---|---|---|
| A1-A2 | SimHash same doc → hamming=0 | |
| A3 | 微小改动 doc1 vs doc1+comma → hamming ≤ 3 bits | |
| A4 | Jaccard 完全相同 → 1.0 | |
| A5 | Hamming 7 bits + Jaccard 0.93 → duplicate cluster | |
| A6 | Hamming 8 bits → NOT duplicate（边界）| |
| A7 | Triage: perfect PICO → Include + conf ≥ 0.85 | |
| A8 | Triage: 人群 T1DM → Exclude + exclude_reason_ids=[3] | |
| A9 | Triage: PICO missing P type → Review (0.62) | |
| A10 | LLM 解析失败 2 次 → 降级 Rule-Based Title Match → decision='review' + failed_steps=['pico_llm'] | |
| A11 | High risk: RCT study_type → NEVER AUTO EXCLUDE（即使 I 错 → Review）| |
| A12-A13 | 置信度公式：已知 4 种边界 → expected 值误差 ≤ 0.01 | |
| A14 | False negative 480 Gold Test → 假阴 ≤ 1 篇（≤ 0.21%）| |
| A15 | 保存 evidence_artifact stage=data_abstractor → roundtrip | |
| A16 | override_by_user_id 人工改推荐 → 写入 user id | |
| A17 | Dashboard 批处理：Include 45.5% / Review 27.5% / Exclude 26.9% 校验 | |
| A18 | 9c → 9a 衔接：`decision='include'` 9c → 自动解锁 screening_fulltext 阶段 | |

### 4.5 9c vitest（V1~V18 共 18 个）
V1-V3: ConfidenceBar 3 档颜色 (绿 92 / 黄 62 / 红 12) + 文字 label
V4-V6: AbstractorCard Include/Exclude/Review 三 snapshot
V7: Include 按钮 onClick → call useEvidenceArtifact.decide('include')
V8: Exclude 按钮 → call decide('exclude') + reason_ids=[2,3]
V9: 修改推荐按钮 → override 记录 user
V10-V12: 置信度公式边界渲染 (0.0/0.5/1.0)
V13-V15: SimHash 去重 (hamming 0/7/8) 徽章显示
V16: LLM failed icon → "⚠️ 规则降级"
V17: 3 档 Pipeline 进度条组件（step 1/2/3 点亮）
V18: Abstractor Dashboard 统计饼图 (45.5% + 27.5% + 26.9%)

---

## §5 · useEvidenceArtifact Hook（统一三模块注入式 Controller）
### 5.1 Props 契约
```ts
interface UseEvidenceArtifactOptions {
  literatureRecordId: string;
  injectFetchClient?: {
    list:    (q: EvidenceQuery)  => Promise<EvidenceArtifact[]>;
    decide:  (payload: DecidePayload) => Promise<EvidenceArtifact>;
    funnelStats?: (pi: string) => Promise<FunnelStepStat[]>;
  };
}
// 10 Actions: list / get(id) / decide(stage,decision)
//  / bulkDecide / funnelStats / rob2Evaluate / abstractorRunPipeline
//  / exportAsCSV / undo / reset
```
- **Injectable fetchClient 不变量**：vitest 0 mock 全局 fetch（注入对象）
- **Hard Lock 规则**：screening_fulltext 解锁条件：E2 (TA exclude) 完成后才能 POST

---

## §6 · Hard-Gate 验收标准（完成后 8 条过才能推进 writing-plans）
| # | 项 | 目标 |
|---|---|---|
| AC1 | pytest passed (全部) | ≥ 474 (原) + 15(9a) + 16(9b) + 18(9c) = **≥ 523** |
| AC2 | vitest passed (全部) | ≥ 459 (原) + 22(9a) + 15(9b) + 18(9c) + 10(hook) = **≥ 524** |
| AC3 | TOTAL passed | **≥ 1047** |
| AC4 | NOTOUCH-N1/N2/N3/N4 审计 | git diff → 0 变动已有签名 |
| AC5 | 0 新增第三方依赖 | package.json diff = 0 |
| AC6 | shared-sdk 全部 8 个类型 TSC 无错 | tsc --noEmit exit 0 |
| AC7 | 9b → 5 GRADE 联动 3 个规则 roundtrip 100% | pytest R13-R15 PASSED |
| AC8 | 9c False Negative Gold 480 篇测试 | ≤ 1 篇假阴 |

---

## §7 · 视觉与交互参考
```
打开 Visual Companion · 会话 PRD9:
  wave9-arch-s1-evidence-artifact-engine.html   (§1 Arch 12 文件清单)
  wave9-s2-screening-dual-phase.html            (§2 10 步漏斗 + 双阶段)
  wave9-s3-rob2-quality-matrix.html             (§3 ROB-2 5 域 × N + ROBINS-I 7 域)
  wave9-s4-abstractor-triager.html              (§4 三档 Abstractor + ConfidenceBar)
```
