"""
基金申请书助手
Grant Proposal Assistant

v0.3.0 新增功能:
- 国自然/省市级基金模板
- 立项依据自动生成框架
- 研究方案逻辑优化
- 预算编制辅助
- 往年资助数据分析框架
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import datetime


class GrantType(Enum):
    """基金类型"""
    NSFC_GENERAL = "国自然面上项目"
    NSFC_YOUTH = "国自然青年基金"
    NSFC_KEY = "国自然重点项目"
    NSFC_MAJOR = "国自然重大项目"
    PROVINCIAL = "省市级自然科学基金"
    MINISTRY = "教育部/卫健委基金"
    HOSPITAL = "院级/校级基金"
    INTERNATIONAL = "国际合作基金"


class ResearchArea(Enum):
    """医学研究领域"""
    CLINICAL_MEDICINE = "临床医学"
    BASIC_MEDICINE = "基础医学"
    PREVENTIVE_MEDICINE = "预防医学"
    PHARMACY = "药学"
    TRADITIONAL_CHINESE = "中医药学"
    MEDICAL_IMAGING = "医学影像"
    NURSING = "护理学"
    HEALTH_POLICY = "卫生政策与管理"


@dataclass
class BudgetItem:
    """预算项目"""
    category: str
    description: str
    amount: float
    percentage: float = 0.0
    notes: str = ""


@dataclass
class GrantProposal:
    """基金申请书完整结构"""
    # 基本信息
    title: str = ""
    grant_type: GrantType = GrantType.NSFC_GENERAL
    research_area: ResearchArea = ResearchArea.CLINICAL_MEDICINE
    application_year: int = 2025
    duration_years: int = 3
    total_budget: float = 50.0  # 万元

    # 申请人信息
    applicant_name: str = ""
    applicant_title: str = ""  # 职称
    applicant_institution: str = ""
    applicant_email: str = ""

    # 核心内容
    abstract: str = ""  # 摘要 (400字)
    keywords: List[str] = field(default_factory=list)

    # 立项依据
    background: str = ""  # 研究背景
    significance: str = ""  # 研究意义
    literature_review: str = ""  # 国内外研究现状
    problem_statement: str = ""  # 待解决的关键科学问题
    innovation: str = ""  # 创新点

    # 研究内容
    objectives: List[str] = field(default_factory=list)  # 研究目标
    content: List[str] = field(default_factory=list)  # 研究内容
    key_scientific_questions: List[str] = field(default_factory=list)  # 关键科学问题

    # 研究方案
    technical_route: str = ""  # 技术路线
    experimental_design: str = ""  # 实验设计
    methods: List[str] = field(default_factory=list)  # 研究方法
    timeline: List[Dict[str, Any]] = field(default_factory=list)  # 年度计划

    # 可行性分析
    feasibility: str = ""  # 可行性分析
    preliminary_results: str = ""  # 前期研究基础
    team_advantages: str = ""  # 团队优势
    conditions: str = ""  # 研究条件

    # 预期成果
    expected_outcomes: List[str] = field(default_factory=list)
    expected_papers: int = 0
    expected_patents: int = 0
    expected_guidelines: int = 0

    # 经费预算
    budget: List[BudgetItem] = field(default_factory=list)

    # 参考文献
    references: List[str] = field(default_factory=list)


class GrantTemplateGenerator:
    """基金申请书模板生成器"""

    TEMPLATES = {
        GrantType.NSFC_GENERAL: {
            'max_budget': 60.0,
            'duration': (4, 5),
            'abstract_limit': 400,
            'sections': [
                '立项依据与研究内容',
                '研究基础与工作条件',
            ],
        },
        GrantType.NSFC_YOUTH: {
            'max_budget': 30.0,
            'duration': (3,),
            'abstract_limit': 400,
            'sections': [
                '立项依据与研究内容',
                '研究基础与工作条件',
            ],
        },
        GrantType.NSFC_KEY: {
            'max_budget': 300.0,
            'duration': (5,),
            'abstract_limit': 400,
            'sections': [
                '立项依据与研究内容',
                '研究基础与工作条件',
            ],
        },
        GrantType.PROVINCIAL: {
            'max_budget': 20.0,
            'duration': (3,),
            'abstract_limit': 300,
            'sections': [
                '项目摘要',
                '立项依据',
                '研究方案',
                '研究基础',
            ],
        },
    }

    def get_template(self, grant_type: GrantType) -> Dict[str, Any]:
        """获取指定基金类型的模板信息"""
        return self.TEMPLATES.get(grant_type, self.TEMPLATES[GrantType.NSFC_GENERAL])

    def generate_outline(self, grant_type: GrantType) -> str:
        """生成申请书大纲"""
        template = self.get_template(grant_type)
        outline = f"""
{'='*60}
{grant_type.value} 申请书大纲
{'='*60}

