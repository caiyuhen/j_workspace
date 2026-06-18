"""根据用户提示词推断交付物格式。"""
import re

SUPPORTED_FORMATS = {"md", "docx", "xlsx", "pptx"}

PPT_PATTERNS = [
    r"pptx?",
    r"power\s*point",
    r"演示文稿",
    r"幻灯片",
    r"汇报材料",
]

DOCX_PATTERNS = [
    r"docx?",
    r"word",
    r"文档",
    r"报告",
    r"方案书",
]

XLSX_PATTERNS = [
    r"xlsx?",
    r"excel",
    r"电子表格",
    r"表格文件",
]


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def infer_deliverable_format(prompt: str, requested_format: str | None = None) -> str:
    """优先根据用户自然语言判断格式；无明确格式时保留请求格式。"""
    text = (prompt or "").strip()
    requested = (requested_format or "md").lower()
    if requested not in SUPPORTED_FORMATS:
        requested = "md"

    if _matches_any(text, PPT_PATTERNS):
        return "pptx"
    if _matches_any(text, XLSX_PATTERNS):
        return "xlsx"
    if _matches_any(text, DOCX_PATTERNS):
        return "docx"
    return requested
