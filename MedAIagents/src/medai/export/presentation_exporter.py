"""
PowerPoint (.pptx) 文档导出模块
Presentation Exporter Module

支持:
- 科研汇报幻灯片
- 影像征象教学幻灯片
- 生物信息学可视化汇报幻灯片
"""

import os
from typing import Dict, List, Any, Optional

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    from pptx.enum.shapes import MSO_SHAPE
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False


class BasePresentationExporter:
    """PPT 导出基类"""

    def __init__(self):
        if not HAS_PPTX:
            raise ImportError("python-pptx is required. Install: pip install python-pptx")
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)

    def add_title_slide(self, title: str, subtitle: str = ""):
        """添加标题幻灯片"""
        slide_layout = self.prs.slide_layouts[0]  # Title Slide
        slide = self.prs.slides.add_slide(slide_layout)
        slide.shapes.title.text = title
        if subtitle and len(slide.placeholders) > 1:
            slide.placeholders[1].text = subtitle
        return slide

    def add_content_slide(self, title: str, content_items: List[str]):
        """添加内容幻灯片"""
        slide_layout = self.prs.slide_layouts[1]  # Title and Content
        slide = self.prs.slides.add_slide(slide_layout)
        slide.shapes.title.text = title

        if content_items and len(slide.placeholders) > 1:
            tf = slide.placeholders[1].text_frame
            tf.clear()
            for i, item in enumerate(content_items):
                if i == 0:
                    tf.paragraphs[0].text = item
                else:
                    p = tf.add_paragraph()
                    p.text = item
                    p.level = 0
        return slide

    def add_two_column_slide(self, title: str, left_title: str,
                             left_items: List[str], right_title: str,
                             right_items: List[str]):
        """添加双栏幻灯片"""
        slide_layout = self.prs.slide_layouts[5]  # Blank
        slide = self.prs.slides.add_slide(slide_layout)

        # 标题
        title_shape = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.3), Inches(12), Inches(0.8)
        )
        title_shape.text_frame.text = title
        title_shape.text_frame.paragraphs[0].font.size = Pt(32)
        title_shape.text_frame.paragraphs[0].font.bold = True

        # 左栏
        left_box = slide.shapes.add_textbox(
            Inches(0.5), Inches(1.2), Inches(5.8), Inches(5.5)
        )
        tf = left_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = left_title
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = RGBColor(0x44, 0x72, 0xC4)

        for item in left_items:
            p = tf.add_paragraph()
            p.text = f"• {item}"
            p.font.size = Pt(14)
            p.space_after = Pt(8)

        # 右栏
        right_box = slide.shapes.add_textbox(
            Inches(6.8), Inches(1.2), Inches(5.8), Inches(5.5)
        )
        tf = right_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = right_title
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = RGBColor(0x44, 0x72, 0xC4)

        for item in right_items:
            p = tf.add_paragraph()
            p.text = f"• {item}"
            p.font.size = Pt(14)
            p.space_after = Pt(8)

        return slide

    def save(self, file_path: str):
        """保存演示文稿"""
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        self.prs.save(file_path)
        return file_path


class ResearchPresentationExporter(BasePresentationExporter):
    """科研汇报 PPT 导出器"""

    def export_research_report(self, report_data: Dict[str, Any],
                               file_path: str) -> str:
        """
        将科研报告导出为 PPT

        Args:
            report_data: 报告数据
            file_path: 输出路径
        """
        # 标题页
        self.add_title_slide(
            report_data.get("title", "Research Report"),
            report_data.get("subtitle", "")
        )

        # 背景
        background = report_data.get("background", [])
        if background:
            self.add_content_slide("Background", background)

        # 方法
        methods = report_data.get("methods", [])
        if methods:
            self.add_content_slide("Methods", methods)

        # 结果
        results = report_data.get("results", [])
        if results:
            self.add_content_slide("Results", results)

        # 讨论
        discussion = report_data.get("discussion", [])
        if discussion:
            self.add_content_slide("Discussion", discussion)

        # 结论
        conclusions = report_data.get("conclusions", [])
        if conclusions:
            self.add_content_slide("Conclusions", conclusions)

        # 致谢
        acknowledgments = report_data.get("acknowledgments", [])
        if acknowledgments:
            self.add_content_slide("Acknowledgments", acknowledgments)

        return self.save(file_path)


class ImagingTeachingExporter(BasePresentationExporter):
    """影像征象教学 PPT 导出器"""

    def export_teaching(self, signs: List[Dict[str, Any]],
                        file_path: str) -> str:
        """
        将影像征象教学内容导出为 PPT

        Args:
            signs: 征象列表，每个征象包含 name, description, modalities,
                   anatomy, diseases, severity
            file_path: 输出路径
        """
        self.add_title_slide(
            "Common Imaging Signs",
            "Radiology Teaching Series"
        )

        for sign in signs:
            name = sign.get("name", "Unknown Sign")
            description = sign.get("description", "")
            modalities = sign.get("modalities", [])
            anatomy = sign.get("anatomy", [])
            diseases = sign.get("diseases", [])
            severity = sign.get("severity", "")

            left_items = [
                f"Description: {description}",
                f"Modalities: {', '.join(modalities)}",
                f"Anatomy: {', '.join(anatomy)}",
                f"Severity: {severity}",
            ]
            right_items = [f"{i+1}. {d}" for i, d in enumerate(diseases[:5])]

            self.add_two_column_slide(
                name,
                "Basic Information",
                left_items,
                "Related Diseases",
                right_items
            )

        return self.save(file_path)


class BioinformaticsReportExporter(BasePresentationExporter):
    """生物信息学可视化汇报 PPT 导出器"""

    def export_bioinformatics_report(self, report_data: Dict[str, Any],
                                     file_path: str) -> str:
        """
        将生物信息学分析结果导出为 PPT

        Args:
            report_data: 报告数据
            file_path: 输出路径
        """
        self.add_title_slide(
            report_data.get("title", "Bioinformatics Analysis Report"),
            report_data.get("subtitle", "")
        )

        # 样本信息
        sample_info = report_data.get("sample_info", [])
        if sample_info:
            self.add_content_slide("Sample Information", sample_info)

        # 突变谱
        mutation_summary = report_data.get("mutation_summary", [])
        if mutation_summary:
            self.add_content_slide("Mutation Landscape", mutation_summary)

        # 通路富集
        pathways = report_data.get("pathways", [])
        if pathways:
            self.add_content_slide("Pathway Enrichment", pathways)

        # 生存分析
        survival = report_data.get("survival", [])
        if survival:
            self.add_content_slide("Survival Analysis", survival)

        # 结论
        conclusions = report_data.get("conclusions", [])
        if conclusions:
            self.add_content_slide("Conclusions", conclusions)

        return self.save(file_path)
