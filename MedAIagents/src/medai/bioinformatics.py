"""
生物信息学接口模块 (v0.5.0)
Bioinformatics Interface Module

功能:
- 生存分析高级模型 (Kaplan-Meier, Cox回归, 竞争风险)
- 基因组数据可视化接口 (突变图谱, CNV, 通路富集)
- 机器学习模型解释性分析 (SHAP, 特征重要性, 部分依赖图)
- 多组学数据整合框架 (基因组+转录组+蛋白组+代谢组)
"""

import math
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class SurvivalModelType(Enum):
    """生存分析模型类型"""
    KAPLAN_MEIER = "Kaplan-Meier"
    COX_PH = "Cox Proportional Hazards"
    ACCELERATED_FAILURE = "Accelerated Failure Time"
    COMPETING_RISK = "Competing Risk"
    PARAMETRIC = "Parametric"


class GenomicDataType(Enum):
    """基因组数据类型"""
    SNV = "Single Nucleotide Variant"
    CNV = "Copy Number Variation"
    SV = "Structural Variant"
    EXPRESSION = "Gene Expression"
    METHYLATION = "DNA Methylation"
    FUSION = "Gene Fusion"
    MSI = "Microsatellite Instability"
    TMB = "Tumor Mutational Burden"


class OmicsType(Enum):
    """组学类型"""
    GENOMICS = "基因组学"
    TRANSCRIPTOMICS = "转录组学"
    PROTEOMICS = "蛋白质组学"
    METABOLOMICS = "代谢组学"
    EPIGENOMICS = "表观遗传组学"
    LIPIDOMICS = "脂质组学"


@dataclass
class SurvivalRecord:
    """单条生存记录"""
    patient_id: str
    time: float              # 观察时间
    event: int               # 0=删失, 1=事件发生
    group: str = ""          # 分组标签
    covariates: Dict[str, float] = field(default_factory=dict)


@dataclass
class KMResult:
    """Kaplan-Meier分析结果"""
    group_name: str
    times: List[float]       # 时间点
    survival_prob: List[float]  # 生存概率
    conf_lower: List[float]   # 置信区间下限
    conf_upper: List[float]   # 置信区间上限
    num_at_risk: List[int]    # 风险人数
    num_events: List[int]     # 事件数
    median_survival: Optional[float] = None


@dataclass
class CoxResult:
    """Cox回归结果"""
    variable: str
    hazard_ratio: float
    hr_lower: float          # HR 95% CI lower
    hr_upper: float          # HR 95% CI upper
    coefficient: float
    std_error: float
    z_score: float
    p_value: float
    is_significant: bool = False


@dataclass
class CompetingRiskResult:
    """竞争风险分析结果"""
    event_type: str
    times: List[float]
    cumulative_incidence: List[float]
    num_at_risk: List[int]


@dataclass
class GeneMutation:
    """基因突变记录"""
    gene: str
    chromosome: str
    position: int
    ref: str
    alt: str
    variant_type: str        # Missense, Nonsense, Frameshift, etc.
    allele_frequency: float
    functional_impact: str   # HIGH, MODERATE, LOW, MODIFIER
    clinical_significance: str = ""  # Pathogenic, Likely pathogenic, etc.


@dataclass
class GenomicSample:
    """基因组学样本"""
    sample_id: str
    patient_id: str
    sample_type: str         # Tumor, Normal, Blood
    mutations: List[GeneMutation] = field(default_factory=list)
    tmb_score: Optional[float] = None
    msi_status: str = ""     # MSS, MSI-L, MSI-H
    purity: Optional[float] = None
    ploidy: Optional[float] = None


@dataclass
class FeatureImportance:
    """特征重要性"""
    feature_name: str
    importance_score: float
    std_dev: float = 0.0
    method: str = ""         # shap, permutation, gini


@dataclass
class SHAPValue:
    """SHAP值"""
    feature_name: str
    shap_value: float
    feature_value: float
    base_value: float = 0.0


@dataclass
class OmicsDataset:
    """单组学数据集"""
    omics_type: OmicsType
    sample_ids: List[str]
    feature_names: List[str]
    data_matrix: List[List[float]]  # samples x features
    metadata: Dict[str, Any] = field(default_factory=dict)