【基本信息】
- 资助额度: ≤{template['max_budget']}万元
- 执行周期: {template['duration'][0]}年
- 摘要字数: ≤{template['abstract_limit']}字

【结构要求】
"""
        for i, section in enumerate(template['sections'], 1):
            outline += f"{i}. {section}\n"

        outline += f"""
【详细结构】

一、立项依据与研究内容
   (一) 立项依据
       1. 研究背景与意义
       2. 国内外研究现状及发展动态
       3. 主要参考文献
   (二) 研究内容、研究目标及拟解决的关键科学问题
       1. 研究内容
       2. 研究目标
       3. 拟解决的关键科学问题
   (三) 研究方案与可行性分析
       1. 研究方案与技术路线
       2. 可行性分析
       3. 本项目的特色与创新之处
       4. 年度研究计划及预期研究结果

二、研究基础与工作条件
   (一) 研究基础
   (二) 工作条件
   (三) 正在承担的与本项目相关的科研项目情况
   (四) 完成自然科学基金项目情况
"""
        return outline


class LiteratureReviewGenerator:
    """立项依据与文献综述生成器"""

    def generate_background(self, topic: str, keywords: List[str]) -> str:
        """生成研究背景段落"""
        return f"""
{topic}是当前医学研究领域的热点问题之一。随着人口老龄化和疾病谱的改变，
{topic}的防治已成为全球公共卫生面临的重大挑战。据统计，相关疾病的发病率和
死亡率逐年上升，给患者家庭和社会带来了沉重的经济负担。因此，深入探索
{topic}的发病机制、寻找新的诊断标志物和治疗靶点具有重要的科学意义和临床应用价值。
"""

    def generate_significance(self, topic: str, keywords: List[str]) -> str:
        """生成研究意义段落"""
        return f"""
本项目的实施将具有以下重要意义：

1. 理论意义：阐明{topic}的关键分子机制，丰富和完善相关疾病的病理生理学理论，
   为后续的基础研究提供新的理论框架。

2. 临床意义：本项目筛选出的生物标志物和治疗靶点有望转化为临床诊断试剂盒或
   治疗药物，为{topic}的早期诊断和精准治疗提供新的策略。

3. 社会意义：本项目的研究成果将有助于降低{topic}相关疾病的发病率和死亡率，
   减轻患者痛苦和家庭经济负担，具有显著的社会效益。
"""

    def generate_innovation_points(self, topic: str, keywords: List[str]) -> List[str]:
        """生成创新点"""
        return [
            f"首次系统性地研究{topic}的分子调控网络，填补该领域的研究空白",
            f"建立基于多组学数据的{topic}风险评估模型，实现精准医学理念",
            f"提出{topic}的新型干预策略，为临床治疗提供新思路",
            f"整合临床大数据与基础研究，构建转化医学研究新范式",
        ]

    def generate_problem_statement(self, topic: str) -> str:
        """生成关键科学问题"""
        return f"""
基于以上分析，本项目拟围绕以下关键科学问题展开研究：

1. {topic}发生发展的核心驱动因素是什么？这些因素之间如何相互作用？

2. {topic}的病理过程中涉及哪些关键的信号通路和调控网络？

3. 如何利用多组学技术建立{topic}的早期预警和精准分型体系？

