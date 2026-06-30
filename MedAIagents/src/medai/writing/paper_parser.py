"""
自然语言论文文本解析模块
Natural Language Paper Text Parser

支持从纯文本中自动识别IMRaD结构、提取关键信息和研究特征
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class StudyDesignType(Enum):
    """研究设计类型"""
    RCT = "随机对照试验 (RCT)"
    COHORT = "队列研究"
    CASE_CONTROL = "病例对照研究"
    CROSS_SECTIONAL = "横断面研究"
    META_ANALYSIS = "Meta分析/系统评价"
    CASE_SERIES = "病例系列/病例报告"
    BASIC_RESEARCH = "基础研究"
    OBSERVATIONAL = "观察性研究(未明确)"
    UNKNOWN = "未识别"


@dataclass
class ParsedPaper:
    """解析后的论文数据结构"""
    title: str = ""
    authors: List[str] = None
    abstract: str = ""
    keywords: List[str] = None
    introduction: str = ""
    methods: str = ""
    results: str = ""
    discussion: str = ""
    conclusion: str = ""
    references: List[str] = None
    acknowledgments: str = ""
    funding: str = ""
    ethics_statement: str = ""
    conflicts_of_interest: str = ""
    # 元数据
    study_design: StudyDesignType = StudyDesignType.UNKNOWN
    sample_size: Optional[int] = None
    p_values: List[str] = None
    confidence_intervals: List[str] = None
    effect_sizes: List[str] = None
    statistical_methods: List[str] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.keywords is None:
            self.keywords = []
        if self.references is None:
            self.references = []
        if self.p_values is None:
            self.p_values = []
        if self.confidence_intervals is None:
            self.confidence_intervals = []
        if self.effect_sizes is None:
            self.effect_sizes = []
        if self.statistical_methods is None:
            self.statistical_methods = []

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（兼容PaperEvaluator输入格式）"""
        return {
            'title': self.title,
            'abstract': self.abstract,
            'introduction': self.introduction,
            'methods': self.methods,
            'results': self.results,
            'discussion': self.discussion,
            'conclusion': self.conclusion,
            'references': self.references,
            'authors': self.authors,
        }

    def get_imrad_completeness(self) -> Dict[str, Any]:
        """评估IMRaD结构完整性"""
        sections = {
            'abstract': bool(self.abstract),
            'introduction': bool(self.introduction),
            'methods': bool(self.methods),
            'results': bool(self.results),
            'discussion': bool(self.discussion),
            'conclusion': bool(self.conclusion),
        }
        present = sum(1 for v in sections.values() if v)
        total = len(sections)
        return {
            'sections': sections,
            'completeness_rate': present / total,
            'present_count': present,
            'total_count': total,
            'missing': [k for k, v in sections.items() if not v]
        }


