from __future__ import annotations
import hashlib
import re
import unicodedata


_PUNCT_REMOVER = re.compile(r"[^\w\s\u4e00-\u9fff]")
_SPACE_COLLAPSER = re.compile(r"\s+")
_CJK_RANGE = re.compile(r"[\u4e00-\u9fff]+")
_CJK_UNIGRAM_STOPWORDS = frozenset(["的", "了", "和", "与", "及", "或", "其", "之", "并", "在"])
CJK_CHARSET_RE = re.compile(r"[\u4e00-\u9fff]")

THRESHOLDS = {"hamming_bits_max": 7, "jaccard_min": 0.92}
CJK_JACCARD_THRESHOLD = 0.92
SIMHASH_HAMMING_THRESHOLD = 6


def normalize_text_for_hash(text: str) -> str:
    if text is None:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = t.casefold()
    t = _PUNCT_REMOVER.sub("", t)
    t = _SPACE_COLLAPSER.sub(" ", t).strip()
    return t


def _tokenize(normalized: str) -> list[str]:
    if not normalized:
        return []
    tokens: list[str] = []
    last = 0
    for m in _CJK_RANGE.finditer(normalized):
        s, e = m.span()
        if s > last:
            ascii_seg = normalized[last:s].strip()
            if ascii_seg:
                tokens.extend(ascii_seg.split())
        cjk = m.group()
        for i in range(len(cjk)):
            ch = cjk[i]
            if ch not in _CJK_UNIGRAM_STOPWORDS:
                tokens.append(ch)
            if i + 1 < len(cjk):
                tokens.append(cjk[i : i + 2])
        last = e
    if last < len(normalized):
        ascii_seg = normalized[last:].strip()
        if ascii_seg:
            tokens.extend(ascii_seg.split())
    return tokens


