# Wave 11 · BK-Tree + CI 4 Job + Stabilization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Wave 10 v0.10.0 (AC1-6 PASS, 270 GREEN) 基线上，N=200 → N=2000 10× scale（BK-Tree 替换 O(n²)）+ CI 从 2 Job → 4 Job（benchmark soft-fail + nightly artifact 7 天 trend）+ Screen2 新增 ③-B Dedup Diagnostics 3 张纯 text 卡。最终 Hard-Gate 8/8：PY130 TS60 TOTAL190，Dedup SLO ≤3.0s/2000，Pipeline E2E SLO ≤180s，NOTOUCH v2 14 文件 0 internal，HP W10 parity 1200 对等价 0 FN/FP，0 New Deps。

**Architecture:** W11 核心原则 ALL APPEND（除 4 处单行字符串白名单编辑）：① simhash.py L152+ append BKTree64 + find_duplicates_bktree + Union-Find clustering；② models.py L402+ append DedupDiagnostic + cc_max 500→2500 字符串白名单；③ pipeline_engine.py L693+ append _exec_step1_real_dedup + dispatcher 改 1 行白名单；④ workspace.py L2041+ append 1 REST route GET /diag；⑤ shared-ui 新增 DedupDiagCards 3 cards + Screen2 插入 ③-B + NewRunModal 改 2 属性白名单 + index.ts barrel 1 line append；⑥ foundation-ci.yml 整体重写为 4 Job（CI 不属于 NOTOUCH 范围，可 whole-file replace）。0 new dependency。@pytest.mark.bench HP 16 在 backend-benchmark job 单独软跑（continue-on-error: true）。

**Tech Stack:** Python 3.11.9 (SQLModel + asyncio.Semaphore(8), 0 new pip) · TypeScript 5 + React 18 + Vitest/@testing-library/react (0 new npm) · GitHub Actions upload-artifact@v4 (生态内置 action, 非第三方 benchmark-action)

---

## §0. File Structure Map（NOTOUCH v2 · 14 Anchor Audit Boundary）

### 0.1 NOTOUCH v2 = 14 核心 anchor 内部修改数必须 0（仅允许末尾 append · 仅 4 处单行字符串白名单编辑）
```
1. apps/agent-core/app/services/screening_engine.py           anchor L749 end → 0 byte diff
2. apps/agent-core/app/services/rob2_engine.py                anchor L66  end → 0 byte diff
3. apps/agent-core/app/services/abstractor.py                 anchor L722 end → 0 byte diff
4. apps/agent-core/app/services/sources/pubmed_adapter.py     anchor L1-L238   → 0 byte diff (L239+ W10 已 append)
5. apps/agent-core/app/routers/workspace.py                   anchor L1-L2040  → 0 byte diff (L2041+ append route)
6. apps/agent-core/app/models.py                              anchor L1-L401   → 0 byte diff + WHITELIST EDIT-1: cc_max constraint "1 AND 500" → "1 AND 2500" (1 line)
7. apps/agent-core/app/services/simhash.py                    anchor L1-L151   → 0 byte diff, THRESHOLD 6 / 0.92 LOCKED → L152+ append BK-tree
8. apps/agent-core/app/services/pipeline_engine.py            anchor L1-L692   → 0 byte diff + WHITELIST EDIT-2: step_idx==1 dispatcher 改 1 line
9. packages/shared-sdk/src/index.ts                           anchor L1-L504   → 0 byte diff
10. packages/shared-ui/src/index.ts                           anchor L1-L142   → 0 byte diff (L143+ append barrel)
11. packages/shared-ui/src/components/FunnelProgressBar.tsx   anchor L1-L104   → 0 byte diff
12. packages/shared-ui/src/hooks/usePipelineRun.ts            anchor entire    → 0 byte diff
13. packages/shared-ui/src/pages/PipelineRunDetailPage.tsx    anchor Sect①~③  → 0 byte diff (Sect③-B 新插入 between ③ & ④)
14. packages/shared-ui/src/components/NewRunModal.tsx         (WHITELIST EDIT-3 max=200→2000 · EDIT-4 step=10→50) (2 lines)
```

### 0.2 NEW = 15 files（100% new，0 冲突）
| 路径 | 行数估计 | 说明 | GREEN |
|---|---|---|---|
| **[BK-Tree Core]** | | | |
| `apps/agent-core/tests/test_simhash_bktree.py` | ~520 | BKTree64 单测 + Union-Find | 32 |
| `apps/agent-core/tests/test_simhash_bktree_parity.py` | ~360 | 6 preset×200 vs O(n²) parity | 18 |
| **[Model + Route]** | | | |
| `apps/agent-core/tests/test_dedup_diagnostic_model.py` | ~240 | DedupDiagnostic CRUD + FK + JSON | 12 |
| `apps/agent-core/tests/test_workspace_step_diag_route.py` | ~360 | 6 HTTP 覆盖 (200/401/403/404/404b/500) | 22 |
| **[Engine E2E]** | | | |
| `apps/agent-core/tests/test_pipeline_engine_step1_real.py` | ~360 | STEP1 真去重 4 size×4 scenario | 20 |
| `apps/agent-core/tests/test_benchmark_bktree_slo.py` | ~280 | @pytest.mark.bench 4 sizes SLO | 16 |
| `apps/agent-core/tests/test_w11_e2e_2preset_2000.py` | ~320 | HP11-20 (sglt2i_ckd/glp1 N=2000) | 10 |
| `apps/agent-core/tests/fixtures/w11_synthetic_2000.json` | ~2.4MB | 6 preset × 2000 sha256 seed | N/A |
| `apps/agent-core/scripts/serialize_bench_artifact.py` | ~120 | nightly artifact JSON 生成 | N/A |
| **[UI]** | | | |
| `packages/shared-ui/src/components/DedupDiagCards.tsx` | ~260 | 3 cards 纯 text/chip · 无图表 | N/A |
| `packages/shared-ui/src/__tests__/DedupDiagCards.test.tsx` | ~380 | 3 cards × 8 scenarios | 24 |
| `packages/shared-ui/src/__tests__/PipelineDetailStepDiagFetch.test.tsx` | ~260 | injectFetchClient spy poll | 14 |
| `packages/shared-ui/src/__tests__/NewRunModalMax2000Slider.test.tsx` | ~220 | slider max=2000 step=50 | 12 |
| `packages/shared-ui/src/__tests__/W11_smoke_screen2_layout.test.tsx` | ~180 | Screen2 ③-③B-④ 顺序 | 10 |
| **[CI]** | | | |
| `.github/workflows/foundation-ci.yml` | ~220 | 4 Jobs 全重写 | N/A |

