"""
医学写作助手模块
Medical Writing Assistant Module
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class JournalType(Enum):
    """目标期刊类型"""
    GENERAL_MEDICINE = "综合医学"
    SPECIALTY = "专科期刊"
    CLINICAL_RESEARCH = "临床研究"
    REVIEW = "综述类"
    CASE_REPORT = "病例报告"


class PaperSection(Enum):
    """论文章节"""
    ABSTRACT = "摘要"
    INTRODUCTION = "引言"
    METHODS = "方法"
    RESULTS = "结果"
    DISCUSSION = "讨论"
    CONCLUSION = "结论"
    REFERENCES = "参考文献"


@dataclass
class Citation:
    """引用文献数据类"""
    id: str
    authors: List[str]
    title: str
    journal: str
    year: int
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None


class PaperGenerator:
    """医学论文生成器"""
    
    def __init__(self):
        pass
    
    def generate_paper_structure(
        self,
        title: str,
        study_type: str = "临床试验",
        journal_type: JournalType = JournalType.CLINICAL_RESEARCH,
        authors: List[str] = None,
        affiliations: List[str] = None
    ) -> Dict[str, Any]:
        """
        生成论文结构框架
        
        Args:
            title: 论文题目
            study_type: 研究类型
            journal_type: 目标期刊类型
            authors: 作者列表
            affiliations: 单位列表
        
        Returns:
            论文完整结构
        """
        paper = {
            'title': title,
            'authors': authors or ["作者1", "作者2", "作者3"],
            'affiliations': affiliations or ["单位名称"],
            'abstract': self._generate_abstract(study_type),
            'keywords': self._generate_keywords(title, study_type),
            'introduction': self._generate_introduction(study_type),
            'methods': self._generate_methods(study_type),
            'results': self._generate_results(study_type),
            'discussion': self._generate_discussion(study_type),
            'conclusion': self._generate_conclusion(study_type),
            'references': [],
            'guidelines_compliance': {
                'CONSORT': study_type == "临床试验",
                'STROBE': study_type in ["观察性研究", "队列研究", "病例对照"],
                'PRISMA': study_type in ["系统综述", "Meta分析"],
                'CARE': study_type == "病例报告"
            }
        }
        
        return paper
    
    def _generate_abstract(self, study_type: str) -> Dict[str, str]:
        """生成摘要结构（结构化摘要）"""
        return {
            'objective': f"本研究旨在探讨{study_type}的有效性和安全性。",
            'methods': f"采用{study_type}研究设计，纳入符合标准的研究对象。主要评价指标包括...",
            'results': "共纳入XXX例研究对象。主要终点指标显示试验组与对照组相比...（P<0.05）。",
            'conclusion': f"本研究表明{study_type}在该适应症中具有良好的疗效和安全性。",
            'keywords': ""
        }
    
    def _generate_keywords(self, title: str, study_type: str) -> List[str]:
        """生成关键词"""
        # 从标题提取关键词
        words = re.findall(r'[\u4e00-\u9fa5]+', title)
        keywords = words[:3] if len(words) >= 3 else words
        
        # 添加研究类型相关关键词
        keywords.extend([study_type, "临床研究"])
        
        return list(set(keywords))[:6]  # 最多6个关键词
    
    def _generate_introduction(self, study_type: str) -> Dict[str, Any]:
        """生成引言部分"""
        return {
            'background': """
1. 疾病负担：阐述研究疾病的流行病学特征和公共卫生意义
2. 现有治疗现状：总结当前标准治疗方案及其局限性
3. 研究缺口：指出现有证据的不足和争议点
            """.strip(),
            'rationale': """
基于上述背景，本研究拟解决以下科学问题：
- 问题1：...
- 问题2：...
- 问题3：...
            """.strip(),
            'objectives': """
