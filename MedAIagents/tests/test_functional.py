"""
功能集成测试
Functional Integration Tests

测试各模块间的协同工作流
"""

import pytest
import os
import tempfile
import shutil

from medai import (
    get_version, print_version_info,
    DataEncryptor, DataDeidentifier, RBACManager, AuditLogger, SecurityManager,
    StudyDesign, StudyType, StudyPhase, SampleSizeCalculator, RCTProtocolGenerator,
    MetaAnalysisToolkit, EffectMeasureType, StudyData,
    GrantProposal, GrantType, ResearchArea, GrantProposalAssistant,
    PaperGenerator, JournalType, ReferenceManager, Citation,
    ReviewCommentParser, ResponseStrategy, PeerReviewAssistant,
    ImagingFinding, FindingSeverity, RadiologyReportParser,
    ImagingTextAnalyzer, MedicalImagingToolkit,
    SurvivalRecord, SurvivalAnalyzer, GenomicSample, GeneMutation,
    GenomicVisualizer, BioinformaticsToolkit,
    PaperExporter, MetaAnalysisExporter, BudgetExporter,
    WordImporter, ExcelImporter,
)


class TestPackageInitialization:
    """包初始化测试"""

    def test_version(self):
        assert get_version() == "0.6.0"

    def test_version_info_print(self, capsys):
        print_version_info()
        captured = capsys.readouterr()
        assert "MedAIagents" in captured.out
        assert "0.6.0" in captured.out
        assert "临床决策支持" in captured.out
        assert "Office文档导入导出" in captured.out


class TestSecurityResearchWorkflow:
    """安全+科研工作流集成测试"""

    @pytest.fixture
    def temp_dir(self):
        td = tempfile.mkdtemp()
        yield td
        shutil.rmtree(td, ignore_errors=True)

    def test_secure_research_data_pipeline(self, temp_dir):
        """测试加密科研数据全流程"""
        # 1. 初始化安全模块
        security = SecurityManager()

        # 2. 添加科研人员（使用唯一用户名）
        import uuid
        r_user = f"researcher_{uuid.uuid4().hex[:8]}"
        r_id = f"r_{uuid.uuid4().hex[:8]}"
        security.rbac.add_user(r_id, r_user, 'researcher', '肿瘤科')
        assert security.check_access(r_id, 'research.create') is True

        # 3. 生成研究方案
        generator = RCTProtocolGenerator()
        protocol = generator.generate_protocol(
            study_title="加密的肺癌研究",
            indication="晚期NSCLC",
            study_type=StudyType.RCT.value,
            phase=StudyPhase.PHASE_II.value,
            primary_endpoint="PFS",
            secondary_endpoints=["OS", "ORR"],
            intervention="靶向药A",
            control="标准化疗",
            duration=24,
        )
        assert protocol['study_info']['title'] == "加密的肺癌研究"

        # 记录审计日志
        security.audit_logger.log(r_id, r_user, 'protocol.generate', success=True)
        logs = security.audit_logger.query_logs(user_id=r_id)
        assert len(logs) == 1

        # 加密敏感数据
        patient_data = {
            'name': '张三',
            'id_card': '310101199001011234',
            'diagnosis': '肺腺癌IV期',
            'mutation': 'EGFR L858R',
        }
        encrypted = security.secure_data(patient_data, encrypt_fields=['name', 'id_card'])
        assert encrypted['name'] != '张三'
        assert encrypted['diagnosis'] == '肺腺癌IV期'

        # 去标识化
        deidentified = security.deidentifier.deidentify(patient_data)
        assert 'name' not in deidentified
        assert 'id_card' not in deidentified