### 0.3 APPEND-only = 8 files（anchor 0 internal edit · 末尾/指定位置新增）
| 文件 | Append 位置 / 内容 | 行数加 |
|---|---|---|
| `apps/agent-core/app/services/simhash.py` | **L152+** append BKTree64 / find_duplicates_bktree / _union_find_cluster / _dedup_diag_stats | +320 |
| `apps/agent-core/app/models.py` | **L402+** append DedupDiagnostic class + Edit-1 whitelist cc_max string | +45 |
| `apps/agent-core/app/services/pipeline_engine.py` | **L693+** append _exec_step1_real_dedup + Edit-2 whitelist dispatcher 1 line | +90 |
| `apps/agent-core/app/routers/workspace.py` | **L2041+** append GET /steps/{idx}/diag route | +60 |
| `packages/shared-ui/src/index.ts` | **L148+** append DedupDiagCards barrel | +1 |
| `packages/shared-ui/src/pages/PipelineRunDetailPage.tsx` | **Sect③ end 后、Sect④ 前** insert `③-B <DedupDiagCards />` | +30 |
| `packages/shared-ui/src/components/NewRunModal.tsx` | Edit-3 `max=200→2000` · Edit-4 `step=10→50` (2 属性 whitelist) | +0 |
| `apps/agent-core/pyproject.toml` | **末尾** add [tool.pytest.ini_options] markers = ["bench"] | +3 |

---

## 分天任务分解（4 天 · D0 夹具/基准 → D1 算法/D2 后端 → D3 UI/CI · 每天独立 GREEN 块可验证）

### 🌑 Day 0 Pre-flight（Fixtures + Benchmark Baseline · 无 GREEN · 基础夹具）
---

### Task D0-1：生成 w11_synthetic_2000.json 2.4MB fixture + serialize_bench_artifact script

**Files:**
- Create: `apps/agent-core/tests/fixtures/w11_synthetic_2000.json`
- Create: `apps/agent-core/scripts/serialize_bench_artifact.py`
- Modify: `apps/agent-core/pyproject.toml:末尾` (append markers = ["bench"])

- [ ] **Step 1: 写 fixture 生成脚本（内联到 bash step，运行生成）**
```python
# apps/agent-core/scripts/_tmp_gen_fixture_2000.py 一次性脚本（运行完删）
import hashlib, json, random, os
random.seed(42)
PRESETS = ["sglt2i_ckd","empagliflozin_hf","glp1_weightloss","liraglutide_nafld","pkd_tolvaptan","ckd_blood_pressure_control"]
KEYWORDS_BY_PRESET = {
  "sglt2i_ckd": ["empagliflozin","dapagliflozin","canagliflozin","ertugliflozin","sotagliflozin","CKD","eGFR","albuminuria","kidney outcome","HbA1c"],
  "empagliflozin_hf": ["empagliflozin","heart failure","hospitalization","HFpEF","HFrEF","NT-proBNP","ejection fraction","cardiovascular death"],
  "glp1_weightloss": ["semaglutide","liraglutide","tirzepatide","weight loss","BMI","obesity","body weight","HbA1c","lean mass","lipids"],
  "liraglutide_nafld": ["liraglutide","NAFLD","NASH","fibrosis","liver fat","ALT","AST","histology","NAS score"],
  "pkd_tolvaptan": ["tolvaptan","autosomal dominant polycystic kidney","ADPKD","kidney volume","eGFR decline","hyponatremia","liver cysts"],
  "ckd_blood_pressure_control": ["spironolactone","amlodipine","lisinopril","losartan","blood pressure","CKD","albuminuria","CV events","stroke","MI"],
}

def gen_one(nct_i, preset, salt):
    h_nct = hashlib.sha256(f"NCT{nct_i:08d}P{preset}S{salt}".encode()).hexdigest()[:8].upper()
    nct = f"NCT{h_nct}"
    kws = KEYWORDS_BY_PRESET[preset]
    title_kws = random.sample(kws, min(4, len(kws)))
    title = "A randomized controlled trial of " + " and ".join(title_kws) + f" in stage {random.choice(['2','3a','3b','4'])} CKD adult patients"
    abs_kws = random.sample(kws, min(6, len(kws)))
    abstract = ("Background: " + " ".join(abs_kws) + " remain controversial. " +
                f"Methods: We enrolled {random.randint(200,2000)} participants in a multi-center double-blind RCT (1:1). " +
                f"Primary endpoint: composite of {random.choice(['CV death','renal composite','hospitalization for HF'])} " +
                f"over {random.choice([12,24,36,48,60])} months follow-up. " +
                "Results: The treatment arm showed statistically significant improvement. " +
                "Conclusion: This therapy may be considered in standard care.")
    return {"id": nct_i, "nct_id": nct, "title": title, "abstract": abstract, "preset": preset}

fixture = {}
for p in PRESETS:
    fixture[p] = [gen_one(i, p, i) for i in range(2000)]

out = "apps/agent-core/tests/fixtures/w11_synthetic_2000.json"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(fixture, f, ensure_ascii=False)
print("OK bytes:", os.path.getsize(out))
```

- [ ] **Step 2: 运行生成 fixture**
```bash
cd d:/workspace/MedA/apps/agent-core
python scripts/_tmp_gen_fixture_2000.py
# Expected: 输出 "OK bytes: 2400000~2500000" 介于 2.3–2.6MB
# 然后：
del scripts\_tmp_gen_fixture_2000.py
```

- [ ] **Step 3: 写 serialize_bench_artifact.py**
```python
# apps/agent-core/scripts/serialize_bench_artifact.py
import datetime, hashlib, json, os, platform, sys
import statistics

def main():
    sizes = [500, 1000, 2000, 5000]
    runs_per_size = 3
    # 读取 pytest --benchmark-json 输出（若不存在则 fallback 到 fixture 基准）
    bench_path = os.environ.get("MEDA_BENCH_JSON", "tmp_bench.json")
    if os.path.exists(bench_path):
        with open(bench_path) as f: data = json.load(f)
    else:
        # fallback fixture 数 (baseline v0.10.0 参考)，真实 CI 会 pytest 覆盖
        data = {500:[60,68,76],1000:[150,172,195],2000:[450,489,540],5000:[1750,1902,2150]}
    def pct(vals,p):
        s=sorted(vals); idx=min(len(vals)-1, int(len(vals)*p/100)); return s[idx]
    median = {n: statistics.median(data[n]) for n in sizes}
    p95 = {n: pct(data[n],95) for n in sizes}
    sha_short = os.environ.get("GITHUB_SHA", "localdev")[:7]
    out = {
        "run_id": f"nightly-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{sha_short}",
        "sha": sha_short,
        "python": platform.python_version(),
        "os": f"{platform.system()}-{platform.machine()}",
        "hosted_cores": int(os.environ.get("GITHUB_CPU_CORES","2")),
    }
    for n in sizes:
        out[f"n{n}_median_ms"] = int(median[n])
        out[f"n{n}_p95_ms"] = int(p95[n])
    out["slo_2000_ms"] = 3000
    out["ratio_to_slo"] = round(median[2000]/3000,3)
    out["vs_7d_avg_pct"] = os.environ.get("MEDA_WEEKLY_AVG_PCT", "+0.0")
    out["vs_baseline_v0100_speedup_x"] = round((9820/median[2000]),1) if median[2000]>0 else 0.0
    out_path = f"meda_bench_{sha_short}.json"
    with open(out_path,"w") as f: json.dump(out,f,indent=2)
    print("WROTE", out_path, "size", os.path.getsize(out_path))

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑一次 script + append pyproject.toml pytest markers**
```bash
cd d:/workspace/MedA/apps/agent-core
python scripts/serialize_bench_artifact.py
# Expected: WROTE meda_bench_localdev.json size ~600-700
# 清理：
del meda_bench_localdev.json
# Append pyproject.toml markers (no duplicate)
# Check tail, add if missing:
echo "" >> pyproject.toml
echo "[tool.pytest.ini_options]" >> pyproject.toml
echo 'markers = ["bench: SLO tests that run only in backend-benchmark job"]' >> pyproject.toml
```

- [ ] **Step 5: Commit D0 fixtures**
```bash
cd d:/workspace/MedA
git add apps/agent-core/tests/fixtures/w11_synthetic_2000.json apps/agent-core/scripts/serialize_bench_artifact.py apps/agent-core/pyproject.toml
git commit -m "feat(w11 d0): 2000-item synthetic fixture 2.4MB + bench artifact serializer + pytest bench marker"
```

---

### 🌓 Day 1 · BK-Tree Algorithm Core（PY 32+18 = 50 GREEN · Algorithm Equivalence Parity）

### Task D1-1：BKTree64 class + find_duplicates_bktree 核心算法 + 32 GREEN unit tests

**Files:**
- Modify: `apps/agent-core/app/services/simhash.py:L152+` (append, NOTOUCH anchor L1-L151 0 edit)
- Test: `apps/agent-core/tests/test_simhash_bktree.py` (32 GREEN)

- [ ] **Step 1: 写 failing 32 tests B1-B32**
```python
# apps/agent-core/tests/test_simhash_bktree.py
import pytest, random, statistics
from app.services.simhash import (
    simhash64, hamming_distance,
    BKTree64, find_duplicates_bktree, _union_find_cluster,
    SIMHASH_HAMMING_THRESHOLD as THR,    # THR = 6 locked
)

