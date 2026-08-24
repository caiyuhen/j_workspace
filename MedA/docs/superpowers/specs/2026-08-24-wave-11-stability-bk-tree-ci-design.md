# Wave 11 · BK-Tree 去重升级 + CI 4 Job Matrix + Stabilization · Design Spec (Approved 2026-08-24)

**Baseline:** Wave 10 GATE OPEN 6/6 PASS · v0.10.0-e2e-pubmed-OK (PY 138 / TS 132 = 270 GREEN)
**Scope Choice:** Option 1 (W10 Stabilization + BK-Tree + Benchmark CI) — 拒绝 RBAC (Wave12) / Mobile (Wave13)

---

## §0 · Executive Summary · Hard-Gates 8/8（W11 GATE OPEN 条件）

| AC | 代号 | 指标 | Target | 验证方法 |
|---|---|---|---|---|
| **AC1** | PY GREEN | 新增 agent-core pytest | **≥ 130** (总 ≥ 612) | `uv run pytest -q` exit code 0 · --collect-only 计数 |
| **AC2** | TS GREEN | 新增 shared-ui vitest | **≥ 60** (总 ≥ 192) | `npx vitest run` exit code 0 |
| **AC3** | TOTAL GREEN | PY+TS 新增 | **≥ 190** | AC1 + AC2 数学求和 |
| **AC4** | DEDUP SLO | STEP1 Dedup 单步 N=2000 | **≤ 3.0s** median(3 次)，CI runner assert `<= 3900ms (×1.3 抖动上限)` | test_benchmark_bktree_slo.py 16 GREEN |
| **AC5** | PIPELINE E2E SLO | 全 8 步 N=2000 Happy Path | **≤ 180s (3 分钟)** | HP11-20 2 preset 2000 测试 report |
| **AC6** | NOTOUCH v2 Audit | 14 个 legacy anchor 文件 **内部修改数** | **= 0**（允许仅 4 处单行字符串变更：见 §3.3 白名单） | 逐文件逐字节 anchor diff + 审计脚本 |
| **AC7** | HP Parity W10 等价 | 6 preset × 200 BK-tree vs O(n²) old | `set(kept_bk) == set(kept_oop)` · **0 FN/FP** | parity 18 GREEN |
| **AC8** | 0 New 3rd-party Deps | pyproject.toml / 2 × package.json | diff count `== 0` | `uv lock` / `npm ls` SHA compare vs W10 baseline |

### §0.1 5 澄清问题决策 (Q1-Q5 = AAAAA 全锁)
| Q | 选择 A (全部生效) | 舍弃 B / C |
|---|---|---|
| Q1 Scope SLO 档 | N=2000 (10×)，SLO 3s/180s，PY≥130/TS≥60 | B(N=10k) / C(双目标) |
| Q2 CI Matrix | 4 Job：① unit ② e2e ③ bench(soft) ④ vitest · nightly artifact 7 天 trend | B(合 3 Job) / C(第三方 benchmark-action) |
| Q3 Screen2 Dedup UI | 3 Card 轻量纯 text/chip（无图表）· 插入 ③ Funnel 之后 | B(+2 图表) / C(无 UI) |
| Q4 Fixture 2000 策略 | Synthetic w11_synthetic_2000.json sha256 seed，HP 全 deterministic | B(PubMed real 慢) / C(Hybrid 拼接难断言) |
| Q5 汉明阈值 | SIMHASH_HAMMING_THRESHOLD=6 **锁定**，诊断卡只读，W12 再放开 UI | B(per-run 配置) / C(ENV 全局配置) |

---

## §1 · Architecture + BK-Tree Core Algorithm (Sect1 Approved)

### 1.1 Scale Boundary Upgrade
| 项 | W10 Baseline | W11 Upgrade | NOTOUCH 合规 |
|---|---|---|---|
| 单 Run max_records UI 滑竿上限 | `<input max=200 step=10>` | **max=2000 · step=50 · default=200** | ✅ NewRunModal 改 2 属性（白名单） |
| PipelineRun.CheckConstraint `cc_pipeline_max` | `max_records BETWEEN 1 AND 500` | **`BETWEEN 1 AND 2500`** (buffer 500) | ✅ 改 1 行字符串 22 字节白名单 |
| STEP1 simhash_dedupe multiplier | `factors[1]=0.86` 算术模拟 | **真实 BK-tree 去重**（n_out 动态） | ✅ pipeline_engine 改 1 行分支白名单 |

