"""
MedAIagents v0.5.0 功能演示脚本
展示医学影像AI分析与生物信息学接口模块
"""
import sys
sys.path.insert(0, '../src')

from medai import (
    MedicalImagingToolkit, BioinformaticsToolkit,
    DICOMReader, FindingSeverity, ImagingFinding,
    SurvivalRecord, GenomicSample, GeneMutation,
    OmicsDataset, OmicsType,
)


def demo_imaging():
    """演示医学影像AI分析功能"""
    print("\n" + "=" * 60)
    print("🩻 医学影像AI分析模块演示")
    print("=" * 60)

    toolkit = MedicalImagingToolkit()

    # 1. 影像报告结构化解析
    print("\n📄 1. 放射学报告结构化提取")
    report_text = """
    检查类型：胸部CT平扫+增强
    临床诊断：体检发现肺结节
    影像表现：
    右肺上叶见结节影，大小约12mm，边界尚清，增强后轻度强化。
    左肺下叶见磨玻璃影，范围约15mm，密度较淡。
    纵隔见肿大淋巴结，短径约8mm。
    双侧胸腔未见明显积液。
    诊断意见：
    1. 右肺上叶结节，建议3个月随访复查
    2. 左肺下叶磨玻璃影，性质待定，建议抗炎治疗后复查
    3. 纵隔淋巴结肿大，建议进一步检查
    """

    structured = toolkit.parse_radiology_report(
        report_text, report_id="CT-2025-001", patient_id="P-12345"
    )
    print(f"\n  检查类型: {structured.exam_type}")
    print(f"  检查部位: {structured.body_part}")
    print(f"  临床指征: {structured.clinical_indication}")
    print(f"  发现征象: {len(structured.findings)} 个")
    for f in structured.findings:
        size_str = f" ({f.size_mm}mm)" if f.size_mm else ""
        print(f"    • [{f.severity.value}] {f.anatomy}{size_str}: {f.finding_type}")

    # 2. 影像-临床关联分析
    print("\n🔬 2. 影像征象与临床背景关联分析")
    clinical_context = {
        "age": 62,
        "smoking_history": True,
        "family_history_cancer": True,
    }
    for finding in structured.findings[:2]:
        result = toolkit.correlate_finding_with_clinical(finding, clinical_context)
        print(f"\n  征象: {result['finding']} @ {result['anatomy']}")
        print(f"  鉴别诊断: {', '.join(result['differential_diagnosis'][:3])}")
        print(f"  风险评分: {result['risk_assessment']['score']} ({result['risk_assessment']['level']}风险)")
        if result['risk_assessment']['factors']:
            print(f"  风险因素: {', '.join(result['risk_assessment']['factors'])}")

    # 3. 影像征象库查询
    print("\n📚 3. 常见影像征象智能识别模板库")
    signs_to_query = ["磨玻璃影", "树芽征", "牛眼征"]
    for sign_name in signs_to_query:
        info = toolkit.get_sign_info(sign_name)
        if info:
            print(f"\n  【{sign_name}】")
            print(f"    描述: {info['description']}")
            print(f"    适用模态: {', '.join(info['modalities'])}")
            print(f"    相关疾病: {', '.join(info['diseases'][:3])}")

    # 4. 报告摘要生成
    print("\n📝 4. 结构化报告摘要")
    summary = toolkit.generate_report_summary(structured)
    print(f"\n{summary}")


