"""
论文质量评分预测系统
Paper Quality Evaluation & Journal Recommendation System
"""

import json
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class JournalTier(Enum):
    """期刊分区"""
    TOP = "顶刊 (IF>20)"
    Q1 = "Q1 (IF 10-20)"
    Q2 = "Q2 (IF 5-10)"
    Q3 = "Q3 (IF 2-5)"
    Q4 = "Q4 (IF<2)"


class StudyTypeWeights:
    """不同研究类型的差异化评分权重"""

    @staticmethod
    def get_weights(study_type: str = "clinical") -> List[Tuple[str, float]]:
        """
        获取指定研究类型的评分权重

        Args:
            study_type: 研究类型标识
                - 'rct': 随机对照试验
                - 'observational': 观察性研究
                - 'meta': Meta分析/系统评价
                - 'basic': 基础研究
                - 'case_report': 病例报告
                - 'clinical': 默认临床研究

        Returns:
            维度名称和权重的列表
        """
        weights_map = {
            "rct": [
                ("创新程度", 0.18),
                ("方法学质量", 0.25),  # RCT方法学要求更高
                ("结果呈现", 0.15),
                ("讨论深度", 0.12),
                ("写作规范性", 0.10),
                ("参考文献质量", 0.10),
                ("结构完整性", 0.05),
                ("伦理合规性", 0.05),
            ],
            "observational": [
                ("创新程度", 0.20),
                ("方法学质量", 0.22),  # 偏倚控制关键
                ("结果呈现", 0.15),
                ("讨论深度", 0.18),  # 局限性讨论更重要
                ("写作规范性", 0.10),
                ("参考文献质量", 0.10),
                ("结构完整性", 0.03),
                ("伦理合规性", 0.02),
            ],
            "meta": [
                ("创新程度", 0.15),
                ("方法学质量", 0.25),  # 检索策略、质量评价
                ("结果呈现", 0.20),  # 森林图、敏感性分析
                ("讨论深度", 0.15),
                ("写作规范性", 0.10),
                ("参考文献质量", 0.10),
                ("结构完整性", 0.03),
                ("伦理合规性", 0.02),
            ],
            "basic": [
                ("创新程度", 0.25),  # 基础研究创新更重要
                ("方法学质量", 0.20),
                ("结果呈现", 0.15),
                ("讨论深度", 0.15),
                ("写作规范性", 0.10),
                ("参考文献质量", 0.10),
                ("结构完整性", 0.03),
                ("伦理合规性", 0.02),
            ],
            "case_report": [
                ("创新程度", 0.25),  # 罕见病例价值
                ("方法学质量", 0.10),
                ("结果呈现", 0.15),
                ("讨论深度", 0.20),  # 文献复习深度
                ("写作规范性", 0.15),
                ("参考文献质量", 0.10),
                ("结构完整性", 0.03),
                ("伦理合规性", 0.02),
            ],
            "clinical": [
                ("创新程度", 0.20),
                ("方法学质量", 0.20),
                ("结果呈现", 0.15),
                ("讨论深度", 0.15),
                ("写作规范性", 0.10),
                ("参考文献质量", 0.10),
                ("结构完整性", 0.05),
                ("伦理合规性", 0.05),
            ]
        }

        # 规范化study_type
        study_type_lower = study_type.lower()
        type_mapping = {
            'rct': 'rct', 'randomized': 'rct', 'randomised': 'rct', '临床试验': 'rct',
            'observational': 'observational', 'cohort': 'observational', 'case-control': 'observational',
            '队列': 'observational', '病例对照': 'observational', '横断面': 'observational',
            'meta': 'meta', 'systematic review': 'meta', 'meta-analysis': 'meta',
            '系统评价': 'meta', 'meta分析': 'meta',
            'basic': 'basic', '基础研究': 'basic', 'mechanism': 'basic', '机制': 'basic',
            'case report': 'case_report', '病例报告': 'case_report', 'case series': 'case_report',
            'clinical': 'clinical', '临床研究': 'clinical'
        }

        mapped_type = type_mapping.get(study_type_lower, 'clinical')
        return weights_map.get(mapped_type, weights_map['clinical'])


@dataclass
class EvaluationDimension:
    """评分维度"""
    name: str
    weight: float  # 权重 0-1
    score: float  # 得分 0-100
    feedback: str  # 评价和建议


@dataclass
class JournalRecommendation:
    """期刊推荐结果"""
    name: str
    impact_factor: float
    tier: JournalTier
    field_match_score: float
    acceptance_rate_prediction: float  # 预测接收率
    recommendation_level: int  # 1-5，5为最高推荐
    pros: List[str]
    cons: List[str]


