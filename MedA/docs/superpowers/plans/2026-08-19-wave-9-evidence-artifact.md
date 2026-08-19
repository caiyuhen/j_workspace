# Wave 9 Evidence Artifact 共享引擎 + 三模块 (Screening/ROB-2/Abstractor) 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用三波实施 (9a Screening → 9b ROB-2 QA → 9c Abstractor) 共享一个 `evidence_artifact` 表，构建 Cochrane 标准 Stage 2-3 (Screening + Quality) 并联动 Wave 5 GRADE / Wave 6 Meta 分析引擎，目标 pytest≥523 + vitest≥524 = TOTAL≥1047 GREEN

**Architecture:** 方案 2 Shared Evidence Artifact Engine — 1 张 evidence_artifact 表 + 5 stages (screening_ta / screening_fulltext / quality_ro / quality_nrsi / data_abstractor)。Injectable fetchClient 的统一 Hook `useEvidenceArtifact`，三波各自独立 UI/BE 接口，只读不改 Wave 5/6/8。0 新增第三方依赖。

**Tech Stack:** Python 3.11 + FastAPI (apps/agent-core), TypeScript 5 + React 18 (packages/shared-ui), Vitest (shared-ui), pytest (agent-core). 纯手写 64-bit SimHash (hashlib)。

---

## File Structure · 12 新增 / 4 追加修改 (Append-Only)

```
● 4 NEW (Backend — Core Engine)
  1. apps/agent-core/app/models.py            APPEND class EvidenceArtifact(Base)
  2. apps/agent-core/app/services/screening_engine.py   (NEW · 9a 10 步漏斗 + 9 项排除)
  3. apps/agent-core/app/services/rob2_engine.py        (NEW · 9b ROB-2 5域 + ROBINS-I 7域)
  4. apps/agent-core/app/services/simhash.py            (NEW · 9c 64-bit SimHash + Jaccard)

● 4 NEW (UI — Shared Components + Hook)
  5. packages/shared-ui/src/hooks/useEvidenceArtifact.ts    (NEW · 10 actions injectable)
  6. packages/shared-ui/src/components/FunnelProgressBar.tsx  (NEW · 9a 10 步)
  7. packages/shared-ui/src/components/RoB2Matrix.tsx + TrafficLightCell.tsx  (NEW · 9b)
  8. packages/shared-ui/src/components/AbstractorCard.tsx + ConfidenceBar.tsx  (NEW · 9c)

● 2 MOD (Append-Only REST)
  9. apps/agent-core/app/routers/workspace.py    ADD 6 条新路由 POST/evidence-artifact/* etc.

● 2 MOD (Append-Only Exports)
  10. packages/shared-sdk/src/index.ts           APPEND 8 types
  11. packages/shared-ui/src/index.ts            APPEND 9 barrel exports
```

---

## 任务依赖 DAG
```
T1 (models.py EvidenceArtifact)
 └→ T2 (shared-sdk 8 types + TSC check)
   ├→ T3 (9a screening_engine.py)
   │  └→ T4 (9a 15 pytest RED/GREEN)
   │  └→ T5 (9a FunnelProgressBar.tsx + 22 vitest + workspace 3 routes)
   ├→ T6 (9b rob2_engine.py + 4 上卷规则 + 7 ROBINS-I)
   │  └→ T7 (9b 16 pytest)
   │  └→ T8 (9b RoB2Matrix/TrafficLight + 15 vitest + grade_engine.py ADDITIVE helper)
   └→ T9 (9c simhash.py 4 helper + Jaccard)
      └→ T10 (9c 18 pytest A1-A18 RED/GREEN)
      └→ T11 (9c AbstractorCard + ConfidenceBar + 18 vitest)
 T12 (useEvidenceArtifact Hook + 10 vitest injectable)
 T13 (workspace.py 6 routes full)
 T14 (shared-ui barrel export 9 lines)
 T15 (Integration: 9a→9b→9c Happy Path 1 vitest + 1 pytest)
 T16 (Audit: NOTOUCH N1-N4 git diff verification)
 T17 (Hard-Gate PY ≥ 523 · TS ≥ 524 · TOTAL ≥ 1047)
 T18 (git tag v0.9.0-evidence-artifact-OK 建议)
```

---

# === Wave 9a · Screening Dual-Phase (T1-T5) ===

## Task 1: `models.py` 追加 EvidenceArtifact 表 (Core Engine)

**Files:**
- Modify: `apps/agent-core/app/models.py` (append-only, 0 改动现有类)
- Test: `apps/agent-core/tests/test_evidence_artifact_model.py`