class TestResearchWritingWorkflow:
    """科研+写作工作流集成测试"""

    def test_meta_analysis_to_paper(self):
        """Meta分析到论文生成工作流"""
        # 1. 进行Meta分析
        toolkit = MetaAnalysisToolkit()
        studies = [
            StudyData("s1", "Study A", a=45, b=55, c=30, d=70),
            StudyData("s2", "Study B", a=50, b=50, c=35, d=65),
            StudyData("s3", "Study C", a=40, b=60, c=25, d=75),
        ]
        results = toolkit.run_complete_analysis(studies, EffectMeasureType.OR, model='fixed')
        meta = results['meta_analysis']

        assert meta.pooled_effect > 0
        assert meta.heterogeneity.i_squared >= 0

        # 2. 生成论文结构
        paper_gen = PaperGenerator()
        paper = paper_gen.generate_paper_structure(
            title="EGFR-TKI治疗NSCLC的Meta分析",
            study_type="Meta分析",
            journal_type=JournalType.REVIEW,
        )
        assert paper['guidelines_compliance']['PRISMA'] is True

        # 3. 添加参考文献
        ref_manager = ReferenceManager()
        ref_manager.add_citation(
            citation_id="ref1",
            authors=["Zhang S", "Li W"],
            title="EGFR mutations in NSCLC",
            journal="JCO",
            year=2023,
            volume="41",
            pages="123-130",
        )
        formatted = ref_manager.format_citation("ref1", style="vancouver")
        assert "JCO" in formatted

    def test_grant_to_protocol_workflow(self):
        """基金申请到方案设计工作流"""
        # 1. 创建基金申请
        assistant = GrantProposalAssistant()
        proposal = assistant.create_proposal(
            title="AI辅助肺癌早期诊断",
            grant_type=GrantType.NSFC_GENERAL,
            research_area=ResearchArea.MEDICAL_IMAGING,
            keywords=["AI", "肺癌", "早期诊断"],
            total_budget=50.0,
            duration_years=3,
        )

        assert proposal.title == "AI辅助肺癌早期诊断"
        assert proposal.total_budget == 50.0

        # 3. 预算规划
        total_items = sum(item.amount for item in proposal.budget)
        assert abs(total_items - 50.0) < 0.01

        # 4. 样本量计算
        sample_size = SampleSizeCalculator.calculate_proportion(
            p1=0.3, p2=0.5, alpha=0.05, power=0.8
        )
        assert sample_size['sample_size']['control_group'] > 0


class TestImagingBioinformaticsWorkflow:
    """影像+生物信息学工作流集成测试"""

    def test_imaging_to_structured_report(self):
        """影像报告结构化工作流"""
        toolkit = MedicalImagingToolkit()

        report_text = """
        检查项目：胸部CT平扫
        临床诊断：体检发现肺结节
        影像表现：右肺上叶见磨玻璃影，大小约12mm，边界尚清。
        诊断意见：右肺上叶磨玻璃结节，建议3-6个月复查。
        """

        sr = toolkit.parse_radiology_report(report_text)
        assert sr.modality == "CT"
        assert len(sr.findings) > 0

    def test_risk_assessment_workflow(self):
        """影像风险评估工作流"""
        analyzer = ImagingTextAnalyzer()

        finding = ImagingFinding(
            finding_type="结节",
            anatomy="右肺上叶",
            size_mm=15,
            severity=FindingSeverity.SUSPICIOUS,
            confidence=0.8,
        )

        clinical_context = {
            "age": 65,
            "smoking_history": True,
            "family_history_cancer": False,
        }

        correlation = analyzer.analyze_finding_clinical_correlation(
            finding, clinical_context
        )
        assert correlation['finding'] == "结节"
        assert len(correlation['differential_diagnosis']) > 0
        assert correlation['risk_assessment']['level'] in ["低", "中", "高"]

    def test_survival_genomic_workflow(self):
        """生存分析+基因组学工作流"""
        toolkit = BioinformaticsToolkit()

        # 1. 生存分析
        records = [
            SurvivalRecord("P1", 12, 1, "Treatment", {"age": 65}),
            SurvivalRecord("P2", 24, 0, "Treatment", {"age": 70}),
            SurvivalRecord("P3", 8, 1, "Control", {"age": 68}),
            SurvivalRecord("P4", 15, 1, "Control", {"age": 72}),
        ]

        km_results = toolkit.survival.kaplan_meier(records)
        assert len(km_results) == 2

        group_t = [r for r in records if r.group == "Treatment"]
        group_c = [r for r in records if r.group == "Control"]
        logrank = toolkit.survival.log_rank_test(group_t, group_c)
        assert 'p_value' in logrank

        # 2. 基因组可视化
        samples = [
            GenomicSample(
                sample_id="S1", patient_id="P1", sample_type="Tumor",
                mutations=[
                    GeneMutation("TP53", "chr17", 1, "G", "A", "Missense", 0.5, "HIGH"),
                    GeneMutation("KRAS", "chr12", 1, "C", "T", "Missense", 0.4, "MODERATE"),
                ],
                tmb_score=15.0,
            ),
            GenomicSample(
                sample_id="S2", patient_id="P2", sample_type="Tumor",
                mutations=[
                    GeneMutation("TP53", "chr17", 1, "G", "A", "Nonsense", 0.6, "HIGH"),
                ],
                tmb_score=8.0,
            ),
        ]

        tmb_summary = toolkit.genomic_viz.generate_tmb_summary(samples)
        assert tmb_summary['type'] == "tmb"
        assert tmb_summary['statistics']['mean'] > 0

        oncoprint = toolkit.genomic_viz.generate_oncoprint_data(
            samples, genes=["TP53", "KRAS"]
        )
        assert oncoprint['total_samples'] == 2


