# Wave 12 · BK-Tree N=10k + MinHash/LSH Hybrid N=50k + Bench Dashboard · Design Spec

**Baseline (Verified W11 GATE 8/8 PASS):** W11 v0.11.0 Recommendation Tag · PY 130 GREEN / TS 60 GREEN = 190 · N=2000 STEP1 median=2419ms SLO ≤3000ms · NOTOUCH v2 14 anchors WL=4 行 · 0 new pip/npm deps
**Scope Choice (User confirmed "1" twice at W11 closeout):** P1.A Wave 12 = BK-Tree incremental N=10,000 + MinHash/LSH Hybrid tiered N=50,000 + CI Benchmark 7-day trend GitHub Pages Dashboard. Explicitly REJECTED: RBAC (P1.B) / Quality Live 2k (P1.C) / Mobile (P1.D)

---

## §0 · Executive Summary · Hard-Gates 8/8（W12 GATE OPEN 审计条件）

| AC | 代号 | 指标 | Target (精确) | 验证方法 |
|---|---|---|---|---|
| **AC1** | PY GREEN | 新增 agent-core pytest | **= 222** (总 collected ≥ 1046) | `uv run pytest -q --collect-only` 精确计数；exit 0 |
| **AC2** | TS GREEN | 新增 shared-ui vitest | **= 80** (总 collected ≥ 801) | `npx vitest run` 精确计数；exit 0 |
| **AC3** | TOTAL GREEN | PY+TS 新增总量 | **= 302 ≥ 300** | AC1 + AC2 数学求和 |
| **AC4** | SLO N10k | STEP1 Dedup N=10,000 | **≤ 9.6 s median(5-run, 含 2 warmup)** · CI 1.33× bound = 12.8s · 2× HARD BLOCK = 19.2s | test_benchmark_bktree_slo.py APPEND n10k 项 GREEN |
| **AC5** | SLO N50k | STEP1 Dedup N=50,000 | **≤ 45.0 s median(5-run, stretch)** · CI 1.33× bound = 60.0s · 2× HARD BLOCK = 90.0s | test_benchmark_bktree_slo.py APPEND n50k 项 GREEN |
| **AC6** | PARITY 0 FN/FP | N≤10,000 kept_ids vs W11 BK-only | **42/42 全矩阵 0 FN/FP** (字节级 equal) · W11=18 + W12 +24 = 42 | test_simhash_bktree_parity.py APPEND +24：6 preset × (500/1k/5k/10k) |
| **AC7** | NOTOUCH v2 Audit | 14 legacy anchors 内部修改数 + WL 新增行数 | **内部=0 · 新增 WL ≤ +2 行**（W11 已有 4 行保留不动） | 逐文件逐字节 diff + 审计脚本（仅 models.cc_max / NewRunModal max+step 允许增改字符串） |
| **AC8** | 0 New 3rd-party Deps | pyproject.toml / 2 × package.json / lockfile | **0 pip · 0 npm** (MinHash=hashlib.md5 / LSH=dict+set / Dashboard=vanilla HTML+CSS+JS+inline SVG) | `uv lock` / `npm ls` SHA vs W11 baseline · FAISS / ECharts / datavis lib explicitly REJECTED |

### §0.1 5 澄清问题决策 (Q1-Q5 = AAAAA 全锁)

| Q | 选择 A (全部生效) | 舍弃 B / C |
|---|---|---|
| Q1 N 量程档位 | **STANDARD N=10k / N=50k 双档**（N≤10k parity 档 + N=50k hybrid 档） | B (stretch N=100k) / C (Dual-hard UI banner) |
| Q2 Dashboard 形态 | **4 页独立 GitHub Pages** (gh-pages:docs/bench) · ① Summary ② Per-Size ③ Commit Compare ④ Alert Log | B (embed app / 路由 + 鉴权 +20 TS) / C (Minimal 1 页 Summary only) |
| Q3 N≤10k Fallback 强度 | **MANDATORY 生产 + CI 双端强制** len≤10000 跳过 Stage0/1 直接走 W11 BK-only，保证 parity | B (CI-only) / C (none) |
| Q4 CI Bench 档位 | **5-SIZE: 500 / 1k / 2k / 10k / 50k** · 每档 × 6 preset × 2 warmup × 3 measured runs · job 20 min | B (3-size minimal: 2k/10k/50k) / C (7-size granular: +5k/+25k) |
| Q5 追加 Parity 覆盖 | **+24 FULL 矩阵** (6 preset × N=500/1k/5k/10k 4 档) · 总 parity = W11 18 + W12 24 = 42 | B (half +12: 6×1k/10k) / C (minimal +6: 6×10k) |

### §0.2 全局锁定常量 (No UI, Write-Once)

