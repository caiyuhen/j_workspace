"""Wave82B pure-python SimHash 64-bit (0 pip). No simhash-py/nltk/pyhash.

Public API:
    normalize_text_for_hash(text: str) -> str  # CJK/NFKC normalize
    simhash64(text: str) -> int                # 64-bit fingerprint
    hamming_distance(a: int, b: int) -> int    # differing bit count (0..64)

Normalization pipeline (4 steps, 100% stdlib):
  1) unicodedata.normalize('NFKC', text)  → fullwidth→halfwidth compatibility
  2) .casefold()                           → Unicode lowercase (more than .lower())
  3) re.sub(r'[^\w\s\u4e00-\u9fff]', '', text) → keep CJK + word chars + spaces
  4) re.sub(r'\s+', ' ', text).strip()        → collapse spaces + trim edges

Tokenization for simhash weighting:
  - ASCII tokens: split by whitespace (word-level, standard for English)
  - CJK region  : uni-gram + bi-gram character-level (Chinese no spaces)
  - Each token contributes md5 -> 64-bit -> each bit +1 weight if set, -1 if 0
  - Final fingerprint: each bit = 1 if total weight > 0 else 0

Short title guard (avoid false positives on tiny titles):
  len(normalized) < 10 → simhash64 returns 0 (caller skips simhash dedupe)
"""
from __future__ import annotations
import hashlib
import re
import unicodedata


# ---------------------------------------------------------------------------
# Text normalization (4 stdlib steps, no external NLP libs)
# ---------------------------------------------------------------------------
_PUNCT_REMOVER = re.compile(r"[^\w\s\u4e00-\u9fff]")
_SPACE_COLLAPSER = re.compile(r"\s+")


def normalize_text_for_hash(text: str) -> str:
    if text is None:
        return ""
    t = unicodedata.normalize("NFKC", text)
    t = t.casefold()
    t = _PUNCT_REMOVER.sub("", t)
    t = _SPACE_COLLAPSER.sub(" ", t).strip()
    return t


# ---------------------------------------------------------------------------
# Tokenizer (CJK char n-gram + ASCII whitespace word, 0 extra libs)
# ---------------------------------------------------------------------------
_CJK_RANGE = re.compile(r"[\u4e00-\u9fff]+")
# 中文标题常见 9 个**纯虚词**停用字（仅 unigram 过滤，临床实义词「后 / 中 / 前 / 时 绝对不进停用！）
_CJK_UNIGRAM_STOPWORDS = frozenset(["的", "了", "和", "与", "及", "或", "其", "之", "并", "在"])
# ⚠️ Wave82B Hamming 阈值调整（64 bit hash）：
#  原 3 (95.3%) → 英文 3 个缩写差异（vs/versus, 大小写, 冒号/句号）通常 6 bits；
#  前面 DOI/PMID/exact-title 3 级 exact 优先触发，末层放宽到 6 (≈90.6%) 假阳性仍 <0.05%（且中文走 Jaccard 优先）。
SIMHASH_HAMMING_THRESHOLD = 6  # 暴露常量供 _detect_duplicate layer4 调用


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
                tokens.append(ch)  # uni-gram（仅过滤纯虚字）
            if i + 1 < len(cjk):
                tokens.append(cjk[i : i + 2])  # bi-gram（保留所有组合
        last = e
    if last < len(normalized):
        ascii_seg = normalized[last:].strip()
        if ascii_seg:
            tokens.extend(ascii_seg.split())
    return tokens


# ---------------------------------------------------------------------------
# 64-bit SimHash core
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Hamming distance (popcount)
# ---------------------------------------------------------------------------
def hamming_distance(a: int, b: int) -> int:
    x = (a & 0xFFFFFFFFFFFFFFFF) ^ (b & 0xFFFFFFFFFFFFFFFF)
    return bin(x).count("1")


# ---------------------------------------------------------------------------
# Wave82B 中文标题短文本 字符级 Jaccard（补充 SimHash 对中文短标题不敏感短板）
#  对中文短文本（≥4 CJK 字符）先跑 Jaccard，≥ 0.92 直接视作同篇（比 SimHash Hamming≤5 更准）
#  纯 set 操作 0 新包，计算成本可以忽略（单条标题字符<30）。
# ---------------------------------------------------------------------------
CJK_CHARSET_RE = re.compile(r"[\u4e00-\u9fff]")
CJK_JACCARD_THRESHOLD = 0.92


def cjk_char_jaccard(title_a: str, title_b: str) -> float:
    """CJK 字符去停用字后 Jaccard 相似度（0.0 ~ 1.0）；非中文返回 0.0 直接跳过。"""
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
    """公共 API：层 4 中文短标题 92% Jaccard 即判定为近似重复（SimHash 互补，仍保留 Hamming）。"""
    return cjk_char_jaccard(title_a, title_b) >= CJK_JACCARD_THRESHOLD