主要研究目的：
次要研究目的：
            """.strip(),
            'hypothesis': "本研究假设试验组在主要终点指标上非劣效（或优于）对照组。"
        }
    
    def _generate_methods(self, study_type: str) -> Dict[str, Any]:
        """生成方法部分"""
        methods = {
            'study_design': f"本研究为{study_type}研究，在XX家研究中心开展。",
            'study_population': {
                'inclusion_criteria': [
                    "1. 符合疾病诊断标准",
                    "2. 年龄18-75岁",
                    "3. 签署知情同意书"
                ],
                'exclusion_criteria': [
                    "1. 对研究药物过敏",
                    "2. 严重肝肾功能异常",
                    "3. 妊娠或哺乳期妇女"
                ]
            },
            'interventions': {
                'experimental_group': "试验组干预措施描述",
                'control_group': "对照组干预措施描述",
                'treatment_duration': "治疗/随访时长"
            },
            'outcome_measures': {
                'primary_endpoint': "主要终点指标定义",
                'secondary_endpoints': [
                    "次要终点1",
                    "次要终点2",
                    "次要终点3"
                ],
                'safety_endpoints': [
                    "不良事件发生率",
                    "严重不良事件",
                    "实验室检查异常"
                ]
            },
            'sample_size': "基于主要终点指标的预期效应量计算样本量（详见统计部分）",
            'randomization': "采用中央随机化系统，按1:1比例分组",
            'blinding': "双盲设计（受试者、研究者、评价者）",
            'statistical_analysis': {
                'analysis_sets': ["全分析集(FAS)", "符合方案集(PPS)", "安全性分析集(SS)"],
                'primary_analysis': "主要疗效指标的组间比较（t检验/卡方检验）",
                'secondary_analysis': "次要终点分析、亚组分析、敏感性分析",
                'significance_level': "双侧α=0.05"
            },
            'ethical_approval': "本研究已获得XX医院伦理审查委员会批准（编号：XXX）"
        }
        
        return methods
    
    def _generate_results(self, study_type: str) -> Dict[str, Any]:
        """生成结果部分"""
        return {
            'patient_flow': {
                'enrollment': "共筛选XX例，随机化XX例",
                'disposition': "试验组完成XX例，对照组完成XX例",
                'dropout_reasons': ["失访", "不良事件", "依从性差", "其他"]
            },
            'baseline_characteristics': {
                'demographics': "两组人口学特征（年龄、性别、种族等）基线均衡可比",
                'clinical_characteristics': "两组疾病严重程度、病程、合并症等基线均衡可比",
                'concomitant_medications': "合并用药情况两组相似"
            },
            'efficacy_results': {
                'primary_endpoint': {
                    'description': "主要终点指标结果描述",
                    'statistics': "试验组 vs 对照组：均值差异/率差异，P值",
                    'confidence_interval': "95% CI：(下限，上限)"
                },
                'secondary_endpoints': [
                    "次要终点1结果",
                    "次要终点2结果",
                    "次要终点3结果"
                ],
                'subgroup_analysis': "亚组分析结果（年龄、性别、病情严重程度等）"
            },
            'safety_results': {
                'adverse_events': "两组不良事件发生率比较",
                'serious_adverse_events': "严重不良事件列表和分析",
                'laboratory_findings': "实验室检查异常情况",
                'vital_signs': "生命体征变化"
            },
            'tables_figures': [
                "表1：基线人口学和临床特征",
                "表2：主要疗效指标分析",
                "表3：次要疗效指标分析",
                "表4：不良事件汇总",
                "图1：受试者流程图（CONSORT）",
                "图2：主要终点森林图/生存曲线"
            ]
        }
    
    def _generate_discussion(self, study_type: str) -> Dict[str, Any]:
        """生成讨论部分"""
        return {
            'key_findings': """
本研究的主要发现：
1. 主要终点：试验组在XX指标上显著优于/非劣效于对照组
2. 次要终点：在XX、XX等指标上也显示出一致的趋势
3. 安全性：两组安全性特征相似，未发现新的安全信号
            """.strip(),
            'interpretation': """
研究结果的解释：
- 与已有文献的一致性/差异性
- 可能的机制解释
- 临床意义讨论
            """.strip(),
            'comparison_with_literature': """
与现有研究比较：
1. 与研究A的结果一致...
2. 与研究B的差异可能由于...
3. 本研究的创新点在于...
            """.strip(),
            'limitations': """
研究局限性：
1. 样本量大小的限制
2. 研究人群的代表性
3. 随访时间的限制
4. 可能的未测量混杂因素
            """.strip(),
            'clinical_implications': """
临床意义：
- 对临床实践的启示
- 对指南制定的影响
- 未来研究方向建议
            """.strip()
        }
    
    def _generate_conclusion(self, study_type: str) -> str:
        """生成结论部分"""
        return """
基于本研究结果，我们得出以下结论：
1. 主要结论1
2. 主要结论2
3. 对临床实践的建议