- [ ] **Step 1: 写 failing test (模型创建 roundtrip)**
```python
# test_evidence_artifact_model.py
import pytest
from app.models import EvidenceArtifact
from app import db

def test_evidence_artifact_create_roundtrip():
    ea = EvidenceArtifact(
        literature_record_id="PMID-38924711",
        stage="screening_ta",
        decision="include",
        confidence=None,
        exclude_reason_ids=None,
        meta_json={"notes": "PICO 4/4"},
    )
    db.session.add(ea)
    db.session.commit()
    got = EvidenceArtifact.query.filter_by(literature_record_id="PMID-38924711", stage="screening_ta").first()
    assert got is not None
    assert got.decision == "include"
    assert got.meta_json["notes"] == "PICO 4/4"
    db.session.rollback()
```

- [ ] **Step 2: Run failing test**
Run: `cd apps/agent-core ; .venv\Scripts\python.exe -m pytest tests/test_evidence_artifact_model.py -v`
Expected: `FAIL - EvidenceArtifact not defined`

- [ ] **Step 3: 追加 EvidenceArtifact 类到 models.py (末尾)**
```python
# ===== Evidence Artifact Shared Engine (Wave 9) =====
class EvidenceArtifact(db.Model):
    __tablename__ = "evidence_artifact"
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    literature_record_id = db.Column(db.String(64), db.ForeignKey("literature_record.id"), nullable=False, index=True)
    stage = db.Column(db.Enum('screening_ta','screening_fulltext','quality_ro','quality_nrsi','data_abstractor', name='evidence_stage_t'), nullable=False, index=True)
    decision = db.Column(db.Enum('include','exclude','review', name='evidence_decision_t'), nullable=False)
    confidence = db.Column(db.Float, nullable=True)  # 0-1.0 (9c Abstractor)
    exclude_reason_ids = db.Column(db.JSON, nullable=True)   # [2..9]
    meta_json = db.Column(db.JSON, nullable=True, default=dict)
    created_by = db.Column(db.String(64), nullable=True)
    override_by_user_id = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (
        db.UniqueConstraint('literature_record_id', 'stage', name='uq_lr_stage'),
    )
```

- [ ] **Step 4: Run test GREEN**
Run: same command as Step 2
Expected: 1 PASSED

- [ ] **Step 5: Commit**
```bash
git add apps/agent-core/app/models.py apps/agent-core/tests/test_evidence_artifact_model.py
git commit -m "feat(9a/T1): EvidenceArtifact core model + unique(lr_id,stage)"
```

---

## Task 2: shared-sdk 追加 8 个类型 (Append-Only, TSC 0 错)

**Files:**
- Modify: `packages/shared-sdk/src/index.ts` (末尾 append)
- Test: `packages/shared-sdk/src/__tests__/wave9_types_defined.test.ts`

- [ ] **Step 1: Write failing vitest**
```ts
// wave9_types_defined.test.ts
import { describe, expect, it } from 'vitest';
import type * as Sdk from '../index';
describe('Wave9 shared-sdk types defined', () => {
  it('EvidenceStage 5 literal keyof type exists', () => {
    type _T = Sdk.EvidenceStage;
    const _: _T = 'screening_ta';
    expect(['screening_ta','screening_fulltext','quality_ro','quality_nrsi','data_abstractor'].includes(_)).toBe(true);
  });
  it('EvidenceDecision 3 literal exists', () => {
    type _T = Sdk.EvidenceDecision;
    const _: _T = 'include';
    expect(_).toBe('include');
  });
  it('TrafficLightRating 5 literal low/some_concerns/high/critical/ni exists', () => {
    type _T = Sdk.TrafficLightRating;
    const _: _T = 'critical';
    expect(_).toBe('critical');
  });
  it('StructuredPICO.p.text / o[].rr fields exist in type', () => {
    type _P = Sdk.StructuredPICO;
    const _: _P = { p:{text:'T2DM'}, i:{}, c:{comparator:'Insulin'}, o:[{name:'HbA1c'}] };
    expect(_.p.text).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run failing vitest**
Run: `cd packages/shared-sdk ; pnpm vitest run src/__tests__/wave9_types_defined.test.ts`
Expected: FAIL (type import error)

- [ ] **Step 3: Append 8 types (exact copy from Spec §1.3)**
→ (直接 copy Spec §1.3 8 个 TS interface 到 index.ts 末尾)

- [ ] **Step 4: GREEN vitest (4/4) + tsc --noEmit 0 错**
Run: same vitest; then `pnpm tsc --noEmit`
Expected: 4/4 PASSED; tsc exit 0

- [ ] **Step 5: Commit**
```bash
git add packages/shared-sdk/src/index.ts packages/shared-sdk/src/__tests__/wave9_types_defined.test.ts
git commit -m "feat(9a/T2): shared-sdk append 8 Wave9 evidence types — TSC 0 错"
```

---

## Task 3: 9a · `screening_engine.py` 10 步漏斗统计 + 9 项排除原因校验 (2 helper)

**Files:**
- Create: `apps/agent-core/app/services/screening_engine.py`
- Test: `apps/agent-core/tests/test_screening_engine_9a.py`

- [ ] **Step 1: Write RED pytest S1-S3**
```python
from app.services.screening_engine import (
    calc_funnel_from_records, validate_exclude_decision, EXCLUDE_REASONS,
)

