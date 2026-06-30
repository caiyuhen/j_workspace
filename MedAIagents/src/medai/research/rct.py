"""
临床科研自动化模块 - RCT 试验设计
Clinical Research Automation - RCT Trial Design
"""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class StudyPhase(Enum):
    """临床试验分期"""
    PHASE_I = "I期"
    PHASE_II = "II期"
    PHASE_III = "III期"
    PHASE_IV = "IV期"
    PILOT = "预试验"
    REAL_WORLD = "真实世界研究"


class StudyType(Enum):
    """研究类型"""
    RCT = "随机对照试验"
    COHORT = "队列研究"
    CASE_CONTROL = "病例对照研究"
    CROSS_SECTIONAL = "横断面研究"
    SYSTEMATIC_REVIEW = "系统综述"
    META_ANALYSIS = "Meta分析"


@dataclass
class StudyDesign:
    """研究设计基础信息"""
    title: str
    study_type: StudyType
    phase: StudyPhase
    indication: str
    primary_endpoint: str
    secondary_endpoints: List[str]
    sample_size: int
    duration_months: int
    inclusion_criteria: List[str]
    exclusion_criteria: List[str]
    intervention: str
    control: str


class SampleSizeCalculator:
    """样本量计算器"""
    
    @staticmethod
    def calculate_proportion(
        p1: float,
        p2: float,
        alpha: float = 0.05,
        power: float = 0.8,
        ratio: float = 1.0
    ) -> Dict[str, Any]:
        """
        两个率比较的样本量计算
        
        Args:
            p1: 对照组阳性率
            p2: 试验组阳性率
            alpha: 显著性水平
            power: 检验效能
            ratio: 试验组/对照组样本量比例
        
        Returns:
            样本量计算结果
        """
        import math
        
        # Z 值
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)
        
        p_bar = (p1 + ratio * p2) / (1 + ratio)
        
        # 计算公式
        n_control = (z_alpha * math.sqrt(p_bar * (1 - p_bar) * (1 + 1/ratio)) + 
                    z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio)) ** 2
        n_control = n_control / (p1 - p2) ** 2
        
        n_treatment = n_control * ratio
        
        # 考虑失访率（加20%）
        dropout_rate = 0.2
        n_control_final = math.ceil(n_control / (1 - dropout_rate))
        n_treatment_final = math.ceil(n_treatment / (1 - dropout_rate))
        
        return {
            'parameters': {
                'p1': p1,
                'p2': p2,
                'alpha': alpha,
                'power': power,
                'ratio': ratio
            },
            'sample_size': {
                'control_group': n_control_final,
                'treatment_group': n_treatment_final,
                'total': n_control_final + n_treatment_final
            },
            'dropout_rate': dropout_rate,
            'formula': '两个独立样本率比较的样本量计算公式'
        }
    
    @staticmethod
    def calculate_mean(
        mean1: float,
        mean2: float,
        std_dev: float,
        alpha: float = 0.05,
        power: float = 0.8,
        ratio: float = 1.0
    ) -> Dict[str, Any]:
        """
        两个均数比较的样本量计算
        
        Args:
            mean1: 对照组均值
            mean2: 试验组均值
            std_dev: 标准差
            alpha: 显著性水平
            power: 检验效能
            ratio: 样本量比例
        
        Returns:
            样本量计算结果
        """
        import math
        from scipy.stats import norm
        
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)
        
        delta = abs(mean1 - mean2)
        
        n_control = (z_alpha + z_beta) ** 2 * std_dev ** 2 * (1 + 1/ratio) / (delta ** 2)
        n_treatment = n_control * ratio
        
        # 考虑失访率
        dropout_rate = 0.2
        n_control_final = math.ceil(n_control / (1 - dropout_rate))
        n_treatment_final = math.ceil(n_treatment / (1 - dropout_rate))
        
        return {
            'parameters': {
                'mean1': mean1,
                'mean2': mean2,
                'std_dev': std_dev,
                'alpha': alpha,
                'power': power,
                'ratio': ratio
            },
            'sample_size': {
                'control_group': n_control_final,
                'treatment_group': n_treatment_final,
                'total': n_control_final + n_treatment_final
            },
            'dropout_rate': dropout_rate,
            'formula': '两个独立样本均数比较的样本量计算公式'
        }
    
    @staticmethod
    def calculate_survival(
        median_survival_control: float,
        median_survival_treatment: float,
        hazard_ratio: float,
        alpha: float = 0.05,
        power: float = 0.8,
        ratio: float = 1.0
    ) -> Dict[str, Any]:
        """
        生存分析的事件数计算（使用对数秩检验）
        """
        import math
        from scipy.stats import norm
        
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)
        
        # 所需事件数
        events = (z_alpha + z_beta) ** 2 * (1 + ratio) / (ratio * math.log(hazard_ratio) ** 2)
        
        return {
            'parameters': {
                'median_survival_control': median_survival_control,
                'median_survival_treatment': median_survival_treatment,
                'hazard_ratio': hazard_ratio,
                'alpha': alpha,
                'power': power,
                'ratio': ratio
            },
            'required_events': math.ceil(events),
            'formula': '对数秩检验的事件数计算公式'
        }


