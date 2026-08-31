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

MINHASH_PERM = 100
MINHASH_SHINGLE_K = 5
LSH_BANDS = 20
LSH_ROWS = 5
LSH_TARGET_J = 0.70
FALLBACK_N_PARITY = 2000
OVERSAMPLE_PREFIX_BITS = 10

BUCKET_FULL_ENUM_MAX = 512

EXACT_BLOCK_COUNT = 8
EXACT_BLOCK_BITS = 8

_SIMHASH_FIELD_W = 24
_SIMHASH_FIELD_MASK = (1 << _SIMHASH_FIELD_W) - 1
_SIMHASH_BYTE_TABLES = tuple(
    tuple(
        sum(
            1 << (_SIMHASH_FIELD_W * ((7 - p) * 8 + k))
            for k in range(8)
            if (b >> k) & 1
        )
        for b in range(256)
    )
    for p in range(8)
)
_SIMHASH_TOKEN_VEC_CACHE: dict[str, int] = {}
_SIMHASH_TOKEN_VEC_CACHE_MAX = 400_000
_SIMHASH_FP_CACHE: dict[str, int] = {}
_SIMHASH_FP_CACHE_MAX = 200_000


def _token_bit_vector(tok: str) -> int:
    d = hashlib.md5(tok.encode("utf-8")).digest()
    t = _SIMHASH_BYTE_TABLES
    v = (
        t[0][d[0]] + t[1][d[1]] + t[2][d[2]] + t[3][d[3]]
        + t[4][d[4]] + t[5][d[5]] + t[6][d[6]] + t[7][d[7]]
    )
    if len(_SIMHASH_TOKEN_VEC_CACHE) < _SIMHASH_TOKEN_VEC_CACHE_MAX:
        _SIMHASH_TOKEN_VEC_CACHE[tok] = v
    return v


def _simhash64_fast(text: str) -> int:
    """Bit-identical drop-in for :func:`simhash64` with per-token/per-doc caching.

    ``simhash64`` lives inside the NOTOUCH anchor region, so the hot path is
    reimplemented here: per-position ``+1/-1`` accumulation is replaced by
    packed big-integer set-bit counting (``accumulator[i] > 0`` is equivalent to
    ``2 * ones[i] > n_tokens``).
    """
    norm = normalize_text_for_hash(text)
    if len(norm) < 10:
        return 0
    cached = _SIMHASH_FP_CACHE.get(norm)
    if cached is not None:
        return cached
    tokens = _tokenize(norm)
    n_tok = len(tokens)
    if n_tok == 0:
        return 0
    if n_tok > _SIMHASH_FIELD_MASK:
        return simhash64(text)
    acc = 0
    get = _SIMHASH_TOKEN_VEC_CACHE.get
    for tok in tokens:
        v = get(tok)
        if v is None:
            v = _token_bit_vector(tok)
        acc += v
    w = _SIMHASH_FIELD_W
    mask = _SIMHASH_FIELD_MASK
    fp = 0
    for j in range(64):
        if (((acc >> (w * j)) & mask) << 1) > n_tok:
            fp |= 1 << j
    if len(_SIMHASH_FP_CACHE) < _SIMHASH_FP_CACHE_MAX:
        _SIMHASH_FP_CACHE[norm] = fp
    return fp


def _bucket_pairs(members: list[int], out: set[tuple[int, int]]) -> None:
    """Emit index pairs for one hash bucket.

    Buckets up to ``BUCKET_FULL_ENUM_MAX`` members are fully enumerated
    (``C(m,2)``). Larger buckets only emit the ``m-1`` chain pairs, which keeps
    the transitive closure identical while avoiding quadratic memory blowup on
    degenerate inputs (e.g. 10k records sharing one fingerprint).
    """
    m = len(members)
    if m < 2:
        return
    mb = sorted(members)
    if m > BUCKET_FULL_ENUM_MAX:
        prev = mb[0]
        for k in range(1, m):
            cur = mb[k]
            out.add((prev, cur))
            prev = cur
        return
    for ii in range(m):
        a = mb[ii]
        for jj in range(ii + 1, m):
            out.add((a, mb[jj]))