class PaperTextParser:
    """论文文本解析器"""

    # IMRaD章节标题关键词（中英文）
    SECTION_KEYWORDS = {
        'abstract': [
            'abstract', 'summary', '摘要', '提要',
            'background', 'objective', 'aim', 'purpose', '目的',
        ],
        'introduction': [
            'introduction', 'background', 'intro', '引言', '前言', '背景',
        ],
        'methods': [
            'methods', 'methodology', 'materials and methods', 'experimental',
            'patients and methods', 'subjects and methods',
            '方法', '材料与方法', '对象与方法', '实验方法', '研究方法',
            'method', 'material',
        ],
        'results': [
            'results', 'findings', '结果', '研究发现', '主要结果',
        ],
        'discussion': [
            'discussion', 'discussions', '讨论', '结果讨论',
        ],
        'conclusion': [
            'conclusion', 'conclusions', '总结', '结论',
        ],
        'references': [
            'references', 'bibliography', 'literature cited',
            '参考文献', '文献', '引用文献',
        ],
        'acknowledgments': [
            'acknowledgments', 'acknowledgements', 'funding', '致谢', '基金',
        ],
        'ethics': [
            'ethics', 'ethical', 'declaration', 'conflicts of interest',
            'competing interests', '伦理', '利益冲突', '声明',
        ],
    }

    # 研究设计类型识别关键词
    DESIGN_KEYWORDS = {
        StudyDesignType.RCT: [
            'randomized', 'randomised', 'randomization', 'randomisation',
            'double-blind', 'single-blind', 'placebo-controlled',
            '随机', '双盲', '单盲', '安慰剂对照', ' RCT ', 'clinical trial',
        ],
        StudyDesignType.COHORT: [
            'cohort', 'prospective', 'retrospective', 'follow-up',
            '队列', '前瞻性', '回顾性', '随访',
        ],
        StudyDesignType.CASE_CONTROL: [
            'case-control', 'case control', 'matched',
            '病例对照', '配对',
        ],
        StudyDesignType.CROSS_SECTIONAL: [
            'cross-sectional', 'cross sectional', 'prevalence',
            '横断面', '现况', '患病率',
        ],
        StudyDesignType.META_ANALYSIS: [
            'meta-analysis', 'meta analysis', 'systematic review',
            'meta分析', '系统评价', '荟萃分析',
        ],
        StudyDesignType.CASE_SERIES: [
            'case report', 'case series', '病例报告', '病例系列',
        ],
        StudyDesignType.BASIC_RESEARCH: [
            'in vitro', 'in vivo', 'animal model', 'cell line',
            'mechanism', 'pathway', 'knockout', 'transgenic',
            '体外', '体内', '动物模型', '细胞系', '机制', '通路',
        ],
    }

    # 统计方法关键词
    STAT_METHODS_KEYWORDS = [
        't-test', 'chi-square', 'chi-squared', 'fisher exact',
        'anova', 'ancova', 'mann-whitney', 'kruskal-wallis',
        'logistic regression', 'cox regression', 'kaplan-meier',
        'linear regression', 'multivariate', 'univariate',
        'survival analysis', 'log-rank', 'hazard ratio',
        'propensity score', 'mixed effects', 'generalized estimating',
        't检验', '卡方检验', '方差分析', '协方差分析',
        'logistic回归', 'Cox回归', '生存分析', 'Kaplan-Meier',
        '倾向评分', '多元回归', '线性回归',
    ]

    def __init__(self):
        pass

    def parse(self, text: str) -> ParsedPaper:
        """
        解析论文文本

        Args:
            text: 论文全文文本

        Returns:
            ParsedPaper对象
        """
        paper = ParsedPaper()

        # 1. 预处理
        cleaned_text = self._preprocess(text)

        # 2. 提取元数据
        paper.title = self._extract_title(cleaned_text)
        paper.authors = self._extract_authors(cleaned_text)
        paper.doi = self._extract_doi(cleaned_text)
        paper.pmid = self._extract_pmid(cleaned_text)

        # 3. 识别IMRaD章节
        sections = self._split_sections(cleaned_text)
        paper.abstract = sections.get('abstract', '')
        paper.introduction = sections.get('introduction', '')
        paper.methods = sections.get('methods', '')
        paper.results = sections.get('results', '')
        paper.discussion = sections.get('discussion', '')
        paper.conclusion = sections.get('conclusion', '')
        paper.references = self._extract_references(sections.get('references', ''))
        paper.acknowledgments = sections.get('acknowledgments', '')

        # 4. 提取伦理与利益冲突声明
        ethics_text = sections.get('ethics', '')
        paper.ethics_statement = self._extract_ethics(ethics_text)
        paper.conflicts_of_interest = self._extract_conflicts(ethics_text)
        paper.funding = self._extract_funding(ethics_text)

        # 5. 提取关键词
        paper.keywords = self._extract_keywords(cleaned_text, paper.abstract)

        # 6. 识别研究设计
        paper.study_design = self._identify_study_design(paper.methods, paper.title)

        # 7. 提取统计信息
        stats = self._extract_statistics(paper.results + paper.methods)
        paper.sample_size = stats['sample_size']
        paper.p_values = stats['p_values']
        paper.confidence_intervals = stats['confidence_intervals']
        paper.effect_sizes = stats['effect_sizes']
        paper.statistical_methods = stats['statistical_methods']

        return paper

    def _preprocess(self, text: str) -> str:
        """文本预处理"""
        # 统一换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # 去除多余空行但保留段落结构
        lines = text.split('\n')
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            stripped = line.strip()
            if stripped:
                cleaned_lines.append(stripped)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        return '\n'.join(cleaned_lines)

    def _extract_title(self, text: str) -> str:
        """提取标题"""
        lines = text.split('\n')
        # 标题通常是前几行中非空的、较长的行
        for line in lines[:10]:
            line = line.strip()
            # 排除作者行（通常包含逗号或数字标记）
            if len(line) > 30 and len(line) < 300:
                if not re.match(r'^[\d\s,;]+$', line):
                    if 'university' not in line.lower() and 'hospital' not in line.lower():
                        if 'doi:' not in line.lower() and 'pmid' not in line.lower():
                            return line
        return ""

    def _extract_authors(self, text: str) -> List[str]:
        """提取作者列表"""
        authors = []
        lines = text.split('\n')[:15]
        for line in lines:
            # 匹配 "作者1, 作者2, 作者3" 或 "作者1; 作者2" 格式
            if re.search(r'[,;]\s*[A-Z][a-z]+', line) and len(line) < 500:
                # 分割作者
                parts = re.split(r'[,;]\s*', line)
                for part in parts:
                    part = part.strip()
                    if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$', part):
                        if len(part) > 3 and len(part) < 50:
                            authors.append(part)
                if authors:
                    break
        return authors[:20]  # 最多20个作者

    def _extract_doi(self, text: str) -> Optional[str]:
        """提取DOI"""
        match = re.search(r'10\.\d{4,}/[^\s\])]+', text)
        return match.group(0) if match else None

    def _extract_pmid(self, text: str) -> Optional[str]:
        """提取PubMed ID"""
        match = re.search(r'PMID:\s*(\d+)', text, re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r'PubMed\s*ID:\s*(\d+)', text, re.IGNORECASE)
        return match.group(1) if match else None

    def _split_sections(self, text: str) -> Dict[str, str]:
        """
        将文本分割为IMRaD章节
        """
        sections = {}
        lines = text.split('\n')

        # 构建章节边界检测器
        section_boundaries = []
        for i, line in enumerate(lines):
            line_lower = line.strip().lower()
            # 检查是否是章节标题行
            for section_name, keywords in self.SECTION_KEYWORDS.items():
                for kw in keywords:
                    # 标题行特征：行首匹配、简短、可能带编号
                    patterns = [
                        rf'^{re.escape(kw)}[\s\d:：\.]*$',
                        rf'^\d+[\.\s]+{re.escape(kw)}[\s\d:：\.]*$',
                        rf'^{re.escape(kw)}[\s\d:：\.]{{0,3}}$',
                    ]
                    for pattern in patterns:
                        if re.match(pattern, line_lower, re.IGNORECASE):
                            section_boundaries.append((i, section_name, line))
                            break

        # 按行号排序，去重（同一行只保留第一个匹配的章节）
        section_boundaries.sort(key=lambda x: x[0])
        seen_positions = set()
        filtered_boundaries = []
        for pos, name, line in section_boundaries:
            if pos not in seen_positions:
                seen_positions.add(pos)
                filtered_boundaries.append((pos, name, line))

        # 提取各章节内容
        for idx, (pos, name, _) in enumerate(filtered_boundaries):
            start = pos + 1
            if idx + 1 < len(filtered_boundaries):
                end = filtered_boundaries[idx + 1][0]
            else:
                end = len(lines)
            content = '\n'.join(lines[start:end]).strip()
            # 如果该章节已存在，保留较长的版本
            if name not in sections or len(content) > len(sections[name]):
                sections[name] = content

        return sections

    def _extract_references(self, text: str) -> List[str]:
        """从参考文献章节提取单条引用"""
        if not text:
            return []

        references = []
        # 尝试按编号分割
        numbered = re.split(r'\n\s*\[?\d+\]?[\.\s]+', text)
        if len(numbered) > 2:
            references = [r.strip() for r in numbered[1:] if len(r.strip()) > 20]
        else:
            # 尝试按换行分割
            lines = text.split('\n')
            current = []
            for line in lines:
                line = line.strip()
                if not line:
                    if current:
                        ref = ' '.join(current)
                        if len(ref) > 30:
                            references.append(ref)
                        current = []
                else:
                    current.append(line)
            if current:
                ref = ' '.join(current)
                if len(ref) > 30:
                    references.append(ref)

        return references[:100]  # 最多100条

    def _extract_ethics(self, text: str) -> str:
        """提取伦理声明"""
        ethics_keywords = ['ethic', 'irb', 'institutional review', '伦理委员会', '伦理审查']
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in ethics_keywords):
                return line.strip()
        return ""

    def _extract_conflicts(self, text: str) -> str:
        """提取利益冲突声明"""
        conflict_keywords = ['conflict', 'competing', 'disclosure', '利益冲突', '竞争利益']
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in conflict_keywords):
                return line.strip()
        return ""

    def _extract_funding(self, text: str) -> str:
        """提取基金资助信息"""
        funding_keywords = ['funding', 'grant', 'supported by', '资助', '基金', ' supported']
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in funding_keywords):
                return line.strip()
        return ""

    def _extract_keywords(self, text: str, abstract: str) -> List[str]:
        """提取关键词"""
        keywords = []
        # 方法1: 查找显式声明的关键词
        kw_match = re.search(r'[Kk]eywords?[:：]\s*(.+?)(?:\n|\r|$)', text)
        if kw_match:
            kw_text = kw_match.group(1)
            keywords = [k.strip() for k in re.split(r'[,;；]', kw_text) if len(k.strip()) > 1]

        # 方法2: 如果关键词太少，从摘要中提取高频医学术语
        if len(keywords) < 3 and abstract:
            common_medical_terms = [
                'diabetes', 'hypertension', 'cancer', 'tumor', 'cardiovascular',
                'stroke', 'infection', 'inflammation', 'depression', 'anxiety',
                'surgery', 'therapy', 'treatment', 'diagnosis', 'prognosis',
                'randomized', 'cohort', 'meta-analysis', 'clinical trial',
                'mortality', 'survival', 'risk factor', 'biomarker',
                '糖尿病', '高血压', '肿瘤', '心血管', '卒中', '感染',
                '炎症', '抑郁', '焦虑', '手术', '治疗', '诊断', '预后',
            ]
            abstract_lower = abstract.lower()
            for term in common_medical_terms:
                if term in abstract_lower and term not in [k.lower() for k in keywords]:
                    keywords.append(term)
                    if len(keywords) >= 8:
                        break

        return keywords[:15]

    def _identify_study_design(self, methods_text: str, title: str) -> StudyDesignType:
        """识别研究设计类型"""
        combined = (methods_text + " " + title).lower()

        scores = {}
        for design, keywords in self.DESIGN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in combined)
            if score > 0:
                scores[design] = score

        if scores:
            # 返回得分最高的设计类型
            return max(scores, key=scores.get)

        return StudyDesignType.UNKNOWN

    def _extract_statistics(self, text: str) -> Dict[str, Any]:
        """提取统计学信息"""
        result = {
            'sample_size': None,
            'p_values': [],
            'confidence_intervals': [],
            'effect_sizes': [],
            'statistical_methods': [],
        }

        if not text:
            return result

        text_lower = text.lower()

        # 1. 样本量
        sample_patterns = [
            r'(?:included|enrolled|recruited|sample size|n\s*=)\s*(\d{2,5})\s*(?:patients|subjects|participants|cases|individuals)?',
            r'(?:total\s+of\s+)(\d{2,5})\s*(?:patients|subjects|participants)',
            r'纳入了?\s*(\d{2,5})\s*例',
            r'共\s*(\d{2,5})\s*例',
        ]
        for pattern in sample_patterns:
            match = re.search(pattern, text_lower)
            if match:
                result['sample_size'] = int(match.group(1))
                break

        # 2. P值
        p_patterns = [
            r'p\s*[<>=]\s*0?\.\d+',
            r'p\s*=\s*0?\.\d+',
            r'p值\s*[<>=]\s*0?\.\d+',
        ]
        for pattern in p_patterns:
            matches = re.findall(pattern, text_lower)
            result['p_values'].extend(matches)
        result['p_values'] = list(set(result['p_values']))[:20]  # 去重，最多20个

        # 3. 置信区间
        ci_patterns = [
            r'95%\s*ci\s*[:，]\s*[^\s,;]+',
            r'95%\s*confidence interval\s*[:，]\s*[^\s,;]+',
            r'95%\s*可信区间\s*[:，]\s*[^\s,;]+',
        ]
        for pattern in ci_patterns:
            matches = re.findall(pattern, text_lower)
            result['confidence_intervals'].extend(matches)
        result['confidence_intervals'] = list(set(result['confidence_intervals']))[:10]

        # 4. 效应量 (HR, OR, RR, MD等)
        effect_patterns = [
            r'(?:hr|or|rr|md|rd|arr|nnt)\s*[\(=]\s*\d+\.?\d*',
            r'hazard ratio\s*[:，=]\s*\d+\.?\d*',
            r'odds ratio\s*[:，=]\s*\d+\.?\d*',
            r'risk ratio\s*[:，=]\s*\d+\.?\d*',
            r'mean difference\s*[:，=]\s*[\-]?\d+\.?\d*',
        ]
        for pattern in effect_patterns:
            matches = re.findall(pattern, text_lower)
            result['effect_sizes'].extend(matches)
        result['effect_sizes'] = list(set(result['effect_sizes']))[:10]

        # 5. 统计方法
        for method in self.STAT_METHODS_KEYWORDS:
            if method.lower() in text_lower:
                result['statistical_methods'].append(method)
        result['statistical_methods'] = list(set(result['statistical_methods']))

        return result

    def parse_from_file(self, file_path: str) -> ParsedPaper:
        """
        从文件解析论文

        Args:
            file_path: 文件路径 (.txt)

        Returns:
            ParsedPaper对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return self.parse(text)

    def get_parsing_summary(self, paper: ParsedPaper) -> str:
        """生成解析摘要报告"""
        imrad = paper.get_imrad_completeness()

        summary = f"""
{'='*60}
论文解析报告
{'='*60}