class PaperQualityScorer:
    """论文质量评分器"""

    def __init__(self):
        self.dimensions = [
            ("创新程度", 0.20),  # 创新性权重最高
            ("方法学质量", 0.20),  # 研究设计和统计方法
            ("结果呈现", 0.15),  # 结果展示和图表质量
            ("讨论深度", 0.15),  # 讨论的深度和完整性
            ("写作规范性", 0.10),  # 语言和格式规范
            ("参考文献质量", 0.10),  # 参考文献的相关性和时效性
            ("结构完整性", 0.05),  # IMRaD结构完整性
            ("伦理合规性", 0.05),  # 伦理声明和合规性
        ]

    def evaluate(self, paper_content: Dict[str, Any],
                 study_type: str = "clinical") -> Dict[str, Any]:
        """
        全面评估论文质量

        Args:
            paper_content: 论文内容字典，包含各章节内容
            study_type: 研究类型，用于差异化权重 (rct/observational/meta/basic/case_report/clinical)

        Returns:
            完整的评估报告
        """
        # 根据研究类型获取差异化权重
        type_weights = StudyTypeWeights.get_weights(study_type)
        weight_map = {name: weight for name, weight in type_weights}

        scores = []

        # 1. 创新程度评估
        innovation_score = self._evaluate_innovation(paper_content)
        innovation_score.weight = weight_map.get("创新程度", 0.20)
        scores.append(innovation_score)

        # 2. 方法学质量评估
        methodology_score = self._evaluate_methodology(paper_content)
        methodology_score.weight = weight_map.get("方法学质量", 0.20)
        scores.append(methodology_score)

        # 3. 结果呈现评估
        results_score = self._evaluate_results(paper_content)
        results_score.weight = weight_map.get("结果呈现", 0.15)
        scores.append(results_score)

        # 4. 讨论深度评估
        discussion_score = self._evaluate_discussion(paper_content)
        discussion_score.weight = weight_map.get("讨论深度", 0.15)
        scores.append(discussion_score)

        # 5. 写作规范性评估
        writing_score = self._evaluate_writing_quality(paper_content)
        writing_score.weight = weight_map.get("写作规范性", 0.10)
        scores.append(writing_score)

        # 6. 参考文献质量评估
        references_score = self._evaluate_references(paper_content)
        references_score.weight = weight_map.get("参考文献质量", 0.10)
        scores.append(references_score)

        # 7. 结构完整性评估
        structure_score = self._evaluate_structure(paper_content)
        structure_score.weight = weight_map.get("结构完整性", 0.05)
        scores.append(structure_score)

        # 8. 伦理合规性评估
        ethics_score = self._evaluate_ethics(paper_content)
        ethics_score.weight = weight_map.get("伦理合规性", 0.05)
        scores.append(ethics_score)

        # 计算加权总分
        total_score = sum(s.score * s.weight for s in scores)

        # 生成总体评价
        overall_feedback = self._generate_overall_feedback(total_score, scores)

        # 生成改进建议
        improvement_suggestions = self._generate_improvement_suggestions(scores)

        return {
            "total_score": round(total_score, 1),
            "grade": self._score_to_grade(total_score),
            "dimensions": [
                {
                    "name": s.name,
                    "score": round(s.score, 1),
                    "weight": s.weight,
                    "weighted_score": round(s.score * s.weight, 1),
                    "feedback": s.feedback
                }
                for s in scores
            ],
            "overall_feedback": overall_feedback,
            "improvement_suggestions": improvement_suggestions,
            "publication_potential": self._predict_publication_potential(total_score),
            "recommended_tier": self._predict_recommended_tier(total_score)
        }

    def _evaluate_innovation(self, paper: Dict[str, Any]) -> EvaluationDimension:
        """评估创新程度"""
        score = 50.0  # 默认基础分
        feedback_points = []

        abstract = paper.get('abstract', '')
        introduction = paper.get('introduction', '')
        title = paper.get('title', '')

        # 1. 检查创新点明确表述
        innovation_keywords = ['novel', 'new', '首次', '创新', '首创', 'pioneer',
                               'innovative', 'groundbreaking', 'unprecedented']
        innovation_mentioned = any(k in abstract.lower() or k in introduction.lower()
                                   for k in innovation_keywords)

        if innovation_mentioned:
            score += 15
            feedback_points.append("✓ 明确表述了研究创新性")
        else:
            feedback_points.append("✗ 建议在摘要和引言中明确阐述创新点")

        # 2. 检查研究缺口阐述
        gap_keywords = ['gap', 'lack', 'limited', 'few studies', 'no study',
                        '研究空白', '尚未报道', '鲜有研究', '不足']
        gap_identified = any(k in introduction.lower() for k in gap_keywords)

        if gap_identified:
            score += 10
            feedback_points.append("✓ 明确识别了研究缺口")
        else:
            feedback_points.append("✗ 建议在引言中明确阐述研究空白")

        # 3. 检查原创性声明
        hypothesis_keywords = ['hypothesis', 'aim', 'objective', '目的', '假设', '目标']
        has_clear_aim = any(k in abstract.lower() for k in hypothesis_keywords)

        if has_clear_aim:
            score += 5
            feedback_points.append("✓ 研究目的明确")

        # 4. 标题吸引力
        if len(title) > 10 and len(title) < 50:
            score += 5
            feedback_points.append("✓ 标题长度合适")
        elif len(title) >= 50:
            feedback_points.append("✗ 标题建议精简到50字以内")

        # 5. 摘要质量
        abstract_structure = self._check_abstract_structure(abstract)
        if abstract_structure['complete']:
            score += 15
            feedback_points.append("✓ 结构化摘要完整，包含目的、方法、结果、结论")
        else:
            score += abstract_structure['score']
            feedback_points.append(f"✗ 摘要完整性: {abstract_structure['missing']}")

        # 确保分数不超过100
        score = min(score, 100)

        return EvaluationDimension(
            name="创新程度",
            weight=0.20,
            score=score,
            feedback="\n".join(feedback_points)
        )

    def _check_abstract_structure(self, abstract: str) -> Dict[str, Any]:
        """检查摘要结构完整性"""
        elements = {
            'background': ['背景', '目的', 'background', 'objective', 'aim'],
            'methods': ['方法', '方法', 'method', 'methodology'],
            'results': ['结果', '结果', 'result', 'outcome', 'finding'],
            'conclusion': ['结论', '结论', 'conclusion', 'conclude']
        }

        found = []
        missing = []

        for elem, keywords in elements.items():
            if any(k in abstract.lower() for k in keywords):
                found.append(elem)
            else:
                missing.append(elem)

        score = (len(found) / len(elements)) * 15

        return {
            'complete': len(missing) == 0,
            'score': score,
            'missing': missing,
            'found': found
        }

    def _evaluate_methodology(self, paper: Dict[str, Any]) -> EvaluationDimension:
        """评估方法学质量"""
        score = 40.0
        feedback_points = []

        methods = paper.get('methods', '')

        # 1. 研究设计类型
        design_keywords = {
            'RCT': ['randomized', 'randomised', '随机', 'RCT', 'random'],
            'Cohort': ['cohort', '队列', 'longitudinal'],
            'Case-Control': ['case-control', '病例对照'],
            'Systematic Review': ['systematic review', 'meta-analysis', '系统评价', 'meta分析'],
            'Observational': ['cross-sectional', '横断面', 'observational']
        }

        design_level = 0
        identified_design = []

        for design, keywords in design_keywords.items():
            if any(k in methods.lower() for k in keywords):
                identified_design.append(design)
                if design == 'RCT':
                    design_level = 25
                elif design == 'Systematic Review':
                    design_level = 22
                elif design == 'Cohort':
                    design_level = 20
                elif design == 'Case-Control':
                    design_level = 18
                else:
                    design_level = 15
                break

        if design_level > 0:
            score += design_level
            feedback_points.append(f"✓ 识别研究设计: {', '.join(identified_design)}")
        else:
            feedback_points.append("✗ 建议明确描述研究设计类型")

        # 2. 样本量说明
        sample_size_keywords = ['sample size', 'power calculation', '样本量', 'power analysis',
                                'power calculation']
        has_sample_size = any(k in methods.lower() for k in sample_size_keywords)

        if has_sample_size:
            score += 15
            feedback_points.append("✓ 包含样本量计算/说明")
        else:
            feedback_points.append("✗ 建议补充样本量计算依据")

        # 3. 统计方法描述
        stats_keywords = ['statistic', 'analysis', 'regression', 't-test', 'chi-square',
                          'logistic', 'cox', 'kaplan-meier', '统计', '分析', '回归']
        stats_count = sum(1 for k in stats_keywords if k in methods.lower())

        if stats_count >= 3:
            score += 15
            feedback_points.append("✓ 统计方法描述充分")
        elif stats_count >= 1:
            score += 8
            feedback_points.append("○ 统计方法描述基本充分")
        else:
            feedback_points.append("✗ 建议详细描述统计分析方法")

        # 4. 伦理声明
        ethics_keywords = ['ethic', 'informed consent', 'irb', '伦理', '知情同意',
                            '伦理委员会', 'approval']
        has_ethics = any(k in methods.lower() for k in ethics_keywords)

        if has_ethics:
            score += 5
            feedback_points.append("✓ 包含伦理声明")
        else:
            feedback_points.append("✗ 建议补充伦理审查和知情同意声明")

        score = min(score, 100)

        return EvaluationDimension(
            name="方法学质量",
            weight=0.20,
            score=score,
            feedback="\n".join(feedback_points)
        )

    def _evaluate_results(self, paper: Dict[str, Any]) -> EvaluationDimension:
        """评估结果呈现质量"""
        score = 50.0
        feedback_points = []

        results = paper.get('results', '')

        # 1. 结果结构化程度
        section_keywords = ['table', 'figure', '表', '图', 'figure', 'chart']
        section_count = sum(1 for k in section_keywords if k in results.lower())

        if section_count >= 5:
            score += 20
            feedback_points.append("✓ 图表丰富，结果展示充分")
        elif section_count >= 2:
            score += 12
            feedback_points.append("✓ 图表基本充分")
        else:
            feedback_points.append("✗ 建议增加图表以直观展示结果")

        # 2. 统计学显著性报告
        p_value_keywords = ['p<', 'p =', 'p value', 'p值', 'significant', '显著性',
                            'statistical significance']
        has_p_value = any(k in results.lower() for k in p_value_keywords)

        if has_p_value:
            score += 15
            feedback_points.append("✓ 报告了统计学显著性")
        else:
            feedback_points.append("✗ 建议报告具体的统计量和P值")

        # 3. 置信区间报告
        ci_keywords = ['95% ci', 'confidence interval', '可信区间', '置信区间']
        has_ci = any(k in results.lower() for k in ci_keywords)

        if has_ci:
            score += 10
            feedback_points.append("✓ 报告了置信区间")
        else:
            feedback_points.append("✗ 建议报告效应量和置信区间")

        # 4. 结果描述的客观性
        subjective_words = ['amazing', 'incredible', 'wonderful', 'fantastic',
                            '惊人', '难以置信', '太棒了']
        has_subjective = any(k in results.lower() for k in subjective_words)

        if not has_subjective:
            score += 5
            feedback_points.append("✓ 结果描述客观")
        else:
            feedback_points.append("✗ 建议使用更客观的表述描述结果")

        score = min(score, 100)

        return EvaluationDimension(
            name="结果呈现",
            weight=0.15,
            score=score,
            feedback="\n".join(feedback_points)
        )

    def _evaluate_discussion(self, paper: Dict[str, Any]) -> EvaluationDimension:
        """评估讨论深度"""
        score = 45.0
        feedback_points = []

        discussion = paper.get('discussion', '')

        # 1. 与现有研究比较
        comparison_keywords = ['consistent with', 'in line with', 'similar to',
                               'compared with', 'previous study', '与...一致',
                               '与...相比', '现有研究']
        comparison_count = sum(1 for k in comparison_keywords if k in discussion.lower())

        if comparison_count >= 5:
            score += 20
            feedback_points.append("✓ 与现有研究比较充分")
        elif comparison_count >= 2:
            score += 12
            feedback_points.append("✓ 有一定的文献比较")
        else:
            feedback_points.append("✗ 建议增加与现有研究的比较讨论")

        # 2. 研究局限性分析
        limitation_keywords = ['limitation', 'weakness', 'drawback', '局限',
                               '不足', 'caveat']
        has_limitation = any(k in discussion.lower() for k in limitation_keywords)

        if has_limitation:
            score += 15
            feedback_points.append("✓ 分析了研究局限性")
        else:
            feedback_points.append("✗ 建议增加研究局限性讨论")

        # 3. 临床意义/实践启示
        implication_keywords = ['clinical implication', 'clinical practice', 'practice',
                                'implication', '意义', '启示', '临床实践']
        has_implication = any(k in discussion.lower() for k in implication_keywords)

        if has_implication:
            score += 10
            feedback_points.append("✓ 阐述了临床/实践意义")
        else:
            feedback_points.append("✗ 建议阐述研究结果的实际意义")

        # 4. 未来研究方向
        future_keywords = ['future research', 'future study', 'further study',
                           '未来研究', '进一步研究']
        has_future = any(k in discussion.lower() for k in future_keywords)

        if has_future:
            score += 10
            feedback_points.append("✓ 指出了未来研究方向")
        else:
            feedback_points.append("✗ 建议提出未来研究方向")

        score = min(score, 100)

        return EvaluationDimension(
            name="讨论深度",
            weight=0.15,
            score=score,
            feedback="\n".join(feedback_points)
        )

    def _evaluate_writing_quality(self, paper: Dict[str, Any]) -> EvaluationDimension:
        """评估写作规范性"""
        score = 60.0
        feedback_points = []

        full_text = str(paper)

        # 1. 缩写规范检查
        abbreviation_issues = self._check_abbreviations(full_text)
        if not abbreviation_issues:
            score += 15
            feedback_points.append("✓ 缩写使用规范")
        else:
            score += 5
            feedback_points.append(f"✗ 发现{len(abbreviation_issues)}个缩写可能未定义: {', '.join(abbreviation_issues[:3])}")

        # 2. 术语一致性
        # 简单检查常见术语
        feedback_points.append("○ 术语一致性: 建议全文统一术语使用")
        score += 5

        # 3. 格式规范性
        feedback_points.append("○ 建议检查目标期刊的格式要求")
        score += 10

        # 4. 英文写作质量（如适用）
        # 简单的长度和复杂度评估
        avg_sentence_length = len(full_text.split()) / max(1, len(full_text.split('.')))
        if 15 <= avg_sentence_length <= 25:
            score += 10
            feedback_points.append("✓ 句子长度适中")
        else:
            feedback_points.append("○ 建议调整句子长度，提高可读性")

        score = min(score, 100)

        return EvaluationDimension(
            name="写作规范性",
            weight=0.10,
            score=score,
            feedback="\n".join(feedback_points)
        )

    def _check_abbreviations(self, text: str) -> List[str]:
        """检查缩写是否首次出现时给出全称"""
        issues = []

        # 查找所有大写缩写
        abbreviations = re.findall(r'\b([A-Z]{2,5})\b', text)

        for abbr in set(abbreviations):
            # 检查附近是否有定义格式: xxx (XXX)
            pattern = rf'\([^)]*{abbr}[^)]*\)'
            if not re.search(pattern, text):
                issues.append(abbr)

        return issues[:10]  # 最多返回10个

    def _evaluate_references(self, paper: Dict[str, Any]) -> EvaluationDimension:
        """评估参考文献质量"""
        score = 50.0
        feedback_points = []

        references = paper.get('references', [])
        ref_count = len(references) if isinstance(references, list) else 0

        # 1. 参考文献数量
        if ref_count >= 30:
            score += 20
            feedback_points.append("✓ 参考文献数量充足")
        elif ref_count >= 15:
            score += 12
            feedback_points.append("✓ 参考文献数量基本适当")
        else:
            feedback_points.append("✗ 建议增加参考文献数量")

        # 2. 时效性评估
        years = re.findall(r'\b(19|20)\d{2}\b', str(references))
        if years:
            recent_count = sum(1 for y in years if int(y) >= 2019)  # 近5年
            recent_ratio = recent_count / len(years) if years else 0

            if recent_ratio >= 0.5:
                score += 15
                feedback_points.append(f"✓ 参考文献时效性良好 ({recent_ratio:.0%} 为近5年)")
            elif recent_ratio >= 0.3:
                score += 8
                feedback_points.append(f"○ 参考文献时效性一般 ({recent_ratio:.0%} 为近5年)")
            else:
                feedback_points.append("✗ 建议增加近年文献")

        # 3. 经典文献引用
        # 简单检查: 引用分布较广可能更好
        if years and len(set(years)) >= 5:
            score += 10
            feedback_points.append("✓ 参考文献时间分布合理")

        # 4. 国际文献比例
        # 简单检查非中文字符
        non_chinese_count = sum(1 for ref in references
                               if isinstance(ref, str) and re.search(r'[a-zA-Z]{4,}', ref))
        if ref_count > 0 and non_chinese_count / ref_count >= 0.7:
            score += 5
            feedback_points.append("✓ 国际文献比例适当")

        score = min(score, 100)

        return EvaluationDimension(
            name="参考文献质量",
            weight=0.10,
            score=score,
            feedback="\n".join(feedback_points)
        )

    def _evaluate_structure(self, paper: Dict[str, Any]) -> EvaluationDimension:
        """评估结构完整性"""
        score = 60.0
        feedback_points = []

        # 检查IMRaD各部分是否存在
        required_sections = ['abstract', 'introduction', 'methods', 'results',
                            'discussion', 'references', 'title']

        present_sections = [s for s in required_sections if paper.get(s)]

        completeness = len(present_sections) / len(required_sections)
        score += completeness * 25

        if completeness == 1.0:
            feedback_points.append("✓ IMRaD结构完整")
        else:
            missing = [s for s in required_sections if not paper.get(s)]
            feedback_points.append(f"✗ 缺少以下部分: {', '.join(missing)}")

        # 检查是否有结论部分
        if paper.get('conclusion'):
            score += 10
            feedback_points.append("✓ 包含结论部分")

        # 检查是否有作者信息
        if paper.get('authors'):
            score += 5
            feedback_points.append("✓ 包含作者信息")

        score = min(score, 100)

        return EvaluationDimension(
            name="结构完整性",
            weight=0.05,
            score=score,
            feedback="\n".join(feedback_points)
        )

    def _evaluate_ethics(self, paper: Dict[str, Any]) -> EvaluationDimension:
        """评估伦理合规性"""
        score = 70.0
        feedback_points = []

        methods = paper.get('methods', '')
        full_text = str(paper)

        # 1. 伦理委员会批准声明
        ethics_keywords = ['ethic committee', 'institutional review board', 'irb',
                           '伦理委员会', '伦理审查', 'ethics approval']
        has_ethics = any(k in full_text.lower() for k in ethics_keywords)

        if has_ethics:
            score += 15
            feedback_points.append("✓ 包含伦理委员会批准声明")
        else:
            feedback_points.append("✗ 建议补充伦理审查批准声明")

        # 2. 知情同意声明
        consent_keywords = ['informed consent', '知情同意']
        has_consent = any(k in full_text.lower() for k in consent_keywords)

        if has_consent:
            score += 15
            feedback_points.append("✓ 包含知情同意声明")
        else:
            feedback_points.append("✗ 建议补充知情同意声明")

        score = min(score, 100)

        return EvaluationDimension(
            name="伦理合规性",
            weight=0.05,
            score=score,
            feedback="\n".join(feedback_points)
        )

    def _score_to_grade(self, score: float) -> str:
        """将分数转换为等级"""
        if score >= 90:
            return "A+ (优秀 - 顶刊潜力)"
        elif score >= 85:
            return "A (优秀 - Q1潜力)"
        elif score >= 80:
            return "A- (良好 - Q1/Q2潜力)"
        elif score >= 75:
            return "B+ (中上 - Q2潜力)"
        elif score >= 70:
            return "B (中等 - Q2/Q3潜力)"
        elif score >= 65:
            return "B- (一般 - Q3潜力)"
        elif score >= 60:
            return "C (及格 - Q3/Q4潜力)"
        else:
            return "D (需要重大修改)"

    def _generate_overall_feedback(self, total_score: float, scores: List[EvaluationDimension]) -> str:
        """生成总体反馈"""
        if total_score >= 85:
            return ("论文质量优秀，各方面表现均衡，具有很高的发表潜力。"
                    "建议选择Q1区甚至顶刊投稿。")
        elif total_score >= 75:
            return ("论文质量良好，具有明显的优势但也存在一些可改进之处。"
                    "建议针对性修改后投Q1/Q2区期刊。")
        elif total_score >= 65:
            return ("论文质量中等，有一定基础但需要较多修改。"
                    "建议完善方法学和讨论部分后投稿Q2/Q3区期刊。")
        else:
            return ("论文需要重大修改。建议重点加强创新点阐述、"
                    "方法学质量和结果呈现的规范性。")

    def _generate_improvement_suggestions(self, scores: List[EvaluationDimension]) -> List[Dict[str, Any]]:
        """生成改进建议"""
        suggestions = []

        # 找出得分最低的3个维度
        sorted_scores = sorted(scores, key=lambda x: x.score)

        for s in sorted_scores[:3]:
            if s.score < 70:
                suggestions.append({
                    'dimension': s.name,
                    'score': s.score,
                    'priority': 'high' if s.score < 60 else 'medium',
                    'suggestion': f"建议重点改进{s.name}: 分析具体不足并针对性修改"
                })

        return suggestions

    def _predict_publication_potential(self, total_score: float) -> Dict[str, Any]:
        """预测发表潜力"""
        if total_score >= 85:
            potential = "高"
            timeline = "预计6-12个月接收（顺利情况下）"
            acceptance_rate = "40-60%（目标期刊匹配良好的情况下）"
        elif total_score >= 75:
            potential = "较高"
            timeline = "预计9-15个月接收"
            acceptance_rate = "30-45%"
        elif total_score >= 65:
            potential = "中等"
            timeline = "预计12-18个月，可能需要1-2次大修"
            acceptance_rate = "20-35%"
        else:
            potential = "较低"
            timeline = "需要重大修改后再评估"
            acceptance_rate = "<20%"

        return {
            'level': potential,
            'estimated_timeline': timeline,
            'predicted_acceptance_rate': acceptance_rate
        }

    def _predict_recommended_tier(self, total_score: float) -> str:
        """预测推荐期刊分区"""
        if total_score >= 90:
            return JournalTier.TOP.value
        elif total_score >= 80:
            return JournalTier.Q1.value
        elif total_score >= 70:
            return JournalTier.Q2.value
        elif total_score >= 60:
            return JournalTier.Q3.value
        else:
            return JournalTier.Q4.value