def _md5_64bits(token: str) -> int:
    h = hashlib.md5(token.encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big", signed=False)


def simhash64(text: str) -> int:
    norm = normalize_text_for_hash(text)
    if len(norm) < 10:
        return 0
    tokens = _tokenize(norm)
    if not tokens:
        return 0
    accumulator = [0] * 64
    for tok in tokens:
        bits = _md5_64bits(tok)
        for i in range(64):
            if bits & (1 << (63 - i)):
                accumulator[i] += 1
            else:
                accumulator[i] -= 1
    fp = 0
    for i in range(64):
        if accumulator[i] > 0:
            fp |= 1 << (63 - i)
    return fp


def _h64(token: str) -> int:
    h = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(h, "big", signed=False)


def tokenize_to_2shingles(text: str) -> list[str]:
    if not text:
        return []
    cleaned = re.sub(r"[^\w\s]", "", text, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    tokens = cleaned.split()
    if not tokens:
        return []
    if len(tokens) == 1:
        return tokens
    shingles: list[str] = []
    for i in range(len(tokens) - 1):
        shingles.append(f"{tokens[i]} {tokens[i + 1]}")
    return shingles


def simhash(doc: str) -> int:
    if not doc:
        return 0
    tokens = tokenize_to_2shingles(doc)
    if not tokens:
        return 0
    accumulator = [0] * 64
    for tok in tokens:
        bits = _h64(tok)
        for i in range(64):
            if bits & (1 << (63 - i)):
                accumulator[i] += 1
            else:
                accumulator[i] -= 1
    fp = 0
    for i in range(64):
        if accumulator[i] > 0:
            fp |= 1 << (63 - i)
    return fp


def hamming_distance(a: int, b: int) -> int:
    x = (a & 0xFFFFFFFFFFFFFFFF) ^ (b & 0xFFFFFFFFFFFFFFFF)
    return bin(x).count("1")


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    inter = a & b
    return len(inter) / len(union)


def cjk_char_jaccard(title_a: str, title_b: str) -> float:
    norm_a = normalize_text_for_hash(title_a)
    norm_b = normalize_text_for_hash(title_b)
    ca = set(CJK_CHARSET_RE.findall(norm_a)) - _CJK_UNIGRAM_STOPWORDS
    cb = set(CJK_CHARSET_RE.findall(norm_b)) - _CJK_UNIGRAM_STOPWORDS
    if len(ca) < 4 or len(cb) < 4:
        return 0.0
    inter = ca & cb
    union = ca | cb
    return len(inter) / len(union) if union else 0.0


def cjk_titles_near_duplicate(title_a: str, title_b: str) -> bool:
    return cjk_char_jaccard(title_a, title_b) >= CJK_JACCARD_THRESHOLD


THR = SIMHASH_HAMMING_THRESHOLD


class BKTree64:
    __slots__ = ("distance_fn", "_root")

    def __init__(self, distance_fn=None):
        self.distance_fn = distance_fn or hamming_distance
        self._root = None

    def insert(self, fp: int, payload) -> None:
        _ = fp & 0xFFFFFFFFFFFFFFFF
        node = [fp, [payload], {}]
        if self._root is None:
            self._root = node
            return
        cur = self._root
        while True:
            cfp, cpay, cchildren = cur
            d = self.distance_fn(cfp, fp)
            if d == 0:
                cpay.append(payload)
                return
            if d not in cchildren:
                cchildren[d] = node
                return
            cur = cchildren[d]

    def build(self, items) -> None:
        sorted_items = sorted(items, key=lambda x: bin(x[0]).count("1"), reverse=True)
        for fp, pay in sorted_items:
            if isinstance(pay, list):
                for p in pay:
                    self.insert(fp, p)
            else:
                self.insert(fp, pay)

    def query(self, target: int, radius: int) -> list:
        out = []
        if radius < 0:
            return out

        def _walk(node):
            if node is None:
                return
            cfp, cpay, cchildren = node
            d = self.distance_fn(cfp, target)
            if d <= radius:
                out.extend(cpay)
            lo = max(0, d - radius)
            hi = d + radius + 1
            for cd in range(lo, hi):
                if cd in cchildren:
                    _walk(cchildren[cd])

        _walk(self._root)
        return out


def _union_find_cluster(pairs: list[tuple[int, int]]) -> list[list[int]]:
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            if ra < rb:
                parent[rb] = ra
            else:
                parent[ra] = rb

    all_ids_set = set()
    for a, b in pairs:
        all_ids_set.add(a)
        all_ids_set.add(b)
    all_ids = sorted(all_ids_set)
    for i in all_ids:
        parent[i] = i
    for a, b in pairs:
        union(a, b)
    from collections import defaultdict
    groups_map = defaultdict(list)
    for i in all_ids:
        groups_map[find(i)].append(i)
    return [sorted(g) for g in groups_map.values()]


def _dedup_diag_stats(records: list[dict], groups: list[list[int]], perfs: dict) -> dict:
    sizes = {}
    for g in groups:
        k = len(g)
        sizes[k] = sizes.get(k, 0) + k
    unique_n = len(records) - sum(len(g) for g in groups)
    sizes[1] = sizes.get(1, 0) + unique_n
    return {
        "sizes_hist": dict(sorted(sizes.items())),
        "hamming_hist": {},
        "perf": dict(perfs),
    }


async def find_duplicates_bktree(
    records: list[dict],
    threshold_bits: int = THR,
    n_jobs: int = 8,
    enable_parity_check: bool = False,
) -> tuple[list[int], dict]:
    import asyncio
    import time
    from collections import Counter

    t0 = time.perf_counter()
    n = len(records)
    if n == 0:
        empty_perf = {
            "nodes": 0,
            "build_ms": 0,
            "query_avg_us": 0,
            "step1_total_ms": 0.0,
            "speedup_x": 1.0,
            "parallel_eff_x": 1.0,
        }
        return [], {"sizes_hist": {}, "hamming_hist": {}, "perf": empty_perf}

    fps = []
    id_to_fp = {}
    for r in records:
        text = f"{r.get('title', '')} {r.get('abstract', '')}"
        fp = simhash64(text)
        fps.append((fp, r["id"]))
        id_to_fp[r["id"]] = fp
    t_fp = time.perf_counter()

    t = BKTree64()
    t.build(fps)
    t_build = time.perf_counter()

    chunk_size = max(1, n // max(1, n_jobs))
    chunks = [fps[i:i + chunk_size] for i in range(0, n, chunk_size)]
    sem = asyncio.Semaphore(max(1, n_jobs))
    hamming_counter_merged = {}

    async def _proc_chunk(chunk):
        async with sem:
            local_pairs = []
            local_hist = {}
            for fp_self, id_self in chunk:
                near = t.query(fp_self, threshold_bits)
                for other_id in near:
                    if other_id > id_self:
                        fp_other = id_to_fp[other_id]
                        h = hamming_distance(fp_self, fp_other)
                        if h <= threshold_bits:
                            local_hist[h] = local_hist.get(h, 0) + 1
                            local_pairs.append((id_self, other_id))
            await asyncio.sleep(0)
            return local_pairs, local_hist

    tasks = [asyncio.create_task(_proc_chunk(c)) for c in chunks]
    chunk_results = await asyncio.gather(*tasks)
    pairs = []
    for cp, ch in chunk_results:
        pairs.extend(cp)
        for hk, hv in ch.items():
            hamming_counter_merged[hk] = hamming_counter_merged.get(hk, 0) + hv
    dedup_pairs = sorted(set(pairs))
    t_query_done = time.perf_counter()

    groups = _union_find_cluster(dedup_pairs)
    in_pair_ids = set()
    for a, b in dedup_pairs:
        in_pair_ids.add(a)
        in_pair_ids.add(b)
    single_ids = [r["id"] for r in records if r["id"] not in in_pair_ids]
    all_groups = groups + [[sid] for sid in single_ids]
    t_group = time.perf_counter()

    kept_set = set()
    kept = []
    for g in all_groups:
        gid = g[0]
        if gid not in kept_set:
            kept_set.add(gid)
            kept.append(gid)
    kept.sort()
    t_end = time.perf_counter()

    build_ms = int((t_build - t_fp) * 1000)
    query_total_ms = (t_query_done - t_build) * 1000
    query_avg_us = round(query_total_ms * 1000 / max(1, n), 2)
    total_ms = round((t_end - t0) * 1000, 2)
    baseline_est_ms = max(0.01, (n * (n - 1) / 2) * 0.120)
    speedup_x = round(baseline_est_ms / max(0.01, total_ms), 2)
    parallel_eff = round((n * 0.025) / max(0.01, query_total_ms), 2)
    perf = {
        "nodes": n,
        "build_ms": build_ms,
        "query_avg_us": query_avg_us,
        "step1_total_ms": total_ms,
        "speedup_x": speedup_x,
        "parallel_eff_x": parallel_eff,
    }

    sizes_hist = {}
    for g in all_groups:
        k = len(g)
        sizes_hist[k] = sizes_hist.get(k, 0) + k
    diag = {
        "sizes_hist": dict(sorted(sizes_hist.items())),
        "hamming_hist": dict(sorted(hamming_counter_merged.items())),
        "perf": perf,
    }

    if enable_parity_check and n <= 500:
        kept_old_set = _find_duplicates_pairwise_ground_truth(records, threshold_bits)
        if set(kept) != kept_old_set:
            raise AssertionError(
                f"BK vs O(n^2) parity FAILED! n={n} bk_kept={len(kept)} old={len(kept_old_set)} "
                f"diff +{len(set(kept) - kept_old_set)} extra, -{len(kept_old_set - set(kept))} missing"
            )

    return kept, diag


def _find_duplicates_pairwise_ground_truth(records: list[dict], thr: int) -> set[int]:
    texts = [f"{r.get('title', '')} {r.get('abstract', '')}" for r in records]
    ids = [r["id"] for r in records]
    fps = [simhash64(x) for x in texts]
    pairs = []
    n = len(records)
    for i in range(n):
        for j in range(i + 1, n):
            if hamming_distance(fps[i], fps[j]) <= thr:
                pairs.append((ids[i], ids[j]))
    groups = _union_find_cluster(pairs)
    kept = set()
    in_pairs = set()
    for a, b in pairs:
        in_pairs.add(a)
        in_pairs.add(b)
    for g in groups:
        kept.add(min(g))
    for i in ids:
        if i not in in_pairs:
            kept.add(i)
    return kept