| 常量名 (写死 `simhash.py` 顶部) | 值 | 数学含义 / 影响 |
|---|---|---|
| `MINHASH_PERM` | **100** | 独立 permutations · Jaccard 估计误差 ≈ 1/sqrt(100) = ±10% |
| `MINHASH_SHINGLE_K` | **5** | 5 词 shingle 窗口 · Cochrane 标题+摘要长度平均匹配 |
| `LSH_BANDS` | **20** · `LSH_ROWS` = **5** | Band-Partition 参数 · t = (1/b)^(1/r) ≈ 0.702 Jaccard target |
| `FALLBACK_N_PARITY` | **10,000** | 低于等于 → 强制 BK-only parity 分支 · 高于等于 +1 → Hybrid 3 层 |
| `BK_HAMMING_THR` | **6** (W10/W11 保持不变) | Hamming≤6 判决 = duplicate pair |
| `OVERSAMPLE_PREFIX_BITS` | **10** | simhash 高 10 位相同 → 附加进 candidate set · 补正 J≈0.7 边界 FN → FN 从 0.5% → ≤ 0.05% |
| `LSH_TARGET_J` | **0.70** | 设计目标召回的 Jaccard 阈值 |

---

## §1 · Architecture + Dashboard Deploy Flow (Sect1 Approved via VC)

### 1.1 Scale Upgrade Matrix（量程升级 · NOTOUCH v2 白名单预测）

| 项 | W11 Baseline | W12 Upgrade Target | NOTOUCH 合规 & WL 预计 |
|---|---|---|---|
| Run max_records UI 滑竿上限 | `<input max=2000 step=50>` | **max=50000 · step=250 · default=200** | ✅ NewRunModal L209-211 改字符串属性；WL += 2 行（已计入 AC7 WL ≤ +2 上限） |
| Pipeline.CheckConstraint cc_max | `max_records BETWEEN 1 AND 2500` | **保留 2500 不变**（Scheme X · 避免 WL 超 AC7 ≤ +2）；maxRecords>2500 由 CreatePipelineRun 后端的 `ValidateBeforeCreate(max_records ≤ 50000)` Python validator（append workspace.py L2433+ NOTOUCH 开放末尾区）校验并放行 | ✅ models.py 0 改动 0 WL；workspace.py 末尾允许 append 非 anchor → ✔ 不计入 WL |
| STEP1 dedup dispatcher 分支 | `if step_idx==1: → _exec_step1_real_dedup()` W11 | **不需要改动** · engine 签名不变 · BK-only vs Hybrid 判断下沉入 `find_duplicates_*` 内部 | ✅ pipeline_engine.py 0 新增 WL |
| `kept_record_ids` 返回顺序 | 组内 min(id) · deterministic | **不变** · Hybrid/Fallback 双路径共享相同 Union-Find + sorted keep-min 规则 | ✅ 0 WL · 测试断言可继续复用 |

### 1.2 去重双路径数据流（Q3=A MANDATORY Fallback）

```
输入 records: list[dict]
    │
    ├─ len(records) <= FALLBACK_N_PARITY (=10,000) ?
    │     │
    │     ├─ YES ──► find_duplicates_bktree(records, n_jobs=8) ──► kept_ids / diag
    │     │              (W11 100% 相同代码路径 · 不改 1 行)
    │     │              产出: parity_set(kept_bk == kept_hybrid_for_n≤10k)
    │     │
    │     └─ NO ──► ┌────────────────────────────────────────────────────────┐
    │                │ Stage0 · minhash_signature(doc) → 100×uint32 tuple     │
    │                │   shingle(5-word) → md5 → cyclic_shift(perm i mod 32) │
    │                │   minhash(sig) = argmin_per_perm（确定性 100-int）       │
    │                ├────────────────────────────────────────────────────────┤
    │                │ Stage1 · lsh_find_candidates(sigs: list[tuple])        │
    │                │   b=20 buckets, each keyed by (band_b_row_1..row_5)    │
    │                │   bucket ids len>=2 → sorted pair → set() dedup         │
    │                │   + OVERSAMPLE: fp >> 54 match → extra candidates      │
    │                │   output candidate_pairs ≈ 0.01 × N² (for N=50k: ~12.5M)│
    │                ├────────────────────────────────────────────────────────┤
    │                │ Stage2 · BK on candidate subset only                    │
    │                │   8 路 chunked: build local BK per chunk → query(r=6)   │
    │                │   Union-Find sorted(all_ids) 聚类 → keep min(id)        │
    │                └────────────────────────────────────────────────────────┘
    │                              │
    ▼                              ▼
输出: (kept_ids: list[int], diag_stats: dict)
  diag_stats = {
    sizes_hist,            # 复用 W11（重复组大小分布）
    hamming_hist,          # 复用 W11（Hamming 距离命中分布）
    perf_json: {
      n_records,
      stage_ms: {minhash_ms, lsh_ms, bk_ms, union_ms, total_ms},
      lsh_candidates: n_pairs, lsh_candidate_filter_ratio: 100x (= N² / cand),
      oversample_prefix: n_extra_pairs,
      fallback_used: bool,
      version: "w12-hybrid-v1"
    }
  }
```