class TestExportImportWorkflow:
    """导入导出工作流集成测试"""

    @pytest.fixture
    def temp_dir(self):
        td = tempfile.mkdtemp()
        yield td
        shutil.rmtree(td, ignore_errors=True)

    def test_round_trip_excel(self, temp_dir):
        """Excel导出+导入往返测试"""
        # 1. 导出生存数据
        exporter = BudgetExporter()
        budget_data = {
            'items': [
                {'name': '设备费', 'amount': 20.0, 'notes': '仪器'},
                {'name': '材料费', 'amount': 10.0, 'notes': '耗材'},
            ],
            'total': 30.0,
        }
        export_path = os.path.join(temp_dir, 'budget.xlsx')
        exporter.export_budget(budget_data, export_path)
        assert os.path.exists(export_path)

        # 2. 用Excel导入读取
        importer = ExcelImporter()
        imported = importer.read_sheet(export_path)
        assert len(imported) >= 2

    def test_paper_export_roundtrip(self, temp_dir):
        """论文导出+解析工作流"""
        # 1. 生成论文
        paper_gen = PaperGenerator()
        paper = paper_gen.generate_paper_structure(
            title="Test Integration",
            study_type="临床试验",
        )

        # 2. 导出为Word
        exporter = PaperExporter()
        docx_path = os.path.join(temp_dir, 'paper.docx')
        exporter.export_paper(paper, docx_path)
        assert os.path.exists(docx_path)

        # 3. 解析Word
        importer = WordImporter()
        text = importer.extract_text(docx_path)
        assert len(text) > 0
        assert "Test Integration" in text

    def test_meta_analysis_to_excel(self, temp_dir):
        """Meta分析结果导出Excel"""
        toolkit = MetaAnalysisToolkit()
        studies = [
            StudyData("s1", "Study A", a=40, b=60, c=30, d=70),
            StudyData("s2", "Study B", a=45, b=55, c=35, d=65),
        ]
        results = toolkit.run_complete_analysis(studies, EffectMeasureType.OR)
        meta = results['meta_analysis']

        result_data = {
            'studies': [
                {
                    'name': e.study_name,
                    'effect_size': e.effect_size,
                    'se': e.standard_error,
                    'ci_lower': e.lower_ci,
                    'ci_upper': e.upper_ci,
                    'weight': e.weight,
                }
                for e in meta.studies
            ],
            'pooled_effect': meta.pooled_effect,
            'ci_lower': meta.pooled_lower_ci,
            'ci_upper': meta.pooled_upper_ci,
            'heterogeneity': {
                'i_squared': meta.heterogeneity.i_squared,
                'p_value': meta.heterogeneity.q_pvalue,
            },
        }

        exporter = MetaAnalysisExporter()
        path = os.path.join(temp_dir, 'meta.xlsx')
        exporter.export_meta_analysis(result_data, path)
        assert os.path.exists(path)

        # 验证可读取
        importer = ExcelImporter()
        data = importer.read_sheet(path)
        assert len(data) > 0