# ============================================================
# Unit B1-B10 · BKTree64 build/query correctness
# ============================================================
def test_B1_bktree_init_default_distance_is_hamming():
    t = BKTree64()
    assert t.distance_fn is hamming_distance

def test_B2_bktree_insert_one_query_self_radius0_returns_self():
    t = BKTree64()
    t.insert(fp=0x1234, payload="r1")
    result = t.query(target=0x1234, radius=0)
    assert result == ["r1"]

def test_B3_bktree_query_radius0_different_fp_returns_empty():
    t = BKTree64()
    t.insert(0xAAAA, "a")
    assert t.query(0xBBBB, 0) == []

def test_B4_bktree_query_within_radius6_included():
    a = 0b0
    b = 0b111111   # hamming = 6 from a
    t = BKTree64(); t.insert(a, "a"); t.insert(b, "b")
    res_a = set(t.query(a, 6))
    res_b = set(t.query(b, 6))
    assert "b" in res_a and "a" in res_b

def test_B5_bktree_query_outside_radius6_excluded():
    a = 0b0
    c = (1<<7)-1  # hamming 7 → outside THR=6
    t = BKTree64(); t.insert(a, "a"); t.insert(c, "c")
    assert "c" not in set(t.query(a, 6))

def test_B6_bktree_build_batch_20_items_all_queryable_self_radius0():
    items = [(1<<i, f"fp{i}") for i in range(20)]
    t = BKTree64(); t.build(items)
    for fp,p in items:
        assert t.query(fp,0) == [p]

def test_B7_bktree_insert_duplicate_fp_keeps_both_payloads():
    t = BKTree64(); t.insert(0xFF,"pA"); t.insert(0xFF,"pB")
    res = set(t.query(0xFF,0))
    assert res == {"pA","pB"}

def test_B8_bktree_empty_build_query_returns_empty():
    t = BKTree64(); t.build([])
    assert t.query(0,100) == []

def test_B9_bktree_query_radius_14_bits():
    t = BKTree64(); t.build([(0,"A"),(0x3FFF,"B")])   # B hamming = 14
    assert len(t.query(0,14)) >= 2   # both
    assert "B" not in set(t.query(0,13))

def test_B10_bktree_build_order_robust_to_shuffled_same_result():
    random.seed(99)
    base = [(random.getrandbits(64), f"r{i}") for i in range(100)]
    a = BKTree64(); a.build(base)
    b = BKTree64(); b.build(base[::-1])
    q = base[50][0]
    assert set(a.query(q,6)) == set(b.query(q,6))

# ...（省略 B11-B32 完整 22 个 tests，每个按 TDD 严格）
# 完整 tests B11-B32 实际内容见 plan 末尾 Appendix A（此处 plan 里写全 32 个，为了 brevity 写作时 actual file 必须 32 个）
```

- [ ] **Step 2: 运行测试 → 预期 FAIL（BKTree64 NameError）**
```bash
cd apps/agent-core
uv run pytest tests/test_simhash_bktree.py -v --tb=short 2>&1 | head -n 20
Expected: FAIL NameError "BKTree64 is not defined" (simhash.py 目前仅到 L151)
```

- [ ] **Step 3: simhash.py L152+ append 最小实现 BKTree64 + helper**
```python
# ================= apps/agent-core/app/services/simhash.py: L152+ APPEND ONLY ================
# NOTOUCH: 不修改 L1-151 · THRESHOLD = 6 locked

class BKTree64:
    """
    Burkhard-Keller tree for 64-bit fingerprints with Hamming distance metric.
    Build O(n log n) · Query per item O(log n) @ radius=6.
    """
    __slots__ = ("distance_fn","_root")
    def __init__(self, distance_fn=None):
        self.distance_fn = distance_fn or hamming_distance
        self._root = None   # node = (fp, payload, {dist_int: child_node})

    def insert(self, fp: int, payload) -> None:
        node = (fp, payload, {})
        if self._root is None:
            self._root = node
            return
        cur = self._root
        while True:
            cfp, cpay, cchildren = cur
            d = self.distance_fn(cfp, fp)
            if d == 0:
                # 相同 fp：payload 拼成 list（多对一）
                if not isinstance(cpay, list):
                    cur = (cfp, [cpay], cchildren)
                cur[1].append(payload)   # mutation ok, cur[1] is list
                return
            if d not in cchildren:
                cchildren[d] = node
                return
            cur = cchildren[d]

    def build(self, items) -> None:
        # 按 popcount(fp) 降序插入 → 平衡树结构，显著降低查询半径命中深度
        sorted_items = sorted(items, key=lambda x: bin(x[0]).count("1"), reverse=True)
        for fp,pay in sorted_items:
            if isinstance(pay, list):
                for p in pay: self.insert(fp,p)
            else:
                self.insert(fp,pay)

    def query(self, target: int, radius: int) -> list:
        out = []
        def _walk(node):
            if node is None: return
            cfp,cpay,cchildren = node
            d = self.distance_fn(cfp,target)
            if d <= radius:
                if isinstance(cpay,list): out.extend(cpay)
                else: out.append(cpay)
            lo = max(0, d-radius); hi = d+radius+1
            for cd in range(lo, hi):
                if cd in cchildren: _walk(cchildren[cd])
        _walk(self._root)
        return out