class JournalRecommender:
    """智能期刊推荐系统"""

    def __init__(self):
        self.journals_database = self._build_journals_database()

    def _build_journals_database(self) -> Dict[str, Dict[str, Any]]:
        """
        构建期刊数据库
        优先从外部JSON文件加载（120+期刊），失败时回退到内置精简库
        """
        # 尝试加载外部JSON数据库
        json_path = self._get_json_database_path()
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                journals = data.get('journals', {})
                # 转换tier字符串为枚举
                for jid, jinfo in journals.items():
                    tier_str = jinfo.get('tier')
                    if tier_str is None:
                        # 无tier字段时，从jcr_quartile推断
                        tier_str = jinfo.get('jcr_quartile', 'Q2')
                    if isinstance(tier_str, str):
                        jinfo['tier'] = self._parse_tier(tier_str)
                return journals
            except Exception:
                pass  # 加载失败时回退到内置库

        # 内置精简数据库（18个核心期刊作为fallback）
        return self._build_fallback_database()

    def _get_json_database_path(self) -> Optional[str]:
        """获取外部JSON数据库路径"""
        # 1. 尝试与当前文件同目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, 'journals_database.json')
        if os.path.exists(json_path):
            return json_path

        # 2. 尝试项目根目录下的data目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        json_path = os.path.join(project_root, 'data', 'journals_database.json')
        if os.path.exists(json_path):
            return json_path

        return None

    @staticmethod
    def _parse_tier(tier_str: str) -> JournalTier:
        """解析分区字符串为枚举"""
        tier_map = {
            'TOP': JournalTier.TOP,
            'Q1': JournalTier.Q1,
            'Q2': JournalTier.Q2,
            'Q3': JournalTier.Q3,
            'Q4': JournalTier.Q4,
        }
        return tier_map.get(tier_str.upper(), JournalTier.Q2)

    def _build_fallback_database(self) -> Dict[str, Dict[str, Any]]:
        """内置精简期刊数据库（18个核心期刊）"""
        return {
            "NEJM": {
                "full_name": "New England Journal of Medicine",
                "impact_factor": 91.245,
                "jcr_quartile": "Q1", "cas_quartile": "1区",
                "tier": JournalTier.TOP,
                "field": ["General Medicine", "Clinical Research"],
                "acceptance_rate": 0.06,
                "typical_review_time": "4-8周",
                "open_access": False, "publication_fee_usd": 0,
                "strengths": ["影响力最高", "临床相关性强", "高引用率"],
                "weaknesses": ["竞争极激烈", "接收率低", "审稿标准严格"]
            },
            "Lancet": {
                "full_name": "The Lancet",
                "impact_factor": 79.321,
                "jcr_quartile": "Q1", "cas_quartile": "1区",
                "tier": JournalTier.TOP,
                "field": ["General Medicine", "Public Health", "Clinical Research"],
                "acceptance_rate": 0.07,
                "typical_review_time": "4-6周",
                "open_access": True, "publication_fee_usd": 6300,
                "strengths": ["综合性强", "公共卫生领域权威", "国际影响力大"],
                "weaknesses": ["竞争激烈", "临床样本量要求高"]
            },
            "JAMA": {
                "full_name": "Journal of the American Medical Association",
                "impact_factor": 56.272,
                "jcr_quartile": "Q1", "cas_quartile": "1区",
                "tier": JournalTier.TOP,
                "field": ["General Medicine", "Clinical Research"],
                "acceptance_rate": 0.08,
                "typical_review_time": "3-6周",
                "open_access": False, "publication_fee_usd": 0,
                "strengths": ["美国医学会会刊", "临床指南权威", "高影响力"],
                "weaknesses": ["偏好美国数据", "接收率低"]
            },
            "BMJ": {
                "full_name": "British Medical Journal",
                "impact_factor": 39.890,
                "jcr_quartile": "Q1", "cas_quartile": "1区",
                "tier": JournalTier.Q1,
                "field": ["General Medicine", "Epidemiology", "Public Health"],
                "acceptance_rate": 0.10,
                "typical_review_time": "4-8周",
                "open_access": True, "publication_fee_usd": 3500,
                "strengths": ["注重方法学质量", "流行病学权威", "开放获取选项"],
                "weaknesses": ["样本量要求高", "统计方法要求严格"]
            },
            "Nature Medicine": {
                "full_name": "Nature Medicine",
                "impact_factor": 87.241,
                "jcr_quartile": "Q1", "cas_quartile": "1区",
                "tier": JournalTier.TOP,
                "field": ["Translational Medicine", "Basic Research"],
                "acceptance_rate": 0.05,
                "typical_review_time": "6-10周",
                "open_access": True, "publication_fee_usd": 11390,
                "strengths": ["转化医学权威", "基础与临床结合", "极高影响力"],
                "weaknesses": ["创新性要求极高", "审稿周期长"]
            },
            "Cell": {
                "full_name": "Cell",
                "impact_factor": 66.850,
                "jcr_quartile": "Q1", "cas_quartile": "1区",
                "tier": JournalTier.TOP,
                "field": ["Basic Research", "Molecular Biology", "Translational"],
                "acceptance_rate": 0.04,
                "typical_review_time": "6-12周",
                "open_access": True, "publication_fee_usd": 9900,
                "strengths": ["基础研究顶级期刊", "机制研究要求高", "影响力巨大"],
                "weaknesses": ["接收率极低", "审稿周期长", "机制要求高"]
            },
            "Circulation": {
                "full_name": "Circulation",
                "impact_factor": 39.918,
                "jcr_quartile": "Q1", "cas_quartile": "1区",
                "tier": JournalTier.Q1,
                "field": ["Cardiology", "Cardiovascular Research"],
                "acceptance_rate": 0.10,
                "typical_review_time": "4-8周",
                "open_access": False, "publication_fee_usd": 0,
                "strengths": ["心血管领域权威", "临床指南源", "高影响力"],
                "weaknesses": ["样本量要求大", "统计学要求严格"]
            },
            "Gastroenterology": {
                "full_name": "Gastroenterology",
                "impact_factor": 33.883,
                "jcr_quartile": "Q1", "cas_quartile": "1区",
                "tier": JournalTier.Q1,
                "field": ["Gastroenterology", "Hepatology"],
                "acceptance_rate": 0.15,
                "typical_review_time": "4-6周",
                "open_access": False, "publication_fee_usd": 0,
                "strengths": ["消化领域顶级", "临床与基础结合", "高引用率"],
                "weaknesses": ["方法学要求高", "创新性要求高"]
            },
            "Diabetes Care": {
                "full_name": "Diabetes Care",
                "impact_factor": 17.152,
                "jcr_quartile": "Q1", "cas_quartile": "1区",
                "tier": JournalTier.Q2,
                "field": ["Diabetes", "Endocrinology", "Clinical Care"],
                "acceptance_rate": 0.18,
                "typical_review_time": "3-6周",
                "open_access": False, "publication_fee_usd": 0,
                "strengths": ["临床护理关注", "ADA官方期刊", "实用性强"],
                "weaknesses": ["创新性要求相对较低"]
            },
            "PLOS ONE": {
                "full_name": "PLOS ONE",
                "impact_factor": 3.752,
                "jcr_quartile": "Q2", "cas_quartile": "3区",
                "tier": JournalTier.Q3,
                "field": ["General Science", "Multidisciplinary"],
                "acceptance_rate": 0.40,
                "typical_review_time": "2-4周",
                "open_access": True, "publication_fee_usd": 1800,
                "strengths": ["接收率高", "审稿快", "开放获取", "多学科"],
                "weaknesses": ["创新性要求不高", "版面费较高"]
            },
            "Scientific Reports": {
                "full_name": "Scientific Reports",
                "impact_factor": 4.996,
                "jcr_quartile": "Q2", "cas_quartile": "3区",
                "tier": JournalTier.Q3,
                "field": ["Multidisciplinary", "General Science"],
                "acceptance_rate": 0.35,
                "typical_review_time": "2-4周",
                "open_access": True, "publication_fee_usd": 1800,
                "strengths": ["Nature子刊系列", "覆盖领域广", "审稿高效"],
                "weaknesses": ["创新性要求一般"]
            },
            "BMJ Open": {
                "full_name": "BMJ Open",
                "impact_factor": 2.692,
                "jcr_quartile": "Q2", "cas_quartile": "3区",
                "tier": JournalTier.Q3,
                "field": ["Open Access", "General Medicine", "Public Health"],
                "acceptance_rate": 0.45,
                "typical_review_time": "2-4周",
                "open_access": True, "publication_fee_usd": 1800,
                "strengths": ["开放获取", "审稿透明", "接受阴性结果"],
                "weaknesses": ["创新性要求较低"]
            },
            "Medicine": {
                "full_name": "Medicine",
                "impact_factor": 1.817,
                "jcr_quartile": "Q3", "cas_quartile": "4区",
                "tier": JournalTier.Q4,
                "field": ["General Medicine", "Case Reports", "Clinical Studies"],
                "acceptance_rate": 0.50,
                "typical_review_time": "1-3周",
                "open_access": True, "publication_fee_usd": 1500,
                "strengths": ["接收率高", "审稿快", "接受病例报告"],
                "weaknesses": ["影响因子较低", "预警期刊风险"]
            }
        }

    def recommend(self,
                  paper_evaluation: Dict[str, Any],
                  field: str = "General Medicine",
                  study_type: str = "Clinical Study",
                  max_recommendations: int = 5) -> Dict[str, Any]:
        """
        推荐期刊

        Args:
            paper_evaluation: 论文评估结果
            field: 研究领域
            study_type: 研究类型
            max_recommendations: 最大推荐数量

        Returns:
            推荐结果
        """
        total_score = paper_evaluation.get('total_score', 60)
        dimension_scores = {d['name']: d['score'] for d in paper_evaluation.get('dimensions', [])}

        recommendations = []

        for journal_id, journal_info in self.journals_database.items():
            # 1. 领域匹配度
            field_match = self._calculate_field_match(field, journal_info['field'])

            # 2. 研究类型匹配
            study_type_match = self._calculate_study_type_match(study_type, journal_id)

            # 3. 得分匹配度
            score_match = self._calculate_score_match(total_score, journal_info['impact_factor'])

            # 4. 方法学质量匹配
            methodology_score = dimension_scores.get('方法学质量', 60)
            method_match = methodology_score / 100 if methodology_score > 70 else methodology_score / 120

            # 计算综合匹配分数
            match_score = (field_match * 0.30 +
                           study_type_match * 0.15 +
                           score_match * 0.35 +
                           method_match * 0.20) * 100

            # 预测接收率
            predicted_acceptance = self._predict_acceptance_rate(
                total_score, journal_info['acceptance_rate'], match_score
            )

            # 推荐等级
            recommendation_level = self._calculate_recommendation_level(
                match_score, predicted_acceptance, journal_info['tier']
            )

            recommendations.append({
                'journal_id': journal_id,
                'journal_name': journal_info['full_name'],
                'impact_factor': journal_info['impact_factor'],
                'jcr_quartile': journal_info.get('jcr_quartile', 'Q2'),
                'cas_quartile': journal_info.get('cas_quartile', '2区'),
                'tier': journal_info['tier'].value,
                'field_match_score': round(field_match * 100, 1),
                'overall_match_score': round(match_score, 1),
                'predicted_acceptance_rate': f"{predicted_acceptance:.1%}",
                'recommendation_level': recommendation_level,
                'typical_review_time': journal_info['typical_review_time'],
                'open_access': journal_info.get('open_access', False),
                'publication_fee_usd': journal_info.get('publication_fee_usd', 0),
                'pros': journal_info['strengths'],
                'cons': journal_info['weaknesses']
            })

        # 按推荐等级排序，然后按匹配分数排序
        recommendations.sort(key=lambda x: (-x['recommendation_level'], -x['overall_match_score']))

        # 取前N个
        top_recommendations = recommendations[:max_recommendations]

        # 生成投稿策略建议
        strategy = self._generate_submission_strategy(top_recommendations, total_score)

        return {
            'total_score': total_score,
            'recommended_tier': paper_evaluation.get('recommended_tier', 'Q2'),
            'recommendations': top_recommendations,
            'submission_strategy': strategy
        }

    def _calculate_field_match(self, user_field: str, journal_fields: List[str]) -> float:
        """计算领域匹配度"""
        user_field_lower = user_field.lower()

        # 关键词匹配
        field_keywords = {
            'General Medicine': ['general', '内科', '综合'],
            'Diabetes': ['diabetes', 'diabetic', '糖尿病', '内分泌'],
            'Endocrinology': ['endocrinology', '内分泌', 'hormone', '激素'],
            'Cardiology': ['cardiology', 'cardiac', 'heart', '心血管', '心脏'],
            'Gastroenterology': ['gastroenterology', 'gi', '消化', '胃肠'],
            'Oncology': ['oncology', 'cancer', 'tumor', '肿瘤', '癌症'],
            'Clinical Research': ['clinical', '临床', 'patient'],
            'Epidemiology': ['epidemiology', 'population', '流行病学', '人群'],
            'Public Health': ['public health', '公共卫生'],
            'Translational Medicine': ['translational', '转化'],
            'Basic Research': ['basic', '基础', 'mechanism', '机制']
        }

        best_match = 0.3  # 基础匹配分

        for jf in journal_fields:
            keywords = field_keywords.get(jf, [])
            for kw in keywords:
                if kw in user_field_lower:
                    best_match = max(best_match, 1.0)
                    break
                # 部分匹配
                if len(kw) >= 3 and kw[:3] in user_field_lower:
                    best_match = max(best_match, 0.6)

        return best_match

    def _calculate_study_type_match(self, study_type: str, journal_id: str) -> float:
        """计算研究类型匹配度"""
        study_type_lower = study_type.lower()

        preferences = {
            'New England Journal of Medicine': ['rct', 'randomized', 'clinical trial', '多中心'],
            'Lancet': ['rct', 'epidemiology', 'public health', '临床试验', '流行病学'],
            'JAMA': ['clinical trial', 'rct', 'guideline', '指南'],
            'BMJ': ['epidemiology', 'cohort', '流行病学', '队列研究'],
            'Nature Medicine': ['translational', 'basic', '机制', '转化'],
            'Journal of Clinical Oncology': ['oncology', 'cancer', 'clinical trial', '肿瘤', '临床试验'],
            'Gastroenterology': ['basic', 'mechanistic', '基础', '机制'],
            'Circulation': ['cardiology', 'cardiovascular', '心血管'],
            'PLOS ONE': ['all types', '所有类型', '阴性结果'],
            'Scientific Reports': ['all types', '所有类型']
        }

        preferred = preferences.get(journal_id, ['clinical', '临床'])

        for pref in preferred:
            if pref in study_type_lower or pref in ['all types', '所有类型']:
                return 1.0

        return 0.5  # 一般匹配

    def _calculate_score_match(self, paper_score: float, impact_factor: float) -> float:
        """计算得分匹配度"""
        # 根据论文得分和影响因子计算匹配度
        if paper_score >= 90:
            # 高分论文偏好高影响因子
            if impact_factor >= 20:
                return 1.0
            elif impact_factor >= 10:
                return 0.8
            else:
                return 0.5
        elif paper_score >= 80:
            if 10 <= impact_factor <= 30:
                return 1.0
            elif impact_factor > 30:
                return 0.8
            else:
                return 0.6
        elif paper_score >= 70:
            if 5 <= impact_factor <= 15:
                return 1.0
            elif impact_factor > 15:
                return 0.6
            else:
                return 0.7
        else:
            if impact_factor < 5:
                return 1.0
            else:
                return 0.5

    def _predict_acceptance_rate(self, paper_score: float, base_rate: float, match_score: float) -> float:
        """预测接收率"""
        # 论文得分调整
        score_factor = paper_score / 75  # 以75分为基准

        # 匹配度调整
        match_factor = match_score / 75

        # 预测接收率
        predicted = base_rate * score_factor * match_factor

        # 设定边界
        return min(max(predicted, base_rate * 0.3), base_rate * 1.5)

    def _calculate_recommendation_level(self, match_score: float,
                                       acceptance_rate: float, tier: JournalTier) -> int:
        """计算推荐等级 1-5"""
        score = match_score / 20  # 转换为0-5分

        # 考虑接收率的调整
        if acceptance_rate > 0.3:
            score += 0.5
        elif acceptance_rate > 0.15:
            score += 0.25

        # 限制在1-5分
        return max(1, min(5, round(score)))

    def _generate_submission_strategy(self,
                                      recommendations: List[Dict],
                                      paper_score: float) -> Dict[str, Any]:
        """生成投稿策略"""
        high_tier = [r for r in recommendations if r['recommendation_level'] >= 4]
        mid_tier = [r for r in recommendations if 3 <= r['recommendation_level'] < 4]
        low_tier = [r for r in recommendations if r['recommendation_level'] < 3]

        strategy = {
            "immediate_action": "建议首先处理得分最低的维度，提升论文质量",
            "timeline": "",
            "submission_sequence": [],
            "key_suggestions": []
        }

        if paper_score >= 85:
            strategy['timeline'] = "预计总周期: 6-12个月（含可能1次修回）"
            if high_tier:
                strategy['submission_sequence'].append({
                    'stage': '首选冲击',
                    'journals': [h['journal_name'] for h in high_tier[:2]],
                    'expected_time': '2-3个月',
                    'advice': '争取顶刊机会，注意cover letter突出创新性'
                })
            if mid_tier:
                strategy['submission_sequence'].append({
                    'stage': '稳妥选择',
                    'journals': [m['journal_name'] for m in mid_tier[:2]],
                    'expected_time': '2-3个月',
                    'advice': 'Q1区期刊，成功率较高'
                })
        elif paper_score >= 75:
            strategy['timeline'] = "预计总周期: 9-15个月（含1-2次修回）"
            if high_tier:
                strategy['submission_sequence'].append({
                    'stage': '冲刺尝试',
                    'journals': [h['journal_name'] for h in high_tier[:1]],
                    'expected_time': '1-2个月',
                    'advice': '可以尝试投1次高分区期刊，但要有被拒稿准备'
                })
            if mid_tier:
                strategy['submission_sequence'].append({
                    'stage': '主攻目标',
                    'journals': [m['journal_name'] for m in mid_tier[:3]],
                    'expected_time': '3-4个月',
                    'advice': 'Q1/Q2区期刊，成功率适中'
                })
            if low_tier:
                strategy['submission_sequence'].append({
                    'stage': '保底选择',
                    'journals': [l['journal_name'] for l in low_tier[:2]],
                    'expected_time': '2-3个月',
                    'advice': 'Q3/Q4区，成功率很高'
                })
        else:
            strategy['timeline'] = "预计总周期: 12-18个月（建议先改进论文）"
            strategy['key_suggestions'].append("建议先系统性改进论文质量，重点提升创新性和方法学质量")
            if mid_tier:
                strategy['submission_sequence'].append({
                    'stage': '初期目标',
                    'journals': [m['journal_name'] for m in mid_tier[:2]],
                    'expected_time': '3-4个月',
                    'advice': '从Q2/Q3区开始尝试'
                })

        # 通用建议
        strategy['key_suggestions'].extend([
            "投稿前仔细对照目标期刊的Author Guide for Authors",
            "精心准备Cover Letter，突出研究亮点和创新性",
            "建议准备Response Letter模板以备修回",
            "注意图表格式和分辨率要求",
            "确保参考文献格式与目标期刊一致"
        ])

        return strategy