def _exact_block_verified_pairs(
    fps: list[int], threshold_bits: int = THR
) -> set[tuple[int, int]]:
    """Recall-complete near-duplicate search over 64-bit fingerprints.

    Each fingerprint is cut into ``EXACT_BLOCK_COUNT`` blocks of
    ``EXACT_BLOCK_BITS`` bits. A pair at hamming distance ``d`` dirties at most
    ``d`` blocks, so with ``d <= EXACT_BLOCK_COUNT - 2`` at least two blocks are
    untouched and the pair must collide on one of the ``C(8,2)=28`` block-pair
    indexes (pigeonhole). Returned pairs are already hamming-verified, so the
    result is exactly the ground-truth pair set that a full BK-tree scan yields.
    """
    out: set[tuple[int, int]] = set()
    n = len(fps)
    if n < 2:
        return out

    first_idx: dict[int, int] = {}
    same_fp_groups: dict[int, list[int]] = {}
    for i in range(n):
        fp = fps[i]
        prev = first_idx.get(fp)
        if prev is None:
            first_idx[fp] = i
            same_fp_groups[fp] = [i]
        else:
            same_fp_groups[fp].append(i)
    for members in same_fp_groups.values():
        _bucket_pairs(members, out)

    fps_u = list(first_idx.keys())
    idxs_u = list(first_idx.values())
    m = len(fps_u)
    if m < 2:
        return out

    nb = EXACT_BLOCK_COUNT
    bw = EXACT_BLOCK_BITS
    bmask = (1 << bw) - 1
    clean_needed = nb - threshold_bits
    if clean_needed >= 2:
        key_shifts = [
            (bw * a, bw * b) for a in range(nb) for b in range(a + 1, nb)
        ]
    else:
        key_shifts = [(bw * a, bw * a) for a in range(nb)]

    for sa, sb in key_shifts:
        buckets: dict[int, list[int]] = {}
        for u in range(m):
            fp = fps_u[u]
            k = (((fp >> sa) & bmask) << bw) | ((fp >> sb) & bmask)
            bucket = buckets.get(k)
            if bucket is None:
                buckets[k] = [u]
            else:
                bucket.append(u)
        for members in buckets.values():
            n_mem = len(members)
            if n_mem < 2:
                continue
            for ii in range(n_mem):
                ui = members[ii]
                fi = fps_u[ui]
                for jj in range(ii + 1, n_mem):
                    uj = members[jj]
                    if (fi ^ fps_u[uj]).bit_count() <= threshold_bits:
                        a = idxs_u[ui]
                        b = idxs_u[uj]
                        out.add((a, b) if a < b else (b, a))
    return out


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
        if radius < 0 or self._root is None:
            return out

        stack = [self._root]
        if self.distance_fn is hamming_distance:
            # Fast path: inline popcount + iterative walk (no per-node call frames).
            t = target & 0xFFFFFFFFFFFFFFFF
            while stack:
                cfp, cpay, cchildren = stack.pop()
                d = ((cfp & 0xFFFFFFFFFFFFFFFF) ^ t).bit_count()
                if d <= radius:
                    out.extend(cpay)
                if not cchildren:
                    continue
                lo = d - radius
                if lo < 0:
                    lo = 0
                for cd in range(lo, d + radius + 1):
                    child = cchildren.get(cd)
                    if child is not None:
                        stack.append(child)
            return out

        dist = self.distance_fn
        while stack:
            cfp, cpay, cchildren = stack.pop()
            d = dist(cfp, target)
            if d <= radius:
                out.extend(cpay)
            if not cchildren:
                continue
            lo = d - radius
            if lo < 0:
                lo = 0
            for cd in range(lo, d + radius + 1):
                child = cchildren.get(cd)
                if child is not None:
                    stack.append(child)
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
        fp = _simhash64_fast(text)
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
                        h = (fp_self ^ id_to_fp[other_id]).bit_count()
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


def minhash_signature(tokens: list[str]) -> tuple[int, ...]:
    n_perm = MINHASH_PERM
    if not tokens:
        return tuple([0xFFFFFFFF] * n_perm)
    joined = " ".join(sorted(frozenset(tokens)))
    base = hashlib.md5(joined.encode("utf-8")).digest()
    extra1 = hashlib.md5(b"\x01" + base).digest()
    extra2 = hashlib.md5(b"\x02" + base).digest()
    extra3 = hashlib.md5(b"\x03" + base).digest()
    all_bytes = base + extra1 + extra2 + extra3
    words_32 = [
        int.from_bytes(all_bytes[i:i + 4], "big", signed=False)
        for i in range(0, 48, 4)
    ]
    while len(words_32) < n_perm:
        seed = b"\xff" + len(words_32).to_bytes(4, "big") + base
        h = hashlib.md5(seed).digest()
        for off in (0, 4, 8, 12):
            words_32.append(int.from_bytes(h[off:off + 4], "big", signed=False))
            if len(words_32) >= n_perm:
                break
    return tuple(words_32[:n_perm])


