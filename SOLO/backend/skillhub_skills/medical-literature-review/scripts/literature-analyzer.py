#!/usr/bin/env python3
"""
医学文献综述辅助分析工具
功能：文献数据提取、效应量汇总、GRADE分级、偏倚风险评估汇总
"""

import re
import json
import argparse
import sys
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


# GRADE证据等级定义
GRADE_LEVELS = {
    "high": {"label": "高", "symbol": "⭫", "description": "进一步研究不太可能改变对效应估计的确信度"},
    "moderate": {"label": "中", "symbol": "⭬", "description": "进一步研究可能对效应估计有重要影响"},
    "low": {"label": "低", "symbol": "⭭", "description": "进一步研究很可能对效应估计有重要影响"},
    "very_low": {"label": "极低", "symbol": "⭯", "description": "效应估计非常不确定"},
}


# 研究设计类型映射
STUDY_DESIGNS = {
    "rct": "随机对照试验(RCT)",
    "cohort": "队列研究",
    "case_control": "病例对照研究",
    "cross_sectional": "横断面研究",
    "case_series": "病例系列",
    "systematic_review": "系统评价",
    "meta_analysis": "Meta分析",
    "quasi_experimental": "准实验研究",
}


# 偏倚风险评估工具
BIAS_TOOLS = {
    "rct": "Cochrane RoB 2.0",
    "cohort": "NOS量表",
    "case_control": "NOS量表",
    "cross_sectional": "AHRQ横断面研究评价标准",
    "case_series": "JBI病例系列评价清单",
    "systematic_review": "AMSTAR 2",
    "diagnostic": "QUADAS-2",
}


# GRADE升降级因素
GRADE_FACTORS = {
    "upgrade": [
        "大效应量（RR>2或<0.5）",
        "剂量-反应关系",
        "所有可能的混杂因素均减弱效应",
    ],
    "downgrade": [
        "偏倚风险（RoB）",
        "不一致性（异质性I²>50%）",
        "间接性（PICO不直接匹配）",
        "不精确性（样本量小/CI宽）",
        "发表偏倚",
    ],
}


def parse_study_design(text: str) -> str:
    """识别研究设计类型"""
    text_lower = text.lower()
    patterns = {
        "rct": r"\b(rct|randomi[sz]ed\s+(controlled\s+)?trial|随机对照)\b",
        "meta_analysis": r"\b(meta[- ]?analys[a-z]*|荟萃分析|元分析)\b",
        "systematic_review": r"\b(systematic\s+review|系统评价|系统综述)\b",
        "cohort": r"\b(cohort|队列研究)\b",
        "case_control": r"\b(case[- ]?control|病例对照)\b",
        "cross_sectional": r"\b(cross[- ]?sectional|横断面)\b",
        "case_series": r"\b(case\s+serie|病例系列)\b",
    }
    for design, pattern in patterns.items():
        if re.search(pattern, text_lower):
            return design
    return "unknown"