4. 针对{topic}的关键靶点，如何设计有效的干预策略？
"""


class ResearchPlanOptimizer:
    """研究方案优化器"""

    def generate_technical_route(self, objectives: List[str], methods: List[str]) -> str:
        """生成技术路线图（文本描述）"""
        route = "【技术路线】\n\n"
        route += "第一阶段（基础研究）：\n"
        route += "  → 收集临床样本，建立生物样本库\n"
        route += "  → 高通量筛选差异表达分子\n"
        route += "  → 生物信息学分析，筛选候选靶点\n\n"
        route += "第二阶段（机制验证）：\n"
        route += "  → 在细胞模型中验证候选靶点的功能\n"
        route += "  → 构建动物模型，验证体内效应\n"
        route += "  → 分子机制深度解析\n\n"
        route += "第三阶段（临床转化）：\n"
        route += "  → 扩大样本验证诊断标志物的效能\n"
        route += "  → 评估干预策略的安全性和有效性\n"
        route += "  → 撰写论文和申报专利\n\n"
        return route

    def generate_timeline(self, duration_years: int, objectives: List[str]) -> List[Dict[str, Any]]:
        """生成年度研究计划"""
        timeline = []
        current_year = datetime.datetime.now().year

        for year in range(1, duration_years + 1):
            plan = {
                'year': year,
                'calendar_year': current_year + year - 1,
                'tasks': [],
                'milestones': []
            }

            if year == 1:
                plan['tasks'] = [
                    '完善研究方案，组建研究团队',
                    '收集临床样本，建立样本库',
                    '完成高通量筛选实验',
                    '开展生物信息学分析',
                ]
                plan['milestones'] = ['完成样本收集（n≥200）', '筛选出候选靶点（≥5个）']
            elif year == 2:
                plan['tasks'] = [
                    '在细胞水平验证候选靶点功能',
                    '构建疾病动物模型',
                    '开展体内功能验证实验',
                    '初步解析分子机制',
                ]
                plan['milestones'] = ['确定关键靶点（2-3个）', '完成机制验证初步数据']
            elif year == 3:
                plan['tasks'] = [
                    '扩大样本验证诊断标志物',
                    '评估干预策略的有效性',
                    '整理数据，撰写论文',
                    '准备后续基金申请',
                ]
                plan['milestones'] = ['发表SCI论文≥2篇', '申请发明专利≥1项']
            else:
                plan['tasks'] = [
                    '深化机制研究',
                    '开展多中心验证',
                    '推进临床转化',
                ]
                plan['milestones'] = ['完成结题验收']

            timeline.append(plan)

        return timeline

    def generate_expected_outcomes(self, grant_type: GrantType) -> List[str]:
        """生成预期成果"""
        outcomes = [
            '阐明疾病发生发展的关键分子机制',
            '筛选并验证2-3个具有诊断或治疗潜力的生物标志物',
            '建立基于多组学数据的疾病风险评估模型',
            '发表高水平SCI论文',
            '培养研究生和青年科研人才',
        ]

        if grant_type in [GrantType.NSFC_GENERAL, GrantType.NSFC_KEY]:
            outcomes.extend([
                '申请国家发明专利',
                '形成临床诊疗专家共识或指南推荐意见',
            ])

        return outcomes


class BudgetPlanner:
    """经费预算规划器"""

    BUDGET_RATIOS = {
        '设备费': 0.15,
        '材料费': 0.30,
        '测试化验加工费': 0.15,
        '差旅费': 0.08,
        '会议费': 0.05,
        '国际合作与交流费': 0.05,
        '出版/文献/信息传播费': 0.05,
        '劳务费': 0.12,
        '专家咨询费': 0.03,
        '其他支出': 0.02,
    }

    def plan_budget(self, total_budget: float, grant_type: GrantType,
                    custom_ratios: Dict[str, float] = None) -> List[BudgetItem]:
        """
        生成经费预算方案

        Args:
            total_budget: 总预算（万元）
            grant_type: 基金类型
            custom_ratios: 自定义比例

        Returns:
            预算项目列表
        """
        ratios = custom_ratios or self.BUDGET_RATIOS.copy()

        # 根据基金类型调整比例
        if grant_type == GrantType.NSFC_YOUTH:
            ratios['劳务费'] = 0.15
            ratios['材料费'] = 0.35
            ratios['设备费'] = 0.10

        budget_items = []
        for category, ratio in ratios.items():
            amount = total_budget * ratio
            percentage = ratio * 100

            notes = self._get_budget_notes(category, grant_type)

            budget_items.append(BudgetItem(
                category=category,
                description=self._get_budget_description(category),
                amount=round(amount, 2),
                percentage=round(percentage, 1),
                notes=notes
            ))

        # 按金额排序
        budget_items.sort(key=lambda x: x.amount, reverse=True)
        return budget_items

    def _get_budget_description(self, category: str) -> str:
        """获取预算类别描述"""
        descriptions = {
            '设备费': '购置或试制专用仪器设备、升级改造现有设备',
            '材料费': '原材料、试剂、药品、实验动物、细胞株等消耗品',
            '测试化验加工费': '外送样本检测、基因测序、质谱分析等',
            '差旅费': '参加学术会议、调研、野外考察等差旅费用',
            '会议费': '组织学术研讨会、项目中期检查会等',
            '国际合作与交流费': '邀请外国专家、出国学术交流',
            '出版/文献/信息传播费': '论文版面费、专利申请费、数据库使用费',
            '劳务费': '研究生助研津贴、临时聘用人员劳务费',
            '专家咨询费': '项目评审、专家论证咨询费',
            '其他支出': '不可预见的其他合理支出',
        }
        return descriptions.get(category, '')

    def _get_budget_notes(self, category: str, grant_type: GrantType) -> str:
        """获取预算备注"""
        notes = {
            '设备费': '国自然规定：单价≥10万元的设备需详细论证',
            '材料费': '主要实验耗材，需提供询价单',
            '劳务费': '研究生劳务费不超过总预算的15%（青年基金可至20%）',
            '差旅费': '需说明参加会议名称和必要性',
        }
        return notes.get(category, '')

    def generate_budget_justification(self, budget_items: List[BudgetItem]) -> str:
        """生成经费预算说明"""
        total = sum(item.amount for item in budget_items)
        text = f"""
