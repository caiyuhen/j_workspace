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