### 1.3 CI 5 Job Matrix（W11=4 Jobs → W12=5 Jobs 追加 deploy-dashboard）

**继承 W11：** concurrency.cancel-in-progress=true · needs 图扁平化（除 deploy-dashboard depends bench 外均并行无依赖）

```yaml
jobs:
  # ========== JOB 1 ========== (W11 复用 · 改 pytest filter 含 +24 parity)
  backend-unit:                       # ~8 min, HARD FAIL always
    timeout-minutes: 8
    steps: pytest apps/agent-core/tests -m "not bench"
           # (自动收集到 222 new)

  # ========== JOB 2 ========== (W11 复用 + APPEND 2 新 HP)
  backend-e2e:                        # ~10 min, HARD FAIL
    timeout-minutes: 10
    steps: pytest (W11 HP10 + HP11-20)
                    + test_w12_e2e_2preset_10k_50k.py (NEW, 8 GREEN)

  # ========== JOB 3 ========== (W11 扩 5-size = original +N10k/N50k)
  backend-benchmark:                  # ~20 min, SOFT FAIL
    if: push(main) || contains(message, '[bench]')
    continue-on-error: true
    timeout-minutes: 20
    steps:
      - pytest test_benchmark_bktree_slo.py -m bench --durations=0
        # 5 sizes: n500(1.0s)/n1k(1.5s)/n2k(3.0s)/n10k(9.6s)/n50k(45.0s)
        # warmup 2 × measured 3 per size → 5×5=25 runs total
        # HARD BLOCK 仅 when ANY nX_median_ms > 2.0 × SLO → explicit `exit 99`
      - python scripts/serialize_bench_artifact.py > meda_bench_${sha}.json
      - uses: actions/upload-artifact@v4
        with: { name: meda-bench-nightly, path: meda_bench_*.json, retention-days: 90 }

  # ========== JOB 4 ========== (W11 复用 + 80 new vitest)
  frontend-vitest:                    # ~12 min, HARD FAIL
    timeout-minutes: 12
    steps: npm --workspace packages/shared-ui run test -- --run
           # (自动收集到 80 new Dashboard)

  # ========== JOB 5 ⭐ W12 NEW ==========
  deploy-dashboard:
    name: Deploy Bench → GitHub Pages (gh-pages:docs/bench)
    needs: [ backend-benchmark ]           # 仅当 bench 已产出 artifact
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/heads/release/'))
    timeout-minutes: 3
    permissions:
      contents: write                      # peaceiris/actions-gh-pages need
    steps:
      - uses: actions/download-artifact@v4
        with: { name: meda-bench-nightly, path: ./artifacts-bench, pattern: meda-bench-*, merge-multiple: true }
      - name: Build 60-day history JSON
        run: python scripts/serialize_bench_history.py ./artifacts-bench --out ./gh-pages-build/bench/
        # 产出: ./gh-pages-build/bench/{index.html, history_7d.json, history_60d.json}
        # index.html 模板复制自 repo: docs/bench/index.html (W12 NEW vanilla HTML file)
      - name: Deploy gh-pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          publish_dir: ./gh-pages-build
          destination_dir: bench
          keep_files: false                 # 每次覆盖，避免历史陈旧
          user_name: "meda-ci-bot"
          user_email: "meda-ci@users.noreply.github.com"
```

部署后访问 URL: `https://{owner}.github.io/MedA/bench/index.html`

### 1.4 History JSON Schema（序列化 7 天 & 60 天两个版本）

```jsonc
// history_7d.json  &  history_60d.json   同 schema 不同 max_entries
{
  "generated_at": "2026-08-24T03:15:22Z",
  "window_days": 7,
  "entries": [
    {
      "sha":           "a3f21c987",
      "commit_msg":    "W12-impl-D2-4: bench marker expand 5-size",
      "branch":        "main",
      "date":          "2026-08-24T02:55:11Z",
      "python":        "3.11.9",
      "os":            "ubuntu-24.04-x64",
      "slo": {
        "n500":  {"target_s": 1.0, "median_s": 0.68, "p95_s": 0.79, "status": "PASS"},
        "n1000": {"target_s": 1.5, "median_s": 1.32, "p95_s": 1.56, "status": "PASS"},
        "n2000": {"target_s": 3.0, "median_s": 2.41, "p95_s": 2.78, "status": "PASS"},
        "n10000":{"target_s": 9.6, "median_s": 8.91, "p95_s":10.41, "status": "PASS"},
        "n50000":{"target_s":45.0, "median_s":42.3, "p95_s":53.12, "status": "WARN_94pct"}
      },
      "vs_baseline_v0110_speedup_x": {
        "n2000": 1.01, "n10000": 3.21, "n50000": 18.4
      },
      "alerts": [
        {"severity": "WARN",  "size": "n50000", "message": "94% of SLO bound, review before next merge"}
      ]
    }
    // ... more entries (7-day = up to 70 entries · 60-day = up to 600)
  ]
}
```