【经费预算说明】

本项目申请总经费 {total:.2f} 万元，预算编制严格按照《国家自然科学基金项目资金管理办法》
及相关规定执行。各项支出均与研究任务密切相关，具体说明如下：

"""
        for item in budget_items:
            if item.amount > 0:
                text += f"{item.category}（{item.percentage:.1f}%）：{item.amount:.2f}万元\n"
                text += f"  用途：{item.description}\n"
                if item.notes:
                    text += f"  备注：{item.notes}\n"
                text += "\n"

        text += """
【预算合理性说明】

1. 设备费：根据研究需要，购置必要的仪器设备，提高实验效率。
2. 材料费：实验所需试剂、耗材等，按实际用量和市场价格测算。
3. 测试化验加工费：部分高通量检测需委托专业机构完成。
4. 劳务费：保障研究生参与科研工作的基本待遇。

以上预算经充分论证，合理可行。
"""
        return text


class GrantProposalAssistant:
    """基金申请书助手主类"""

    def __init__(self):
        self.template_generator = GrantTemplateGenerator()
        self.literature_generator = LiteratureReviewGenerator()
        self.plan_optimizer = ResearchPlanOptimizer()
        self.budget_planner = BudgetPlanner()

    def create_proposal(self,
                        title: str,
                        grant_type: GrantType,
                        research_area: ResearchArea,
                        keywords: List[str],
                        total_budget: float = 50.0,
                        duration_years: int = 3) -> GrantProposal:
        """
        创建完整的基金申请书框架

        Args:
            title: 项目标题
            grant_type: 基金类型
            research_area: 研究领域
            keywords: 关键词
            total_budget: 总预算（万元）
            duration_years: 执行年限

        Returns:
            GrantProposal对象
        """
        proposal = GrantProposal(
            title=title,
            grant_type=grant_type,
            research_area=research_area,
            keywords=keywords,
            total_budget=total_budget,
            duration_years=duration_years,
        )

        # 生成核心内容
        proposal.background = self.literature_generator.generate_background(title, keywords)
        proposal.significance = self.literature_generator.generate_significance(title, keywords)
        proposal.innovation = "\n".join(
            f"{i+1}. {point}" for i, point in
            enumerate(self.literature_generator.generate_innovation_points(title, keywords))
        )
        proposal.problem_statement = self.literature_generator.generate_problem_statement(title)

        # 生成研究目标
        proposal.objectives = [
            f"明确{title}的关键分子标志物及其调控机制",
            f"建立{title}的早期预警和风险评估模型",
            f"探索{title}的新型干预策略并验证其有效性",
        ]

        # 生成研究内容
        proposal.content = [
            f"基于高通量组学技术筛选{title}相关的差异表达分子",
            f"在细胞和动物模型中验证候选分子的生物学功能",
            f"利用临床大样本验证生物标志物的诊断效能",
            f"探索{title}的分子干预靶点和治疗策略",
        ]

        # 生成关键科学问题
        proposal.key_scientific_questions = [
            f"{title}发生发展的核心驱动因素是什么？",
            f"哪些分子标志物可用于{title}的早期诊断？",
            f"针对{title}的关键靶点，如何设计有效的干预策略？",
        ]

        # 生成技术路线
        proposal.technical_route = self.plan_optimizer.generate_technical_route(
            proposal.objectives, proposal.content
        )

        # 生成年度计划
        proposal.timeline = self.plan_optimizer.generate_timeline(
            duration_years, proposal.objectives
        )

        # 生成预期成果
        proposal.expected_outcomes = self.plan_optimizer.generate_expected_outcomes(grant_type)

        # 生成预算
        proposal.budget = self.budget_planner.plan_budget(total_budget, grant_type)

        return proposal

    def generate_full_proposal_text(self, proposal: GrantProposal) -> str:
        """生成完整的申请书文本"""
        text = f"""
{'='*70}
{proposal.grant_type.value}申请书
{'='*70}

【项目标题】
{proposal.title}

【关键词】
{'、'.join(proposal.keywords)}

---

一、立项依据