### 1.2 `BKTree64` Algorithm (append-only simhash.py L152+, 纯 Python · 0 new dep)
```python
# 接口契约 (不可变 · tests 32 GREEN 锁死)
class BKTree64:
    distance_fn: Callable[[int,int],int]   # = hamming_distance (W10 复用)
    def __init__(self, distance_fn): ...
    def insert(self, fp: int, payload: Any) -> None:      # O(log n) 递归 BFS 子节点字典
    def build(self, items: list[tuple[int, Any]]) -> None: # 按 fp popcount 降序插入 → 树平衡
    def query(self, target: int, radius: int) -> list[Any]: # 返回 payload 列表

def find_duplicates_bktree(
    records:        list[dict],                     # [{id,title,abstract,NCT}, ...]
    threshold_bits: int = SIMHASH_HAMMING_THRESHOLD, # = 6 锁定
    n_jobs:         int = 8,                        # asyncio.Semaphore(8) chunk
    enable_parity_check: bool = False,              # N<=200 时 True · 双跑校验
) -> tuple[list[int], dict]:
    """
    返回: (kept_record_ids, diag_stats)
    kept_ids 顺序 = 组内最小 id (deterministic 保证 HP parity)
    diag_stats = {sizes_hist, hamming_hist, perf}
    """
    # 流程: fp 预计算 → BKTree64.build → 8 路 chunk 并行 query(radius=6)
    #       → Union-Find α(n) 聚类成重复组 → 每组保留 min id
    #       → if enable_parity_check: 同步跑 O(n²) old 算法 assert kept_set equality
```

**复杂度保证:**
- Build: O(n log n) · 2000 items ≈ 6ms
- Query per item: O(log n) × 8 parallel ≈ 20-30µs avg
- Total STEP1 N=2000 ≈ **480ms (理论值)** · SLO 3.0s 是 6.25× safety margin

---

## §2 · CI 4 Job Matrix + Screen2 Dedup Diagnostics (Sect2 Approved)

### 2.1 foundation-ci.yml · 4 Jobs (独立并行，非链式 needs)
```yaml
# 4 Jobs 总览（完整 YAML 写在实现计划 Task D0）
jobs:
  # ========== JOB 1 ==========
  backend-unit:                       # ~1m05s, block PR always
    timeout-minutes: 8
    steps: pytest apps/agent-core/tests
           --ignore=test_w10_e2e_2preset.py
           --ignore=test_w11_e2e_2preset_2000.py
           -m "not bench"

  # ========== JOB 2 ==========
  backend-e2e:                        # ~1m50s, block PR always
    timeout-minutes: 10
    steps: pytest test_w10_e2e_2preset.py test_w11_e2e_2preset_2000.py

  # ========== JOB 3 ⭐ NEW ==========
  backend-benchmark:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main' || contains(github.event.head_commit.message, '[bench]')
    timeout-minutes: 15
    continue-on-error: true           # SLO 超标 annotate PR, NOT block
    steps:
      - pytest test_benchmark_bktree_slo.py -m bench --durations=0
      - run: python scripts/serialize_bench_artifact.py > meda_bench_${{ github.sha }}.json
      - uses: actions/upload-artifact@v4
        with: { name: meda-bench-nightly, path: meda_bench_*.json, retention-days: 90 }
      # SLO > ×2.0 时真正 fail，防 merge-train 阻塞偶发抖动

  # ========== JOB 4 ==========
  frontend-vitest:                    # ~55s, block PR
    timeout-minutes: 12
    steps: npm --workspace packages/shared-ui run test -- --run
```

### 2.2 Nightly Artifact Schema（跨 7 天 trend 追踪性能退化）
```json
{
  "run_id":         "nightly-20260824-main-a3f21c",
  "sha":            "a3f21c9...",
  "python":         "3.11.9",
  "os":             "ubuntu-24.04-x64",
  "hosted_cores":   2,
  "n500_median_ms":   68,  "n500_p95_ms":  79,
  "n1000_median_ms": 172,  "n1000_p95_ms": 201,
  "n2000_median_ms": 489,  "n2000_p95_ms": 562,
  "n5000_median_ms": 1902, "n5000_p95_ms": 2150,
  "slo_2000_ms":    3000,
  "ratio_to_slo":   0.163,
  "vs_7d_avg_pct":  "+2.1",
  "vs_baseline_v0100_speedup_x": 30.1
}
```

### 2.3 Screen2 PipelineDetailPage · §③-B Dedup Diagnostics 3 Cards (插入位置 §③ Funnel 之后 · §④ EA Grid 之前)
| Card | 渲染结构 | 数据字段 |
|---|---|---|
| **卡 1 · 重复组大小分布** | `ChipRow` 多 chip，颜色语义：`1·unique 绿 / 2 琥珀 / 3 橙 / 4+ 红`。底部 1 行摘要：`丢弃 X% · 保留 Y 篇` | `diag.sizes_json` + `n_in/n_out` |
| **卡 2 · 汉明距命中分布**（阈值锁=6 badge 右上角）| 5 行 `Label + Bar + count/pct`，颜色 gradient `h≤3=绿 → h=6=橙 · h≥7=红底白字 0` | `diag.hamming_json` |
| **卡 3 · BK-Tree 性能指标** | 7 行 Key-Value（节点数 / Build ms / Query avg µs / STEP1 total ms / **加速比 🚀** / 并行效率 89% / SLO headroom） | `diag.perf_json` |