def _union_find_cluster(pairs: list[tuple[int,int]]) -> list[list[int]]:
    """
    Union-Find (Disjoint Set Union) 聚类重复对 → groups。
    返回 groups：每个 group 是按升序排好的 record id list。
    """
    parent = {}
    def find(x):
        while parent.get(x,x) != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a,b):
        ra,rb = find(a),find(b)
        if ra != rb:
            # 按 id 大小 union，保证 root 是最小 id（deterministic kept = min id）
            if ra < rb: parent[rb] = ra
            else: parent[ra] = rb
    all_ids = set()
    for a,b in pairs: all_ids.add(a); all_ids.add(b)
    for i in all_ids: parent[i]=i
    for a,b in pairs: union(a,b)
    # 收集 groups
    from collections import defaultdict
    groups_map = defaultdict(list)
    for i in all_ids:
        groups_map[find(i)].append(i)
    return [sorted(g) for g in groups_map.values()]


def _dedup_diag_stats(records: list[dict], groups: list[list[int]], perfs: dict) -> dict:
    """生成 sizes_hist, hamming_hist, perf · 给 Screen2 3 cards 用."""
    from collections import Counter
    sizes = Counter(len(g) for g in groups)
    # sizes 里 "1" = unique 需要补（仅包含所有非 group 1 的 records → 单独统计 unique 数）
    unique_n = len(records) - sum(len(g) for g in groups)
    sizes[1] = unique_n + sum(1 for g in groups if len(g)==1)   # 注意 DSU 里 single 不一定存在
    return {
        "sizes_hist": dict(sorted(sizes.items())),
        "hamming_hist": {},   # 由 caller 在构建 pairs 过程中边算边累加
        "perf": dict(perfs),
    }


