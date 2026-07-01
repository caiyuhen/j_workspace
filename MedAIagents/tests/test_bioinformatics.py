"""
生物信息学模块单元测试
Bioinformatics Module Unit Tests
"""

import pytest
import math

from medai.bioinformatics import (
    SurvivalModelType, GenomicDataType, OmicsType,
    SurvivalRecord, KMResult, CoxResult,
    CompetingRiskResult, GeneMutation, GenomicSample,
    FeatureImportance, SHAPValue, OmicsDataset,
    SurvivalAnalyzer, GenomicVisualizer,
    ModelExplainer, MultiOmicsIntegrator,
    BioinformaticsToolkit
)


class TestEnums:
    """枚举类型测试"""

    def test_survival_model_types(self):
        assert SurvivalModelType.KAPLAN_MEIER.value == "Kaplan-Meier"
        assert SurvivalModelType.COX_PH.value == "Cox Proportional Hazards"

    def test_genomic_data_types(self):
        assert GenomicDataType.SNV.value == "Single Nucleotide Variant"
        assert GenomicDataType.CNV.value == "Copy Number Variation"

    def test_omics_types(self):
        assert OmicsType.GENOMICS.value == "基因组学"
        assert OmicsType.TRANSCRIPTOMICS.value == "转录组学"


class TestSurvivalAnalyzer:
    """生存分析器测试"""

    @pytest.fixture
    def sample_records(self):
        return [
            SurvivalRecord(patient_id="P1", time=12, event=1, group="A", covariates={"age": 65}),
            SurvivalRecord(patient_id="P2", time=24, event=0, group="A", covariates={"age": 70}),
            SurvivalRecord(patient_id="P3", time=8, event=1, group="A", covariates={"age": 55}),
            SurvivalRecord(patient_id="P4", time=36, event=0, group="A", covariates={"age": 60}),
            SurvivalRecord(patient_id="P5", time=6, event=1, group="B", covariates={"age": 75}),
            SurvivalRecord(patient_id="P6", time=18, event=1, group="B", covariates={"age": 68}),
            SurvivalRecord(patient_id="P7", time=30, event=0, group="B", covariates={"age": 62}),
            SurvivalRecord(patient_id="P8", time=10, event=1, group="B", covariates={"age": 72}),
        ]

    def test_kaplan_meier_basic(self, sample_records):
        results = SurvivalAnalyzer.kaplan_meier(sample_records)
        assert len(results) == 2  # 两个分组

        group_names = [r.group_name for r in results]
        assert "A" in group_names
        assert "B" in group_names

        for result in results:
            assert len(result.times) > 0
            assert len(result.survival_prob) > 0
            assert result.survival_prob[0] == 1.0
            assert all(0 <= s <= 1 for s in result.survival_prob)
            assert len(result.conf_lower) == len(result.times)
            assert len(result.conf_upper) == len(result.times)
            assert len(result.num_at_risk) == len(result.times)
            assert len(result.num_events) == len(result.times)

    def test_kaplan_meier_single_group(self):
        records = [
            SurvivalRecord(patient_id="P1", time=10, event=1),
            SurvivalRecord(patient_id="P2", time=20, event=0),
            SurvivalRecord(patient_id="P3", time=15, event=1),
        ]
        results = SurvivalAnalyzer.kaplan_meier(records)
        assert len(results) == 1
        assert results[0].group_name == "All"

    def test_kaplan_meier_median_survival(self, sample_records):
        results = SurvivalAnalyzer.kaplan_meier(sample_records)
        for result in results:
            # 中位生存时间应在数据范围内或None
            if result.median_survival is not None:
                assert result.median_survival >= 0

    def test_log_rank_test(self, sample_records):
        group_a = [r for r in sample_records if r.group == "A"]
        group_b = [r for r in sample_records if r.group == "B"]
        result = SurvivalAnalyzer.log_rank_test(group_a, group_b)

        assert 'chi2' in result
        assert 'p_value' in result
        assert result['chi2'] >= 0
        assert 0 <= result['p_value'] <= 1
        assert 'interpretation' in result

    def test_cox_regression(self, sample_records):
        results = SurvivalAnalyzer.cox_regression(
            sample_records, covariate_names=["age"]
        )
        assert len(results) >= 1
        for result in results:
            assert isinstance(result, CoxResult)
            assert result.variable == "age"
            assert result.hazard_ratio > 0
            assert result.hr_lower < result.hr_upper
            assert isinstance(result.is_significant, bool)
            assert result.p_value >= 0

    def test_cox_regression_empty_groups(self):
        records = [
            SurvivalRecord(patient_id="P1", time=10, event=1, covariates={"age": 50}),
            SurvivalRecord(patient_id="P2", time=10, event=1, covariates={"age": 50}),
        ]
        results = SurvivalAnalyzer.cox_regression(records, ["age"])
        # 当所有值相同时，可能无法分组
        assert isinstance(results, list)

    def test_competing_risk(self, sample_records):
        for r in sample_records:
            r.group = "event1" if r.patient_id in ["P1", "P3", "P5", "P6"] else "event2"
        results = SurvivalAnalyzer.competing_risk_analysis(
            sample_records, event_types=["event1", "event2"]
        )
        assert len(results) == 2
        for result in results:
            assert isinstance(result, CompetingRiskResult)
            assert len(result.times) > 0
            assert len(result.cumulative_incidence) > 0
            assert all(0 <= c <= 1 for c in result.cumulative_incidence)