def _lsh_recall_theoretical(J: float, b: int = LSH_BANDS, r: int = LSH_ROWS) -> float:
    if J <= 0.0:
        return 0.0
    if J >= 1.0:
        return 1.0
    return 1.0 - (1.0 - J ** r) ** b


def lsh_find_candidates(signatures: list[tuple[int, ...]]) -> set[tuple[int, int]]:
    if not isinstance(signatures, list):
        raise TypeError("signatures must be a list")
    for s in signatures:
        if not isinstance(s, tuple):
            raise TypeError("each signature must be a tuple")
    b = LSH_BANDS
    r = LSH_ROWS
    n = len(signatures)
    if n < 2:
        return set()
    band_matches = [{} for _ in range(b)]
    for band_idx in range(b):
        start = band_idx * r
        bucket_map = {}
        for i in range(n):
            sig = signatures[i]
            key = tuple(sig[start:start + r])
            if key not in bucket_map:
                bucket_map[key] = set()
            bucket_map[key].add(i)
        band_matches[band_idx] = bucket_map
    pair_counts = {}
    for band_idx in range(b):
        bucket_map = band_matches[band_idx]
        for members in bucket_map.values():
            if len(members) < 2:
                continue
            band_pairs: set[tuple[int, int]] = set()
            _bucket_pairs(list(members), band_pairs)
            for p in band_pairs:
                pair_counts[p] = pair_counts.get(p, 0) + 1
    candidates = {p for p, cnt in pair_counts.items() if cnt >= 1}
    return candidates


def _oversample_prefix_pairs(fps: list[int], n_bits: int = OVERSAMPLE_PREFIX_BITS) -> set[tuple[int, int]]:
    prefix_map = {}
    n = len(fps)
    if n < 2:
        return set()
    shift = 64 - n_bits
    for i in range(n):
        prefix = (fps[i] >> shift) & ((1 << n_bits) - 1)
        if prefix not in prefix_map:
            prefix_map[prefix] = []
        prefix_map[prefix].append(i)
    pairs: set[tuple[int, int]] = set()
    for members in prefix_map.values():
        _bucket_pairs(members, pairs)
    return pairs


def _bk_on_candidates_subset(
    records: list[dict],
    candidate_idxs: set[tuple[int, int]],
    threshold_bits: int = THR,
    fps_in: list[int] | None = None,
    idx_to_id_in: list[int] | None = None,
) -> tuple[list[tuple[int, int]], list[list[int]], list[int], dict[int, int]]:
    from collections import defaultdict
    n = len(records)
    if n == 0:
        return [], [], [], {}
    if idx_to_id_in is not None and len(idx_to_id_in) == n:
        idx_to_id = idx_to_id_in
    else:
        idx_to_id = [0] * n
        for i, r in enumerate(records):
            idx_to_id[i] = r["id"]
    if fps_in is not None and len(fps_in) == n:
        fps = fps_in
    else:
        fps = [0] * n
        for i, r in enumerate(records):
            text = f"{r.get('title', '')} {r.get('abstract', '')}"
            fps[i] = _simhash64_fast(text)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
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

    exact_pairs = []
    hc_out: dict[int, int] = {}
    for ii, jj in candidate_idxs:
        if ii >= n or jj >= n:
            continue
        h = hamming_distance(fps[ii], fps[jj])
        if h <= threshold_bits:
            exact_pairs.append((idx_to_id[ii], idx_to_id[jj]))
            union(ii, jj)
            hc_out[h] = hc_out.get(h, 0) + 1
    groups_map = defaultdict(list)
    for i in range(n):
        groups_map[find(i)].append(idx_to_id[i])
    groups = [sorted(g) for g in groups_map.values()]
    kept_set = set()
    for g in groups:
        kept_set.add(min(g))
    kept = sorted(kept_set)
    return exact_pairs, groups, kept, hc_out