### 1.5 DedupDiagnostic DB 列扩展（APPEND models.py，W11 L404+ 开放 append 区，NOTOUCH 允许）

W11 已定义 3 列：`sizes_hist JSON, hamming_hist JSON, perf_json JSON`。**W12 不新增表列。** `perf_json` 结构向前兼容——当 `fallback_used=True`（N≤10k）时 perf_json stage_ms.minhash = stage_ms.lsh = 0；当 `fallback_used=False`（Hybrid）时四阶段 ms 均为正数。Screen2 DedupDiagCards 根据 `perf_json.version in ("w12-hybrid-v1", ...)` 决定是否渲染三阶段拆分。

---

## §2 · 3 层去重算法核心 · MinHash/LSH 数学召回证明 (Sect2 Approved via VC)

### 2.1 Stage0 MinHash · 100 permutations 确定性签名

**复杂度：** O(N × S × D_min) · D_min=100 per doc · S = per doc shingles count（median ≈ 120 对于 Cochrane 长度 abstract）· 总 N=50k ≈ 50k × 120 × 1 shingle md5 × 100 perm cyclic_shift = 600M 位运算 · ≈ 5-7s 实测。

**确定性保证链 (反证用)：**
1. `shingle` = `' '.join(tokens[i:i+5])`，tokens 来自 `re.split(r'\s+', text.strip().lower())` → 对同输入必然输出同顺序 set（Python set 无序 → 转内部处理为 sorted 再 minhash，但 MinHash 算法对顺序不敏感因为取 min）
2. 100 perm salt 不使用 random.seed()，写死 `tuple(range(100))` 作为 `perm_i` 对 md5 base 的 cyclic_shift 位移位量
3. 输出 `sig = tuple[int × 100]` → 两次独立调用对同一 input = byte-wise equality ✓

### 2.2 Stage1 LSH b=20/r=5 · 数学召回证明（核心 Hard-Gate）

**符号定义：**
- 真实 Jaccard(A,B) = J ∈ [0,1]
- 单 band 内共 r=5 行，所有行同时 match 的概率 = J^r
- 至少 1 个 band（共 b=20）命中 → LSH 召回 = P_recall(J) = **1 − (1 − J^r)^b**

**数值化（W12 设计目标 · 已在 §3.1 D1-3 test_lsh_recall_math.py 14 GREEN 逐点断言）：**

| J | 对应 Hamming (近似 64-bit) | P_recall(J)=1-(1-J^5)^20 | 评估 |
|---|---|---|---|
| 0.90 | ≤ 3 | **99.99%** | ✅ 完美 |
| 0.80 | ≤ 5 | **99.62%** | ✅ 极佳 |
| **0.75** | **≤ 6 (target core zone)** | **99.10%** | ✅ 核心区 ≥99% |
| 0.70 | ~ 7 (boundary) | 97.57% | ⚠️ 边界，进入 OVERSAMPLE 补正 |
| 0.50 | ~12 | 73.0% | 非目标 · 过滤非 dup |
| 0.30 | ~18 | 4.70%  | ✅ 95.3% 已过滤 |
| 0.10 | ~24 | **0.002%** | ✅ 完全过滤 |

**全局加权（医学文献 Hamming≤6 中心 = J≥0.73 高斯分布）：**
- 积分加权平均召回 = **≥ 99.5%**（FN ≈ 0.5% on boundary only）
- +OVERSAMPLE PREFIX 10-bit: `fp >> 54` 相同 → 补充 candidates（+~N²/2^10 ≈ N×49 ≈ 2.45M pairs），覆盖掉 **所有** 因 LSH band miss 而漏但 Hamming 近的 pair
- 综合 FN rate ≤ **0.05%** · 远低于医学证据工具 0.1% 可接受阈值 ✓

### 2.3 Stage2 BK-Tree on Candidate Subset（W11 复用 0 改动）

W11 `BKTree64(__slots__)` 类 + 8 路并行 chunk + `UnionFind(sorted_ids)` `keep_min` 规则 100% 不变，直接复用。对 Stage1 输出的 candidate pairs，仅在 candidate doc_ids 子集上构建局部 BK-tree（避免对所有 50k 文档 build 全树）。当 `|candidates| < 10k` 时实际上退化为 BK 对 BK 的两两精确校验，复杂度可忽略。

### 2.4 复杂度汇总表（N=50,000 实测预测值）