class RCTProtocolGenerator:
    """RCT 试验方案生成器"""
    
    def __init__(self):
        self.sample_calculator = SampleSizeCalculator()
    
    def generate_protocol(
        self,
        study_title: str,
        indication: str,
        study_type: str = "RCT",
        phase: str = "III期",
        primary_endpoint: str = "",
        secondary_endpoints: List[str] = None,
        sample_size_params: Dict[str, Any] = None,
        intervention: str = "",
        control: str = "安慰剂",
        duration: int = 12
    ) -> Dict[str, Any]:
        """
        生成 RCT 试验方案
        
        Args:
            study_title: 研究题目
            indication: 适应症
            study_type: 研究类型
            phase: 试验分期
            primary_endpoint: 主要终点
            secondary_endpoints: 次要终点列表
            sample_size_params: 样本量计算参数
            intervention: 试验组干预措施
            control: 对照组干预
            duration: 研究时长（月）
        
        Returns:
            完整的试验方案
        """
        secondary_endpoints = secondary_endpoints or []
        
        # 计算样本量
        sample_size_result = None
        if sample_size_params:
            calc_type = sample_size_params.get('type', 'proportion')
            if calc_type == 'proportion':
                sample_size_result = self.sample_calculator.calculate_proportion(
                    p1=sample_size_params.get('p1', 0.3),
                    p2=sample_size_params.get('p2', 0.4),
                    alpha=sample_size_params.get('alpha', 0.05),
                    power=sample_size_params.get('power', 0.8)
                )
            elif calc_type == 'mean':
                sample_size_result = self.sample_calculator.calculate_mean(
                    mean1=sample_size_params.get('mean1', 50),
                    mean2=sample_size_params.get('mean2', 60),
                    std_dev=sample_size_params.get('std_dev', 15)
                )
        
        total_sample = sample_size_result['sample_size']['total'] if sample_size_result else 300
        
        # 生成入排标准
        inclusion, exclusion = self._generate_criteria(indication)
        
        protocol = {
            'study_info': {
                'title': study_title,
                'study_type': study_type,
                'phase': phase,
                'indication': indication,
                'duration_months': duration
            },
            'study_objectives': self._generate_objectives(indication, primary_endpoint),
            'endpoints': {
                'primary': primary_endpoint or self._generate_primary_endpoint(indication),
                'secondary': secondary_endpoints or self._generate_secondary_endpoints(indication)
            },
            'study_design': self._generate_study_design(study_type, phase, total_sample),
            'sample_size': sample_size_result or {
                'sample_size': {'total': total_sample},
                'note': '使用默认样本量，建议进行正式样本量计算'
            },
            'inclusion_criteria': inclusion,
            'exclusion_criteria': exclusion,
            'interventions': {
                'treatment_group': intervention or self._generate_intervention(indication),
                'control_group': control
            },
            'statistical_analysis': self._generate_statistical_plan(),
            'safety_assessment': self._generate_safety_assessment(),
            'data_management': self._generate_data_management(),
            'ethical_considerations': self._generate_ethical_considerations(),
            'consort_compliant': True
        }
        
        return protocol
    
    def _generate_criteria(self, indication: str) -> tuple[List[str], List[str]]:
        """生成入排标准模板"""
        inclusion = [
            f"1. 符合 {indication} 诊断标准的患者",
            "2. 年龄在 18-75 岁之间",
            "3. 自愿参加本研究并签署知情同意书",
            "4. 能够配合完成研究流程和随访",
            "5. 预期生存期 ≥ 6个月（如适用）"
        ]
        
        exclusion = [
            "1. 对研究药物或其成分过敏者",
            "2. 妊娠或哺乳期妇女",
            "3. 严重肝肾功能异常（ALT/AST > 3×ULN，肌酐 > 2×ULN）",
            "4. 合并严重心脑血管疾病、恶性肿瘤等",
            "5. 近3个月内参加其他临床试验者",
            "6. 研究者认为不适合参加本研究的其他情况"
        ]
        
        return inclusion, exclusion
    
    def _generate_objectives(self, indication: str, primary_endpoint: str) -> Dict[str, str]:
        """生成研究目的"""
        return {
            'primary': f"评价研究药物治疗 {indication} 的有效性和安全性",
            'secondary': f"探索研究药物治疗 {indication} 的长期疗效、耐受性和生活质量影响"
        }
    
    def _generate_primary_endpoint(self, indication: str) -> str:
        """生成默认主要终点"""
        return f"治疗xx周后，与对照组相比，试验组 {indication} 相关指标的改善情况"
    
    def _generate_secondary_endpoints(self, indication: str) -> List[str]:
        """生成默认次要终点"""
        return [
            f"治疗期间 {indication} 急性发作率",
            "生活质量评分改善情况",
            "药物安全性和耐受性评估",
            "生物标志物变化分析"
        ]
    
    def _generate_study_design(self, study_type: str, phase: str, sample_size: int) -> Dict[str, Any]:
        """生成研究设计描述"""
        return {
            'description': f"多中心、随机、双盲、平行对照 {phase} 临床试验",
            'randomization': "中央随机化系统，按1:1比例分组",
            'blinding': "双盲设计（受试者、研究者、评价者、统计分析人员）",
            'control_type': "安慰剂对照/阳性对照",
            'study_center': "预计 10-20 家研究中心",
            'study_flow': [
                "筛选期（-2周至0周）",
                "治疗期（根据研究设计）",
                "随访期（治疗结束后4-12周）"
            ]
        }
    
    def _generate_intervention(self, indication: str) -> str:
        """生成干预措施描述"""
        return f"研究药物，根据 {indication} 标准治疗方案调整剂量"
    
    def _generate_statistical_plan(self) -> Dict[str, Any]:
        """生成统计分析计划"""
        return {
            'analysis_sets': [
                "全分析集（FAS）：意向性治疗原则",
                "符合方案集（PPS）：符合方案要求的患者",
                "安全性分析集（SS）：至少接受一次研究药物"
            ],
            'primary_analysis': "主要疗效指标的组间比较（协方差分析/卡方检验）",
            'secondary_analysis': [
                "次要疗效指标的组间比较",
                "亚组分析（年龄、性别、基线特征等）",
                "敏感性分析"
            ],
            'interim_analysis': "如设计包含中期分析，需明确分析时点和终止边界",
            'significance_level': "双侧 α = 0.05",
            'missing_data': "采用多重插补等方法处理缺失数据"
        }
    
    def _generate_safety_assessment(self) -> Dict[str, Any]:
        """生成安全性评估"""
        return {
            'adverse_events': "记录所有不良事件（AE）、严重不良事件（SAE）",
            'laboratory_tests': "血常规、生化、心电图等安全性指标",
            'vital_signs': "血压、心率、体温等",
            'physical_examination': "定期体格检查",
            'follow_up': "末次用药后30天安全性随访"
        }
    
    def _generate_data_management(self) -> Dict[str, Any]:
        """生成数据管理计划"""
        return {
            'edc_system': "使用电子数据采集系统（EDC）",
            'data_quality': "数据核查、质疑管理、源数据验证（SDV）",
            'database_lock': "数据库锁定流程和标准",
            'data_privacy': "符合 HIPAA/GDPR/个人信息保护法要求"
        }
    
    def _generate_ethical_considerations(self) -> Dict[str, Any]:
        """生成伦理考虑"""
        return {
            'irb_approval': "研究方案需经伦理审查委员会（IRB/IEC）批准",
            'informed_consent': "所有受试者需签署书面知情同意书",
            'risk_benefit': "评估研究风险与获益比",
            'patient_rights': "保护受试者权益，允许随时退出研究",
            'data_confidentiality': "患者数据保密和去标识化处理"
        }