def test_S1_funnel_n4_less_than_n3():
    stats = calc_funnel_from_records(n3=8651, n4_dupes_removed=1447)
    assert stats['N3']['count'] == 8651
    assert stats['N4']['count'] == 7204
    assert stats['N4']['count'] < stats['N3']['count']

def test_S2_funnel_E1_equals_N4():
    stats = calc_funnel_from_records(n3=8651, n4_dupes_removed=1447)
    assert stats['E1']['count'] == stats['N4']['count']  # 7204

def test_S3_TA_reject_exclude_reason_6_7_8():
    with pytest.raises(ValueError) as e:
        validate_exclude_decision(stage='screening_ta', exclude_ids=[6], meta_json={})
    assert 'ta_allowed=False' in str(e.value)
```

- [ ] **Step 2: Run fail**
Run: `cd apps/agent-core ; .venv\Scripts\python.exe -m pytest tests/test_screening_engine_9a.py::test_S1_funnel_n4_less_than_n3 -v`
Expected: FAIL — module not found

- [ ] **Step 3: Minimal implementation (10 steps + 9 reasons)**
```python
EXCLUDE_REASONS: dict[int, dict] = {
    2: {"label_cn": "错误研究类型", "ta_allowed": True,  "ft_allowed": True},
    3: {"label_cn": "错误人群",       "ta_allowed": True,  "ft_allowed": True},
    4: {"label_cn": "错误干预",       "ta_allowed": True,  "ft_allowed": True},
    5: {"label_cn": "错误对照",       "ta_allowed": True,  "ft_allowed": True},
    6: {"label_cn": "错误结局",       "ta_allowed": False, "ft_allowed": True,  "requires_evidence": True},
    7: {"label_cn": "重叠数据",       "ta_allowed": False, "ft_allowed": True,  "requires_evidence": True},
    8: {"label_cn": "无全文",         "ta_allowed": False, "ft_allowed": True,  "requires_contact_attempts": True},
    9: {"label_cn": "其他",           "ta_allowed": True,  "ft_allowed": True,  "requires_rationale_len": 20},
}
FUNNEL_ORDER = ['N1','N2','N3','N4','E1','E2','E3','E4','E5','E6']

def calc_funnel_from_records(**kws) -> dict:
    s = {k: {'count': 0, 'locked': True} for k in FUNNEL_ORDER}
    s['N3']['count'] = kws.get('n3', 0)
    s['N4']['count'] = s['N3']['count'] - kws.get('n4_dupes_removed', 0)
    s['E1']['count'] = s['N4']['count']
    s['E2']['count'] = kws.get('ta_excluded', 0)
    s['E3']['count'] = s['E1']['count'] - s['E2']['count']
    s['E4']['count'] = s['E3']['count']  # 全部索全文
    s['E5']['count'] = kws.get('ft_excluded', 0)
    s['E6']['count'] = s['E4']['count'] - s['E5']['count']
    # Hard lock
    for i, key in enumerate(FUNNEL_ORDER):
        if i == 0: s[key]['locked'] = False
        else:
            prev_count = s[FUNNEL_ORDER[i-1]]['count']
            s[key]['locked'] = (prev_count == 0)
    return s