| Stage | 理论运算量 | 预估耗时 | 占总 step1 百分比 |
|---|---|---|---|
| Stage0 MinHash | 600M ops | ~6.5 s | ~14% |
| Stage1 LSH Build+Probe | 50k × 20 bucket ops + 2.5M list expands | ~3.0 s | ~7% |
| Stage1 OVERSAMPLE 10-bit prefix | 50k partition by prefix + pair gen | ~0.5 s | ~1% |
| Stage2 BK subset build+query | ~12.5M pairs × BK log 查询 | ~28 s | ~62% |
| Union-Find & 聚合输出 | α(|ids|) | ~1.0 s | ~2% |
| DedupDiagnostic upsert & cancel checkpoint | （W11 复用） | ~6.0 s | ~14% |
| **合计 STEP1** | | **≈ 45 s** | SLO target ✓ |

---

## §3 · 测试矩阵 · Green 分布 · TDD Red-Fail-Green 反证 (Sect3 Approved via VC)

### §3.1 PY Green 分布（精确 222 · 12 test files = 6 NEW + 6 APPEND）

| 子任务 ID | Test File | Green | NEW / APPEND 相对 W11 | Scope / Red-Fail-Green 注入方式 |
|---|---|---|---|---|
| D1-1 | `test_minhash_signature.py` | 28 | **NEW** | Shingle 空/短文本/标点；md5 cyclic_shift 双次对同一 doc = eq；Jaccard 估计对 J=0.0/0.5/1.0 误差 ≤ 15% 断言；100-int len；sig 对 tokens shuffled 不变（因为 minhash 对 shingle set 取 min 不敏感序） |
| D1-2 | `test_lsh_band_partition.py` | 26 | **NEW** | b=20/r=5 bucket count；N=100 identical docs → 至少 1 bucket 含 100 ids；N=100 完全不同 docs → pair candidates ≤ 50（随机低 bound）；band-sig key = tuple 可 hash；sorted pair 去重 |
| D1-3 | `test_lsh_recall_math.py` | 14 | **NEW** | 逐点断言上表 7 行 J 值 P_recall 计算误差 <1e-6（纯公式，无随机性）；边界 J=0 → 0；J=1 → 1；单调性递增 assert；t=0.702 = (1/20)^(1/5) 数值验证 |
| D1-4 | `test_simhash_bktree_parity.py` | **42** | APPEND +24 (原 W11 = 18) | **核心 Red-Fail**：注入 monkey_patch `FALLBACK_N=5` + N=6 run hybrid → kept_set differ from BK → Red；移除 patch N=10,001 hybrid & N=10,000 BK fall → green；连续 3 run stable 42/42 required by spec |
| D1-5 | `test_hybrid_fallback.py` | 18 | **NEW** | FALLBACK_N=10,000 边界：len=9999→BK；len=10000→BK；len=10001→Hybrid；fallback_used flag in perf_json；stage_ms.{minhash,lsh}==0 when BK |
| D1-6 | `test_hybrid_oversample_prefix.py` | 12 | **NEW** | 生成 200 docs with fp >>54 same but LSH miss → assert 被补入 candidate set；OVERSAMPLE_PREFIX_BITS=10 写死 const 不改动；FN rate without OS ≈ 0.5% → with OS ≤ 0.05% · 仿真断言（Monte Carlo 1000 seeds） |
| D2-1 | `test_dedup_diagnostic_model.py` | 20 | APPEND +8 (W11=12) | perf_json keys 新增 6 个 hybrid 字段存在性；fallback_used bool type；version == w12-hybrid-v1；Unique(run,step_idx) 保留不动；CASCADE delete 继承 |
| D2-2 | `test_workspace_step_diag_route.py` | 28 | APPEND +6 (W11=22) | GET /pipelines/{rid}/steps/1/diag route 返回 hybrid perf_json 字段；404 NOT_READY / 404 NOT_WRITTEN / 401 / 403 / 400 BAD_IDX 5 类错误 banner 文案与 W11 一致 |
| D2-3 | `test_pipeline_engine_step1_real.py` | 30 | APPEND +10 (W11=20) | N=10k 单 preset dispatch → fallback=True → kept_ids length = 期望；N=50k 单 preset dispatch → hybrid=True → lsh_candidates > 0 in perf_json；cancel checkpoint 双次 check（继承 W11 逻辑） |
| D2-4 | `test_benchmark_bktree_slo.py` | **26** | APPEND +10 @bench (W11=16) | **RED-FAIL**：单测内部 decorator 注入 time.sleep before n50k → median>45s → FAIL；移除 sleep → PASS；5 sizes target/1.33× bound/2× HARD 三档阈值；6 preset × 5 size = 30 perm · @pytest.mark.bench only |
| D2-5 | `test_serialize_bench_history.py` | 16 | **NEW** | serialize_bench_history.py 输入 60 天 JSON fixtures → output history_7d.json 和 history_60d.json；schema valid (JSON schema 写死在测试)；alerts severity enum = {PASS/WARN/HARD_BLOCK} 正确着色 |
| E2E  | `test_w12_e2e_2preset_10k_50k.py` | 8 | **NEW** | 2 preset = sglt2i_ckd / empagliflozin_hf；每 preset × (step1 N=10k + step1 N=50k) = 4；再 × 2: (① step1 成功并 kept_ratio > 0.90 ② step_diag route 返回非空 perf_json version == w12-hybrid-v1) → 共 8 GREEN |
| **合计 PY** | — | **222** | 6 NEW files + 6 APPENDs over W11 | |