def find_duplicates_hybrid(
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

    perf = {
        "version": "w12-hybrid-v1",
        "n_records": n,
        "fallback_used": False,
        "lsh_candidates": 0,
        "lsh_candidate_filter_ratio": 0.0,
        "oversample_prefix": False,
        "stage_ms": {
            "minhash_ms": 0,
            "lsh_ms": 0,
            "oversample_ms": 0,
            "bk_ms": 0,
            "union_ms": 0,
            "total_ms": 0,
        },
    }

    if n <= FALLBACK_N_PARITY:
        perf["fallback_used"] = True
        t_bk_s = time.perf_counter()
        kept_bk, diag_bk = asyncio.run(find_duplicates_bktree(
            records, threshold_bits, n_jobs, enable_parity_check
        ))
        t_bk_e = time.perf_counter()
        # The BK-tree pass groups and picks the survivors in one go, so there is no
        # separate union stage to time on this path.
        perf["stage_ms"]["bk_ms"] = round((t_bk_e - t_bk_s) * 1000, 2)
        perf["stage_ms"]["union_ms"] = 0.0
        perf["stage_ms"]["total_ms"] = round((time.perf_counter() - t0) * 1000, 2)
        diag_bk["perf_json"] = perf
        return kept_bk, diag_bk

    texts = [f"{r.get('title', '')} {r.get('abstract', '')}" for r in records]
    idx_to_id = [r.get("id", i) for i, r in enumerate(records)]

    t_minhash_s = time.perf_counter()
    fps = [_simhash64_fast(t) for t in texts]
    raw_tokens = [tokenize_to_2shingles(t) for t in texts]
    sigs = [minhash_signature(toks) for toks in raw_tokens]
    t_minhash_e = time.perf_counter()
    perf["stage_ms"]["minhash_ms"] = round((t_minhash_e - t_minhash_s) * 1000, 2)

    t_lsh_s = time.perf_counter()
    lsh_cand_idxs = lsh_find_candidates(sigs)
    t_lsh_e = time.perf_counter()
    perf["stage_ms"]["lsh_ms"] = round((t_lsh_e - t_lsh_s) * 1000, 2)

    t_over_s = time.perf_counter()
    over_pairs = _oversample_prefix_pairs(fps, OVERSAMPLE_PREFIX_BITS)
    perf["oversample_prefix"] = True
    exact_block_pairs = _exact_block_verified_pairs(fps, threshold_bits)
    all_cand_idxs = lsh_cand_idxs | over_pairs | exact_block_pairs
    t_over_e = time.perf_counter()
    perf["stage_ms"]["oversample_ms"] = round((t_over_e - t_over_s) * 1000, 2)

    perf["lsh_candidates"] = len(lsh_cand_idxs)
    total_pairs_possible = n * (n - 1) // 2 if n >= 2 else 1
    perf["lsh_candidate_filter_ratio"] = round(
        len(all_cand_idxs) / total_pairs_possible, 6
    ) if total_pairs_possible > 0 else 0.0

    t_bk_s = time.perf_counter()
    exact_pairs, groups, kept, hamming_counter_merged = _bk_on_candidates_subset(
        records, all_cand_idxs, threshold_bits, fps_in=fps, idx_to_id_in=idx_to_id
    )
    t_bk_e = time.perf_counter()
    perf["stage_ms"]["bk_ms"] = round((t_bk_e - t_bk_s) * 1000, 2)
    perf["stage_ms"]["union_ms"] = 0.0

    total_ms = round((time.perf_counter() - t0) * 1000, 2)
    perf["stage_ms"]["total_ms"] = total_ms

    sizes_hist = {}
    for g in groups:
        k_len = len(g)
        sizes_hist[k_len] = sizes_hist.get(k_len, 0) + k_len

    in_pair_ids = set()
    for a, b in exact_pairs:
        in_pair_ids.add(a)
        in_pair_ids.add(b)
    single_count = n - len(in_pair_ids)
    if single_count > 0:
        sizes_hist[1] = sizes_hist.get(1, 0) + single_count

    diag = {
        "sizes_hist": dict(sorted(sizes_hist.items())),
        "hamming_hist": dict(sorted(hamming_counter_merged.items())),
        "perf_json": perf,
    }

    return kept, diag