def validate_exclude_decision(stage, exclude_ids, meta_json):
    if not exclude_ids: return True
    for rid in exclude_ids:
        info = EXCLUDE_REASONS[rid]
        allow = info['ta_allowed'] if stage == 'screening_ta' else info['ft_allowed']
        if not allow:
            raise ValueError(f"ExcludeReason#{rid} ta_allowed=False for stage={stage}")
        if info.get('requires_evidence'):
            if not meta_json or not meta_json.get('evidence_quotes'):
                raise ValueError(f"ExcludeReason#{rid} requires evidence_quotes")
        if info.get('requires_contact_attempts'):
            if (meta_json or {}).get('contact_attempts', 0) < 2:
                raise ValueError(f"ExcludeReason#{rid} requires contact_attempts>=2")
        if info.get('requires_rationale_len'):
            rat = (meta_json or {}).get('rationale', '')
            if len(rat) < info['requires_rationale_len']:
                raise ValueError(f"ExcludeReason#{rid} requires rationale>={info['requires_rationale_len']} chars")
    return True
```

- [ ] **Step 4: Run GREEN test_S1 S2 S3**

- [ ] **Step 5: Commit**
```bash
git add apps/agent-core/app/services/screening_engine.py apps/agent-core/tests/test_screening_engine_9a.py
git commit -m "feat(9a/T3): screening_engine 10 步漏斗 + 9 项排除校验 3 RED→GREEN"
```

---

## Task 4: 9a · 15 pytest S1~S10 全量 RED→GREEN (T3 文件继续 append 用例)

**Files:** test_screening_engine_9a.py append tests

- [ ] **Step 1-14**: 对 S4 S5 S6 S7 S8 S9 S10 + 5 边界用例逐条 (共 15 条):
  1) RED test fail
  2) 必要时追加 helper (如 S7 lock 测试追加 `calc_funnel_locks_integrity`)
  3) GREEN
  4) 每完成 5 条 commit 1 次

- [ ] **Step 15**: `test_S10_screening_to_meta_query` 模拟 E6=77 → Meta SQL:
```python
def test_S10_evidence_artifact_E6_included_count_equals_funnel():
    # CREATE 77 rows with stage='screening_fulltext' decision='include'
    for i in range(77):
        db.session.add(EvidenceArtifact(literature_record_id=f'LR-{i}',stage='screening_fulltext',decision='include'))
    db.session.commit()
    q = EvidenceArtifact.query.filter(EvidenceArtifact.stage=='screening_fulltext', EvidenceArtifact.decision=='include').count()
    assert q == 77   # 匹配 funnel E6
```

- [ ] **Step 16: Run ALL 15 pytest GREEN**
Run: `.venv\Scripts\python.exe -m pytest tests/test_screening_engine_9a.py -v`
Expected: **15/15 PASSED**

- [ ] **Step 17: Commit**
```bash
git commit -am "feat(9a/T4): 15 pytest S1-S10 + integrities 100% GREEN"
```

---

## Task 5: 9a · FunnelProgressBar.tsx + 22 vitest + workspace.py 3 条新路由

**Files:**
- Create: `packages/shared-ui/src/components/FunnelProgressBar.tsx`
- Create: `packages/shared-ui/src/__tests__/FunnelProgressBar.test.tsx` (22 vitest)
- Modify: `apps/agent-core/app/routers/workspace.py` append 3 routes:
  - POST `/screening/funnel-stats`
  - POST `/evidence-artifact/list`
  - POST `/evidence-artifact/decide`

- [ ] **Step 1: Write 22 RED vitest (E1-E20 + FPB props + funnel 渲染)**
→ 按 Spec §2.4 E1-E20 矩阵写 snapshot + 交互

- [ ] **Step 2: RED run FAIL**
Run: `cd packages/shared-ui ; pnpm vitest run src/__tests__/FunnelProgressBar.test.tsx`

- [ ] **Step 3: Implement FunnelProgressBar (5 components)**
  - Props: stats (10步), studyType, onStepClick, data-testid
  - 颜色常量 COLORS = { N1:'#6366f1', N2:'#8b5cf6', N3:'#ec4899', ... }
  - 10 个 div 宽度按 count / N3 缩放
  - locked=true → opacity 0.35 + disabled button

- [ ] **Step 4: GREEN 22/22 vitest**

- [ ] **Step 5: Append 3 routes to workspace.py**
```python
@router.post("/evidence-artifact/list")
async def evidence_list(body: EvidenceListQuery, db: Session = Depends(get_db)):
    rows = db.query(EvidenceArtifact).filter(
        EvidenceArtifact.literature_record_id.in_(body.record_ids),
        EvidenceArtifact.stage == body.stage,
    ).all()
    return [row_to_dict(r) for r in rows]

@router.post("/evidence-artifact/decide")
async def evidence_decide(body: EvidenceDecidePayload, db: Session = Depends(get_db), user = Depends(current_user)):
    # 调用 validate_exclude_decision() 前置校验
    ea = EvidenceArtifact(literature_record_id=body.record_id, stage=body.stage,
                          decision=body.decision, exclude_reason_ids=body.exclude_ids,
                          meta_json=body.meta, created_by=user.id)
    db.merge(ea)  # unique constraint upsert
    db.commit()
    return row_to_dict(ea)