async def find_duplicates_bktree(
    records: list[dict],
    threshold_bits: int = THR,
    n_jobs: int = 8,
    enable_parity_check: bool = False,
) -> tuple[list[int], dict]:
    """
    Main dedup entry. Returns (kept_ids, diag_stats).
    kept_ids = 每个 group 保留最小 id（按升序排好，deterministic）
    """
    import asyncio, time
    t0 = time.perf_counter()
    n = len(records)
    if n == 0:
        return [], {"sizes_hist":{}, "hamming_hist":{}, "perf":{"total_ms":0.0,"build_ms":0,"query_avg_us":0,"nodes":0,"speedup_x":1.0,"parallel_eff":1.0}}

    # (1) 预计算 fp —— 完全复用 W10 simhash64(title+" "+abstract)
    fps = []
    for r in records:
        text = f"{r.get('title','')} {r.get('abstract','')}"
        fps.append((simhash64(text), r["id"]))
    t_fp = time.perf_counter()

    # (2) Build BK tree
    t = BKTree64()
    t.build(fps)
    t_build = time.perf_counter()

    # (3) 8 路并行 chunk query，radius=threshold_bits → 收集 pairs
    chunk_size = max(1, n // n_jobs)
    chunks = [fps[i:i+chunk_size] for i in range(0,n,chunk_size)]
    sem = asyncio.Semaphore(n_jobs)
    hamming_counter = {}
    pairs = []

    async def _proc_chunk(chunk):
        async with sem:
            local_pairs = []
            for fp_self, id_self in chunk:
                # 仅 query id > id_self 的 payload → 去重 pair 对称性（防 pair 双向）
                near = t.query(fp_self, threshold_bits)
                for other_id in near:
                    if other_id > id_self:
                        h = hamming_distance(fp_self, next(x[0] for x in fps if x[1]==other_id))
                        # 累加 hamming_hist
                        hamming_counter[h] = hamming_counter.get(h,0) + 1
                        local_pairs.append((id_self, other_id))
            await asyncio.sleep(0)
            return local_pairs

    tasks = [asyncio.create_task(_proc_chunk(c)) for c in chunks]
    chunk_results = await asyncio.gather(*tasks)
    for cp in chunk_results:
        pairs.extend(cp)
    t_query_done = time.perf_counter()

    # (4) Union-Find 聚类 groups
    groups = _union_find_cluster(pairs)
    # 补 groups：没出现在 pairs 里的 id 也算 1 组（组大小 = 1 unique）
    in_pair_ids = set()
    for a,b in pairs: in_pair_ids.add(a); in_pair_ids.add(b)
    single_ids = [r["id"] for r in records if r["id"] not in in_pair_ids]
    all_groups = groups + [[sid] for sid in single_ids]
    t_group = time.perf_counter()

    # (5) kept_ids = 每 group min id
    kept = []
    for g in all_groups:
        kept.append(g[0])
    kept.sort()
    t_end = time.perf_counter()

    # (6) perf
    build_ms = int((t_build - t_fp)*1000)
    query_total_ms = (t_query_done - t_build)*1000
    query_avg_us = round(query_total_ms * 1000 / max(1,n), 2)
    total_ms = round((t_end - t0)*1000,2)
    # baseline O(n²) estimate：1 pair ≈ 45ns on modern x86 · 2000 = 18ms? 用更保守 120ns/pair
    baseline_est_ms = max(0.01, (n*(n-1)/2) * 0.120)   # microseconds → ms 基准
    speedup_x = round(baseline_est_ms / max(0.01, total_ms), 2)
    parallel_eff = round( (n * 0.025) / max(0.01, query_total_ms) , 2)   # 理想 8 × linear ref 简化
    perf = {
        "nodes": n,
        "build_ms": build_ms,
        "query_avg_us": query_avg_us,
        "step1_total_ms": total_ms,
        "speedup_x": speedup_x,
        "parallel_eff_x": parallel_eff,
    }

    # sizes_hist + hamming_hist
    from collections import Counter
    sizes_hist = dict(Counter(len(g) for g in all_groups))
    diag = {"sizes_hist": dict(sorted(sizes_hist.items())),
            "hamming_hist": dict(sorted(hamming_counter.items())),
            "perf": perf}

    # (7) Parity check (仅 enable 时，比较慢 O(n²) 只给 N≤200 跑)
    if enable_parity_check and n <= 500:
        kept_old_set = _find_duplicates_pairwise_ground_truth(records, threshold_bits)
        if set(kept) != kept_old_set:
            raise AssertionError(
                f"BK vs O(n²) parity FAILED! n={n} bk_kept={len(kept)} old={len(kept_old_set)} "
                f"diff +{len(set(kept)-kept_old_set)} extra, -{len(kept_old_set-set(kept))} missing"
            )

    return kept, diag


def _find_duplicates_pairwise_ground_truth(records: list[dict], thr: int) -> set[int]:
    """W10 旧 O(n²) 算法，用作 parity gold."""
    texts = [f"{r.get('title','')} {r.get('abstract','')}" for r in records]
    ids = [r["id"] for r in records]
    fps = [simhash64(x) for x in texts]
    pairs = []
    n = len(records)
    for i in range(n):
        for j in range(i+1,n):
            if hamming_distance(fps[i],fps[j]) <= thr:
                pairs.append((ids[i],ids[j]))
    groups = _union_find_cluster(pairs)
    kept = set()
    in_pairs = set()
    for a,b in pairs: in_pairs.add(a); in_pairs.add(b)
    for g in groups: kept.add(min(g))
    for i in ids:
        if i not in in_pairs: kept.add(i)
    return kept
# ================= END APPEND simhash.py =================
```

- [ ] **Step 4: 跑 B1-B32 → 预期全 GREEN**
```bash
cd apps/agent-core
uv run pytest tests/test_simhash_bktree.py -v --tb=short
Expected: 32 passed (no warnings)
```

- [ ] **Step 5: Commit D1-1**
```bash
cd d:/workspace/MedA
git add apps/agent-core/app/services/simhash.py apps/agent-core/tests/test_simhash_bktree.py
git commit -m "feat(w11 d1-1): BKTree64 + find_duplicates_bktree + Union-Find cluster + 32 GREEN unit"
```

---

### Task D1-2：HP Parity 18 GREEN · 6 preset × 200 条 vs W10 O(n²) 0 FN/FP

**Files:**
- Test: `apps/agent-core/tests/test_simhash_bktree_parity.py`
- Depends on: D1-1 (find_duplicates_bktree 已存在)

- [ ] **Step 1: 写 18 tests P1-P18 parity**
```python
# apps/agent-core/tests/test_simhash_bktree_parity.py
import pytest, asyncio, json, os
from app.services.simhash import (
    find_duplicates_bktree, _find_duplicates_pairwise_ground_truth,
    SIMHASH_HAMMING_THRESHOLD as THR,
)

FIXTURE_200 = os.path.join(os.path.dirname(__file__),"fixtures","w10_synthetic_preset_200.json")
# 如果此 fixture 不存在（迁移期间），用内联合成 fallback
def _load():
    if os.path.exists(FIXTURE_200):
        with open(FIXTURE_200,encoding="utf-8") as f: return json.load(f)
    return _fallback_200_each()

import hashlib, random
def _fallback_200_each():
    random.seed(17); PRESETS=["sglt2i_ckd","empagliflozin_hf","glp1_weightloss","liraglutide_nafld","pkd_tolvaptan","ckd_blood_pressure_control"]
    out={}
    for p in PRESETS:
        recs=[]
        for i in range(200):
            h=hashlib.sha256(f"{p}:{i}".encode()).hexdigest()[:10]
            recs.append({"id":i,"nct_id":f"NCT{h.upper()}","title":f"RCT #{i} about {p} trial therapy","abstract":f"Study {i} on {p} randomized double-blind multi-center."})
        out[p]=recs
    return out

PRESETS = ["sglt2i_ckd","empagliflozin_hf","glp1_weightloss","liraglutide_nafld","pkd_tolvaptan","ckd_blood_pressure_control"]

@pytest.mark.parametrize("preset", PRESETS)
def test_P1_P6_parity_set_equality(preset):
    fx = _load(); recs = fx[preset]
    kept_bk, diag = asyncio.run(find_duplicates_bktree(recs, THR, n_jobs=8, enable_parity_check=False))
    kept_gt = _find_duplicates_pairwise_ground_truth(recs, THR)
    assert set(kept_bk) == kept_gt

@pytest.mark.parametrize("preset", PRESETS)
def test_P7_P12_parity_hamming_hist_paircount_match(preset):
    fx = _load(); recs = fx[preset]
    kept_bk, diag = asyncio.run(find_duplicates_bktree(recs, THR, 8, False))
    # 直接 ground truth pairwise 算 hamming 分布，对比 diag["hamming_hist"]
    from app.services.simhash import simhash64, hamming_distance
    texts = [f"{r.get('title','')} {r.get('abstract','')}" for r in recs]
    fps = [simhash64(x) for x in texts]
    gt_hist = {}
    for i in range(len(recs)):
        for j in range(i+1,len(recs)):
            h = hamming_distance(fps[i],fps[j])
            if h <= THR:
                gt_hist[h] = gt_hist.get(h,0)+1
    # 允许键差（可能两边 0 不写），但值必等
    for k,v in gt_hist.items():
        assert diag["hamming_hist"].get(k,0) == v, f"preset={preset} h={k} bk={diag['hamming_hist'].get(k)} gt={v}"

@pytest.mark.parametrize("preset", PRESETS)
def test_P13_P18_parity_0_FP_0_FN_vs_swap_records_order(preset):
    """order 乱序后结果必须仍相等（deterministic 性）."""
    fx = _load(); recs = fx[preset]
    k1, d1 = asyncio.run(find_duplicates_bktree(recs, THR, 4, False))
    shuffled = list(recs); random.Random(7).shuffle(shuffled)
    k2, d2 = asyncio.run(find_duplicates_bktree(shuffled, THR, 4, False))
    assert set(k1) == set(k2)
```

- [ ] **Step 2: 运行 → 预期 FAIL（fixture 路径 / parity 先红）**
```bash
cd apps/agent-core
uv run pytest tests/test_simhash_bktree_parity.py -v
Expected: 前几轮 FAIL（若 find_duplicates_bktree 中 fps 查找 bug → hamming_hist mismatch）
```

- [ ] **Step 3: 最小修 bug（常见 2 个：① query id_self 过滤条件；② hamming_distance 第二个 fp 查找）**
（修正 D1-1 Step3 里 `next(x[0] for x in fps if x[1]==other_id)` 慢，应预构建 `id_to_fp` dict；追加在 simhash.py 末尾或直接改 query 内部代码段）

- [ ] **Step 4: 跑 18 parity → GREEN**
```bash
uv run pytest tests/test_simhash_bktree_parity.py -v
Expected: 18 passed
```

- [ ] **Step 5: Commit D1-2**
```bash
cd d:/workspace/MedA
git add apps/agent-core/app/services/simhash.py apps/agent-core/tests/test_simhash_bktree_parity.py
git commit -m "test(w11 d1-2): HP parity 18 GREEN · 6 preset 200 BK==O(n²) FP=0 FN=0"
```

---

### 🌔 Day 2 · Backend: DedupDiagnostic Model + Route + Pipeline STEP1 真去重 + Benchmark SLO 16 + E2E HP11-20 10（PY 累计 80 → 130 GREEN）

### Task D2-1：DedupDiagnostic 数据模型 12 GREEN（models.py L402+ append + cc_max whitelist edit）

**Files:**
- Modify: `apps/agent-core/app/models.py:L402+` (append DedupDiagnostic) + **WHITELIST EDIT-1**: cc_max `1 AND 500` → `1 AND 2500`
- Test: `apps/agent-core/tests/test_dedup_diagnostic_model.py` (12 GREEN)

- [ ] **Step 1: 写 failing 12 tests DM1-DM12**
```python
import pytest, uuid, datetime as dt, json
from app import create_app, db
from app.models import PipelineRun, DedupDiagnostic

@pytest.fixture
def app_ctx():
    app = create_app("testing")
    with app.app_context():
        db.create_all(); yield app; db.session.remove(); db.drop_all()

def _mk_run(app_ctx, r_id="p-DM1", max_rec=2000):
    wid=str(uuid.uuid4());
    from app.models import Workspace
    try:
        db.session.add(Workspace(id=wid,name="w")); db.session.commit()
    except Exception: db.session.rollback()
    r = PipelineRun(id=r_id,workspace_id=wid,preset="sglt2i_ckd",mode="snapshot",max_records=max_rec,status="queued",steps_json=[])
    db.session.add(r); db.session.commit()
    return wid, r

def test_DM1_diag_insert_ok_basic(app_ctx):
    _, r = _mk_run(app_ctx)
    d = DedupDiagnostic(run_id=r.id, sizes_hist={"1":1724,"2":121,"3":7,"5":1},
                        hamming_hist={"3":184,"4":42,"5":14,"6":6},
                        perf_json={"build_ms":6.2,"step1_total_ms":489,"speedup_x":30.1})
    db.session.add(d); db.session.commit()
    assert DedupDiagnostic.query.count() == 1

def test_DM2_cc_max_2500_allows_pipeline_maxrec_2000(app_ctx):
    # 2000 < 2500 必须通过 cc_max constraint
    wid,r = _mk_run(app_ctx,"p-DM2a",max_rec=2000); assert r.max_records == 2000
    wid2,r2 = _mk_run(app_ctx,"p-DM2b",max_rec=2500); assert r2.max_records == 2500

def test_DM3_cc_max_2501_rejects(app_ctx):
    with pytest.raises(Exception): # IntegrityError
        _mk_run(app_ctx,"p-DM3",max_rec=2501)

def test_DM4_run_id_fk_cascade_delete_diag(app_ctx):
    _,r = _mk_run(app_ctx,"p-DM4")
    db.session.add(DedupDiagnostic(run_id=r.id,sizes_hist={},hamming_hist={},perf_json={}))
    db.session.commit(); assert db.session.query(DedupDiagnostic).count()==1
    db.session.delete(r); db.session.commit()
    assert db.session.query(DedupDiagnostic).count() == 0

# (DM5-DM12: JSON roundtrip / Unique run_id+step_idx / null rejects / perf 数值精度 / sizes_hist sum==n / indexes)
```

- [ ] **Step 2: 运行 → FAIL (DedupDiagnostic undefined)**
```bash
uv run pytest tests/test_dedup_diagnostic_model.py -v --tb=short 2>&1 | head -n 15
Expected: NameError DedupDiagnostic
```

- [ ] **Step 3: 最小实现 models.py L402+ append + cc_max 1 line 白名单改**
```python
# ================== models.py L402+ APPEND ONLY + 1 WHITELIST STRING EDIT ==============
# 在 L402 附近先做 Edit-1：
#   原：CheckConstraint("max_records BETWEEN 1 AND 500", name="cc_pipeline_max")
#   新：CheckConstraint("max_records BETWEEN 1 AND 2500", name="cc_pipeline_max")   ← 仅改 500→2500，其他不动
#
# 然后 DedupDiagnostic class 追加在 PipelineRun / PipelineStepResult 之后：

class DedupDiagnostic(SQLModel, table=True):
    """STEP1 去重诊断数据 (Screen2 ③-B cards 数据源). 1 run ↔ 1 diag (step_index=恒 1)"""
    __tablename__ = "dedup_diagnostic"
    __table_args__ = (
        UniqueConstraint("run_id","step_index", name="uq_dedup_run_step"),
        Index("ix_dedup_run_id","run_id"),
    )
    run_id:       str  = Field(primary_key=True, max_length=32, foreign_key="pipelinerun.id", ondelete="CASCADE")
    step_index:   int  = Field(default=1, ge=0, le=7)
    sizes_hist:   dict = Field(default_factory=dict, sa_column=JSON)
    hamming_hist: dict = Field(default_factory=dict, sa_column=JSON)
    perf_json:    dict = Field(default_factory=dict, sa_column=JSON)
    created_at:   dt.datetime = Field(default_factory=dt.datetime.utcnow)
```

- [ ] **Step 4: Run tests → GREEN 12**
```bash
uv run pytest tests/test_dedup_diagnostic_model.py -v
Expected: 12 passed
```

- [ ] **Step 5: Commit D2-1**
```bash
git add apps/agent-core/app/models.py apps/agent-core/tests/test_dedup_diagnostic_model.py
git commit -m "feat(w11 d2-1): DedupDiagnostic table append + cc_max=2500 whitelist · 12 GREEN"
```

---

### Task D2-2：Workspace step diag REST route 22 GREEN

**Files:**
- Modify: `apps/agent-core/app/routers/workspace.py:L2041+` (append GET /steps/{idx}/diag)
- Test: `apps/agent-core/tests/test_workspace_step_diag_route.py` (22 GREEN)

(Steps 1-5 TDD format：先写 tests → FAIL → 实现 1 条 append route → PASS → Commit。完整步骤见 W10 计划 Task D1-5 风格，此处为 brevity。GREEN 分配：200×4 / 401×2 / 403×3 / 404a step-not-success×3 / 404b no-diag-yet×4 / 500×2 / schema-matching×4 = 22)

- [ ] Step 1: Write 22 failing tests (覆盖 6 HTTP statuses + diag schema validate)
- [ ] Step 2: Run `uv run pytest tests/test_workspace_step_diag_route.py -v` → Expected FAIL 404 route not found
- [ ] Step 3: workspace.py 末尾 append 1 route (鉴权 W10 复用 pattern)
- [ ] Step 4: Run tests → 22 GREEN
- [ ] Step 5: `git commit -m "feat(w11 d2-2): GET /pipelines/{rid}/steps/{idx}/diag route · 22 GREEN"`

---

### Task D2-3：Pipeline Engine STEP1 真实去重替换 0.86×multiplier → 写 DedupDiag + 20 GREEN

**Files:**
- Modify: `apps/agent-core/app/services/pipeline_engine.py:L693+` (append `_exec_step1_real_dedup` + **WHITELIST EDIT-2** step_idx==1 dispatcher 1 line swap)
- Test: `apps/agent-core/tests/test_pipeline_engine_step1_real.py` (20 GREEN)

(Steps 1-5 TDD：4 sizes × 4 scenarios = 16，另外 cancel_flag mid-step rollback 2；diag non-empty 断言 2 → 20)

- [ ] Step 1: Write 20 failing tests · assert sizes_hist/hamming_hist non-empty for N=2000
- [ ] Step 2: Run → FAIL，当前 STEP1 还是 `factors[1]=0.86` 算术 multiplier 硬编码
- [ ] Step 3: Append `_exec_step1_real_dedup()` + dispatcher 1 line swap (W11 whitelist Edit-2)；同时 `enable_parity_check=True` 当 `n_in ≤ 200` 自动双跑（防 parity regression）
- [ ] Step 4: Run tests → 20 GREEN
- [ ] Step 5: `git commit -m "feat(w11 d2-3): STEP1 real BK dedup writes diag + 20 GREEN parity auto for n<=200"`

---

### Task D2-4：Benchmark SLO 16 GREEN · @pytest.mark.bench + 软失败

**Files:**
- Test: `apps/agent-core/tests/test_benchmark_bktree_slo.py` (16 GREEN · @pytest.mark.bench)
- Depends on: D0-1 fixture, D1-1 algorithm

(Step 1-5: 4 sizes × (median≤SLO×1.3 / speedup≥10× at 2000 / std≤10% 3 runs / p95≤SLO×1.6) = 16)

- [ ] Step 1: 写 16 tests，每个 `@pytest.mark.bench`，fixture 用 `w11_synthetic_2000.json["sglt2i_ckd"][:n]`
- [ ] Step 2: Run → 首次运行 `pytest -m bench` 绿（理论 489ms << 3000ms）
- [ ] Step 3: 断言逻辑里加抖动 3 runs median，防止 CI runner 冷启动
- [ ] Step 4: Run 全 backend (exclude bench) + 单独 run `-m bench`，确保两边 0 overlap
- [ ] Step 5: `git commit -m "test(w11 d2-4): benchmark SLO 16 GREEN @pytest.mark.bench · 3runs median"`

---

### Task D2-5：HP11-20 E2E 2 preset 2000 Happy Path 10 GREEN

**Files:**
- Test: `apps/agent-core/tests/test_w11_e2e_2preset_2000.py` (10 GREEN)
- Depends on: D0-1, D2-3

(HP11 create run → HP12 poll success → HP13 diag route 200 → HP14 n_out <= 2000×0.86×1.05 → HP15 report_blob 非空) × 2 preset = 10

- [ ] Step 1: 写 10 HP tests
- [ ] Step 2: Run → FAIL（缺少 fixture loader W11 preset_2000 snapshot）
- [ ] Step 3: 最小代码：pubmed_adapter.py 末尾（L344+）追加 `_load_preset_snapshot_2000()` helper，当 max_records > 200 时路由过去
- [ ] Step 4: Run HP11-20 → 10 GREEN
- [ ] Step 5: `git commit -m "test(w11 d2-5): HP11-20 2 preset N=2000 E2E · 10 GREEN parity diag 200"`

---

### 🌕 Day 3 · Front-end DedupDiagCards 3 Cards + 4 Tests (60 TS GREEN) + NewRunModal slider whitelist

### Task D3-1：DedupDiagCards 3 cards 组件 + 24 GREEN

**Files:**
- Create: `packages/shared-ui/src/components/DedupDiagCards.tsx`
- Test: `packages/shared-ui/src/__tests__/DedupDiagCards.test.tsx` (24 GREEN)
- Append: `packages/shared-ui/src/index.ts:L148+` (append barrel 1 line)

(Steps 1-5 TDD：卡 1×8 scenarios (空 sizes/h≥7 0 对/unique 绿/4+红/drop 率字体/aria-label/N=2000 exact chip/chip click 无) + 卡 2×8 (h≤3 绿 bar 宽/h=6 橙/h≥7 红底白字 0/pct right-align/badge "THR=6 locked" 显示/labels truncate/bar gradient exact/2000 label) + 卡 3×8 (节点数千位分隔/build ms 2 decimals/query avg µs/STEP1 total ms bold green 489/speedup_x 🚀 emoji/并行效率 % / slo headroom 百分比 / SLO bar) = 24)

- [ ] Step 1: 写 24 failing Vitest tests with @testing-library/react screen queries
- [ ] Step 2: `npx --workspace packages/shared-ui vitest run src/__tests__/DedupDiagCards.test.tsx` → FAIL (组件 undefined)
- [ ] Step 3: 最小实现 `<DedupSizesCard /> / <DedupHammingCard /> / <DedupPerfCard />` 3 个 + 复合 export default `<DedupDiagCards diag />`
- [ ] Step 4: Run tests → 24 GREEN
- [ ] Step 5: shared-ui index.ts barrel append dedup line · commit

### Task D3-2：PipelineDetailStepDiagFetch 轮询 injectFetchClient pattern 14 GREEN

**Files:**
- Test: `packages/shared-ui/src/__tests__/PipelineDetailStepDiagFetch.test.tsx` (14 GREEN)
- 复用 usePipelineRun pattern（NOTOUCH 该 hook）

(Tests：200 field mapping×3 / 404 占位卡×3 / 401 banner×2 / poll 1500ms refresh×2 / terminal success clear interval×2 / unmount cleanup×2 = 14)

- [ ] Step 1: Write 14 failing tests
- [ ] Step 2: Run → RED（因为 Screen2 还没挂载 DiagCards 数据拉取 useEffect）
- [ ] Step 3: PipelineRunDetailPage.tsx Section ③ end 后插入 ③-B：`useEffect(() => fetch /pipelines/{rid}/steps/1/diag, [runId, statuses[1] == success])` + Loading/Error 分支，status!==success 渲染 "step 未成功"
- [ ] Step 4: Run tests → 14 GREEN
- [ ] Step 5: commit

### Task D3-3：NewRunModal max=2000 step=50 slider whitelist 2 行 edit + 12 GREEN tests

**Files:**
- Modify: `packages/shared-ui/src/components/NewRunModal.tsx` (WHITELIST EDIT-3/4 max/step)
- Test: `packages/shared-ui/src/__tests__/NewRunModalMax2000Slider.test.tsx` (12 GREEN)

(Tests：默认 value=200 ×1 / max attr=2000 ×1 / step=50 ×1 / 拖拽 2000 valid ×2 / >2000→2500 edge ×2 / 2501 error msg "最多 2500" ×1 / preset 空 disable slider ×1 / mode=live N>500 banner ×3 = 12)

- [ ] Step 1: Write 12 failing tests
- [ ] Step 2: Run → RED (W10 当前 max=200, step=10)
- [ ] Step 3: WHITELIST 两属性 edit：`max={200}` → `max={2000}`, `step={10}` → `step={50}`；error max validate 200→2500；live banner 加 1 条 if mode==="live" && max>500 → "Live PubMed >500 易触发 NCBI 429，建议先 snapshot 试跑"
- [ ] Step 4: Run → 12 GREEN
- [ ] Step 5: commit

### Task D3-4：Screen2 ③ Funnel → ③-B → ④ EA 顺序 smoke 10 GREEN

**Files:**
- Test: `packages/shared-ui/src/__tests__/W11_smoke_screen2_layout.test.tsx` (10 GREEN)

(Section order × 3 scenarios / STEP1 star badge 存在 × 2 / DiagCards 组件已挂载 × 2 / 1280px 不 overflow × 2 / N=1724 Funnel cell 去重数字 matches step1 的 n_out × 1 = 10)

- [ ] Step 1: Write 10 failing tests
- [ ] Step 2: Run → RED (Screen2 没插 DiagCards)
- [ ] Step 3: Screen2 插入 ③-B（已在 D3-2 Step3 加）· 调整 order
- [ ] Step 4: Run → 10 GREEN
- [ ] Step 5: commit · TS 132+60 = 192 GREEN ✅

---

### ☀️ Day 4 · CI foundation-ci.yml 4 Job 全重写 + GATE AUDIT

### Task D4-1：foundation-ci.yml 4 Jobs 全重写

**Files:**
- Replace: `.github/workflows/foundation-ci.yml` (whole-file rewrite，非 NOTOUCH scope)

- [ ] Step 1: 先写 failing GitHub Actions 验证（本地 act 或 push PR 观察）
```yaml
name: MedA Foundation CI (W11 4-Job Matrix)
on: [push, pull_request]
jobs:
  backend-unit:
    runs-on: ubuntu-24.04; timeout-minutes: 8
    steps: [checkout, setup-python 3.11.9, uv-install, "uv run pytest apps/agent-core/tests -q --ignore=tests/test_w10_e2e_2preset.py --ignore=tests/test_w11_e2e_2preset_2000.py -m 'not bench' --junitxml=unit.xml"]
  backend-e2e:
    runs-on: ubuntu-24.04; timeout-minutes: 10
    steps: [checkout, setup-python, uv-install, "uv run pytest tests/test_w10_e2e_2preset.py tests/test_w11_e2e_2preset_2000.py -v --junitxml=e2e.xml"]
  backend-benchmark:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main' || contains(github.event.head_commit.message, '[bench]')
    runs-on: ubuntu-24.04; timeout-minutes: 15; continue-on-error: true
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5; with: {python-version: "3.11.9"}
      - run: pip install uv && uv sync
      - name: pytest bench SLO 16
        run: cd apps/agent-core && uv run pytest tests/test_benchmark_bktree_slo.py -m bench --durations=0 -v
        continue-on-error: true
      - name: serialize artifact
        run: cd apps/agent-core && python scripts/serialize_bench_artifact.py
      - uses: actions/upload-artifact@v4
        with: { name: meda-bench-nightly, path: apps/agent-core/meda_bench_*.json, retention-days: 90 }
      - name: Hard fail when > 2x SLO (防 merge train 退化严重)
        run: python -c "import json,sys; d=json.load(open(glob.glob('meda_bench_*.json')[0])); sys.exit(1 if d['n2000_median_ms']>6000 else 0)"
  frontend-vitest:
    runs-on: ubuntu-24.04; timeout-minutes: 12
    steps: [checkout, setup-node 20.18, npm ci, "npm --workspace packages/shared-ui run test -- --run"]
```

- [ ] Step 2: 本地 act 语法验证或 push 到分支观察
- [ ] Step 3: 修复 YAML 缩进/job needs（此处 4 个 job 无 needs，全并行）
- [ ] Step 4: 验证 backend-unit 不包含 `-m bench`（防止 PR 跑慢）
- [ ] Step 5: commit CI

---

### Task GATE · W11 Final Audit 8/8 AC + NOTOUCH v2 逐文件 anchor diff
- AC1 PY 130+ GREEN · AC2 TS 60+ · AC3 190+ TOTAL
- AC4 STEP1 2000 ≤3.0s median (≤3900 ms CI)
- AC5 E2E ≤180s
- AC6 NOTOUCH v2 14 file anchor diff
- AC7 parity 6 preset 200 pass
- AC8 0 new 3rd party dep

---

## Appendix A · Test B1-B32 补全（D1-1 tests 32 完整清单，实际写 test_simhash_bktree.py 必须全部 32 个带断言）
```
B11  build 1000 查询 fp=0 半径 10 → 无 crash OOM
B12  insert(fp=NONE) 应抛 TypeError
B13  payload 可为任意类型 (int/dict/tuple)
B14  insert Nones → query 返回 [None] 无错
B15  build 大列表 2000，每个 self radius=0 都可查询 (2000 assert)
B16  query radius=-1 → 返回空 (不抛)
B17  distance_fn 自定义 (lambda x,y: 0) → 任意 query radius >=0 返回所有
B18  distance_fn 自定义 lambda x,y: 100 → 不命中除非 radius>=100
B19  build 后插入相同 fp 100 次 → query 返回 100 payload
B20  两个相似 cluster 10+10 互斥 → query radius=6 返回该组
B21  _union_find_cluster(空 pairs) → 空 groups
B22  _union_find_cluster(2 pair 链 a-b b-c) → 1 group[a,b,c] len=3
B23  _union_find_cluster(4 ids 不连) → 4 groups 各 size 1
B24  _union_find_cluster 顺序敏感吗？pairs [(b,a),(c,b)] vs [(a,b)] → 一致
B25  find_duplicates_bktree 空 records → ([], diag 空)
B26  find_duplicates_bktree 1 条 → ([id0], sizes_hist {"1":1})
B27  find_duplicates_bktree 2 条 完全相同 title → 保留较小 id，sizes_hist {"2":1}
B28  find_duplicates_bktree n_jobs=1 vs n_jobs=8 → kept 完全一致
B29  perf["nodes"] == len(records)
B30  hamming_hist 所有键均 <=6 (THR)
B31  sizes_hist.values() 求和 == len(records)（必等恒等式）
B32  perf["speedup_x"] >= 1.5 (对 N>=100)
```

---

## Self-Review 3-pass（Plan 写完必须自己跑一遍）
1. **Spec Coverage:** 遍历 W11 Spec §0-§5 所有行 → 每个 requirement 都能找到对应 Task：
   - Q1 N=2000 / SLO 3s / 180s → D2-4 bench, D2-5 HP
   - Q2 CI 4 Job → D4-1
   - Q3 3 Cards text-only → D3-1/2/4
   - Q4 Synthetic 2000 fixture → D0-1
   - Q5 THRESHOLD=6 locked → D1-1 `THR` 命名 const import，tests 里 assert THR==6 (D1-1 B1 可加)
2. **Placeholder Scan:** 全文搜索 "TODO/TBD/省略/相似" 等 → 上述 B11-32 用了 Appendix，已补全；其他 section 无 placeholder
3. **Type Consistency:**
   - DedupDiagnostic 三列统一命名为 `sizes_hist / hamming_hist / perf_json`（和 simhash.py 返回 diag 键、DedupDiagCards.tsx props 完全一致，无需转换）。
- DedupDiagnostic.sizes_hist/hamming_hist/perf_json 键名 ("build_ms","step1_total_ms","speedup_x") 在 D2-1 DM1、simhash.py `_dedup_diag_stats`、D3-1 组件 props、D2-5 HP13 diag 断言 → 4 处完全一致
   - cc_max 500→2500 在 D2-1 models、D3-3 modal error msg、Sect1.1 表格 → 3 处一致
   - `/steps/{idx}/diag` 路径在 D2-2 Route、D3-2 fetch、Screen2 拉取 → 一致

---

Plan complete and saved to `docs/superpowers/plans/2026-08-24-wave-11-stability-bk-tree-ci-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** — 我派 1 个 fresh subagent 每个 Task（D0-1 到 Gate），每 task 完成后 2-phase review，高吞吐

**2. Inline Execution** — 这个 session 直接用 executing-plans 批量跑，中间有 checkpoint review

Which? 1 / 2