class TestGenomicVisualizer:
    """基因组可视化测试"""

    @pytest.fixture
    def sample_samples(self):
        return [
            GenomicSample(
                sample_id="S1", patient_id="P1", sample_type="Tumor",
                mutations=[
                    GeneMutation("TP53", "chr17", 7579472, "G", "A", "Missense", 0.45, "HIGH"),
                    GeneMutation("KRAS", "chr12", 25398284, "C", "T", "Missense", 0.32, "MODERATE"),
                ],
                tmb_score=12.5,
                msi_status="MSS",
            ),
            GenomicSample(
                sample_id="S2", patient_id="P2", sample_type="Tumor",
                mutations=[
                    GeneMutation("TP53", "chr17", 7579472, "G", "A", "Nonsense", 0.51, "HIGH"),
                    GeneMutation("BRCA1", "chr17", 43051065, "A", "G", "Missense", 0.28, "MODERATE"),
                ],
                tmb_score=8.3,
                msi_status="MSI-H",
            ),
            GenomicSample(
                sample_id="S3", patient_id="P3", sample_type="Tumor",
                mutations=[
                    GeneMutation("EGFR", "chr7", 55249005, "C", "T", "Missense", 0.65, "HIGH"),
                ],
                tmb_score=5.2,
                msi_status="MSS",
            ),
        ]

    def test_generate_oncoprint_data(self, sample_samples):
        visualizer = GenomicVisualizer()
        result = visualizer.generate_oncoprint_data(
            sample_samples, genes=["TP53", "KRAS", "BRCA1", "EGFR"]
        )
        assert result['type'] == "oncoprint"
        assert result['total_samples'] == 3
        assert len(result['genes']) == 4
        assert len(result['samples']) == 3
        assert len(result['data']) == 4
        assert 'frequencies' in result
        assert result['frequencies']['TP53'] >= 0.5

    def test_generate_tmb_summary(self, sample_samples):
        visualizer = GenomicVisualizer()
        result = visualizer.generate_tmb_summary(sample_samples)
        assert result['type'] == "tmb"
        assert len(result['values']) == 3
        assert 'statistics' in result
        assert result['statistics']['mean'] > 0
        assert result['statistics']['high_tmb_count'] >= 0

    def test_pathway_enrichment(self):
        visualizer = GenomicVisualizer()
        mutated_genes = ["TP53", "KRAS", "BRCA1", "EGFR"]
        result = visualizer.generate_pathway_enrichment_data(mutated_genes)
        assert result['type'] == "pathway_enrichment"
        assert len(result['pathways']) > 0
        assert result['total_mutated_genes'] == 4

    def test_cnv_plot_data(self, sample_samples):
        visualizer = GenomicVisualizer()
        result = visualizer.generate_cnv_plot_data(
            sample_samples, chromosomes=["chr1", "chr2", "chr17"]
        )
        assert result['type'] == "cnv"
        assert 'segments' in result
        assert 'color_map' in result