class PaperEvaluator:
    """论文质量评估主类"""

    def __init__(self):
        self.scorer = PaperQualityScorer()
        self.recommender = JournalRecommender()

    def full_evaluation(self,
                        paper_content: Dict[str, Any],
                        field: str = "General Medicine",
                        study_type: str = "Clinical Study") -> Dict[str, Any]:
        """
        完整论文评估流程

        Args:
            paper_content: 论文内容字典
            field: 研究领域
            study_type: 研究类型

        Returns:
            完整的评估报告
        """
        # 1. 质量评分（传递研究类型以应用差异化权重）
        evaluation = self.scorer.evaluate(paper_content, study_type)

        # 2. 期刊推荐
        recommendations = self.recommender.recommend(
            evaluation, field, study_type
        )

        # 3. 生成雷达图数据（用于可视化）
        radar_data = self._generate_radar_data(evaluation)

        return {
            "quality_score": evaluation,
            "journal_recommendations": recommendations,
            "radar_chart_data": radar_data,
            "summary": self._generate_summary(evaluation, recommendations)
        }

    def _generate_radar_data(self, evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """生成雷达图数据"""
        dimensions = evaluation['dimensions']
        return {
            'labels': [d['name'] for d in dimensions],
            'scores': [d['score'] for d in dimensions],
            'weights': [d['weight'] for d in dimensions]
        }

    def _generate_summary(self, evaluation: Dict[str, Any],
                          recommendations: Dict[str, Any]) -> str:
        """生成总结报告"""
        total_score = evaluation['total_score']
        grade = evaluation['grade']
        potential = evaluation['publication_potential']['level']

        summary = f"""
{'='*60}
论文质量评估与期刊推荐报告
{'='*60}

📊 总体评分: {total_score:.1f}/100
🎯 等级: {grade}
🏆 发表潜力: {potential}

推荐投稿分区: {recommendations['recommended_tier']}

---

📈 各维度得分:
"""
        for dim in evaluation['dimensions']:
            bar = '█' * int(dim['score'] // 5)
            summary += f"{dim['name']:15s} {bar} {dim['score']:.1f}/100\n"

        top_journals = recommendations['recommendations'][:3]
        summary += f"""
---

📚 推荐投稿期刊 (Top 3):
"""
        for i, j in enumerate(top_journals, 1):
            stars = '⭐' * j['recommendation_level']
            summary += f"\n{i}. {j['journal_name']} (IF: {j['impact_factor']:.1f}) {stars}"
            summary += f"\n   匹配度: {j['overall_match_score']:.1f}% | 预测接收率: {j['predicted_acceptance_rate']}"

        summary += f"\n\n---\n\n"
        summary += f"📋 总体评价: {evaluation['overall_feedback']}\n\n"
        summary += f"⏱️ 预计发表周期: {evaluation['publication_potential']['estimated_timeline']}\n"

        if evaluation['improvement_suggestions']:
            summary += f"\n\n🎯 重点改进建议:\n"
            for i, sugg in enumerate(evaluation['improvement_suggestions'], 1):
                priority_icon = '🔴' if sugg['priority'] == 'high' else '🟡'
                summary += f"{i}. {priority_icon} {sugg['dimension']} ({sugg['score']:.1f}分): {sugg['suggestion']}\n"

        return summary