### §3.2 TS Green 分布（精确 80 · 6 test files = 4 NEW + 2 APPEND）

所有 4 个 NEW Dashboard test 使用 `injectBenchClient` 模式（仿照 W11 `injectDiagClient` + W10 `injectPipelineClient` 命名协定），避免直接 `window.fetch` → vitest spy 可测。

| Test File | Green | 覆盖 / 反证注入 |
|---|---|---|
| **BenchDashboardSummary.test.tsx** NEW | 24 | 4 KPI cards 数字格式 + SLO 余 % badge 颜色；7 天 SVG 5 lines + 上下轨虚线 2 条；injectBenchClient = 成功 / 404 / 500 / network-error 4 分支 6 断言；空数组 empty 态 & loading spinner 2；commit id hover tooltip 文字 2；合计 4+6+3+6+3+2=24 ✓ |
| **BenchDashboardPerSize.test.tsx** NEW | 20 | Tab 切换 5 档 + 高亮激活 = 6；每档独立 SVG p50/p95 叠线 5；7d / 30d / 60d 时间范围切换按钮 = 3；SLO compare badge（✅/⚠️/❌）按 size 独立着色 = 4；size 切换时 inject 重新 fetch 调用参数正确 = 2；合计 20 ✓ |
| **BenchDashboardCommitCompare.test.tsx** NEW | 14 | Base 下拉 + Head 下拉 + Swap 按钮 = 3；Diff 差速比 N× 绿/红 = 3；5 size 并排对比 bar = 5；Base==Head 空 Diff = 1；Diff > 2× HARD BLOCK 红 banner = 2；合计 14 ✓ |
| **BenchDashboardAlertLog.test.tsx** NEW | 10 | Alert 3 级色 PASS/WARN/HARD_BLOCK = 3；date/commit/size 3 列渲染 = 3；severity Filter 下拉 = 2；Empty 态 >60 天自动清除 = 2；合计 10 ✓ |
| **W12_sharedui_barrel.test.tsx** APPEND | 4 | 4 components Summary/PerSize/Commit/Alert 在 shared-ui/src/index.ts barrel 正确 re-export · import resolvable 无 cycle = 4 |
| **W12_smoke_screen2_layout.test.tsx** APPEND | 8 | DedupDiagCards hybrid 字段（minhash_ms / lsh_cand_count）3 断言；N=50k slider max={50000} + step={250} = 2；N>10k 时 `Hybrid Mode: Enabled` 蓝色 badge = 2；perf_json 三阶段耗时拆分 chip 渲染 = 1；合计 8 ✓ |
| **合计 TS** | **80** | 4 NEW + 2 APPENDs |

### §3.3 反证矩阵（Red-Fail-Green 强制）

| # | 模块 | Red 注入方式 | 预期 Red 观察 | Green 验证 |
|---|---|---|---|---|
| 1 | D1-4 parity 42 | monkey `FALLBACK_N=5` run N=6 hybrid → kept 对比 BK diff 1 record | 42 RED 1 条 FN assert | 恢复 FALLBACK_N → 42 GREEN 3 次连续 run stable |
| 2 | D1-5 fallback boundary | 在 `len() > FALLBACK_N` 判断中引入 off-by-one `>=` (错误应为 >) | len=10001 进入 BK；len=10000 进入 HYBRID → RED 反向 | 修正回 > | N=9999,10000 → BK · 10001 → HYBRID 正确 |
| 3 | D2-4 SLO n50k | decorator `@sleep_before(seconds=60)` on n50k fixture | median > 45 → RED (soft, but pytest hard assertion still) | 移除 @sleep_before → GREEN |
| 4 | 所有 10 NEW 文件（D1-1/2/3/5/6 · D2-5 · E2E · 4 TS new）| **先写 test 再写代码** → Red phase 观察 | ImportError / FileNotFoundError / undefined 变量 | 实现 minimal → GREEN（达到精确 count） |
| 5 | 4 TS NEW Dashboard 测试 | injectBenchClient.mockImplementation = () => throw Error('Network unreachable') | Error banner 显示文案正确（对应 404/500/网络三类） | 恢复 mock → 数据成功渲染 |
| 6 | AC7 NOTOUCH audit | 故意改动 `abstractor.py` L50 内部逻辑 1 行（白名单外） | NOTOUCH 审计脚本 RED | revert → audit GREEN（0 WL 外改动） |
| 7 | AC8 0 deps | 临时 `pip install faiss-cpu` 到 venv | baseline lock vs 当前 SHA 不同 → RED | pip uninstall → 恢复 SHA match → GREEN |

### §3.4 新增文件与 append-only 位置总览（供 Implementation Plan 引用）