class RWEAnalyzer:
    """真实世界研究 (RWE) 分析工具"""
    
    def __init__(self):
        pass
    
    def generate_rwe_protocol(
        self,
        title: str,
        indication: str,
        study_type: str = "回顾性队列研究",
        data_source: str = "电子病历数据库",
        study_period: str = "2020-2025"
    ) -> Dict[str, Any]:
        """生成 RWE 研究方案"""
        return {
            'study_basic': {
                'title': title,
                'type': study_type,
                'indication': indication,
                'data_source': data_source,
                'study_period': study_period
            },
            'research_questions': [
                f"评价 {indication} 患者在真实临床实践中的治疗模式",
                f"分析 {indication} 患者的临床结局和预后因素",
                "评估真实世界中治疗方案的安全性和依从性"
            ],
            'study_population': {
                'source': data_source,
                'inclusion': [
                    f"明确诊断为 {indication}",
                    f"诊断时间在 {study_period} 期间",
                    "年龄 ≥ 18 岁"
                ],
                'exclusion': [
                    "合并其他严重疾病可能影响结局",
                    "基线数据不完整",
                    "参加干预性临床试验期间"
                ]
            },
            'variables': self._generate_rwe_variables(),
            'outcome_measures': self._generate_rwe_outcomes(indication),
            'statistical_methods': self._generate_rwe_statistics(),
            'bias_assessment': [
                "选择偏倚评估",
                "混杂因素控制（倾向得分匹配、多因素回归）",
                "敏感性分析",
                "缺失数据处理"
            ],
            'reporting_guideline': "符合 STROBE 声明（观察性研究报告规范）"
        }
    
    def _generate_rwe_variables(self) -> Dict[str, List[str]]:
        """生成 RWE 研究变量"""
        return {
            'demographics': ['年龄', '性别', '种族', 'BMI', '吸烟史', '饮酒史'],
            'clinical': ['诊断', '合并症', '病程', '严重程度', '既往治疗史'],
            'treatment': ['药物治疗方案', '剂量', '疗程', '依从性', '治疗转换'],
            'outcome': ['主要终点事件', '死亡率', '住院率', '急诊就诊率'],
            'healthcare_utilization': ['医疗费用', '住院天数', '门诊次数']
        }
    
    def _generate_rwe_outcomes(self, indication: str) -> List[str]:
        """生成 RWE 研究终点"""
        return [
            f"{indication} 相关住院率",
            "全因死亡率",
            "治疗依从性和持续性",
            "急性发作/加重率",
            "医疗资源使用和费用"
        ]
    
    def _generate_rwe_statistics(self) -> List[str]:
        """生成 RWE 统计方法"""
        return [
            "描述性统计：人口学和基线特征",
            "生存分析：Kaplan-Meier 曲线、Cox 比例风险模型",
            "倾向得分匹配（PSM）：控制混杂因素",
            "多因素回归分析：识别预后因素",
            "亚组分析：不同人群的疗效差异",
            "敏感性分析：验证结果稳健性"
        ]


