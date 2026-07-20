"""
统一视觉设计系统
Unified Visual Design System for MedAIagents Exporters

配色方案: 医学专业蓝主题
"""

from docx.shared import RGBColor, Pt
from pptx.dml.color import RGBColor as PptxRGBColor

# ========== 核心配色 ==========
class Colors:
    """文档统一配色"""
    PRIMARY     = RGBColor(0x1E, 0x5A, 0xA8)   # 医学蓝
    PRIMARY_DK  = RGBColor(0x0D, 0x3B, 0x66)   # 深蓝
    PRIMARY_LT  = RGBColor(0xE8, 0xF4, 0xFD)   # 浅蓝背景
    ACCENT      = RGBColor(0x2E, 0x8B, 0x57)   # 绿色（成功/通过）
    WARNING     = RGBColor(0xE8, 0x91, 0x3A)   # 橙色（警告）
    DANGER      = RGBColor(0xC0, 0x39, 0x2B)   # 红色（失败）
    TEXT        = RGBColor(0x33, 0x33, 0x33)   # 正文深灰
    TEXT_LT     = RGBColor(0x66, 0x66, 0x66)   # 次要文字
    WHITE       = RGBColor(0xFF, 0xFF, 0xFF)   # 白色
    BG_GRAY     = RGBColor(0xF5, 0xF7, 0xFA)   # 背景灰
    BORDER      = RGBColor(0xD0, 0xD7, 0xDE)   # 边框灰

class PptxColors:
    """PPT 专用配色 (pptx 使用不同的 RGBColor 类)"""
    PRIMARY     = PptxRGBColor(0x1E, 0x5A, 0xA8)
    PRIMARY_DK  = PptxRGBColor(0x0D, 0x3B, 0x66)
    PRIMARY_LT  = PptxRGBColor(0xE8, 0xF4, 0xFD)
    ACCENT      = PptxRGBColor(0x2E, 0x8B, 0x57)
    WARNING     = PptxRGBColor(0xE8, 0x91, 0x3A)
    TEXT        = PptxRGBColor(0x33, 0x33, 0x33)
    TEXT_LT     = PptxRGBColor(0x66, 0x66, 0x66)
    WHITE       = PptxRGBColor(0xFF, 0xFF, 0xFF)
    BG_GRAY     = PptxRGBColor(0xF5, 0xF7, 0xFA)

class ExcelColors:
    """Excel 专用配色 (openpyxl 使用字符串格式)"""
    PRIMARY     = "1E5AA8"
    PRIMARY_DK  = "0D3B66"
    PRIMARY_LT  = "E8F4FD"
    ACCENT      = "2E8B57"
    WARNING     = "E8913A"
    DANGER      = "C0392B"
    WHITE       = "FFFFFF"
    BG_GRAY     = "F5F7FA"
    BORDER      = "D0D7DE"
    TEXT        = "333333"
    TEXT_LT     = "666666"
    HEADER_TEXT = "FFFFFF"
    ZEBRA_EVEN  = "FFFFFF"
    ZEBRA_ODD   = "F2F7FC"

# ========== 字体规范 ==========
class Fonts:
    """字体设置"""
    CJK_BODY     = "微软雅黑"
    CJK_HEADING  = "微软雅黑"
    CJK_CODE     = "Consolas"
    LATIN_BODY   = "Calibri"
    LATIN_HEAD   = "Calibri"
    LATIN_CODE   = "Consolas"

    SIZE_TITLE   = Pt(22)
    SIZE_H1      = Pt(18)
    SIZE_H2      = Pt(16)
    SIZE_H3      = Pt(14)
    SIZE_BODY    = Pt(11)
    SIZE_SMALL   = Pt(10)
    SIZE_CAPTION = Pt(9)

# ========== 段落/间距规范 ==========
class Spacing:
    """间距设置"""
    LINE_SPACING      = 1.5
    PARA_BEFORE       = Pt(6)
    PARA_AFTER        = Pt(6)
    HEADING_BEFORE    = Pt(12)
    HEADING_AFTER     = Pt(6)
    TABLE_CELL_MARGIN = Pt(4)

# ========== 品牌标识 ==========
BRAND_NAME = "MedAIagents"
BRAND_TAGLINE = "Medical AI Agent System"
BRAND_LOGO_TEXT = "MedAIagents — AI-Powered Medical Research Assistant"