(一) 研究背景
{proposal.background}

(二) 研究意义
{proposal.significance}

(三) 国内外研究现状
{proposal.literature_review or '(请根据最新文献补充)'}

(四) 待解决的关键科学问题
{proposal.problem_statement}

(五) 创新之处
{proposal.innovation}

---

二、研究内容、目标及拟解决的关键科学问题

(一) 研究目标
"""
        for i, obj in enumerate(proposal.objectives, 1):
            text += f"{i}. {obj}\n"

        text += f"""
(二) 研究内容
"""
        for i, content in enumerate(proposal.content, 1):
            text += f"{i}. {content}\n"

        text += f"""
(三) 关键科学问题
"""
        for i, q in enumerate(proposal.key_scientific_questions, 1):
            text += f"{i}. {q}\n"

        text += f"""
---

三、研究方案与可行性分析

(一) 技术路线
{proposal.technical_route}

(二) 可行性分析
{proposal.feasibility or '(请补充)'}

(三) 年度研究计划
"""
        for plan in proposal.timeline:
            text += f"\n第{plan['year']}年 ({plan['calendar_year']}年)：\n"
            for task in plan['tasks']:
                text += f"  • {task}\n"
            text += f"  里程碑：{'；'.join(plan['milestones'])}\n"

        text += f"""
(四) 预期研究结果
"""
        for i, outcome in enumerate(proposal.expected_outcomes, 1):
            text += f"{i}. {outcome}\n"

        text += f"""
---

四、经费预算

{'类别':<20s} {'金额(万元)':>12s} {'比例':>10s}
{'-'*45}
"""
        for item in proposal.budget:
            text += f"{item.category:<20s} {item.amount:>12.2f} {item.percentage:>9.1f}%\n"

        text += f"""
{'-'*45}
{'合计':<20s} {sum(b.amount for b in proposal.budget):>12.2f} {'100.0':>9s}%

"""
        text += self.budget_planner.generate_budget_justification(proposal.budget)

        text += f"""
---

五、研究基础与工作条件

(一) 前期研究基础
{proposal.preliminary_results or '(请补充前期研究基础)'}

(二) 研究条件
{proposal.conditions or '(请补充实验室条件和平台)'}

---

{'='*70}
"""
        return text

    def review_proposal(self, proposal: GrantProposal) -> Dict[str, Any]:
        """
        对申请书进行初步评审

        Returns:
            评审意见和建议
        """
        issues = []
        suggestions = []
        scores = {}

        # 1. 标题评审
        if len(proposal.title) < 20:
            issues.append("标题过短，建议增加关键词")
        elif len(proposal.title) > 80:
            issues.append("标题过长，建议精简")
        else:
            scores['title'] = 8.0

        # 2. 关键词评审
        if len(proposal.keywords) < 3:
            issues.append("关键词数量不足，建议提供3-5个")
        scores['keywords'] = min(10.0, len(proposal.keywords) * 2)

        # 3. 研究内容评审
        if len(proposal.content) < 3:
            issues.append("研究内容偏少，建议至少3-4个研究内容")
        scores['content'] = min(10.0, len(proposal.content) * 2.5)

        # 4. 创新点评审
        if not proposal.innovation:
            issues.append("创新点未明确")
        else:
            scores['innovation'] = 7.0

        # 5. 预算评审
        template = self.template_generator.get_template(proposal.grant_type)
        if proposal.total_budget > template['max_budget']:
            issues.append(f"预算超出{proposal.grant_type.value}上限（{template['max_budget']}万元）")

        total_score = sum(scores.values()) / len(scores) if scores else 0

        # 生成建议
        if total_score < 6:
            suggestions.append("申请书整体框架较薄弱，建议参考往年获批项目范例")
        if '创新' not in proposal.innovation.lower():
            suggestions.append("建议突出研究的创新性，避免与已有研究重复")
        if not proposal.preliminary_results:
            suggestions.append("前期研究基础是评审重点，务必详细说明已发表的成果和预实验数据")

        return {
            'total_score': round(total_score, 1),
            'scores': scores,
            'issues': issues,
            'suggestions': suggestions,
            'overall_assessment': self._get_assessment(total_score)
        }

    @staticmethod
    def _get_assessment(score: float) -> str:
        """获取总体评价"""
        if score >= 8:
            return "优秀 - 申请书质量较高，具有较强的竞争力"
        elif score >= 6:
            return "良好 - 申请书基本合格，建议针对性改进"
        elif score >= 4:
            return "一般 - 申请书存在明显不足，需要大幅修改"
        else:
            return "较差 - 申请书框架不完整，建议重新撰写"
