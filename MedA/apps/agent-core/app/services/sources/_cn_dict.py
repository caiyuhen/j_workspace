from __future__ import annotations

import re


TERM_DICT: dict[str, str] = {
    "sglt2i": "钠葡萄糖协同转运蛋白2抑制剂",
    "sodium glucose cotransporter 2 inhibitor": "钠葡萄糖协同转运蛋白2抑制剂",
    "empagliflozin": "恩格列净",
    "dapagliflozin": "达格列净",
    "canagliflozin": "卡格列净",
    "ertugliflozin": "艾格列净",
    "hfredef": "射血分数降低的心力衰竭",
    "heart failure with reduced ejection fraction": "射血分数降低的心力衰竭",
    "chronic kidney disease": "慢性肾脏病",
    "ckd": "慢性肾脏病",
    "diabetic nephropathies": "糖尿病肾病",
    "diabetic nephropathy": "糖尿病肾病",
    "cardiovascular": "心血管",
    "cv death": "心血管死亡",
    "mace": "主要不良心血管事件",
    "major adverse cardiovascular events": "主要不良心血管事件",
    "ascvd": "动脉粥样硬化性心血管疾病",
    "diabetic ketoacidosis": "糖尿病酮症酸中毒",
    "dka": "糖尿病酮症酸中毒",
    "euglycemic ketoacidosis": "正常血糖性酮症酸中毒",
    "type 2 diabetes mellitus": "2型糖尿病",
    "t2dm": "2型糖尿病",
    "prediabetes": "糖尿病前期",
    "diabetes prevention program": "糖尿病预防计划",
    "dpp": "糖尿病预防计划",
    "randomised controlled trial": "随机对照试验",
    "randomized controlled trial": "随机对照试验",
    "rct": "随机对照试验",
    "retrospective": "回顾性",
    "cohort": "队列",
    "real-world": "真实世界",
    "metformin": "二甲双胍",
    "insulin resistance": "胰岛素抵抗",
    "glucagon-like peptide-1 receptor agonist": "胰高血糖素样肽-1受体激动剂",
    "glp-1 ra": "胰高血糖素样肽-1受体激动剂",
    "liraglutide": "利拉鲁肽",
    "semaglutide": "司美格鲁肽",
    "dulaglutide": "度拉糖肽",
    "tirzepatide": "替尔泊肽",
    "sulfonylurea": "磺脲类",
    "dpp-4 inhibitor": "二肽基肽酶4抑制剂",
    "placebo": "安慰剂",
    "standard of care": "标准治疗",
    "lifestyle intervention": "生活方式干预",
    "diet and exercise": "饮食和运动",
    "weight loss": "体重减轻",
    "hypoglycaemia": "低血糖",
    "hypovolemia": "血容量不足",
    "genital mycotic infection": "生殖器真菌感染",
}


_PUBMED_TAG_RE = re.compile(r"\[[^\[\]]{1,40}\]")


def _clean_pubmed_tags(text: str) -> str:
    return _PUBMED_TAG_RE.sub("", text)


_LOGIC_SPLIT_RE = re.compile(r"(\s+AND\s+|\s+OR\s+|\s+NOT\s+|\(|\))", re.IGNORECASE)


def _translate_single_term(term: str) -> str:
    stripped = term.strip()
    key1 = stripped.lower()
    if key1 in TERM_DICT:
        return TERM_DICT[key1]
    key2 = stripped.rstrip(".,;:，。；：")
    key2_lower = key2.lower()
    if key2_lower in TERM_DICT:
        trailing = stripped[len(key2):]
        return TERM_DICT[key2_lower] + trailing
    return term


def translate_boolean_for_cn_source(boolean_text: str, source: str = "cnki") -> str:
    try:
        cleaned_text = _clean_pubmed_tags(boolean_text)
        tokens = _LOGIC_SPLIT_RE.split(cleaned_text)
        result_tokens: list[str] = []
        for tok in tokens:
            if not tok:
                continue
            stripped_tok = tok.strip()
            if _LOGIC_SPLIT_RE.fullmatch(tok):
                result_tokens.append(tok)
            else:
                whole_translated = _translate_single_term(tok)
                if whole_translated != tok:
                    result_tokens.append(whole_translated)
                else:
                    sub_tokens = stripped_tok.split()
                    translated_subs = [_translate_single_term(st) for st in sub_tokens]
                    if any(t != st for t, st in zip(translated_subs, sub_tokens)):
                        result_tokens.append(" ".join(translated_subs))
                    else:
                        result_tokens.append(tok)
        joined = "".join(result_tokens)
        final = re.sub(r"\s+", " ", joined).strip()
        final = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", final)
        return final
    except Exception:
        return boolean_text
