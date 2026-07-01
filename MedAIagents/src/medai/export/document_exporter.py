"""
Word (.docx) 文档导出模块
Document Exporter Module

支持:
- 医学论文导出 (IMRaD 结构)
- 基金申请书导出
- Response Letter 导出
- RCT 试验方案导出
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml.ns import qn
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


class BaseDocumentExporter:
    """Word 文档导出基类"""

    def __init__(self):
        if not HAS_DOCX:
            raise ImportError("python-docx is required. Install: pip install python-docx")
        self.doc = Document()
        self._setup_styles()

    def _setup_styles(self):
        """设置文档样式"""
        # 设置默认字体
        style = self.doc.styles['Normal']
        font = style.font
        font.name = 'Times New Roman'
        font.size = Pt(12)
        style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')

        # 标题样式
        for i in range(1, 4):
            heading = self.doc.styles[f'Heading {i}']
            heading.font.name = 'Arial'
            heading.font.bold = True
            heading.font.color.rgb = RGBColor(0, 0, 0)
            heading.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
            if i == 1:
                heading.font.size = Pt(18)
            elif i == 2:
                heading.font.size = Pt(16)
            else:
                heading.font.size = Pt(14)

    def add_title(self, title: str, level: int = 1):
        """添加标题"""
        self.doc.add_heading(title, level=level)

    def add_paragraph(self, text: str, bold: bool = False, italic: bool = False):
        """添加段落"""
        p = self.doc.add_paragraph()
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        return p

    def add_table(self, headers: List[str], rows: List[List[str]],
                  style: str = 'Light Grid Accent 1'):
        """添加表格"""
        table = self.doc.add_table(rows=1, cols=len(headers))
        table.style = style

        # 表头
        hdr_cells = table.rows[0].cells
        for i, header in enumerate(headers):
            hdr_cells[i].text = header
            for paragraph in hdr_cells[i].paragraphs:
                for run in paragraph.runs:
                    run.bold = True

        # 数据行
        for row_data in rows:
            row_cells = table.add_row().cells
            for i, cell_text in enumerate(row_data):
                row_cells[i].text = str(cell_text)

        return table

    def save(self, file_path: str):
        """保存文档"""
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        self.doc.save(file_path)
        return file_path


class PaperExporter(BaseDocumentExporter):
    """医学论文导出器 (IMRaD 结构)"""

    def export_paper(self, paper_data: Dict[str, Any], file_path: str) -> str:
        """
        将论文数据导出为 Word 文档

        Args:
            paper_data: 论文数据字典，包含 title, authors, abstract, keywords,
                       introduction, methods, results, discussion, conclusion, references
            file_path: 输出文件路径

        Returns:
            保存的文件路径
        """
        # 标题
        title = paper_data.get('title', 'Untitled Paper')
        self.add_title(title, level=1)

        # 作者信息
        authors = paper_data.get('authors', '')
        if authors:
            p = self.doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(authors)
            run.italic = True
            run.font.size = Pt(11)

        # 摘要
        abstract = paper_data.get('abstract', '')
        if abstract:
            self.add_title('Abstract', level=2)
            self.add_paragraph(abstract)

        # 关键词
        keywords = paper_data.get('keywords', [])
        if keywords:
            p = self.doc.add_paragraph()
            run = p.add_run('Keywords: ')
            run.bold = True
            p.add_run(', '.join(keywords))

        self.doc.add_page_break()

        # IMRaD 结构
        sections = [
            ('Introduction', 'introduction'),
            ('Methods', 'methods'),
            ('Results', 'results'),
            ('Discussion', 'discussion'),
            ('Conclusion', 'conclusion'),
        ]

        for section_title, key in sections:
            content = paper_data.get(key, '')
            if content:
                self.add_title(section_title, level=2)
                self.add_paragraph(content)

        # 参考文献
        references = paper_data.get('references', [])
        if references:
            self.add_title('References', level=2)
            for i, ref in enumerate(references, 1):
                self.add_paragraph(f"[{i}] {ref}")

        return self.save(file_path)


class GrantProposalExporter(BaseDocumentExporter):
    """基金申请书导出器"""

    def export_proposal(self, proposal_data: Dict[str, Any],
                        file_path: str) -> str:
        """
        将基金申请书导出为 Word 文档

        Args:
            proposal_data: 申请书数据
            file_path: 输出文件路径
        """
        # 封面信息
        self.add_title(proposal_data.get('title', '基金申请书'), level=1)

        metadata = [
            ('申请类型', proposal_data.get('grant_type', '')),
            ('研究领域', proposal_data.get('research_area', '')),
            ('申请人', proposal_data.get('applicant', '')),
            ('依托单位', proposal_data.get('institution', '')),
            ('申请日期', proposal_data.get('date', datetime.now().strftime('%Y-%m-%d'))),
        ]

        for label, value in metadata:
            if value:
                p = self.add_paragraph('')
                run = p.add_run(f"{label}: ")
                run.bold = True
                p.add_run(str(value))

        self.doc.add_page_break()

        # 正文各部分
        sections = [
            ('一、立项依据', 'rationale'),
            ('二、研究内容', 'research_content'),
            ('三、研究目标', 'objectives'),
            ('四、拟解决的关键科学问题', 'key_problems'),
            ('五、研究方案与技术路线', 'methodology'),
            ('六、可行性分析', 'feasibility'),
            ('七、特色与创新之处', 'innovation'),
            ('八、年度计划', 'timeline'),
            ('九、预期成果', 'expected_outcomes'),
        ]

        for section_title, key in sections:
            content = proposal_data.get(key, '')
            if content:
                self.add_title(section_title, level=2)
                self.add_paragraph(content)

        # 经费预算表
        budget = proposal_data.get('budget', {})
        if budget:
            self.add_title('十、经费预算', level=2)
            headers = ['科目', '金额（万元）', '占比', '说明']
            rows = []
            total = budget.get('total', 0)
            for item in budget.get('items', []):
                name = item.get('name', '')
                amount = item.get('amount', 0)
                pct = f"{amount / total * 100:.1f}%" if total > 0 else '0%'
                rows.append([name, f"{amount:.2f}", pct, item.get('notes', '')])
            rows.append(['合计', f"{total:.2f}", '100%', ''])
            self.add_table(headers, rows)

        return self.save(file_path)


class ResponseLetterExporter(BaseDocumentExporter):
    """Response Letter 导出器"""

    def export_response_letter(self, letter_data: Dict[str, Any],
                               file_path: str) -> str:
        """
        将 Response Letter 导出为 Word 文档

        Args:
            letter_data: 包含 manuscript_id, title, authors, responses
            file_path: 输出文件路径
        """
        # 抬头
        self.add_title('Response to Reviewers', level=1)

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.add_run(f"Manuscript ID: {letter_data.get('manuscript_id', 'N/A')}\n")
        p.add_run(f"Title: {letter_data.get('title', 'N/A')}\n")
        p.add_run(f"Authors: {letter_data.get('authors', 'N/A')}\n")

        self.doc.add_paragraph(
            "Dear Editor and Reviewers,\n\n"
            "We would like to express our sincere gratitude for the constructive "
            "comments and suggestions. We have carefully revised the manuscript "
            "according to the reviewers' comments. The detailed point-by-point "
            "responses are provided below."
        )

        # 逐条回复
        responses = letter_data.get('responses', [])
        for i, resp in enumerate(responses, 1):
            self.add_title(f"Comment {i}", level=2)

            p = self.add_paragraph('')
            run = p.add_run("Reviewer's Comment: ")
            run.bold = True
            p.add_run(resp.get('comment', ''))

            p = self.add_paragraph('')
            run = p.add_run("Author's Response: ")
            run.bold = True
            run.font.color.rgb = RGBColor(0, 0, 255)
            p.add_run(resp.get('response', ''))

            if resp.get('changes'):
                p = self.add_paragraph('')
                run = p.add_run("Revisions Made: ")
                run.bold = True
                p.add_run(resp['changes'])

        return self.save(file_path)


class ProtocolExporter(BaseDocumentExporter):
    """RCT 试验方案导出器"""

    def export_protocol(self, protocol_data: Dict[str, Any],
                        file_path: str) -> str:
        """
        将 RCT 试验方案导出为 Word 文档

        Args:
            protocol_data: 试验方案数据
            file_path: 输出文件路径
        """
        study_info = protocol_data.get('study_info', {})
        self.add_title(study_info.get('title', '临床试验方案'), level=1)

        # 基本信息
        self.add_title('一、研究基本信息', level=2)
        info_items = [
            ('研究类型', study_info.get('study_type', '')),
            ('试验分期', study_info.get('phase', '')),
            ('适应症', study_info.get('indication', '')),
            ('研究时长', f"{study_info.get('duration_months', '')} 个月"),
        ]
        for label, value in info_items:
            if value:
                p = self.add_paragraph('')
                run = p.add_run(f"{label}: ")
                run.bold = True
                p.add_run(str(value))

        # 研究目的
        objectives = protocol_data.get('study_objectives', {})
        if objectives:
            self.add_title('二、研究目的', level=2)
            for k, v in objectives.items():
                p = self.add_paragraph('')
                run = p.add_run(f"{k}: ")
                run.bold = True
                p.add_run(str(v))

        # 终点
        endpoints = protocol_data.get('endpoints', {})
        if endpoints:
            self.add_title('三、研究终点', level=2)
            for k, v in endpoints.items():
                p = self.add_paragraph('')
                run = p.add_run(f"{k}: ")
                run.bold = True
                p.add_run(str(v))

        # 入排标准
        inclusion = protocol_data.get('inclusion_criteria', [])
        exclusion = protocol_data.get('exclusion_criteria', [])
        if inclusion:
            self.add_title('四、入选标准', level=2)
            for item in inclusion:
                self.doc.add_paragraph(item, style='List Number')
        if exclusion:
            self.add_title('五、排除标准', level=2)
            for item in exclusion:
                self.doc.add_paragraph(item, style='List Number')

        # 样本量
        sample_size = protocol_data.get('sample_size', {})
        if sample_size:
            self.add_title('六、样本量', level=2)
            self.add_paragraph(str(sample_size))

        # 统计分析
        stats = protocol_data.get('statistical_analysis', {})
        if stats:
            self.add_title('七、统计分析计划', level=2)
            self.add_paragraph(str(stats))

        # 伦理
        ethics = protocol_data.get('ethical_considerations', {})
        if ethics:
            self.add_title('八、伦理考虑', level=2)
            for k, v in ethics.items():
                p = self.add_paragraph('')
                run = p.add_run(f"{k}: ")
                run.bold = True
                p.add_run(str(v))

        return self.save(file_path)