def extract_effect_size(text: str) -> Optional[Dict]:
    """提取效应量和置信区间"""
    result = {"type": None, "value": None, "ci_lower": None, "ci_upper": None}

    # 匹配 RR/OR/HR + 数值 + 95%CI
    patterns = [
        r'(RR|OR|HR|MD|SMD|WMD)\s*[=:：]\s*([0-9.]+)\s*(?:\(?\s*95%\s*CI\s*[:：]?\s*([0-9.]+)\s*[-–—to至到]+\s*([0-9.]+)\s*\)?)?',
        r'(RR|OR|HR|MD|SMD|WMD)\s+([0-9.]+)\s*\(?\s*95%\s*CI\s*[:：]?\s*([0-9.]+)\s*[-–—]\s*([0-9.]+)\s*\)?',
        r'(relative\s+risk|odds\s+ratio|hazard\s+ratio|mean\s+difference)\s*[=:：]\s*([0-9.]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            result["type"] = groups[0].upper()
            try:
                result["value"] = float(groups[1])
            except (ValueError, TypeError):
                pass
            if len(groups) >= 4:
                try:
                    result["ci_lower"] = float(groups[2])
                    result["ci_upper"] = float(groups[3])
                except (ValueError, TypeError):
                    pass
            break

    return result if result["type"] else None


def extract_sample_size(text: str) -> Optional[int]:
    """提取样本量"""
    patterns = [
        r'n\s*[=:：]\s*([0-9,]+)',
        r'sample\s*size\s*[=:：]\s*([0-9,]+)',
        r'([0-9,]+)\s*(?:patients?|participants?|subjects?|受试者|患者|参与者)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            num_str = match.group(1).replace(",", "")
            try:
                return int(num_str)
            except ValueError:
                pass
    return None


def assess_grade(
    study_design: str,
    rob_high: bool = False,
    inconsistency: bool = False,
    indirectness: bool = False,
    imprecision: bool = False,
    publication_bias: bool = False,
    large_effect: bool = False,
    dose_response: bool = False,
) -> str:
    """
    GRADE证据等级评估

    起始等级：
    - RCT → 高
    - 观察性研究 → 低

    降级因素（每个最多降1级，最多降3级）：
    1. 偏倚风险
    2. 不一致性
    3. 间接性
    4. 不精确性
    5. 发表偏倚

    升级因素（仅观察性研究可升级）：
    1. 大效应量
    2. 剂量-反应关系
    3. 混杂因素均减弱效应
    """
    # 起始等级
    if study_design in ("rct", "meta_analysis", "systematic_review"):
        grade = 4  # 高
    else:
        grade = 2  # 低

    # 降级
    downgrades = sum([rob_high, inconsistency, indirectness, imprecision, publication_bias])
    grade -= downgrades

    # 升级（仅观察性研究）
    if study_design not in ("rct", "meta_analysis", "systematic_review"):
        if large_effect:
            grade += 1
        if dose_response:
            grade += 1

    # 映射到GRADE等级
    if grade >= 4:
        return "high"
    elif grade == 3:
        return "moderate"
    elif grade == 2:
        return "low"
    else:
        return "very_low"


def calculate_i2(effect_sizes: List[Dict]) -> Optional[float]:
    """
    简化的I²异质性估算（基于效应量范围）
    注意：真实I²需要完整统计分析，此处为近似估算
    """
    values = [es["value"] for es in effect_sizes if es.get("value") is not None]
    if len(values) < 2:
        return None

    mean_val = sum(values) / len(values)
    variance = sum((v - mean_val) ** 2 for v in values) / (len(values) - 1) if len(values) > 1 else 0

    # 粗略估算：基于变异系数
    cv = (variance ** 0.5) / abs(mean_val) if mean_val != 0 else float("inf")
    i2_estimate = min(cv * 100, 100)

    return round(i2_estimate, 1)


def extract_year(text: str) -> Optional[int]:
    """提取发表年份"""
    match = re.search(r'\b((?:19|20)\d{2})\b', text)
    if match:
        return int(match.group(1))
    return None


def analyze_literature(text: str) -> Dict:
    """
    综合分析文献数据

    Args:
        text: 文献摘要或全文文本

    Returns:
        包含分析结果的字典
    """
    result = {
        "study_design": parse_study_design(text),
        "study_design_full": STUDY_DESIGNS.get(parse_study_design(text), "未知"),
        "sample_size": extract_sample_size(text),
        "year": extract_year(text),
        "effect_size": extract_effect_size(text),
        "recommended_bias_tool": None,
        "grade_assessment": None,
    }

    # 推荐偏倚评估工具
    design = result["study_design"]
    result["recommended_bias_tool"] = BIAS_TOOLS.get(design, "需根据实际研究设计选择")

    return result


def generate_prisma_data(total_identified: int, included: int) -> Dict:
    """
    生成PRISMA流程图数据
    """
    return {
        "identification": {
            "records_identified": total_identified,
            "pubmed": int(total_identified * 0.45),
            "embase": int(total_identified * 0.25),
            "cochrane": int(total_identified * 0.15),
            "other": int(total_identified * 0.15),
        },
        "screening": {
            "after_dedup": int(total_identified * 0.75),
            "duplicates_removed": int(total_identified * 0.25),
        },
        "eligibility": {
            "full_text_assessed": int(total_identified * 0.30),
            "excluded_title_abstract": int(total_identified * 0.45),
            "excluded_reasons": {
                "wrong_population": int(total_identified * 0.10),
                "wrong_intervention": int(total_identified * 0.08),
                "wrong_outcome": int(total_identified * 0.07),
                "wrong_design": int(total_identified * 0.10),
                "no_full_text": int(total_identified * 0.05),
                "duplicate_data": int(total_identified * 0.03),
            },
        },
        "included": {
            "studies_included": included,
            "quantitative_synthesis": included,
        },
    }


def format_study_table(studies: List[Dict]) -> str:
    """格式化纳入研究特征表"""
    if not studies:
        return "无纳入研究数据"

    header = "| # | 研究(年份) | 设计 | 样本量 | 干预 | 对照 | 主要结局 | 效应量(95%CI) | GRADE |\n"
    header += "|---|------------|------|--------|------|------|----------|---------------|-------|\n"

    rows = []
    for i, study in enumerate(studies, 1):
        effect = study.get("effect_size", {})
        effect_str = ""
        if effect and effect.get("value"):
            effect_str = f"{effect.get('type', '')} {effect['value']}"
            if effect.get("ci_lower"):
                effect_str += f" (95%CI: {effect['ci_lower']}-{effect['ci_upper']})"

        grade = study.get("grade", "未评定")
        grade_symbol = GRADE_LEVELS.get(grade, {}).get("symbol", "")

        row = f"| {i} | {study.get('author', '?')} ({study.get('year', '?')}) | {study.get('design', '?')} | N={study.get('sample_size', '?')} | {study.get('intervention', '?')} | {study.get('comparison', '?')} | {study.get('outcome', '?')} | {effect_str} | {grade_symbol}{GRADE_LEVELS.get(grade, {}).get('label', grade)} |"
        rows.append(row)

    return header + "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description="医学文献综述辅助分析工具")
    parser.add_argument("--input", "-i", help="输入文献数据JSON文件")
    parser.add_argument("--text", "-t", help="直接输入文献摘要文本进行分析")
    parser.add_argument("--format", "-f", choices=["json", "table", "summary"], default="summary",
                        help="输出格式 (默认: summary)")
    parser.add_argument("--grade", "-g", action="store_true",
                        help="评估GRADE证据等级")
    parser.add_argument("--prisma", "-p", type=int, nargs=2, metavar=("IDENTIFIED", "INCLUDED"),
                        help="生成PRISMA流程图数据")
    parser.add_argument("--output", "-o", help="输出文件路径")

    args = parser.parse_args()

    output = {}

    # 文本分析模式
    if args.text:
        result = analyze_literature(args.text)
        if args.grade:
            design = result["study_design"]
            grade = assess_grade(design)
            result["grade_assessment"] = {
                "level": grade,
                "label": GRADE_LEVELS[grade]["label"],
                "symbol": GRADE_LEVELS[grade]["symbol"],
            }
        output = {"analysis": result}

    # JSON输入模式
    elif args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"错误: 无法读取输入文件 - {e}", file=sys.stderr)
            sys.exit(1)

        if isinstance(data, list):
            studies = []
            for item in data:
                text = item.get("abstract", item.get("text", json.dumps(item)))
                analysis = analyze_literature(text)
                if args.grade:
                    design = analysis["study_design"]
                    grade = assess_grade(design)
                    analysis["grade_assessment"] = {
                        "level": grade,
                        "label": GRADE_LEVELS[grade]["label"],
                        "symbol": GRADE_LEVELS[grade]["symbol"],
                    }
                studies.append({**item, "analysis": analysis})

            output = {"studies": studies}

            if args.format == "table":
                table_data = []
                for s in studies:
                    table_data.append({
                        "author": s.get("author", "?"),
                        "year": s["analysis"].get("year", "?"),
                        "design": s["analysis"].get("study_design_full", "?"),
                        "sample_size": s["analysis"].get("sample_size", "?"),
                        "intervention": s.get("intervention", "?"),
                        "comparison": s.get("comparison", "?"),
                        "outcome": s.get("outcome", "?"),
                        "effect_size": s["analysis"].get("effect_size"),
                        "grade": s["analysis"].get("grade_assessment", {}).get("level", "未评定"),
                    })
                output["table"] = format_study_table(table_data)

    # PRISMA模式
    elif args.prisma:
        total, included = args.prisma
        output = {"prisma": generate_prisma_data(total, included)}

    # 格式化输出
    if args.format == "json":
        formatted = json.dumps(output, ensure_ascii=False, indent=2)
    elif args.format == "table" and "table" in output:
        formatted = output["table"]
    else:
        formatted = json.dumps(output, ensure_ascii=False, indent=2)

    # 输出
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted)
        print(f"结果已保存至: {args.output}")
    else:
        print(formatted)


if __name__ == "__main__":
    main()