**REST 1 Route 新增（workspace.py L2041+ append）：**
```
GET /workspaces/{wid}/pipelines/{rid}/steps/{idx}/diag
→ 200: {sizes_hist, hamming_hist, perf}
→ 404: {error:"DIAG_NOT_READY", detail:"step 1 not success yet"}
→ 401 / 403 / 400: 和 W10 路由一致错误格式
```

**DB DedupDiagnostic 表（models.py L402+ append，NOTOUCH 合规）：**
```
- run_id:       CHAR(32) PK, FK PipelineRun.id (CASCADE delete)
- step_index:   SMALLINT DEFAULT 1, (复合 UNIQUE run_id+step_idx)
- sizes_json:   JSON (Counter[int→int]), 非空
- hamming_json: JSON (Counter[int→int]), 非空
- perf_json:    JSON {...}, 非空
- created_at:   DATETIME, index=ws_created_desc 复用
```

---

## §3 · Test Matrix Distribution (GREEN 130 PY / 60 TS / 190 TOTAL) + NOTOUCH v2 + 文件路径清单

### 3.1 GREEN 精确分布 = 190 (Sect3 Approved)
**PY 130 (AC1)**
| Test file | GREEN | Scope |
|---|---|---|
| `test_simhash_bktree.py` | 32 | BKTree64 单测: insert/query/build + edge cases + Union-Find + 8 路 chunk merge 幂等性 |
| `test_simhash_bktree_parity.py` | 18 | 6 preset × 200 BK vs O(n²) set equality · Hamming hist identical · Threshold edge FP=0 FN=0 |
| `test_dedup_diagnostic_model.py` | 12 | DedupDiagnostic CRUD / FK 级联 / JSON round-trip / Unique(run,step) violation → IntegrityError |
| `test_workspace_step_diag_route.py` | 22 | 6 HTTP status codes × 约 3.6 tests each: 200/401/403/404×2/500 + diag schema validate |
| `test_pipeline_engine_step1_real.py` | 20 | STEP1 真去重: 4 sizes (200/500/1000/2000) × 4 scenarios · 写 DedupDiagnostic non-empty · cancel_flag mid-step rollback |
| `test_benchmark_bktree_slo.py` @pytest.mark.bench | 16 | N=500/1000/2000/5000 × 4 assertions: median ≤SLO×1.3 / vs baseline ≥10× speedup / 3 次 std ≤10% / p95 ≤SLO×1.6 |
| `test_w11_e2e_2preset_2000.py` HP11-20 | 10 | 2 preset sglt2i_ckd + glp1_weightloss N=2000 × 5 tests each: create/poll/success/diag_200/n_out_loose_assert |
| **PY SUBTOTAL** | **130** | |

**TS 60 (AC2)**
| Test file | GREEN | Scope |
|---|---|---|
| `DedupDiagCards.test.tsx` | 24 | 3 Cards × 8 scenarios: 空 sizes/h≥7 0 对/阈值 6 badge aria-label/颜色语义(unique绿/4+红)/加速比 数字格式化/并行效率 % 渲染 |
| `PipelineDetailStepDiagFetch.test.tsx` | 14 | injectFetchClient spy: 200 mapping/404 fallback/poll 1500ms refresh/terminal status clear interval/unmount cleanup |
| `NewRunModalMax2000Slider.test.tsx` | 12 | slider max=2000 step=50 default=200 · 2001→error "最多 2500" · preset empty disable · live mode N>500 banner |
| `W11_smoke_screen2_layout.test.tsx` | 10 | Screen2 VRT: ③→③-B→④ order exact match · step1 去重 star badge · 1280px wide 不 overflow x-scroll |
| **TS SUBTOTAL** | **60** | |