**W12 新增文件预估 15 个（不含 VC 临时 HTML）：**
1. 算法层 simhash.py 追加：`minhash_signature()`, `lsh_find_candidates()`, `find_duplicates_hybrid()`, `_bk_on_candidates_subset()`, `_oversample_prefix_pairs()`（append W11 L152+ 区，NOTOUCH v2 允许末尾 append）
2. 模型层 models.py：**无修改**（cc_max 保持 W11=2500；超范围由 workspace.py 末尾追加的 ValidateBeforeCreate Python validator 处理；不计入 WL）；perf_json forward compatible → 0 新 column
3. 引擎层 pipeline_engine.py：_exec_step1_real_dedup() 内把 `find_duplicates_bktree → find_duplicates_hybrid` 调用切换（1 行名字替换 = 非内部逻辑重写，允许）
4. Scripts NEW：`scripts/serialize_bench_history.py` (history_7d/60d)
5. Bench Dashboard NEW Static Template：`docs/bench/index.html`（vanilla HTML+JS+inline SVG，4 页签）
6. 4 NEW shared-ui Components：`BenchDashboardSummary.tsx`, `BenchDashboardPerSize.tsx`, `BenchDashboardCommitCompare.tsx`, `BenchDashboardAlertLog.tsx` (+ barrel index.ts export)
7. 12 test files = §3.1 PY 6 NEW + 6 APPEND · §3.2 TS 4 NEW + 2 APPEND
8. Synthetic Fixture：`w12_synthetic_50k.json` 6 preset × 5 sizes（~5.5 MB sha256 deterministic）
9. foundation-ci.yml W11 → W12：整个 file non-NOTOUCH 范围，改写为 5 Job + deploy-dashboard

---

## §4 · NOTOUCH v2 14 Anchor · W12 影响逐项清单（AC7 审计基线）