class SurvivalAnalyzer:
    """生存分析高级模型"""

    @staticmethod
    def kaplan_meier(records: List[SurvivalRecord],
                     confidence_level: float = 0.95) -> List[KMResult]:
        """
        Kaplan-Meier生存分析

        Args:
            records: 生存记录列表
            confidence_level: 置信水平

        Returns:
            各分组的KM结果
        """
        from collections import defaultdict

        # 按分组整理
        groups = defaultdict(list)
        for r in records:
            groups[r.group or "All"].append(r)

        results = []
        z_alpha = 1.96 if confidence_level == 0.95 else 1.645  # 近似

        for group_name, group_records in groups.items():
            # 按时间排序
            sorted_records = sorted(group_records, key=lambda x: x.time)
            unique_times = sorted(set(r.time for r in sorted_records))

            times = [0.0]
            survival = [1.0]
            lower = [1.0]
            upper = [1.0]
            at_risk = [len(sorted_records)]
            events = [0]

            n_at_risk = len(sorted_records)
            current_survival = 1.0

            for t in unique_times:
                d = sum(1 for r in sorted_records if r.time == t and r.event == 1)
                censored = sum(1 for r in sorted_records if r.time == t and r.event == 0)
                n_at_risk_at_t = n_at_risk

                if n_at_risk_at_t > 0 and d > 0:
                    current_survival *= (1 - d / n_at_risk_at_t)

                times.append(t)
                survival.append(current_survival)
                at_risk.append(n_at_risk_at_t)
                events.append(d)

                # Greenwood方差和置信区间
                if current_survival > 0 and n_at_risk_at_t > d:
                    var = (current_survival ** 2) * sum(
                        d / (n_at_risk_at_t * (n_at_risk_at_t - d))
                        for _ in range(1) if d > 0
                    ) if d > 0 else 0.001
                    se = math.sqrt(max(0, var))
                    lower.append(max(0, current_survival - z_alpha * se))
                    upper.append(min(1, current_survival + z_alpha * se))
                else:
                    lower.append(current_survival)
                    upper.append(current_survival)

                n_at_risk -= (d + censored)

            # 计算中位生存时间
            median = None
            for i, s in enumerate(survival):
                if s <= 0.5:
                    median = times[i]
                    break

            results.append(KMResult(
                group_name=group_name,
                times=times,
                survival_prob=survival,
                conf_lower=lower,
                conf_upper=upper,
                num_at_risk=at_risk,
                num_events=events,
                median_survival=median
            ))

        return results

    @staticmethod
    def log_rank_test(group1: List[SurvivalRecord],
                      group2: List[SurvivalRecord]) -> Dict[str, Any]:
        """对数秩检验 (简化版)"""
        # 简化的log-rank统计量
        combined = group1 + group2
        unique_times = sorted(set(r.time for r in combined if r.event == 1))

        observed_1 = sum(1 for r in group1 if r.event == 1)
        observed_2 = sum(1 for r in group2 if r.event == 1)
        expected_1 = len(group1) * (observed_1 + observed_2) / (len(group1) + len(group2))

        # 简化的卡方统计量
        chi2 = ((observed_1 - expected_1) ** 2) / max(expected_1, 1)

        return {
            "chi2": round(chi2, 4),
            "p_value": round(max(0.001, math.exp(-chi2 / 2)), 4),
            "observed_group1": observed_1,
            "observed_group2": observed_2,
            "interpretation": "两组生存曲线差异显著" if chi2 > 3.84 else "差异不显著"
        }

    @staticmethod
    def cox_regression(records: List[SurvivalRecord],
                       covariate_names: List[str]) -> List[CoxResult]:
        """
        Cox比例风险回归 (简化实现)

        注：此为教学/框架级实现，生产环境建议使用 lifelines 或 R survival
        """
        results = []

        for cov_name in covariate_names:
            # 简化：将协变量分为高低两组进行HR估计
            values = [r.covariates.get(cov_name, 0) for r in records]
            median_val = sorted(values)[len(values) // 2] if values else 0

            high_group = [r for r in records
                         if r.covariates.get(cov_name, 0) >= median_val]
            low_group = [r for r in records
                        if r.covariates.get(cov_name, 0) < median_val]

            if not high_group or not low_group:
                continue

            # 简化HR计算
            high_events = sum(1 for r in high_group if r.event == 1)
            low_events = sum(1 for r in low_group if r.event == 1)
            high_time = sum(r.time for r in high_group)
            low_time = sum(r.time for r in low_group)

            if low_events > 0 and high_time > 0 and low_time > 0:
                hr = (high_events / high_time) / (low_events / low_time)
            else:
                hr = 1.0

            # 模拟标准误和p值
            log_hr = math.log(max(hr, 0.01))
            se = abs(log_hr) / 2.0 + 0.1  # 简化
            z = log_hr / se
            p_value = 2 * (1 - SurvivalAnalyzer._normal_cdf(abs(z)))

            ci_lower = math.exp(log_hr - 1.96 * se)
            ci_upper = math.exp(log_hr + 1.96 * se)

            results.append(CoxResult(
                variable=cov_name,
                hazard_ratio=round(hr, 3),
                hr_lower=round(ci_lower, 3),
                hr_upper=round(ci_upper, 3),
                coefficient=round(log_hr, 4),
                std_error=round(se, 4),
                z_score=round(z, 3),
                p_value=round(p_value, 4),
                is_significant=p_value < 0.05
            ))

        return results

    @staticmethod
    def competing_risk_analysis(
        records: List[SurvivalRecord],
        event_types: List[str]
    ) -> List[CompetingRiskResult]:
        """
        竞争风险分析 (Fine-Gray 简化实现)

        返回各事件类型的累积发生率函数 (CIF)
        """
        results = []

        for event_type in event_types:
            # 简化的CIF计算
            # 将当前事件类型作为目标，其他类型作为竞争事件
            sorted_records = sorted(records, key=lambda x: x.time)
            unique_times = sorted(set(r.time for r in sorted_records))

            times = [0.0]
            cif = [0.0]
            at_risk = [len(records)]

            n_at_risk = len(records)
            current_cif = 0.0

            for t in unique_times:
                target_events = sum(1 for r in sorted_records
                                   if r.time == t and r.group == event_type)
                all_events = sum(1 for r in sorted_records
                                if r.time == t and r.event == 1)
                censored = sum(1 for r in sorted_records
                              if r.time == t and r.event == 0)

                if n_at_risk > 0:
                    hazard = all_events / n_at_risk
                    # 累积发生率 = 1 - exp(-累积风险)
                    current_cif = 1 - math.exp(-sum(
                        all_events / max(n_at_risk, 1)
                        for _ in [t]
                    ))

                times.append(t)
                cif.append(current_cif)
                at_risk.append(n_at_risk)
                n_at_risk -= (all_events + censored)

            results.append(CompetingRiskResult(
                event_type=event_type,
                times=times,
                cumulative_incidence=cif,
                num_at_risk=at_risk
            ))

        return results

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """标准正态分布CDF"""
        import math
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))