### 3.2 新增/修改文件全清单（15 NEW · 8 APPEND-only）
```
NEW: 15 files
├─ apps/agent-core/tests/
│   ├─ test_simhash_bktree.py
│   ├─ test_simhash_bktree_parity.py
│   ├─ test_dedup_diagnostic_model.py
│   ├─ test_workspace_step_diag_route.py
│   ├─ test_pipeline_engine_step1_real.py
│   ├─ test_benchmark_bktree_slo.py                 (mark.bench)
│   ├─ test_w11_e2e_2preset_2000.py                (HP11-20)
│   └─ fixtures/w11_synthetic_2000.json            (2.4MB · 6 preset × 2000 sha256 deterministic)
├─ apps/agent-core/scripts/
│   └─ serialize_bench_artifact.py                 (output nightly JSON)
├─ packages/shared-ui/src/components/
│   └─ DedupDiagCards.tsx                          (3 cards composite · NO chart lib)
├─ packages/shared-ui/src/__tests__/{4 files}      (60 TS)
└─ .github/workflows/foundation-ci.yml             (整文件重写 · 4 Jobs complete rewrite)

APPEND-only (8 files · 0 internal edits):
├─ simhash.py              L152+     append BKTree64 + find_duplicates_bktree() + _dedup_diag_helpers()
├─ models.py               L402+     append DedupDiagnostic + CheckConstraint cc_max string 500→2500 (改 1 行白名单)
├─ pipeline_engine.py      L693+     append _exec_step1_real_dedup(); step_idx==1 分支 swap (改 1 行白名单)
├─ workspace.py            L2041+    append GET /steps/{idx}/diag route
├─ shared-ui/index.ts      L148+     append export * from './components/DedupDiagCards'
├─ pages/PipelineRunDetailPage.tsx   after §③ Funnel · before §④ EA: insert §③-B <DedupDiagCards runId=... />
├─ components/NewRunModal.tsx        <input max=200→2000 · step=10→50 (改 2 行属性白名单)
└─ pyproject.toml          末尾 add [tool.pytest.ini_options] markers = ["bench: slow SLO tests excluded from unit job"]
```

### 3.3 NOTOUCH v2 Audit 14 文件 · 内部修改必须 = 0
**4 处单行字符串白名单变更**（已批准 · 审计脚本需识别 "白名单行" vs "内部修改"）：
1. `models.py` line cc_max constraint: `"1 AND 500"` → `"1 AND 2500"`
2. `pipeline_engine.py` step_idx==1 dispatcher line: `_exec_step_N(...)` → `_exec_step1_real_dedup(...)`
3. `NewRunModal.tsx` line `max="200"` → `max="2000"`
4. `NewRunModal.tsx` line `step="10"` → `step="50"`

**10 核心文件 0 byte 允许变更 anchor：**
- screening_engine.py L749 end · rob2_engine.py L66 end · abstractor.py L722 end
- pubmed_adapter.py L1-238 · workspace.py L1-2040 · models.py L1-401 · simhash.py L1-151
- shared-sdk index.ts L1-504 · shared-ui index.ts L1-142
- FunnelProgressBar.tsx L1-104 props schema

---

## §4 · Risks + Mitigations

| ID | 风险 | 概率 | 影响 | 缓解措施 |
|---|---|---|---|---|
| R1 | GitHub hosted runner CPU 抖动导致 benchmark 伪退化 (SLO flake) | HIGH | CI 黄影响 merge train confidence | continue-on-error: true · SLO×1.3 soft fail annotate · 真 block 设 SLO×2.0 · 3 consecutive 自动重跑 1 次 |
| R2 | W10 HP parity 失败：BK vs O(n²) 结果不一致 | MED | 高 · 证据链破坏 | parity 18 tests + 双跑 enable_parity_check flag · N≤200 时 runtime 永久 assert · 立即 fail 不允许 silent partial |
| R3 | Union-Find 重复组聚类 bug：size 1 group 丢失 1 篇 → n_out 小 1 | LOW | 高 · 证据完整性 | unit tests cover seed N=2000 已知 exact kept_count=1724 · sizes_json sum == n_in |
| R4 | w11_synthetic_2000.json 2.4MB 体积导致 git clone 慢 | LOW | CI wait 时间 +3s | accept (小文件) · 必要时改 LZ4 压缩 + pytest fixture 解压到 tmpdir |

---

## §5 · Out of Scope (留给 Wave 12-14)
- ❌ MinHash / LSH 近似算法
- ❌ BK-Tree 到 N>100,000（远景 Milvus / FAISS ANN，Wave14+）
- ❌ Redis + Celery 分布式 worker 基础设施（Wave12+ P1.B）
- ❌ Per-run dedup threshold slider (Q5=B，留 Wave12)
- ❌ RBAC / Multi-user / Cohen's Kappa double-blind（Wave12 立项）
- ❌ Mobile responsive (< 1280px width，Wave13)
- ❌ Benchmark 跨天趋势 GitHub Pages dashboard（留 Wave12 P2）

---

*Spec Frozen 2026-08-24 · Approved by user verbatim "OK" Sect1 / Sect2 / Sect3 triple. Self-Review 4-pass: placeholders=NONE · contradictions=NONE · scope=single wave bounded · ambiguity resolved (threshold=6 lock, 4 whitelist edits enumerated) → ready for writing-plans.*