本研究为[适应症]的治疗提供了新的证据，支持[干预措施]在临床中的应用。
        """.strip()


class ReferenceManager:
    """参考文献管理器"""
    
    def __init__(self):
        self.citations: Dict[str, Citation] = {}
        self.style = "vancouver"  # 默认温哥华格式
    
    def add_citation(
        self,
        citation_id: str,
        authors: List[str],
        title: str,
        journal: str,
        year: int,
        volume: str = None,
        issue: str = None,
        pages: str = None,
        doi: str = None
    ):
        """添加参考文献"""
        citation = Citation(
            id=citation_id,
            authors=authors,
            title=title,
            journal=journal,
            year=year,
            volume=volume,
            issue=issue,
            pages=pages,
            doi=doi
        )
        self.citations[citation_id] = citation
    
    def format_citation(self, citation_id: str, style: str = "vancouver") -> Optional[str]:
        """格式化单条参考文献"""
        citation = self.citations.get(citation_id)
        if not citation:
            return None
        
        if style == "vancouver":
            return self._format_vancouver(citation)
        elif style == "apa":
            return self._format_apa(citation)
        elif style == "gb7714":
            return self._format_gb7714(citation)  # 中国国家标准
        else:
            return self._format_vancouver(citation)
    
    def _format_vancouver(self, citation: Citation) -> str:
        """温哥华格式（医学期刊常用）"""
        # 作者格式化（最多3个作者，后面加et al.）
        authors_str = ""
        if len(citation.authors) <= 3:
            authors_str = ", ".join(citation.authors)
        else:
            authors_str = ", ".join(citation.authors[:3]) + ", et al."
        
        # 基础格式
        parts = [f"{citation.id}. {authors_str}. {citation.title}. {citation.journal}."]
        
        if citation.year:
            parts.append(f" {citation.year}")
        if citation.volume:
            parts.append(f";{citation.volume}")
        if citation.issue:
            parts.append(f"({citation.issue})")
        if citation.pages:
            parts.append(f":{citation.pages}")
        
        if citation.doi:
            parts.append(f". DOI: {citation.doi}")
        
        return "".join(parts)
    
    def _format_apa(self, citation: Citation) -> str:
        """APA 格式"""
        authors_str = ", ".join(citation.authors)
        parts = [f"{citation.id}. {authors_str} ({citation.year}). {citation.title}."]
        
        if citation.journal:
            parts.append(f" {citation.journal}")
        if citation.volume:
            parts.append(f", {citation.volume}")
        if citation.pages:
            parts.append(f", {citation.pages}")
        
        if citation.doi:
            parts.append(f". https://doi.org/{citation.doi}")
        
        return "".join(parts)
    
    def _format_gb7714(self, citation: Citation) -> str:
        """中国国家标准 GB7714 格式"""
        authors_str = ", ".join(citation.authors)
        parts = [f"[{citation.id}] {authors_str}. {citation.title}[J]."]
        
        parts.append(f" {citation.journal}")
        parts.append(f", {citation.year}")
        
        if citation.volume:
            parts.append(f", {citation.volume}")
        if citation.issue:
            parts.append(f"({citation.issue})")
        if citation.pages:
            parts.append(f":{citation.pages}")
        
        parts.append(".")
        
        return "".join(parts)
    
    def generate_reference_list(self, citation_ids: List[str], style: str = "vancouver") -> List[str]:
        """生成参考文献列表"""
        references = []
        for cid in citation_ids:
            formatted = self.format_citation(cid, style)
            if formatted:
                references.append(formatted)
        return references

    # ========== 新增: 更多引用格式支持 (v0.2) ==========

    def _format_mla(self, citation: Citation) -> str:
        """MLA 格式 (Modern Language Association)"""
        authors_str = ", ".join(citation.authors)
        parts = [f"{authors_str}. \"{citation.title}.\""]
        if citation.journal:
            parts.append(f" {citation.journal}")
        if citation.volume:
            parts.append(f", vol. {citation.volume}")
        if citation.issue:
            parts.append(f", no. {citation.issue}")
        if citation.year:
            parts.append(f", {citation.year}")
        if citation.pages:
            parts.append(f", pp. {citation.pages}")
        parts.append(".")
        if citation.doi:
            parts.append(f" DOI: {citation.doi}.")
        return "".join(parts)

    def _format_chicago(self, citation: Citation) -> str:
        """Chicago 格式 (Notes-Bibliography)"""
        authors_str = ", ".join(citation.authors)
        parts = [f"{authors_str}. \"{citation.title}.\""]
        if citation.journal:
            parts.append(f" {citation.journal}")
        if citation.volume:
            parts.append(f" {citation.volume}")
        if citation.issue:
            parts.append(f", no. {citation.issue}")
        if citation.year:
            parts.append(f" ({citation.year})")
        if citation.pages:
            parts.append(f": {citation.pages}")
        parts.append(".")
        if citation.doi:
            parts.append(f" DOI: {citation.doi}.")
        return "".join(parts)

    def _format_harvard(self, citation: Citation) -> str:
        """Harvard 格式 (Author-Date)"""
        authors_str = ", ".join(citation.authors)
        parts = [f"{authors_str} ({citation.year}) '{citation.title}'"]
        if citation.journal:
            parts.append(f", {citation.journal}")
        if citation.volume:
            parts.append(f", {citation.volume}")
        if citation.issue:
            parts.append(f"({citation.issue})")
        if citation.pages:
            parts.append(f", pp. {citation.pages}")
        parts.append(".")
        if citation.doi:
            parts.append(f" Available at: https://doi.org/{citation.doi}")
        return "".join(parts)

    def _format_ieee(self, citation: Citation) -> str:
        """IEEE 格式"""
        authors_str = ", ".join(citation.authors)
        parts = [f"[{citation.id}] {authors_str}, \"{citation.title},\""]
        if citation.journal:
            parts.append(f" {citation.journal}")
        if citation.volume:
            parts.append(f", vol. {citation.volume}")
        if citation.issue:
            parts.append(f", no. {citation.issue}")
        if citation.pages:
            parts.append(f", pp. {citation.pages}")
        if citation.year:
            parts.append(f", {citation.year}")
        parts.append(".")
        if citation.doi:
            parts.append(f" DOI: {citation.doi}.")
        return "".join(parts)

    def _format_nature(self, citation: Citation) -> str:
        """Nature 期刊格式 (编号式)"""
        authors_str = ", ".join(citation.authors)
        parts = [f"{citation.id}. {authors_str} {citation.title}."]
        if citation.journal:
            parts.append(f" {citation.journal}")
        if citation.volume:
            parts.append(f" {citation.volume}")
        if citation.pages:
            parts.append(f", {citation.pages}")
        if citation.year:
            parts.append(f" ({citation.year})")
        if citation.doi:
            parts.append(f". DOI: {citation.doi}")
        parts.append(".")
        return "".join(parts)

    def _format_science(self, citation: Citation) -> str:
        """Science 期刊格式 (编号式)"""
        authors_str = ", ".join(citation.authors)
        parts = [f"{citation.id}. {authors_str}, \"{citation.title},\""]
        if citation.journal:
            parts.append(f" {citation.journal}")
        if citation.volume:
            parts.append(f" {citation.volume}")
        if citation.pages:
            parts.append(f", {citation.pages}")
        if citation.year:
            parts.append(f" ({citation.year})")
        if citation.doi:
            parts.append(f". DOI: {citation.doi}")
        parts.append(".")
        return "".join(parts)

    def _format_cse(self, citation: Citation) -> str:
        """CSE 格式 (Council of Science Editors)"""
        authors_str = ", ".join(citation.authors)
        parts = [f"{citation.id}. {authors_str}. {citation.title}."]
        if citation.journal:
            parts.append(f" {citation.journal}")
        if citation.year:
            parts.append(f". {citation.year}")
        if citation.volume:
            parts.append(f";{citation.volume}")
        if citation.issue:
            parts.append(f"({citation.issue})")
        if citation.pages:
            parts.append(f":{citation.pages}")
        if citation.doi:
            parts.append(f". DOI: {citation.doi}")
        parts.append(".")
        return "".join(parts)

    def _format_bmj(self, citation: Citation) -> str:
        """BMJ/Vancouver 变体格式"""
        authors_str = ""
        if len(citation.authors) <= 6:
            authors_str = ", ".join(citation.authors)
        else:
            authors_str = ", ".join(citation.authors[:3]) + ", et al."
        parts = [f"{citation.id}. {authors_str}. {citation.title}. {citation.journal}"]
        if citation.year:
            parts.append(f" {citation.year}")
        if citation.volume:
            parts.append(f";{citation.volume}")
        if citation.issue:
            parts.append(f"({citation.issue})")
        if citation.pages:
            parts.append(f":{citation.pages}")
        if citation.doi:
            parts.append(f". doi:{citation.doi}")
        parts.append(".")
        return "".join(parts)

    SUPPORTED_STYLES = {
        "vancouver": "温哥华格式 (医学常用)",
        "apa": "APA 格式 (心理学会)",
        "gb7714": "GB7714 国标 (中国)",
        "mla": "MLA 格式 (现代语言协会)",
        "chicago": "Chicago 格式 (芝加哥)",
        "harvard": "Harvard 格式 (哈佛)",
        "ieee": "IEEE 格式 (电气电子工程师)",
        "nature": "Nature 格式 (自然期刊)",
        "science": "Science 格式 (科学期刊)",
        "cse": "CSE 格式 (科学编辑委员会)",
        "bmj": "BMJ 格式 (英国医学期刊)",
    }

    def format_citation(self, citation_id: str, style: str = "vancouver") -> Optional[str]:
        """格式化单条参考文献 (增强版，支持11种格式)"""
        citation = self.citations.get(citation_id)
        if not citation:
            return None

        style = style.lower()
        formatters = {
            "vancouver": self._format_vancouver,
            "apa": self._format_apa,
            "gb7714": self._format_gb7714,
            "mla": self._format_mla,
            "chicago": self._format_chicago,
            "harvard": self._format_harvard,
            "ieee": self._format_ieee,
            "nature": self._format_nature,
            "science": self._format_science,
            "cse": self._format_cse,
            "bmj": self._format_bmj,
        }
        formatter = formatters.get(style, self._format_vancouver)
        return formatter(citation)

    def get_supported_styles(self) -> Dict[str, str]:
        """获取支持的引用格式列表"""
        return self.SUPPORTED_STYLES.copy()

    # ========== 新增: 期刊缩写工具 ==========

    JOURNAL_ABBREVIATIONS = {
        "New England Journal of Medicine": "N Engl J Med",
        "The Lancet": "Lancet",
        "Journal of the American Medical Association": "JAMA",
        "British Medical Journal": "BMJ",
        "Nature Medicine": "Nat Med",
        "Cell": "Cell",
        "Circulation": "Circulation",
        "Gastroenterology": "Gastroenterology",
        "Diabetes Care": "Diabetes Care",
        "Journal of Clinical Oncology": "J Clin Oncol",
        "Annals of Internal Medicine": "Ann Intern Med",
        "PLOS ONE": "PLoS One",
        "Scientific Reports": "Sci Rep",
        "BMJ Open": "BMJ Open",
        "Medicine": "Medicine (Baltimore)",
        "Hepatology": "Hepatology",
        "Journal of Hepatology": "J Hepatol",
        "Diabetologia": "Diabetologia",
        "Thyroid": "Thyroid",
        "Stroke": "Stroke",
        "Neurology": "Neurology",
        "Radiology": "Radiology",
        "Chest": "Chest",
        "Kidney International": "Kidney Int",
        "Blood": "Blood",
        "JAMA Oncology": "JAMA Oncol",
        "Gut": "Gut",
        "JAMA Internal Medicine": "JAMA Intern Med",
        "JAMA Dermatology": "JAMA Dermatol",
        "JAMA Neurology": "JAMA Neurol",
        "JAMA Psychiatry": "JAMA Psychiatry",
        "JAMA Pediatrics": "JAMA Pediatr",
        "JAMA Surgery": "JAMA Surg",
        "The Lancet Oncology": "Lancet Oncol",
        "The Lancet Neurology": "Lancet Neurol",
        "The Lancet Infectious Diseases": "Lancet Infect Dis",
        "The Lancet Diabetes & Endocrinology": "Lancet Diabetes Endocrinol",
        "The Lancet Global Health": "Lancet Glob Health",
        "The Lancet Digital Health": "Lancet Digit Health",
        "European Heart Journal": "Eur Heart J",
        "European Radiology": "Eur Radiol",
        "European Journal of Heart Failure": "Eur J Heart Fail",
        "American Journal of Gastroenterology": "Am J Gastroenterol",
        "American Journal of Obstetrics & Gynecology": "Am J Obstet Gynecol",
        "American Journal of Transplantation": "Am J Transplant",
        "American Journal of Epidemiology": "Am J Epidemiol",
        "Clinical Infectious Diseases": "Clin Infect Dis",
        "Critical Care Medicine": "Crit Care Med",
        "Obstetrics & Gynecology": "Obstet Gynecol",
        "Pediatrics": "Pediatrics",
        "Pain": "Pain",
        "Ophthalmology": "Ophthalmology",
        "Anesthesiology": "Anesthesiology",
        "Transplantation": "Transplantation",
        "Rheumatology": "Rheumatology",
        "Arthritis & Rheumatology": "Arthritis Rheumatol",
        "Journal of Allergy and Clinical Immunology": "J Allergy Clin Immunol",
        "Journal of Clinical Investigation": "J Clin Invest",
        "Journal of Clinical Epidemiology": "J Clin Epidemiol",
        "Journal of Biomedical Science": "J Biomed Sci",
        "BMC Medicine": "BMC Med",
        "BMC Medical Research Methodology": "BMC Med Res Methodol",
        "PLOS Medicine": "PLoS Med",
        "Cochrane Database of Systematic Reviews": "Cochrane Database Syst Rev",
        "Systematic Reviews": "Syst Rev",
        "Research Integrity and Peer Review": "Res Integr Peer Rev",
        "Journal of Medical Ethics": "J Med Ethics",
        "Academic Medicine": "Acad Med",
        "Medical Education": "Med Educ",
        "npj Digital Medicine": "NPJ Digit Med",
        "Nature Communications": "Nat Commun",
        "eClinicalMedicine": "EClinicalMedicine",
        "EBioMedicine": "EBioMedicine",
        "Mayo Clinic Proceedings": "Mayo Clin Proc",
        "Age and Ageing": "Age Ageing",
        "World Psychiatry": "World Psychiatry",
        "CMAJ": "CMAJ",
        "MJA": "Med J Aust",
        "中华医学杂志英文版": "Chin Med J (Engl)",
    }

    def get_journal_abbreviation(self, full_name: str) -> str:
        """获取期刊标准缩写 (NLM/PubMed标准)"""
        return self.JOURNAL_ABBREVIATIONS.get(full_name, full_name)

    def apply_journal_abbreviation(self, citation_id: str):
        """将引用中的期刊名替换为标准缩写"""
        citation = self.citations.get(citation_id)
        if citation and citation.journal:
            citation.journal = self.get_journal_abbreviation(citation.journal)

    def apply_all_abbreviations(self):
        """对所有引用应用期刊缩写"""
        for cid in self.citations:
            self.apply_journal_abbreviation(cid)

    # ========== 新增: 文献解析与导入 ==========

    def parse_from_text(self, text: str, style_hint: str = "auto") -> Optional[Citation]:
        """
        从自由文本解析文献信息 (基础版)

        Args:
            text: 包含文献信息的文本
            style_hint: 格式提示

        Returns:
            解析出的Citation对象，或None
        """
        import re

        # 尝试提取年份
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        year = int(year_match.group(1)) if year_match else None

        # 尝试提取DOI
        doi_match = re.search(r'10\.\d{4,}/[^\s]+', text)
        doi = doi_match.group(0) if doi_match else None

        # 尝试提取作者 (以 et al. 或逗号分隔的名字)
        authors = []
        author_patterns = [
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+(?:,\s+[A-Z][a-z]+\s+[A-Z][a-z]+)*)',
            r'^([A-Z][a-z]+\s+[A-Z]\.?\s*(?:,\s*[A-Z][a-z]+\s+[A-Z]\.?\s*)+)',
        ]
        for pattern in author_patterns:
            am = re.match(pattern, text)
            if am:
                raw = am.group(1)
                authors = [a.strip() for a in raw.split(',')]
                break

        # 尝试提取标题（引号内或句号与期刊名之间）
        title = ""
        title_match = re.search(r'"([^"]+)"', text)
        if title_match:
            title = title_match.group(1)
        else:
            # 简单提取：假设第一个句号后到下一个句号前是标题
            parts = text.split('.')
            if len(parts) >= 2:
                title = parts[1].strip()

        # 生成ID
        cid = f"parsed_{len(self.citations)+1}"
        citation = Citation(
            id=cid,
            authors=authors if authors else ["Unknown Author"],
            title=title if title else "Unknown Title",
            journal="Unknown Journal",
            year=year if year else 2024,
            doi=doi
        )
        self.citations[cid] = citation
        return citation

    def import_from_bibtex(self, bibtex_text: str) -> List[str]:
        """
        从BibTeX格式导入文献

        Args:
            bibtex_text: BibTeX条目文本

        Returns:
            导入的引用ID列表
        """
        import re
        imported_ids = []

        # 匹配每个BibTeX条目
        entries = re.findall(r'@\w+\{([^,]+),\s*([^@]+)\}', bibtex_text, re.DOTALL)

        for entry_key, entry_body in entries:
            fields = {}
            for match in re.finditer(r'(\w+)\s*=\s*\{([^}]+)\}', entry_body):
                fields[match.group(1).lower()] = match.group(2).strip()

            authors_raw = fields.get('author', 'Unknown')
            authors = [a.strip() for a in authors_raw.split(' and ')]

            cid = f"bib_{entry_key}"
            citation = Citation(
                id=cid,
                authors=authors,
                title=fields.get('title', 'Unknown Title'),
                journal=fields.get('journal', fields.get('booktitle', 'Unknown Journal')),
                year=int(fields.get('year', 2024)),
                volume=fields.get('volume'),
                issue=fields.get('number'),
                pages=fields.get('pages'),
                doi=fields.get('doi')
            )
            self.citations[cid] = citation
            imported_ids.append(cid)

        return imported_ids

    def import_from_ris(self, ris_text: str) -> List[str]:
        """
        从RIS格式导入文献

        Args:
            ris_text: RIS格式文本

        Returns:
            导入的引用ID列表
        """
        lines = ris_text.strip().split('\n')
        imported_ids = []
        current = {}

        for line in lines:
            line = line.strip()
            if line.startswith('TY  - '):
                current = {'type': line[6:].strip()}
            elif line.startswith('TI  - '):
                current['title'] = line[6:].strip()
            elif line.startswith('T1  - '):
                current['title'] = line[6:].strip()
            elif line.startswith('AU  - '):
                current.setdefault('authors', []).append(line[6:].strip())
            elif line.startswith('JO  - ') or line.startswith('JA  - ') or line.startswith('JF  - '):
                current['journal'] = line[6:].strip()
            elif line.startswith('PY  - ') or line.startswith('Y1  - '):
                current['year'] = line[6:].strip()[:4]
            elif line.startswith('VL  - '):
                current['volume'] = line[6:].strip()
            elif line.startswith('IS  - '):
                current['issue'] = line[6:].strip()
            elif line.startswith('SP  - '):
                current['spage'] = line[6:].strip()
            elif line.startswith('EP  - '):
                current['epage'] = line[6:].strip()
            elif line.startswith('DO  - '):
                current['doi'] = line[6:].strip()
            elif line == 'ER  - ':
                # 结束当前条目
                cid = f"ris_{len(self.citations)+1}"
                pages = None
                if 'spage' in current and 'epage' in current:
                    pages = f"{current['spage']}-{current['epage']}"
                citation = Citation(
                    id=cid,
                    authors=current.get('authors', ['Unknown']),
                    title=current.get('title', 'Unknown Title'),
                    journal=current.get('journal', 'Unknown Journal'),
                    year=int(current.get('year', 2024)),
                    volume=current.get('volume'),
                    issue=current.get('issue'),
                    pages=pages,
                    doi=current.get('doi')
                )
                self.citations[cid] = citation
                imported_ids.append(cid)
                current = {}

        return imported_ids

    def remove_duplicates(self) -> int:
        """
        去除重复的引用（基于标题和DOI）

        Returns:
            去除的重复数量
        """
        seen = {}
        duplicates = []

        for cid, citation in self.citations.items():
            key = (citation.title.lower().strip(), citation.doi or "")
            if key in seen:
                duplicates.append(cid)
            else:
                seen[key] = cid

        for cid in duplicates:
            del self.citations[cid]

        return len(duplicates)

    def export_to_bibtex(self, citation_ids: List[str]) -> str:
        """导出为BibTeX格式"""
        entries = []
        for cid in citation_ids:
            c = self.citations.get(cid)
            if not c:
                continue
            authors_bib = " and ".join(c.authors)
            entry = f"@article{{{cid},\n"
            entry += f"  title = {{{c.title}}},\n"
            entry += f"  author = {{{authors_bib}}},\n"
            entry += f"  journal = {{{c.journal}}},\n"
            entry += f"  year = {{{c.year}}},\n"
            if c.volume:
                entry += f"  volume = {{{c.volume}}},\n"
            if c.issue:
                entry += f"  number = {{{c.issue}}},\n"
            if c.pages:
                entry += f"  pages = {{{c.pages}}},\n"
            if c.doi:
                entry += f"  doi = {{{c.doi}}}\n"
            entry += "}"
            entries.append(entry)
        return "\n\n".join(entries)

    def export_to_ris(self, citation_ids: List[str]) -> str:
        """导出为RIS格式"""
        entries = []
        for cid in citation_ids:
            c = self.citations.get(cid)
            if not c:
                continue
            entry = "TY  - JOUR\n"
            entry += f"TI  - {c.title}\n"
            for author in c.authors:
                entry += f"AU  - {author}\n"
            entry += f"JO  - {c.journal}\n"
            entry += f"PY  - {c.year}\n"
            if c.volume:
                entry += f"VL  - {c.volume}\n"
            if c.issue:
                entry += f"IS  - {c.issue}\n"
            if c.pages:
                entry += f"SP  - {c.pages.split('-')[0]}\n"
                if '-' in c.pages:
                    entry += f"EP  - {c.pages.split('-')[1]}\n"
            if c.doi:
                entry += f"DO  - {c.doi}\n"
            entry += "ER  - "
            entries.append(entry)
        return "\n\n".join(entries)

    def search_pubmed(self, query: str, max_results: int = 10) -> List[Citation]:
        """从 PubMed 搜索文献（模拟）"""
        # 实际应用中应调用 PubMed API
        # 这里返回模拟结果
        mock_results = [
            Citation(
                id="1",
                authors=["Smith A", "Johnson B", "Williams C"],
                title=f"Systematic review of {query}",
                journal="Journal of Medical Research",
                year=2023,
                volume="45",
                issue="2",
                pages="123-145"
            ),
            Citation(
                id="2",
                authors=["Lee D", "Brown E"],
                title=f"Meta-analysis of {query} randomized controlled trials",
                journal="Clinical Therapeutics",
                year=2022,
                volume="38",
                pages="890-905"
            )
        ]
        return mock_results[:max_results]


class FigureTableGenerator:
    """图表生成器"""
    
    def __init__(self):
        pass
    
    def generate_table_template(
        self,
        table_id: str,
        title: str,
        columns: List[str],
        rows: int = 10
    ) -> Dict[str, Any]:
        """生成表格模板"""
        return {
            'id': table_id,
            'title': f"表 {table_id}. {title}",
            'columns': columns,
            'note': "注：数据以均值±标准差或n(%)表示；*P<0.05表示组间差异具有统计学意义",
            'abbreviations': ["缩写1：全称1", "缩写2：全称2"]
        }
    
    def generate_figure_template(
        self,
        figure_id: str,
        title: str,
        figure_type: str = "line"
    ) -> Dict[str, Any]:
        """生成图形模板"""
        figure_types = {
            'line': "折线图 - 用于显示随时间变化的趋势",
            'bar': "柱状图 - 用于组间比较",
            'box': "箱线图 - 用于显示数据分布",
            'scatter': "散点图 - 用于显示变量间关系",
            'forest': "森林图 - 用于Meta分析结果展示",
            'kaplan_meier': "Kaplan-Meier曲线 - 用于生存分析",
            'flowchart': "流程图 - 用于受试者流程（CONSORT）"
        }
        
        return {
            'id': figure_id,
            'title': f"图 {figure_id}. {title}",
            'type': figure_type,
            'description': figure_types.get(figure_type, "请在此描述图形内容"),
            'legend': "图例说明",
            'note': "注：请在此添加图注和统计显著性标记"
        }
    
    def generate_consort_flowchart(self) -> Dict[str, Any]:
        """生成 CONSORT 受试者流程图模板"""
        return {
            'title': "图1. 受试者流程图（CONSORT）",
            'levels': [
                {
                    'name': "评估合格性",
                    'total': "N = ???",
                    'outcomes': [
                        "随机化：N = ???",
                        "排除：N = ???（原因：不符合入排标准、拒绝参加等）"
                    ]
                },
                {
                    'name': "随机分配",
                    'groups': [
                        "试验组：N = ???",
                        "对照组：N = ???"
                    ]
                },
                {
                    'name': "随访",
                    'outcomes': [
                        "完成研究：N = ???",
                        "失访：N = ???（原因：...）",
                        "退出：N = ???（原因：...）"
                    ]
                },
                {
                    'name': "分析",
                    'analysis_sets': [
                        "全分析集(FAS)：N = ???",
                        "符合方案集(PPS)：N = ???",
                        "安全性分析集(SS)：N = ???"
                    ]
                }
            ]
        }


class MedicalWritingAssistant:
    """医学写作助手主类"""
    
    def __init__(self):
        self.paper_generator = PaperGenerator()
        self.reference_manager = ReferenceManager()
        self.figure_generator = FigureTableGenerator()
    
    def create_manuscript(
        self,
        title: str,
        study_type: str = "临床试验",
        **kwargs
    ) -> Dict[str, Any]:
        """创建完整论文手稿"""
        manuscript = {
            'title_page': self._generate_title_page(title, **kwargs),
            'structure': self.paper_generator.generate_paper_structure(title, study_type),
            'reference_manager': self.reference_manager,
            'templates': {
                'tables': [],
                'figures': []
            },
            'writing_tips': self._generate_writing_tips(study_type),
            'checklist': self._generate_submission_checklist()
        }
        
        return manuscript
    
    def _generate_title_page(self, title: str, **kwargs) -> Dict[str, Any]:
        """生成标题页"""
        return {
            'title': title,
            'authors': kwargs.get('authors', ["作者1¹", "作者2¹,²"]),
            'affiliations': [
                "¹ 单位全称，城市，邮政编码，国家",
                "² 其他单位"
            ],
            'corresponding_author': {
                'name': "通讯作者姓名",
                'email': "email@example.com",
                'phone': "+86-XXX-XXXXXXX",
                'address': "通讯地址"
            },
            'running_title': title[:60] + "..." if len(title) > 60 else title,
            'word_count': "约XXXX字",
            'abstract_word_count': "250-300字",
            'keywords_count': "3-6个",
            'funding': "基金项目信息",
            'conflicts_of_interest': "利益冲突声明",
            'acknowledgments': "致谢"
        }
    
    def _generate_writing_tips(self, study_type: str) -> List[str]:
        """生成写作提示"""
        tips = [
            "使用准确、清晰、简洁的医学专业语言",
            "避免使用模糊表述（如'significant'需明确是统计显著还是临床显著）",
            "正确使用专业术语，参照最新医学名词规范",
            "保持客观中立的科学态度，避免主观推断",
            "数据描述需准确，注明统计量（均值、标准差、例数、P值等）",
            "注意数字和单位的正确格式（如空格、大小写）",
            "使用标准缩写，首次出现时注明全称",
            "参照目标期刊的作者须知（Instructions for Authors）",
            "确保所有引用文献已在参考文献中列出并格式统一",
            "图表应具有自明性，单独阅读也能理解内容"
        ]
        
        if study_type == "临床试验":
            tips.extend([
                "严格遵循 CONSORT 声明规范",
                "样本量计算需提供详细依据",
                "随机化方法需具体描述",
                "所有结局指标需预先设定"
            ])
        elif study_type in ["系统综述", "Meta分析"]:
            tips.extend([
                "遵循 PRISMA 声明",
                "文献检索策略需完整可重复",
                "偏倚风险评估需详细报告",
                "异质性分析和处理方法需说明"
            ])
        
        return tips
    
    def _generate_submission_checklist(self) -> Dict[str, List[str]]:
        """生成投稿检查清单"""
        return {
            'content_check': [
                "所有作者已审阅并同意投稿",
                "内容无抄袭，未一稿多投",
                "伦理审查和知情同意已获得",
                "数据真实准确，统计方法正确",
                "利益冲突已声明",
                "基金资助已注明"
            ],
            'format_check': [
                "符合目标期刊格式要求",
                "字数限制符合要求",
                "参考文献格式统一",
                "图表编号正确，引用完整",
                "缩写首次出现注明全称",
                "计量单位符合规范"
            ],
            'submission_documents': [
                "主文稿（含标题页、摘要、正文、参考文献）",
                "图表文件（单独文件或嵌入文稿）",
                "补充材料（如适用）",
                "投稿信（Cover Letter）",
                "作者贡献声明",
                "版权转让协议"
            ]
        }
    
    def generate_cover_letter(
        self,
        journal_name: str,
        manuscript_title: str,
        key_findings: str,
        significance: str
    ) -> str:
        """生成投稿信（Cover Letter）"""
        return f"""尊敬的 {journal_name} 编辑：

您好！

我们谨此向贵刊投稿，题为「{manuscript_title}」。

本研究的主要发现：
{key_findings}

本研究的意义在于：
{significance}

本研究的创新点：
1. 首次探讨了...
2. 方法学上的改进...
3. 对临床实践的启示...

我们确认：
- 本文为原创性研究，未一稿多投
- 所有作者已审阅并同意投稿
- 研究已获得必要的伦理审查批准
- 无相关利益冲突

感谢您考虑我们的投稿！期待您的回复。

此致

敬礼

通讯作者：XXX
单位：XXX
邮箱：XXX@example.com
日期：202X年XX月XX日
"""