def demo_bioinformatics():
    """演示生物信息学接口功能"""
    print("\n" + "=" * 60)
    print("🧬 生物信息学接口模块演示")
    print("=" * 60)

    toolkit = BioinformaticsToolkit()

    # 1. 生存分析
    print("\n📊 1. 生存分析 (Kaplan-Meier + Cox回归)")
    records = [
        SurvivalRecord("P01", 36, 1, "Immunotherapy", {"age": 55, "stage": 3}),
        SurvivalRecord("P02", 48, 0, "Immunotherapy", {"age": 62, "stage": 2}),
        SurvivalRecord("P03", 24, 1, "Immunotherapy", {"age": 70, "stage": 4}),
        SurvivalRecord("P04", 18, 1, "Chemotherapy", {"age": 58, "stage": 4}),
        SurvivalRecord("P05", 30, 0, "Chemotherapy", {"age": 65, "stage": 3}),
        SurvivalRecord("P06", 12, 1, "Chemotherapy", {"age": 72, "stage": 4}),
        SurvivalRecord("P07", 42, 0, "Immunotherapy", {"age": 60, "stage": 2}),
        SurvivalRecord("P08", 15, 1, "Chemotherapy", {"age": 68, "stage": 3}),
    ]

    surv_result = toolkit.analyze_survival(records, covariates=["age", "stage"])
    print(f"\n  样本量: {surv_result['sample_size']}")
    print(f"  事件数: {surv_result['total_events']}")
    for km in surv_result['km_curves']:
        median = f"{km.median_survival}月" if km.median_survival else "未达到"
        print(f"  组 '{km.group_name}': 中位生存 = {median}")

    if 'cox_regression' in surv_result:
        print(f"\n  Cox回归结果:")
        for cox in surv_result['cox_regression']:
            sig = "*" if cox.is_significant else ""
            print(f"    {cox.variable}: HR={cox.hazard_ratio} (95%CI: {cox.hr_lower}-{cox.hr_upper}) P={cox.p_value}{sig}")

    if 'log_rank_test' in surv_result:
        lr = surv_result['log_rank_test']
        print(f"\n  对数秩检验: χ²={lr['chi2']}, P={lr['p_value']} — {lr['interpretation']}")

    # 2. 基因组可视化
    print("\n🧪 2. 基因组数据可视化")
    samples = [
        GenomicSample("Tumor-01", "Patient-A", "Tumor", mutations=[
            GeneMutation("TP53", "chr17", 7577538, "G", "A", "Missense", 0.45, "HIGH", "Pathogenic"),
            GeneMutation("KRAS", "chr12", 25398284, "C", "T", "Missense", 0.32, "MODERATE"),
            GeneMutation("EGFR", "chr7", 55249005, "C", "T", "Missense", 0.28, "HIGH", "Likely pathogenic"),
        ], tmb_score=8.5, msi_status="MSS"),
        GenomicSample("Tumor-02", "Patient-B", "Tumor", mutations=[
            GeneMutation("TP53", "chr17", 7577538, "G", "A", "Nonsense", 0.51, "HIGH", "Pathogenic"),
            GeneMutation("PIK3CA", "chr3", 178936082, "G", "A", "Missense", 0.22, "MODERATE"),
        ], tmb_score=12.3, msi_status="MSS"),
        GenomicSample("Tumor-03", "Patient-C", "Tumor", mutations=[
            GeneMutation("BRCA1", "chr17", 43045752, "A", "T", "Frameshift", 0.38, "HIGH", "Pathogenic"),
            GeneMutation("KRAS", "chr12", 25398284, "C", "T", "Missense", 0.41, "MODERATE"),
            GeneMutation("TP53", "chr17", 7577538, "G", "A", "Missense", 0.35, "HIGH"),
        ], tmb_score=15.7, msi_status="MSI-H"),
    ]

    viz_result = toolkit.visualize_genomics(
        samples,
        genes=["TP53", "KRAS", "EGFR", "PIK3CA", "BRCA1"],
        plot_types=["oncoprint", "tmb", "pathway"]
    )

    oncoprint = viz_result["oncoprint"]
    print(f"\n  OncoPrint: {oncoprint['total_samples']} 样本 x {len(oncoprint['genes'])} 基因")
    for gene, freq in oncoprint['frequencies'].items():
        if freq > 0:
            print(f"    • {gene}: 突变频率 {freq*100:.0f}%")

    tmb = viz_result["tmb"]
    print(f"\n  TMB统计: 均值={tmb['statistics']['mean']}, 中位数={tmb['statistics']['median']}")
    print(f"    高TMB样本(>10): {tmb['statistics']['high_tmb_count']} 例")

    if 'pathway' in viz_result:
        pathway = viz_result["pathway"]
        print(f"\n  通路富集 (Top 3):")
        for p in pathway['pathways'][:3]:
            print(f"    • {p['name']}: {p['hit_count']}/{p['genes_in_pathway']} 基因突变")

    # 3. 模型可解释性
    print("\n🤖 3. 机器学习模型解释性分析")
    features = ["age", "tumor_size_mm", "lymph_node_positive", "grade", "ki67_percent"]
    predictions = [0.85, 0.32, 0.67, 0.91, 0.45, 0.73]
    labels = [1, 0, 1, 1, 0, 1]
    sample_features = [62, 28, 1, 3, 0.35]

    expl_result = toolkit.explain_model(features, predictions, labels, sample_features)
    print(f"\n  特征重要性 (Top 3):")
    for fi in expl_result['feature_importance'][:3]:
        print(f"    • {fi.feature_name}: {fi.importance_score:.4f}")

    if 'shap_values' in expl_result:
        print(f"\n  SHAP值分析:")
        sorted_shap = sorted(expl_result['shap_values'],
                            key=lambda x: abs(x.shap_value), reverse=True)
        for sv in sorted_shap[:3]:
            direction = "增加" if sv.shap_value > 0 else "降低"
            print(f"    • {sv.feature_name}={sv.feature_value}: SHAP={sv.shap_value:+.4f} → {direction}风险")

    # 4. 多组学整合
    print("\n🔗 4. 多组学数据整合")
    genomics = OmicsDataset(
        OmicsType.GENOMICS,
        ["S1", "S2", "S3"],
        ["TP53", "KRAS", "EGFR"],
        [[1.2, 0.8, 0.0], [1.5, 0.3, 1.1], [0.9, 1.2, 0.5]]
    )
    transcriptomics = OmicsDataset(
        OmicsType.TRANSCRIPTOMICS,
        ["S1", "S2", "S3"],
        ["GeneA", "GeneB"],
        [[2.1, 1.5], [1.8, 2.3], [2.5, 1.9]]
    )
    proteomics = OmicsDataset(
        OmicsType.PROTEOMICS,
        ["S1", "S2", "S3"],
        ["ProteinX", "ProteinY"],
        [[0.8, 1.2], [1.1, 0.9], [0.7, 1.5]]
    )

    integration = toolkit.integrate_multi_omics([genomics, transcriptomics, proteomics])
    stats = integration['integration']['statistics']
    print(f"\n  整合样本数: {stats['total_samples']}")
    print(f"  整合特征数: {stats['total_features']}")
    print(f"  各组学特征数:")
    for omics, count in stats['features_by_omics'].items():
        print(f"    • {omics}: {count} 特征")

    subtypes = integration['subtypes']
    print(f"\n  分子分型结果 ({subtypes['n_subtypes']} 亚型):")
    for st in subtypes['subtypes']:
        print(f"    • {st['subtype_id']}: {st['sample_count']} 例样本")

    # 跨组学关联
    cross = toolkit.cross_omics_analysis(genomics, transcriptomics)
    print(f"\n  跨组学强相关特征 ({cross['omics_pair']}): {len(cross['correlations'])} 对")
    for corr in cross['correlations'][:3]:
        print(f"    • {corr['feature_1']} ↔ {corr['feature_2']}: r={corr['correlation']} ({corr['direction']})")


def main():
    print("🏥 MedAIagents v0.5.0 功能演示")
    print("=" * 60)

    demo_imaging()
    demo_bioinformatics()

    print("\n" + "=" * 60)
    print("✅ v0.5.0 演示完成！")
    print("=" * 60)
    print("""
v0.5.0 新增核心能力:
  • DICOM文件元数据读取 (DICOMReader, 支持 pydicom + 基础解析)
  • 放射学报告结构化提取 (RadiologyReportParser)
  • 影像-文本联合分析 (ImagingTextAnalyzer, 风险评估)
  • 影像征象模板库 (ImagingSignLibrary, 9个经典征象)
  • Kaplan-Meier 生存分析 + 对数秩检验 (SurvivalAnalyzer)
  • Cox比例风险回归 (SurvivalAnalyzer)
  • OncoPrint / TMB / 通路富集可视化 (GenomicVisualizer)
  • SHAP / 特征重要性 / PDP 模型解释 (ModelExplainer)
  • 多组学数据整合与分子分型 (MultiOmicsIntegrator)
    """)


if __name__ == "__main__":
    main()