class TestModelExplainer:
    """模型解释器测试"""

    def test_compute_feature_importance(self):
        explainer = ModelExplainer()
        feature_names = ["age", "gender", "smoking", "tumor_size"]
        predictions = [0.8, 0.3, 0.9, 0.5, 0.7, 0.2, 0.85, 0.4]
        labels = [1, 0, 1, 0, 1, 0, 1, 0]

        results = explainer.compute_feature_importance(
            feature_names, predictions, labels, method="permutation"
        )
        assert len(results) == 4
        total = sum(f.importance_score for f in results)
        assert abs(total - 1.0) < 0.01  # 归一化
        # 按重要性排序
        for i in range(len(results) - 1):
            assert results[i].importance_score >= results[i + 1].importance_score

    def test_compute_shap_values(self):
        explainer = ModelExplainer()
        feature_names = ["age", "tumor_size"]
        feature_values = [0.7, 0.5]

        results = explainer.compute_shap_values(feature_names, feature_values, base_value=0.5)
        assert len(results) == 2
        for r in results:
            assert r.feature_name in feature_names
            assert r.base_value == 0.5

    def test_partial_dependence_data(self):
        explainer = ModelExplainer()
        feature_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        predictions = [0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]

        result = explainer.partial_dependence_data("age", feature_values, predictions)
        assert result['type'] == "pdp"
        assert result['feature'] == "age"
        assert len(result['data']) > 0
        for point in result['data']:
            assert 'feature_value' in point
            assert 'average_prediction' in point
            assert 'count' in point

    def test_generate_explanation_summary(self):
        explainer = ModelExplainer()
        shap_values = [
            SHAPValue("age", 0.5, 65, 0.5),
            SHAPValue("tumor_size", -0.3, 2.5, 0.5),
            SHAPValue("gender", 0.1, 1, 0.5),
        ]
        summary = explainer.generate_explanation_summary(shap_values, top_n=2)
        assert "模型预测解释" in summary
        assert "age" in summary
        assert "Base Value" in summary

    def test_approximate_auc(self):
        explainer = ModelExplainer()
        predictions = [0.9, 0.8, 0.3, 0.2, 0.7, 0.1]
        labels = [1, 1, 0, 0, 1, 0]
        auc = explainer._approximate_auc(predictions, labels)
        assert 0 <= auc <= 1
        assert auc > 0.5  # 应该能区分正负样本

    def test_auc_empty_groups(self):
        explainer = ModelExplainer()
        auc = explainer._approximate_auc([0.5, 0.6], [0, 0])
        assert auc == 0.5


class TestMultiOmicsIntegrator:
    """多组学整合测试"""

    def test_integrate_datasets(self):
        integrator = MultiOmicsIntegrator()

        genomics = OmicsDataset(
            omics_type=OmicsType.GENOMICS,
            sample_ids=["S1", "S2"],
            feature_names=["TP53", "KRAS"],
            data_matrix=[[1, 0], [0, 1]],
        )
        transcriptomics = OmicsDataset(
            omics_type=OmicsType.TRANSCRIPTOMICS,
            sample_ids=["S1", "S2"],
            feature_names=["GENE_A", "GENE_B"],
            data_matrix=[[2.5, 1.3], [0.8, 3.1]],
        )

        result = integrator.integrate_datasets([genomics, transcriptomics])
        assert 'integrated_matrix' in result
        assert 'sample_ids' in result
        assert len(result['sample_ids']) == 2

    def test_cross_omics_correlation(self):
        integrator = MultiOmicsIntegrator()
        dataset1 = OmicsDataset(
            omics_type=OmicsType.GENOMICS,
            sample_ids=["S1", "S2", "S3"],
            feature_names=["F1"],
            data_matrix=[[1], [2], [3]],
        )
        dataset2 = OmicsDataset(
            omics_type=OmicsType.TRANSCRIPTOMICS,
            sample_ids=["S1", "S2", "S3"],
            feature_names=["F2"],
            data_matrix=[[1.1], [2.2], [3.3]],
        )
        result = integrator.cross_omics_correlation(dataset1, dataset2)
        assert 'correlations' in result
        assert 'common_samples' in result


class TestBioinformaticsToolkit:
    """生物信息学工具箱集成测试"""

    def test_toolkit_initialization(self):
        toolkit = BioinformaticsToolkit()
        assert toolkit.survival is not None
        assert toolkit.genomic_viz is not None
        assert toolkit.explainer is not None
        assert toolkit.integrator is not None

    def test_full_survival_workflow(self):
        toolkit = BioinformaticsToolkit()
        records = [
            SurvivalRecord(patient_id="P1", time=12, event=1, group="Treatment"),
            SurvivalRecord(patient_id="P2", time=24, event=0, group="Treatment"),
            SurvivalRecord(patient_id="P3", time=8, event=1, group="Control"),
            SurvivalRecord(patient_id="P4", time=18, event=1, group="Control"),
        ]
        km_results = toolkit.survival.kaplan_meier(records)
        assert len(km_results) == 2

        group_t = [r for r in records if r.group == "Treatment"]
        group_c = [r for r in records if r.group == "Control"]
        logrank = toolkit.survival.log_rank_test(group_t, group_c)
        assert 'p_value' in logrank

    def test_genomic_visualization_workflow(self):
        toolkit = BioinformaticsToolkit()
        samples = [
            GenomicSample(
                sample_id="S1", patient_id="P1", sample_type="Tumor",
                mutations=[
                    GeneMutation("TP53", "chr17", 1, "G", "A", "Missense", 0.4, "HIGH"),
                ],
                tmb_score=10.0,
            ),
        ]
        tmb = toolkit.genomic_viz.generate_tmb_summary(samples)
        assert tmb['type'] == "tmb"
        assert len(tmb['values']) == 1