📄 标题: {paper.title[:80]}{'...' if len(paper.title) > 80 else ''}
👥 作者: {', '.join(paper.authors[:5])}{' 等' if len(paper.authors) > 5 else ''}
🏷️ 关键词: {', '.join(paper.keywords[:8])}
📋 研究设计: {paper.study_design.value}

---

📊 IMRaD结构完整性: {imrad['completeness_rate']*100:.0f}% ({imrad['present_count']}/{imrad['total_count']})
"""
        for section, present in imrad['sections'].items():
            status = '✅' if present else '❌'
            summary += f"   {status} {section.capitalize():15s}\n"

        if imrad['missing']:
            summary += f"\n⚠️ 缺失章节: {', '.join(imrad['missing'])}\n"

        summary += f"""
---

📈 统计信息提取:
"""
        if paper.sample_size:
            summary += f"   • 样本量: {paper.sample_size}\n"
        if paper.p_values:
            summary += f"   • P值: {len(paper.p_values)} 个 ({', '.join(paper.p_values[:3])}{'...' if len(paper.p_values) > 3 else ''})\n"
        if paper.confidence_intervals:
            summary += f"   • 置信区间: {len(paper.confidence_intervals)} 个\n"
        if paper.effect_sizes:
            summary += f"   • 效应量: {len(paper.effect_sizes)} 个 ({', '.join(paper.effect_sizes[:3])}{'...' if len(paper.effect_sizes) > 3 else ''})\n"
        if paper.statistical_methods:
            summary += f"   • 统计方法: {', '.join(paper.statistical_methods[:5])}{'...' if len(paper.statistical_methods) > 5 else ''}\n"

        summary += f"""
---

📚 参考文献: {len(paper.references)} 条
🔖 DOI: {paper.doi or '未提取'}
📰 PMID: {paper.pmid or '未提取'}
"""
        return summary