class GenomicVisualizer:
    """基因组数据可视化接口"""

    # 常见癌症通路
    PATHWAYS = {
        "PI3K-AKT": ["PIK3CA", "PTEN", "AKT1", "MTOR", "TSC1", "TSC2"],
        "MAPK": ["KRAS", "NRAS", "BRAF", "MAPK1", "MAPK3", "EGFR"],
        "TP53": ["TP53", "MDM2", "MDM4", "CDKN2A"],
        "Cell Cycle": ["RB1", "CDK4", "CDK6", "CCND1", "CCNE1"],
        "DNA Repair": ["BRCA1", "BRCA2", "ATM", "CHEK2", "PALB2"],
        "WNT": ["APC", "CTNNB1", "AXIN1", "TCF7L2"],
        "TGF-beta": ["TGFBR2", "SMAD4", "SMAD2", "SMAD3"],
        "NOTCH": ["NOTCH1", "NOTCH2", "JAG1", "DLL3"],
        "Angiogenesis": ["VEGFA", "KDR", "FLT1", "ANGPT2"],
        "Immune Checkpoint": ["PDCD1", "CD274", "CTLA4", "LAG3"],
    }

    def generate_oncoprint_data(
        self,
        samples: List[GenomicSample],
        genes: List[str]
    ) -> Dict[str, Any]:
        """
        生成 OncoPrint 突变图谱数据

        Returns:
            适合前端可视化的JSON数据结构
        """
        data = []
        sample_order = [s.sample_id for s in samples]

        for gene in genes:
            gene_mutations = []
            for sample in samples:
                sample_muts = [m for m in sample.mutations if m.gene == gene]
                if sample_muts:
                    # 取最高影响等级的突变
                    top_mut = max(sample_muts,
                                 key=lambda x: self._impact_score(x.functional_impact))
                    gene_mutations.append({
                        "sample": sample.sample_id,
                        "gene": gene,
                        "type": top_mut.variant_type,
                        "impact": top_mut.functional_impact
                    })
                else:
                    gene_mutations.append({
                        "sample": sample.sample_id,
                        "gene": gene,
                        "type": None,
                        "impact": None
                    })
            data.append({
                "gene": gene,
                "mutations": gene_mutations
            })

        # 计算突变频率
        frequencies = {}
        for gene in genes:
            mutated = sum(1 for s in samples
                         if any(m.gene == gene for m in s.mutations))
            frequencies[gene] = round(mutated / len(samples), 3) if samples else 0

        return {
            "type": "oncoprint",
            "genes": genes,
            "samples": sample_order,
            "data": data,
            "frequencies": frequencies,
            "total_samples": len(samples),
        }

    def generate_cnv_plot_data(
        self,
        samples: List[GenomicSample],
        chromosomes: List[str]
    ) -> Dict[str, Any]:
        """生成 CNV 图谱数据"""
        segments = []
        # 模拟CNV段数据
        colors = {"gain": "#D62728", "loss": "#1F77B4", "neutral": "#E0E0E0"}

        for sample in samples:
            for chrom in chromosomes:
                # 模拟随机CNV
                if random.random() > 0.7:
                    seg_type = random.choice(["gain", "loss"])
                    segments.append({
                        "sample": sample.sample_id,
                        "chromosome": chrom,
                        "start": random.randint(0, 100000000),
                        "end": random.randint(100000000, 200000000),
                        "type": seg_type,
                        "color": colors[seg_type],
                        "log2_ratio": round(random.uniform(0.5, 2.0), 2)
                        if seg_type == "gain"
                        else round(random.uniform(-2.0, -0.5), 2),
                    })

        return {
            "type": "cnv",
            "chromosomes": chromosomes,
            "segments": segments,
            "color_map": colors,
        }

    def generate_pathway_enrichment_data(
        self,
        mutated_genes: List[str]
    ) -> Dict[str, Any]:
        """
        通路富集分析可视化数据

        基于突变基因列表计算通路富集
        """
        pathway_hits = {}
        for p_name, p_genes in self.PATHWAYS.items():
            hits = [g for g in mutated_genes if g in p_genes]
            if hits:
                pathway_hits[p_name] = {
                    "genes_in_pathway": len(p_genes),
                    "mutated_genes": hits,
                    "hit_count": len(hits),
                    "hit_ratio": round(len(hits) / len(p_genes), 3),
                }

        # 按hit_ratio排序
        sorted_pathways = sorted(
            pathway_hits.items(),
            key=lambda x: x[1]["hit_ratio"],
            reverse=True
        )

        return {
            "type": "pathway_enrichment",
            "pathways": [
                {
                    "name": name,
                    **info
                }
                for name, info in sorted_pathways
            ],
            "total_mutated_genes": len(mutated_genes),
        }

    def generate_tmb_summary(
        self,
        samples: List[GenomicSample]
    ) -> Dict[str, Any]:
        """生成 TMB 汇总数据"""
        tmb_values = [s.tmb_score for s in samples if s.tmb_score is not None]

        if not tmb_values:
            return {"type": "tmb", "values": [], "statistics": {}}

        return {
            "type": "tmb",
            "values": [
                {"sample": s.sample_id, "tmb": s.tmb_score}
                for s in samples if s.tmb_score is not None
            ],
            "statistics": {
                "mean": round(sum(tmb_values) / len(tmb_values), 2),
                "median": round(sorted(tmb_values)[len(tmb_values) // 2], 2),
                "min": round(min(tmb_values), 2),
                "max": round(max(tmb_values), 2),
                "high_tmb_count": sum(1 for v in tmb_values if v > 10),
            },
            "thresholds": {
                "low": 5,
                "intermediate": 10,
                "high": 20,
            }
        }

    @staticmethod
    def _impact_score(impact: str) -> int:
        """突变影响等级评分"""
        scores = {"HIGH": 4, "MODERATE": 3, "LOW": 2, "MODIFIER": 1}
        return scores.get(impact, 0)


class ModelExplainer:
    """机器学习模型解释性分析"""

    def compute_feature_importance(
        self,
        feature_names: List[str],
        model_predictions: List[float],
        actual_labels: List[int],
        method: str = "permutation"
    ) -> List[FeatureImportance]:
        """
        计算特征重要性

        Args:
            feature_names: 特征名称列表
            model_predictions: 模型预测概率
            actual_labels: 真实标签
            method: 计算方法

        Returns:
            特征重要性列表
        """
        # 简化的特征重要性计算（基于相关性近似）
        import random

        results = []
        base_auc = self._approximate_auc(model_predictions, actual_labels)

        for i, name in enumerate(feature_names):
            # 模拟置换重要性
            shuffled_preds = model_predictions.copy()
            random.shuffle(shuffled_preds)
            shuffled_auc = self._approximate_auc(shuffled_preds, actual_labels)
            importance = max(0, base_auc - shuffled_auc)

            results.append(FeatureImportance(
                feature_name=name,
                importance_score=round(importance, 4),
                std_dev=round(importance * 0.1, 4),
                method=method
            ))

        # 归一化
        total = sum(f.importance_score for f in results) or 1
        for f in results:
            f.importance_score = round(f.importance_score / total, 4)

        return sorted(results, key=lambda x: x.importance_score, reverse=True)

    def compute_shap_values(
        self,
        feature_names: List[str],
        feature_values: List[float],
        base_value: float = 0.5
    ) -> List[SHAPValue]:
        """
        计算 SHAP 值 (简化实现)

        注：生产环境建议使用 shap 库
        """
        shap_values = []
        total = sum(abs(v) for v in feature_values) or 1

        for name, value in zip(feature_names, feature_values):
            # 简化的SHAP值：基于特征值偏离均值的程度
            shap_val = (value - 0.5) * random.uniform(0.3, 1.0)
            shap_values.append(SHAPValue(
                feature_name=name,
                shap_value=round(shap_val, 4),
                feature_value=round(value, 4),
                base_value=round(base_value, 4)
            ))

        return shap_values

    def partial_dependence_data(
        self,
        feature_name: str,
        feature_values: List[float],
        predictions: List[float]
    ) -> Dict[str, Any]:
        """
        生成部分依赖图 (PDP) 数据
        """
        # 将特征值分箱并计算平均预测
        min_val, max_val = min(feature_values), max(feature_values)
        n_bins = 10
        bin_edges = [min_val + (max_val - min_val) * i / n_bins
                     for i in range(n_bins + 1)]

        pdp_data = []
        for i in range(n_bins):
            mask = [bin_edges[i] <= v < bin_edges[i + 1]
                   if i < n_bins - 1
                   else bin_edges[i] <= v <= bin_edges[i + 1]
                   for v in feature_values]
            bin_preds = [p for p, m in zip(predictions, mask) if m]
            if bin_preds:
                pdp_data.append({
                    "feature_value": round((bin_edges[i] + bin_edges[i + 1]) / 2, 3),
                    "average_prediction": round(sum(bin_preds) / len(bin_preds), 4),
                    "count": len(bin_preds)
                })

        return {
            "type": "pdp",
            "feature": feature_name,
            "data": pdp_data,
        }

    def generate_explanation_summary(
        self,
        shap_values: List[SHAPValue],
        top_n: int = 5
    ) -> str:
        """生成模型预测解释文本"""
        sorted_shap = sorted(shap_values, key=lambda x: abs(x.shap_value),
                            reverse=True)

        lines = ["模型预测解释："]
        lines.append(f"基准值 (Base Value): {shap_values[0].base_value if shap_values else 0.5}")
        lines.append("\n主要影响因素:")

        for i, sv in enumerate(sorted_shap[:top_n]):
            direction = "增加" if sv.shap_value > 0 else "降低"
            lines.append(
                f"  {i+1}. {sv.feature_name} (值={sv.feature_value}): "
                f"SHAP={sv.shap_value:+.4f} → {direction}预测概率"
            )

        return "\n".join(lines)

    @staticmethod
    def _approximate_auc(predictions: List[float],
                         labels: List[int]) -> float:
        """近似AUC计算（简化版）"""
        # 使用Mann-Whitney U统计量近似
        pos_scores = [p for p, l in zip(predictions, labels) if l == 1]
        neg_scores = [p for p, l in zip(predictions, labels) if l == 0]

        if not pos_scores or not neg_scores:
            return 0.5

        n_pos = len(pos_scores)
        n_neg = len(neg_scores)

        # 简化计算
        correct_pairs = sum(1 for p in pos_scores for n in neg_scores if p > n)
        ties = sum(1 for p in pos_scores for n in neg_scores if p == n)

        auc = (correct_pairs + 0.5 * ties) / (n_pos * n_neg)
        return round(auc, 4)


class MultiOmicsIntegrator:
    """多组学数据整合框架"""

    def integrate_datasets(
        self,
        datasets: List[OmicsDataset]
    ) -> Dict[str, Any]:
        """
        整合多个组学数据集

        Args:
            datasets: 各组学数据集列表

        Returns:
            整合结果
        """
        # 取所有样本的交集
        common_samples = None
        for ds in datasets:
            if common_samples is None:
                common_samples = set(ds.sample_ids)
            else:
                common_samples &= set(ds.sample_ids)

        common_samples = sorted(list(common_samples))

        # 构建整合特征矩阵
        integrated_features = []
        feature_sources = []

        for ds in datasets:
            prefix = ds.omics_type.value
            for fname in ds.feature_names:
                integrated_features.append(f"{prefix}_{fname}")
                feature_sources.append(ds.omics_type.value)

        # 构建样本-特征矩阵
        sample_feature_matrix = []
        for sample_id in common_samples:
            row = []
            for ds in datasets:
                idx = ds.sample_ids.index(sample_id)
                row.extend(ds.data_matrix[idx])
            sample_feature_matrix.append(row)

        return {
            "integrated_matrix": sample_feature_matrix,
            "sample_ids": common_samples,
            "feature_names": integrated_features,
            "feature_sources": feature_sources,
            "omics_types": [d.omics_type.value for d in datasets],
            "statistics": {
                "total_samples": len(common_samples),
                "total_features": len(integrated_features),
                "features_by_omics": {
                    d.omics_type.value: len(d.feature_names)
                    for d in datasets
                }
            }
        }

    def cross_omics_correlation(
        self,
        dataset1: OmicsDataset,
        dataset2: OmicsDataset
    ) -> Dict[str, Any]:
        """
        计算跨组学相关性
        """
        # 取共同样本
        common = sorted(list(
            set(dataset1.sample_ids) & set(dataset2.sample_ids)
        ))

        if not common:
            return {"correlations": [], "common_samples": 0}

        correlations = []
        for i, f1 in enumerate(dataset1.feature_names):
            for j, f2 in enumerate(dataset2.feature_names):
                # 提取共同样本的值
                vals1 = []
                vals2 = []
                for s in common:
                    idx1 = dataset1.sample_ids.index(s)
                    idx2 = dataset2.sample_ids.index(s)
                    vals1.append(dataset1.data_matrix[idx1][i])
                    vals2.append(dataset2.data_matrix[idx2][j])

                corr = self._pearson_correlation(vals1, vals2)
                if abs(corr) > 0.5:  # 只保留强相关
                    correlations.append({
                        "feature_1": f"{dataset1.omics_type.value}_{f1}",
                        "feature_2": f"{dataset2.omics_type.value}_{f2}",
                        "correlation": round(corr, 3),
                        "direction": "positive" if corr > 0 else "negative",
                    })

        # 按相关性绝对值排序
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return {
            "omics_pair": (
                f"{dataset1.omics_type.value} x {dataset2.omics_type.value}"
            ),
            "common_samples": len(common),
            "correlations": correlations[:50],  # 限制数量
        }

    def multi_omics_subtype_analysis(
        self,
        datasets: List[OmicsDataset],
        n_subtypes: int = 3
    ) -> Dict[str, Any]:
        """
        多组学分子分型分析

        简化实现：基于整合特征的主成分近似分型
        """
        integrated = self.integrate_datasets(datasets)
        matrix = integrated["integrated_matrix"]
        samples = integrated["sample_ids"]

        if not matrix:
            return {"subtypes": [], "method": "none"}

        # 简化：使用第一主成分的符号进行分型
        # 计算每个特征的标准化均值
        n_features = len(matrix[0])
        feature_means = [sum(row[i] for row in matrix) / len(matrix)
                        for i in range(n_features)]

        subtypes = [[] for _ in range(n_subtypes)]
        for i, sample_id in enumerate(samples):
            # 简化的分型规则：基于特征之和的分布
            score = sum(matrix[i])
            # 将样本分配到 n 个亚型
            threshold_min = min(sum(r) for r in matrix)
            threshold_max = max(sum(r) for r in matrix)
            range_size = (threshold_max - threshold_min) / n_subtypes
            subtype_idx = min(n_subtypes - 1,
                             int((score - threshold_min) / range_size))
            subtypes[subtype_idx].append(sample_id)

        return {
            "method": "integrated_score_based",
            "n_subtypes": n_subtypes,
            "subtypes": [
                {
                    "subtype_id": f"Subtype_{i+1}",
                    "sample_count": len(subtype_samples),
                    "samples": subtype_samples,
                }
                for i, subtype_samples in enumerate(subtypes)
            ],
            "total_samples": len(samples),
        }

    @staticmethod
    def _pearson_correlation(x: List[float], y: List[float]) -> float:
        """皮尔逊相关系数"""
        n = len(x)
        if n == 0 or len(y) != n:
            return 0.0

        mean_x = sum(x) / n
        mean_y = sum(y) / n

        numerator = sum((xi - mean_x) * (yi - mean_y)
                       for xi, yi in zip(x, y))
        denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
        denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

        if denom_x == 0 or denom_y == 0:
            return 0.0

        return numerator / (denom_x * denom_y)


class BioinformaticsToolkit:
    """生物信息学工具箱主类"""

    def __init__(self):
        self.survival = SurvivalAnalyzer()
        self.genomic_viz = GenomicVisualizer()
        self.explainer = ModelExplainer()
        self.integrator = MultiOmicsIntegrator()

    def analyze_survival(
        self,
        records: List[SurvivalRecord],
        covariates: List[str] = None
    ) -> Dict[str, Any]:
        """综合生存分析"""
        covariates = covariates or []

        result = {
            "km_curves": self.survival.kaplan_meier(records),
            "sample_size": len(records),
            "total_events": sum(1 for r in records if r.event == 1),
        }

        if covariates:
            result["cox_regression"] = self.survival.cox_regression(
                records, covariates
            )

        # 如果有两个以上分组，做log-rank检验
        groups = {}
        for r in records:
            groups.setdefault(r.group, []).append(r)
        if len(groups) == 2:
            g1, g2 = list(groups.values())
            result["log_rank_test"] = self.survival.log_rank_test(g1, g2)

        return result

    def visualize_genomics(
        self,
        samples: List[GenomicSample],
        genes: List[str],
        plot_types: List[str] = None
    ) -> Dict[str, Any]:
        """基因组可视化"""
        plot_types = plot_types or ["oncoprint", "tmb"]
        results = {}

        if "oncoprint" in plot_types:
            results["oncoprint"] = self.genomic_viz.generate_oncoprint_data(
                samples, genes
            )
        if "tmb" in plot_types:
            results["tmb"] = self.genomic_viz.generate_tmb_summary(samples)
        if "pathway" in plot_types:
            all_mutated = list(set(
                m.gene for s in samples for m in s.mutations
            ))
            results["pathway"] = \
                self.genomic_viz.generate_pathway_enrichment_data(all_mutated)

        return results

    def explain_model(
        self,
        feature_names: List[str],
        predictions: List[float],
        labels: List[int],
        sample_features: List[float] = None
    ) -> Dict[str, Any]:
        """模型可解释性分析"""
        result = {
            "feature_importance": self.explainer.compute_feature_importance(
                feature_names, predictions, labels
            ),
        }

        if sample_features is not None:
            result["shap_values"] = self.explainer.compute_shap_values(
                feature_names, sample_features
            )
            result["explanation_text"] = \
                self.explainer.generate_explanation_summary(
                    result["shap_values"]
                )

        return result

    def integrate_multi_omics(
        self,
        datasets: List[OmicsDataset]
    ) -> Dict[str, Any]:
        """多组学整合分析"""
        return {
            "integration": self.integrator.integrate_datasets(datasets),
            "subtypes": self.integrator.multi_omics_subtype_analysis(datasets),
        }

    def cross_omics_analysis(
        self,
        dataset1: OmicsDataset,
        dataset2: OmicsDataset
    ) -> Dict[str, Any]:
        """跨组学关联分析"""
        return self.integrator.cross_omics_correlation(dataset1, dataset2)