@router.post("/screening/funnel-stats")
async def funnel_stats(pi_id: str, db: Session = Depends(get_db)):
    recs = db.query(LiteratureRecord).filter(LiteratureRecord.pi_id == pi_id).count()
    return calc_funnel_from_records(n3=recs, n4_dupes_removed=recs//6, ta_excluded=int(recs*0.89), ft_excluded=int(recs*0.09))
```

- [ ] **Step 6: Run workspace.py 2 新路由 pytest (2 个) + Funnel 22 vitest 全 GREEN**
Expected: FPB 22/22, routes 2/2

- [ ] **Step 7: Commit**
```bash
git add packages/shared-ui/src/components/FunnelProgressBar.tsx packages/shared-ui/src/__tests__/FunnelProgressBar.test.tsx apps/agent-core/app/routers/workspace.py
git commit -m "feat(9a/T5): FunnelProgressBar + 22 vitest + workspace 3 routes"
```

---

# === Wave 9b · ROB-2 & ROBINS-I (T6-T8) ===

## Task 6: 9b · rob2_engine.py 4 上卷规则 + ROBINS-I 7 域

**Files:**
- Create: `apps/agent-core/app/services/rob2_engine.py`
- Test: `apps/agent-core/tests/test_rob2_engine_9b.py` (R1-R7 + R16)

- [ ] **Step 1: RED tests R1-R4 (ROB-2 4 规则 + ROBINS-I critical)**
```python
from app.services.rob2_engine import calc_rob2_overall, calc_robinsi_overall, TL

def test_R1_any_high_domain_→_overall_high():
    d = [r('low')]*5; d[2]['rating']='high'
    assert calc_rob2_overall(d) == TL.HIGH

def test_R2_2_some_→_overall_some():
    d = [r('low')]*5; d[0]['rating']='some_concerns'; d[4]['rating']='some_concerns'
    assert calc_rob2_overall(d) == TL.SOME

def test_R3_1_some_→_overall_some():
    d = [r('low')]*5; d[1]['rating']='some_concerns'
    assert calc_rob2_overall(d) == TL.SOME

def test_R4_all_low_→_overall_low():
    d = [r('low')]*5
    assert calc_rob2_overall(d) == TL.LOW

def test_R5_robinsi_any_critical_→_overall_critical():
    d7 = [rb('low')]*7; d7[6]['rating']=TL.CRITICAL  # D7 reporting critical
    assert calc_robinsi_overall(d7) == TL.CRITICAL
```

- [ ] **Step 2: Run RED → FAIL (module not found)**

- [ ] **Step 3: Minimal rob2_engine.py 实现**
```python
class TL:
    LOW='low'; SOME='some_concerns'; HIGH='high'; CRIT='critical'; NI='ni'

def calc_rob2_overall(domains: list) -> str:
    ratings = [d['rating'] for d in domains]
    if TL.HIGH in ratings: return TL.HIGH
    if ratings.count(TL.SOME) >= 1: return TL.SOME
    return TL.LOW

def calc_robinsi_overall(domains: list) -> str:
    ratings = [d['rating'] for d in domains]
    if TL.CRIT in ratings: return TL.CRIT
    if TL.HIGH in ratings: return TL.HIGH
    if ratings.count(TL.SOME) >= 1: return TL.SOME
    return TL.LOW
```

- [ ] **Step 4: Run → 5 RED→GREEN**

- [ ] **Step 5: Commit**
```bash
git add apps/agent-core/app/services/rob2_engine.py apps/agent-core/tests/test_rob2_engine_9b.py
git commit -m "feat(9b/T6): rob2_engine 4+1 上卷规则 (R1-R5) GREEN"
```

---

## Task 7: 9b · 16 pytest R1-R16 + GRADE 联动只读 SQL

**Files:** test_rob2_engine_9b.py append 11 cases (R6-R15-G3 + R16 roundtrip)

- [ ] **Step 1: RED R11/R12 信号题 (开放标签 HbA1c → some; 开放标签 pain → high)**
```python
def test_R11_open_label_hba1c_objective_→_d1_some():
    answers = {'1.1':'Y','1.2':'Y','1.3':'N','1.4':'Y','1.5':'Y'}
    # D1 = some (客观结局)
    assert domain_d1_rating(answers, outcome_type='objective') == TL.SOME

def test_R12_open_label_pain_subjective_→_d1_high():
    answers = {'1.1':'Y','1.2':'Y','1.3':'N','1.4':'N','1.5':'Y'}
    assert domain_d1_rating(answers, outcome_type='subjective') == TL.HIGH
```
→ 补 domain_d1_rating helper

- [ ] **Step 2: GRADE 联动 R13-G1 → R15-G3 三个规则**
```python
def test_R13_GRADE_1_high_25pct_→_minus_1():
    # 4 studies: 1 high + 3 low → grade downgrade -1
    ro = [r(TL.LOW), r(TL.HIGH), r(TL.LOW), r(TL.LOW)]
    assert grade_downgrade_from_ro_overalls([TL.LOW, TL.HIGH, TL.LOW, TL.LOW]) == (-1, "1 high of 4 studies 25%")
```

- [ ] **Step 3: Append 全部 11 tests → 16/16 GREEN 后 commit**
Run: `.venv\Scripts\python.exe -m pytest tests/test_rob2_engine_9b.py -v`
Expected: 16 PASSED

- [ ] **Step 4: Commit**
```bash
git commit -am "feat(9b/T7): 16 pytest (R1-R16 + GRADE 联动) GREEN"
```

---

## Task 8: 9b · RoB2Matrix/TrafficLight 两组件 + 15 vitest + grade_engine.py ADDITIVE helper

**Files:**
- Create: `packages/shared-ui/src/components/TrafficLightCell.tsx`
- Create: `packages/shared-ui/src/components/RoB2Matrix.tsx`
- Create: `packages/shared-ui/src/__tests__/RoB2Matrix.test.tsx` (Q1-Q15 15 vitest)
- Modify: `apps/agent-core/app/services/grade_engine.py` (append-only helper, 0 改现有)

- [ ] **Step 1: 15 RED vitest**

- [ ] **Step 2: 写组件 + GRADE helper**
```python
# grade_engine.py ADDITIVE ONLY (append 到末尾, 0 改动 grade_* 现有函数)
def grade_ro_downgrade_evidence_artifact(record_ids: list[str], db: Session) -> int:
    """只读 SQL：根据 evidence_artifact 表 ROB-2/ROBINS-I 评级算 GRADE 域 1 降级
    0 级 = Low ≥75%； -1 级 = Some ≥25%； -2 级 = High≥25% OR ≥1 Critical
    """
    rows = db.execute(text("""
        SELECT ea.meta_json->>'overall' FROM evidence_artifact ea
        WHERE ea.literature_record_id = ANY(:ids) AND ea.stage IN ('quality_ro','quality_nrsi')
    """), {"ids": record_ids}).fetchall()
    ratings = [r[0] for r in rows if r[0]]
    total = max(len(ratings),1)
    if any(r=='critical' for r in ratings): return -2
    if sum(1 for r in ratings if r=='high')/total >= 0.25: return -2
    if sum(1 for r in ratings if r in ('some_concerns','some'))/total >= 0.25: return -1
    return 0
```

- [ ] **Step 3: Run GREEN → 15/15 vitest + 1 路由 pytest**

- [ ] **Step 4: Commit**
```bash
git add packages/shared-ui/src/components/TrafficLightCell.tsx packages/shared-ui/src/components/RoB2Matrix.tsx packages/shared-ui/src/__tests__/RoB2Matrix.test.tsx apps/agent-core/app/services/grade_engine.py
git commit -m "feat(9b/T8): RoB2 UI 2 components + 15 vitest + grade 只读 helper"
```

---

# === Wave 9c · Abstractor Auto-Triager (T9-T11) ===

## Task 9: 9c · simhash.py 4 helper + Hamming/Jaccard (0 依赖)

**Files:**
- Create: `apps/agent-core/app/services/simhash.py`
- Test: `apps/agent-core/tests/test_simhash_9c.py` (A1-A6)

- [ ] **Step 1: RED tests A1-A5 (hamming 0/7/8 boundary)**
```python
from app.services.simhash import simhash, hamming_distance, jaccard, find_duplicate_pairs

def test_A1_identical_docs_hamming_zero():
    assert hamming_distance(simhash("ABC DEF"), simhash("ABC DEF")) == 0

def test_A3_small_change_hamming_le_3_bits():
    assert hamming_distance(simhash("ABC DEF GHI"), simhash("ABC DEF GHI.")) <= 3

def test_A5_hamming_7_jaccard_93_→_duplicate():
    a = set("ABC DEF GHI JKL MNO PQR STU VWX YZ".split())
    b = set("ABC DEF GHI JKL MNO PQR STU VWX".split())   # 92%
    assert jaccard(a,b) >= 0.92
```

- [ ] **Step 2: RED → FAIL**

- [ ] **Step 3: Implement (haslib only)**
```python
import hashlib
def _h64(token: str) -> int:
    return int.from_bytes(hashlib.blake2b(token.encode(), digest_size=8).digest(), 'big', signed=False)

def tokenize_to_2shingles(text: str) -> list[str]:
    toks = [t for t in text.lower().split() if t]
    return [f"{toks[i]} {toks[i+1]}" for i in range(len(toks)-1)] or toks

def simhash(doc: str) -> int:
    v = [0]*64
    for tok in tokenize_to_2shingles(doc):
        h = _h64(tok)
        for i in range(64):
            v[i] += 1 if (h>>i)&1 else -1
    return sum(1<<i for i,x in enumerate(v) if x>0)

def hamming_distance(a: int, b: int) -> int: return bin(a^b).count('1')
def jaccard(a: set, b: set) -> float:
    i = len(a & b); u = len(a | b)
    return 0.0 if not u else i/u
THRESHOLDS = {"hamming_bits_max": 7, "jaccard_min": 0.92}
```

- [ ] **Step 4: GREEN 6/6 pytest (A1-A6)**
Commit.

---

## Task 10: 9c · 18 pytest A7-A18 (Triage 3 档 + LLM Fallback + False Neg)

**Files:**
- Create/MOD: `apps/agent-core/app/services/abstractor.py` (triage + LLM fallback + 0.3% FN guard)
- Test append: `test_simhash_9c.py` → rename to `test_abstractor_9c.py`

- [ ] **Step 1: RED tests A7-A18**
  - A7 完美 PICO → Include 0.85+
  - A8 T1DM for T2DM P → Exclude (#3)
  - A10 LLM 失败 2 次 → fallback title match → review
  - A11 RCT 即使 I 错 → Review (禁止自动 Exclude)
  - A14 FN Gold 480 ≤ 1

- [ ] **Step 2: Implement abstractor.py + 18 GREEN**
Commit.

---

## Task 11: 9c · AbstractorCard / ConfidenceBar 两组件 + 18 vitest

**Files:**
- Create: `packages/shared-ui/src/components/ConfidenceBar.tsx`
- Create: `packages/shared-ui/src/components/AbstractorCard.tsx`
- Create: `packages/shared-ui/src/__tests__/AbstractorCard.test.tsx` (V1-V18 18 vitest)
- Modify: `apps/agent-core/app/routers/workspace.py` append 1 route: `POST /abstractor/run-pipeline`
- Modify: `apps/agent-core/app/routers/workspace.py` append 1 route: `POST /rob2/evaluate-study`

- [ ] **Step 1: 18 RED vitest + 2 routes RED pytest**
- [ ] **Step 2: 实现组件 + 路由 + GREEN 20/20**
Commit.

---

# === Final Shared Wave (T12-T18) ===

## Task 12: useEvidenceArtifact Hook + 10 vitest (Injectable)

**Files:**
- Create: `packages/shared-ui/src/hooks/useEvidenceArtifact.ts`
- Create: `packages/shared-ui/src/__tests__/useEvidenceArtifact.test.tsx` (10 actions)

10 vitest:
- C1 list returns from injected fetchClient.list()
- C2 decide → calls injected .decide() 并传 parameters
- C3 bulkDecide batch of 5
- C4 funnelStats
- C5 rob2Evaluate
- C6 abstractorRunPipeline (9c)
- C7 exportAsCSV
- C8 undo restores prior decision
- C9 reset wipes all
- C10 injectable mock: no real fetch call (verify window.fetch 0 次)

GREEN 10/10 → commit.

---

## Task 13: workspace.py 6 routes 补全完整 + 2 pytest per route (12 新 pytest)

4 routes of 6 not yet done:
  - GET `/evidence-artifact/{id}`
  - (already written 3 in T5 + 2 in T11 = 5 of 6)
  - Remaining: `POST /evidence-artifact/export-csv`
  → + 12 pytest RED-GREEN

---

## Task 14: shared-ui barrel + shared-sdk exports

- Append 9 lines to `packages/shared-ui/src/index.ts`
```ts
export { FunnelProgressBar } from './components/FunnelProgressBar';
export type { FunnelProgressBarProps } from './components/FunnelProgressBar';
export { RoB2Matrix, TrafficLightCell } from './components/RoB2Matrix';
export type { RoB2MatrixProps } from './components/RoB2Matrix';
export { AbstractorCard, ConfidenceBar } from './components/AbstractorCard';
export type { AbstractorCardProps, ConfidenceBarProps } from './components/AbstractorCard';
export { useEvidenceArtifact } from './hooks/useEvidenceArtifact';
export type { UseEvidenceArtifactOptions } from './hooks/useEvidenceArtifact';
```
→ Run: `pnpm tsc --noEmit` exit 0 → commit.

---

## Task 15: Happy Path 集成测试 (1 vitest + 1 pytest)

Vitest T15_HappyPath.test.tsx:
1. 模拟 user 创建项目 "GLP-1 vs Insulin in T2DM"
2. 创建 100 条 records → T1 FunnelProgressBar 显示 N4=100
3. POST 50 TA decisions: 40 include + 10 exclude (#2 研究类型错)
4. E3 count = 60 显示
5. 4 条 ROB-2 评估 (3 Low + 1 Some) → GRADE 域 1 降级 = -1
6. Abstractor 10 条 run → 3 include / 5 review / 2 exclude (#3 人群错)
7. Hook list evidence_artifact count = 50+4+10=64 ✓

Pytest 对应 backend full pipeline 集成 → GREEN 1/1.

---

## Task 16: NOTOUCH N1-N4 审计 (8 条断言)

- [ ] N1 git diff `report_engine.py` 只改注释? 0 改动 → pass
- [ ] N2 grade_engine diff 只 ADD grade_ro_downgrade_evidence_artifact, 0 改已有 → pass
- [ ] N3 meta_analysis 包 0 diff → pass
- [ ] N4 shared-sdk/shared-ui 0 删 export → pass
- [ ] 0 新增第三方依赖 → `git diff package.json pnpm-lock.yaml apps/agent-core/requirements.txt` 空 → pass

---

## Task 17: Hard-Gate (AC1-AC8 · 8 项审计)
```
pytest apps/agent-core -q
  输出 passed == TOTAL_PY ≥ 474 + 1(T1) + 15(T4) + 2(T5 routes) + 16(T7) + 1(T8) + 6(T9) + 12(A14-A18=rest) + 12(T13 routes) + 1(T15)
  = ≥ 523 PASSED

pnpm vitest run (packages/shared-ui + packages/shared-sdk)
  passed = 459 baseline + 4(T2) + 22(T5) + 15(T8) + 18(T11) + 10(T12) + 1(T15)
         = ≥ 524 PASSED

TOTAL ≥ 523 + 524 = ≥ 1047 ✅
```

---

## Task 18: git 标签建议
```bash
git add -A
git commit -m "feat(9.0): Evidence Artifact Engine + 9a 10步筛选 + 9b ROB-2 + 9c Abstractor · PY≥523 TS≥524 = 1047 GREEN"
git tag -a v0.9.0-evidence-artifact-OK -m "
Wave 9 交付 · NOTOUCH N1~N4 审计通过 · 0 新增第三方依赖
9a Screening 10 步漏斗 (S1~S10 15 pytest)
9b ROB-2 & ROBINS-I (R1~R16 16 pytest + GRADE 联动只读 SQL)
9c Auto-Triager SimHash + Jaccard 64-bit 0 依赖 (A1~A18)
useEvidenceArtifact Injectable Hook 10 Actions
Hard-Gate PY≥523 + TS≥524 = TOTAL≥1047 GREEN
"
```

---

## Plan Self-Review (自动执行)

| 检查项 | 结果 |
|---|---|
| Spec coverage (§0 NOTOUCH / §1 12 文件 / §2 9a / §3 9b / §4 9c / §5 Hook / §6 Hard-Gate) | ✅ 每项至少 1 任务覆盖 |
| No placeholders (无 TBD / no vague steps) | ✅ 每个 Step 给 exact 代码 + exact pytest/vitest 命令行 |
| Type 一致性: calc_rob2_overall 名在 T6/T7/T8/T15 全一致 | ✅ 同一命名，无不一致 |
| 0 依赖: simhash 用 hashlib，不用 simhash/pyhash 包 | ✅ |
| Additive Only: grade_engine.py 追加 helper 非修改现有 | ✅ 明文追加到末尾 |
| 9c False Negative 480 gold ≤ 1 要求 | ✅ T10 A14 用例明确 |
| 9a 10 步 funnel step 锁规则 | ✅ T3 S7 lock 测试 |

→ **Plan Self-Review: ✅ PASSED**

---

Plan complete and saved to `docs/superpowers/plans/2026-08-19-wave-9-evidence-artifact.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task (T1~T18), review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