class TestPeerReviewWorkflow:
    """同行评审工作流集成测试"""

    def test_full_peer_review_cycle(self):
        """完整同行评审周期"""
        # 1. 解析审稿意见
        parser = ReviewCommentParser()
        review_text = (
            "1. Major concern: The sample size is too small for the primary endpoint.\n"
            "2. Minor: Please correct the typo in Figure 2 legend.\n"
            "3. Methodology: The statistical analysis plan should be clarified."
        )
        comments = parser.parse_comments(review_text, reviewer_id="R1")
        assert len(comments) == 3

        # 2. 生成回复
        assistant = PeerReviewAssistant()
        result = assistant.analyze_review(review_text, reviewer_id="R1")
        responses = result['suggested_responses']
        assert len(responses) == 3

        # 3. 验证回复策略
        for response in responses:
            assert response['draft_response'] != ""
            assert response['comment_id'] != ""


class TestEndToEndPatientDataWorkflow:
    """端到端患者数据工作流"""

    @pytest.fixture
    def temp_dir(self):
        td = tempfile.mkdtemp()
        yield td
        shutil.rmtree(td, ignore_errors=True)

    def test_patient_journey(self, temp_dir):
        """模拟患者数据全流程"""
        # 1. 安全初始化
        security = SecurityManager()
        security.rbac.add_user('d1', 'doctor_a', 'doctor')

        # 2. 模拟影像报告
        toolkit = MedicalImagingToolkit()
        report = toolkit.parse_radiology_report("""
            检查项目：胸部CT
            影像表现：右肺上叶见结节影，大小约10mm。
            诊断意见：建议随访。
        """)
        assert report is not None

        # 3. 基因组数据
        bio_toolkit = BioinformaticsToolkit()
        samples = [
            GenomicSample(
                sample_id="S1", patient_id="P1", sample_type="Tumor",
                mutations=[GeneMutation("EGFR", "chr7", 1, "G", "A", "Missense", 0.5, "HIGH")],
                tmb_score=10.0,
            ),
        ]
        tmb = bio_toolkit.genomic_viz.generate_tmb_summary(samples)
        assert tmb['statistics']['mean'] == 10.0

        # 4. 生成科研方案
        protocol_gen = RCTProtocolGenerator()
        protocol = protocol_gen.generate_protocol(
            study_title="EGFR突变NSCLC影像基因组学研究",
            indication="NSCLC",
            study_type=StudyType.COHORT.value,
            phase=StudyPhase.REAL_WORLD.value,
            primary_endpoint="影像-基因关联",
            secondary_endpoints=["预后预测"],
            duration=36,
        )
        assert 'study_info' in protocol

        # 5. 数据加密与审计
        import uuid
        d_user = f"doctor_{uuid.uuid4().hex[:8]}"
        d_id = f"d_{uuid.uuid4().hex[:8]}"
        encrypted = security.encryptor.encrypt("敏感患者数据")
        decrypted = security.encryptor.decrypt(encrypted)
        assert decrypted == "敏感患者数据"

        security.audit_logger.log(d_id, d_user, 'patient.data.access', success=True)
        logs = security.audit_logger.query_logs(user_id=d_id)
        assert len(logs) == 1