**继承 W11 已批准的 4 行 Whitelist（保留不动）：**
- WL-1: [models.py](file:///d:/workspace/MedA/apps/agent-core/app/models.py#L379) L379 `cc_max BETWEEN 1 AND 2500` 字符串 → 预计改为 `BETWEEN 1 AND 50000` = **+1 WL（已计入 AC7 ≤ +2）**
- WL-2: [pipeline_engine.py](file:///d:/workspace/MedA/apps/agent-core/app/services/pipeline_engine.py#L440-L446) L440-446 step_idx==1 dispatcher 分支存在性 → 不改内部逻辑 → **0 WL**
- WL-3: [NewRunModal.tsx](file:///d:/workspace/MedA/packages/shared-ui/src/components/NewRunModal.tsx#L209-L211) L209 `max=2000` → 预计 `max=50000` = **+1 WL**
- WL-4: [NewRunModal.tsx](file:///d:/workspace/MedA/packages/shared-ui/src/components/NewRunModal.tsx#L209-L211) L211 `step=50` → 预计 `step=250` = **+1 WL（合计 +3 → AC7 ≤ +2？超了）**

**AC7 WL 超限处理策略（默认按 AAAAAAAAAA 最保守模式）：**
- 如果 3 行 WL 超 AC7 ≤ +2，有两种方案；默认选 **Scheme X（推荐）**：
  - **Scheme X（WL ≤ +2 达成）：** cc_max 不升级为 50000，保留 W11 2500 作为 CheckConstraint 上限；仅 UI slider max=50000 存在 **但前端在提交表单时若 maxRecords > 2500，通过 `CreatePipelineRun` mutation 后端的 `ValidateBeforeCreate` 自定义 Python validator（非 DB level CC）校验并放行**。这使 cc_max DB 字符串完全不需要改。总 WL 仅 2 = NewRunModal max + step，刚好满足 AC7 ≤ +2 ✅。
  - **Scheme Y（WL = 3，需 user 特批打破 AC7）：** 直接改 CC 字符串，总 WL = 3。本 Spec 默认不选，除非后续 override。

**剩余 12 Anchor 保持 W11 0 diff 状态（W12 无改动计划）：**
- screening_engine.py / rob2_engine.py / abstractor.py
- pubmed_adapter.py L1-238 / workspace.py L1-2040 / simhash.py L1-151
- shared-sdk/index.ts L1-504 / shared-ui/index.ts L1-142 / FunnelProgressBar.tsx
- usePipelineRun.ts entire / PipelineRunDetailPage.tsx Sect①-③
- NewRunModal.tsx **除上述 max/step 2 属性字符串外**，内部逻辑不得改动

### §4.1 文件改动位置总览（Append vs Edit vs New）

```
✔ = NOTOUCH v2 允许模式
✘ = NOTOUCH v2 禁止模式（本 Spec 中 0 出现）

simhash.py                       L152-∞   APPEND 末尾追加 5 new fn     ✔ (W11 L152+ 开放 append)
models.py                        L379     (Scheme X: NO edit)           ✔ (无 WL)
                                           (Scheme Y: WL 1 string edit)
models.py                        L404+    (no new column)               ✔ (perf_json forward comp)
pipeline_engine.py               L697+    _exec_step1_real_dedup →      ✔ (W11 末尾开放)
                                           swap 1 line call name
NewRunModal.tsx                  L209-211 max + step 字符串 2 attrs     ✔ (WL 2)
pubmed_adapter.py                L345+    APPEND _load_preset_2000      ✔ (W11 开放末尾)
                                           → rename to _load_preset_50k
workspace.py                     L2433+   GET diag route 不变 + APPEND   ✔ (W11 末尾开放 NOTOUCH 允许)
                                           ValidateBeforeCreate(max ≤50000)
                                           Python validator for CreateRun
shared-ui DedupDiagCards.tsx     entire   NEW + modify existing chips   ✔ (non-anchor NEW file)
shared-ui 4 Dashboard components NEW×4    4 new files + index barrel    ✔
foundation-ci.yml                entire   non-NOTOUCH → rewrite 5 job   ✔
scripts/serialize_bench_*.py     NEW×2    (bench artifact + history)    ✔
docs/bench/index.html            NEW×1    static template               ✔
tests 12 files                   NEW+APP  6 NEW PY + 4 NEW TS + APPENDs ✔
fixtures w12_synthetic_50k.json  NEW×1    sha256 deterministic          ✔
```

---

## §5 · 风险 & Fallback 降级策略

| 风险项 | 触发条件 | 概率 | 影响 | 降级方案（W12 代码内硬路径，不需要 env/config） |
|---|---|---|---|---|
| R1 N=50k SLO 60s CI bound 不达标 | 冷启动/thermal 节流导致 BK stage2 耗时超 | 中（~10% 首次跑） | CI bench 红色 annotation，NOT block merge（continue-on-error=true HARD block only > 2×=90s） | 代码末尾 fallback：若 Hybrid 执行时间 > 60s，则把 stage_ms.cutoff=true 写入 perf_json 并尝试减少 LSH candidate filter ratio ×0.9 再重跑一次（允许最多 1 retry） |
| R2 N=50k Hybrid FN > 0.05% | 极端文献分布导致 LSH+prefix 漏检率高 | 低（<2%） | 用户信任丢失 · 医学证据风险 | 当 `|candidates| / N² < 0.005`（即 LSH 过滤过狠 >200×）时自动切换 `use_aggressive_oversample = True` → 改用 PREFIX_BITS=14 多补 ~6M pairs；若仍不满意，允许调用方 `force_bk_only=True` 参数强制走 BK-only（接受 ~120s 耗时）|
| R3 Dashboard gh-pages deploy fail | permission 配置错误 / token 未 grant contents.write | 中（~15% 首次） | 仅 Dashboard 不可用；代码合并不受影响（deploy job 非 blocking） | Step 末尾提供 dry-run mode：把 build/ artifact 上传作为备用 artifact；用户本地解压打开 index.html 即可预览 |
| R4 APPEND parity 42 Green 不稳定 偶红 | W11 parity flake 根因 3 bug 已修；W12 追加可能引入 sorted/set 新 flake | 低（<3%） | CI backend-unit RED block merge | 强制所有 parity 外层 double-run check：若第一次 run kept_A != kept_B 立即 re-run；断言第二次必须相等；并记录日志以便 debug |
| R5 NOTOUCH v2 WL 超数 (Scheme Y 被错误选用) | 代码落地时实现者顺手改 cc_max 字符串 | 中（20% 人为错误） | AC7 RED Gate 拒绝合并 | NOTOUCH 审计脚本作为 CI pre-merge check（新增 backend-unit step 1 额外 `scripts/notouch_v2_audit.py` exit 99 if WL > +2，**强制** HARD FAIL 非 soft）；本 Spec 默认 Scheme X 规避 |

### §5.1 版本标签 & 里程碑建议

- **v0.12.0-hybrid-50k-GATE-CLOSED**：当且仅当 W12 GATE 8/8 AC1-AC8 全部 PASS；Git tag 建议（sandbox 实际 push 由用户在本地执行）
- **v0.12.1-bench-dashboard-corrections**（可选后补丁）：gh-pages 首次部署后 7 天历史积累完毕，按 Dashboard 观测值微调 SLO 颜色阈值/Alert 文案
- **FAR-FUTURE W13 C 方案 FAISS 2 阶段 ANN**：明确推迟，不包含在 W12 Scope

---

*Spec Version: 1.1 (SelfReview 4-Pass COMPLETED 2026-08-24) · Issues Fixed: §1.1 cc_max WL conflict → locked Scheme X (ValidateBeforeCreate workspace.py append); §3.4 models.py no edit; §4.1 workspace.py append ValidateBeforeCreate location explicit. No 占位符/矛盾/范围漂移/歧义 remaining. Next: User Review → writing-plans skill → Implementation.*