class StudyReportGenerator:
    """研究报告生成器"""
    
    def __init__(self):
        pass
    
    def generate_consort_checklist(self) -> Dict[str, List[str]]:
        """生成 CONSORT 声明检查清单（RCT 报告规范）"""
        return {
            'title_and_abstract': [
                "研究设计类型（如平行、交叉）",
                "重要的方法、结果、结论摘要"
            ],
            'introduction': [
                "科学背景和原理解释",
                "研究目的和假设"
            ],
            'methods': [
                "试验设计（设计类型、分组比例）",
                "研究对象（入排标准、研究场所）",
                "干预措施（各组干预详情）",
                "结局指标（主要、次要终点定义）",
                "样本量计算（原理和方法）",
                "随机化（序列生成、隐藏、实施）",
                "盲法（谁被设盲、如何实施）",
                "统计方法（主要和次要分析）"
            ],
            'results': [
                "受试者流程（纳入、随机化、失访）",
                "基线资料（各组人口学和临床特征）",
                "分析人数（各分析集的样本量）",
                "结局和估计值（主要和次要结果）",
                "不良事件（各组不良事件情况）"
            ],
            'discussion': [
                "结果解释（考虑研究假设、潜在偏倚）",
                "可推广性（研究结果的适用范围）",
                "总体证据（结合现有证据的综合评价）"
            ],
            'other_info': [
                "试验注册（注册号和注册机构）",
                "研究方案（可获取完整方案的途径）",
                "基金支持（资助来源）"
            ]
        }
    
    def generate_strobe_checklist(self) -> Dict[str, List[str]]:
        """生成 STROBE 声明检查清单（观察性研究报告规范）"""
        return {
            'title_and_abstract': [
                "明确研究设计类型（队列、病例对照、横断面）",
                "研究主要内容摘要"
            ],
            'introduction': [
                "研究背景和科学依据",
                "研究目的"
            ],
            'methods': [
                "研究设计（研究类型、时间框架）",
                "研究现场（数据来源、研究机构）",
                "研究对象（入排标准、来源、随访）",
                "变量（暴露、结局、混杂因素定义）",
                "数据来源/测量（数据收集方法和质量）",
                "偏倚（可能的偏倚来源和控制措施）",
                "样本量（样本量确定依据）",
                "统计学方法（统计分析方法描述）"
            ],
            'results': [
                "研究对象（流程、随访时间、失访）",
                "描述性资料（研究对象特征）",
                "结局数据（结局事件数或统计量）",
                "主要结果（效应估计值和可信区间）",
                "其他分析（亚组分析、敏感性分析）"
            ],
            'discussion': [
                "主要结果总结",
                "局限性（研究的潜在偏倚和不足）",
                "解释（考虑研究目的、局限性、多因素）",
                "可推广性（结果外推的可能性）"
            ],
            'other_info': [
                "基金支持（资助来源）",
                "利益冲突声明"
            ]
        }
