"""交付物正文清洗：移除任务过程、用户原始要求和模型思考内容。"""
import re
from typing import List

NOISE_HEADING_RE = re.compile(
    r"^\s{0,3}#{1,6}\s*(?:"
    r"执行任务(?:内容|计划|步骤)?|"
    r"任务(?:内容|要求|说明|计划|执行过程)|"
    r"用户(?:要求|原始需求|提示词|输入)|"
    r"大模型(?:思考|推理)|"
    r"模型(?:思考|推理)|"
    r"思考(?:过程)?|"
    r"下一步计划\s*(?:\(\s*next\s*steps\s*\))?|"
    r"next\s*steps"
    r")\s*[:：]?\s*$",
    re.IGNORECASE,
)

INLINE_NOISE_RE = re.compile(
    r"^\s*(?:任务|用户要求|提示词|执行任务内容)\s*[:：].*$",
    re.IGNORECASE,
)

LOW_QUALITY_PATTERNS = [
    r"未提供实际",
    r"输入不完整",
    r"需要补充信息",
    r"请上传.*文档",
    r"待确认项",
    r"以下为基于.*草案",
    r"dataset_path\s*.*待确认",
    r"需要数据文件路径",
    r"请补充数据路径",
    r"生成.*草案",
]

SUBSTANTIVE_MARKERS = [
    "EASI", "SCORAD", "DLQI", "NRS", "IGA", "特应性皮炎", "乌帕替尼", "度普利尤单抗",
    "真实世界研究", "随机对照", "倾向评分", "主要终点", "次要终点", "样本量", "混杂"
]


def _strip_thinking_blocks(text: str) -> str:
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text or "", flags=re.IGNORECASE)
    cleaned = re.sub(r"<thinking>[\s\S]*?</thinking>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"```(?:thinking|thought|思考)[\s\S]*?```", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def _heading_level(line: str) -> int:
    match = re.match(r"^\s{0,3}(#{1,6})\s+", line or "")
    return len(match.group(1)) if match else 0


def is_low_quality_tool_output(content: str) -> bool:
    """判断 Skill/工具输出是否更像失败提示或占位草案，而不是正式正文。"""
    text = clean_artifact_content(content or "") if content else ""
    if not text.strip():
        return True
    low_hits = sum(1 for pattern in LOW_QUALITY_PATTERNS if re.search(pattern, text, flags=re.IGNORECASE))
    if low_hits >= 2:
        return True
    marker_hits = sum(1 for marker in SUBSTANTIVE_MARKERS if marker.lower() in text.lower())
    if low_hits >= 1 and marker_hits == 0:
        return True
    if len(text.strip()) < 80 and low_hits >= 1:
        return True
    return False


def clean_artifact_content(content: str) -> str:
    """返回适合写入 Word/PPT 的最终正文。"""
    text = _strip_thinking_blocks(content or "")
    lines = text.splitlines()
    output: List[str] = []
    skip_until_level = 0

    for line in lines:
        level = _heading_level(line)
        if skip_until_level and level and level <= skip_until_level:
            skip_until_level = 0
        if skip_until_level:
            continue

        if NOISE_HEADING_RE.match(line):
            skip_until_level = level or 1
            continue
        if INLINE_NOISE_RE.match(line):
            continue
        output.append(line)

    cleaned = "\n".join(output)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned
