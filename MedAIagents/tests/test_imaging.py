"""
医学影像模块单元测试
Medical Imaging Module Unit Tests
"""

import pytest
import os
import tempfile
from datetime import datetime

from medai.imaging import (
    Modality, BodyPart, FindingSeverity,
    DICOMHeader, ImagingFinding, StructuredReport,
    DICOMReader, RadiologyReportParser,
    ImagingTextAnalyzer, ImagingSignLibrary,
    MedicalImagingToolkit
)


class TestEnums:
    """枚举类型测试"""

    def test_modality_values(self):
        assert Modality.CT.value == "CT"
        assert Modality.MRI.value == "MRI"
        assert Modality.XRAY.value == "X-Ray"
        assert Modality.ULTRASOUND.value == "Ultrasound"

    def test_body_part_values(self):
        assert BodyPart.CHEST.value == "胸部"
        assert BodyPart.HEAD.value == "头部"
        assert BodyPart.ABDOMEN.value == "腹部"

    def test_finding_severity(self):
        assert FindingSeverity.NORMAL.value == "正常"
        assert FindingSeverity.MALIGNANT.value == "恶性"
        assert FindingSeverity.CRITICAL.value == "危急"


class TestDICOMHeader:
    """DICOM头信息测试"""

    def test_default_values(self):
        header = DICOMHeader()
        assert header.patient_id == ""
        assert header.rows == 0
        assert header.columns == 0
        assert header.bits_allocated == 16
        assert header.pixel_spacing == []

    def test_custom_values(self):
        header = DICOMHeader(
            patient_id="P001",
            patient_name="Test",
            rows=512,
            columns=512,
            modality="CT",
        )
        assert header.patient_id == "P001"
        assert header.rows == 512
        assert header.modality == "CT"


class TestImagingFinding:
    """影像征象测试"""

    def test_default_finding(self):
        finding = ImagingFinding()
        assert finding.finding_id == ""
        assert finding.severity == FindingSeverity.NORMAL
        assert finding.confidence == 0.0
        assert finding.size_mm is None

    def test_custom_finding(self):
        finding = ImagingFinding(
            finding_id="F001",
            anatomy="右肺上叶",
            finding_type="结节",
            size_mm=15.5,
            severity=FindingSeverity.SUSPICIOUS,
            confidence=0.85,
        )
        assert finding.anatomy == "右肺上叶"
        assert finding.size_mm == 15.5
        assert finding.severity == FindingSeverity.SUSPICIOUS
        assert finding.confidence == 0.85


class TestDICOMReader:
    """DICOM读取器测试"""

    @pytest.fixture
    def reader(self):
        return DICOMReader()

    def test_is_dicom_with_real_file(self, reader):
        """使用真实DICOM文件测试"""
        pytest.importorskip("pydicom")
        import pydicom
        from pydicom.dataset import FileDataset, FileMetaDataset
        from pydicom.uid import ExplicitVRLittleEndian, ImplicitVRLittleEndian

        # 创建临时DICOM文件
        with tempfile.NamedTemporaryFile(suffix='.dcm', delete=False) as f:
            file_meta = FileMetaDataset()
            file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
            file_meta.MediaStorageSOPInstanceUID = '1.2.3.4.5'
            file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

            ds = FileDataset(f.name, {}, file_meta=file_meta, preamble=b'\x00' * 128)
            ds.PatientName = "TestPatient"
            ds.PatientID = "P001"
            ds.Modality = "CT"
            ds.Rows = 512
            ds.Columns = 512
            ds.is_little_endian = True
            ds.is_implicit_VR = False
            ds.save_as(f.name)
            temp_path = f.name

        try:
            assert reader.is_dicom(temp_path) is True
            header = reader.read_file(temp_path)
            assert header.patient_name == "TestPatient"
            assert header.patient_id == "P001"
            assert header.modality == "CT"
            assert header.rows == 512
            assert header.columns == 512
        finally:
            os.unlink(temp_path)

    def test_is_dicom_non_dicom(self, reader):
        """测试非DICOM文件"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"This is not a DICOM file")
            temp_path = f.name

        try:
            assert reader.is_dicom(temp_path) is False
        finally:
            os.unlink(temp_path)

    def test_read_basic_non_dicom(self, reader):
        """测试基础解析非DICOM文件"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"Some random data without DICM prefix")
            temp_path = f.name
        try:
            header = reader._read_basic(temp_path)
            assert isinstance(header, DICOMHeader)
            assert header.patient_name == ""
        finally:
            os.unlink(temp_path)


class TestRadiologyReportParser:
    """放射学报告解析器测试"""

    @pytest.fixture
    def parser(self):
        return RadiologyReportParser()

    def test_parse_normal_report(self, parser):
        report_text = """
        检查项目：胸部CT平扫
        影像表现：双肺纹理清晰，肺野内未见明显异常密度影。纵隔未见明显肿大淋巴结。
        诊断意见：胸部CT平扫未见明显异常。
        """
        report = parser.parse_report(report_text, report_id="R001")
        assert report.report_id == "R001"
        assert report.modality == "CT"
        assert report.body_part == "" or "胸部" in report.body_part or any("胸部" in f.anatomy for f in report.findings)
        assert len(report.findings) >= 1
        assert any(f.severity == FindingSeverity.NORMAL for f in report.findings)

    def test_parse_nodule_report(self, parser):
        report_text = """
        检查项目：胸部CT
        影像表现：右肺上叶见结节影，大小约15mm。边界尚清。
        诊断意见：右肺上叶结节，建议随访。
        """
        report = parser.parse_report(report_text)
        assert report.modality == "CT"
        assert len(report.findings) > 0
        nodule = [f for f in report.findings if f.finding_type == "结节"]
        assert len(nodule) > 0
        assert nodule[0].size_mm == 15.0

    def test_parse_mass_report(self, parser):
        report_text = """
        检查项目：腹部CT增强
        影像表现：肝脏右叶见占位性病变，大小约5.2cm。
        诊断意见：肝脏占位，性质待定，建议进一步检查。
        """
        report = parser.parse_report(report_text)
        assert "肝脏" in report.body_part or any("肝脏" in f.anatomy for f in report.findings)

    def test_extract_exam_info(self, parser):
        text = "胸部CT平扫检查"
        exam_type, modality, body_part = parser._extract_exam_info(text)
        assert modality == "CT"
        assert "胸部" in body_part or body_part == ""

    def test_extract_indication(self, parser):
        text = "临床诊断：咳嗽咳痰1周。检查目的：排除肺部感染。"
        indication = parser._extract_indication(text)
        assert "咳嗽" in indication or "排除" in indication

    def test_split_sections(self, parser):
        text = "影像表现：正常。诊断意见：未见异常。"
        findings, impression = parser._split_sections(text)
        assert "影像表现" in findings
        assert "诊断意见" in impression

    def test_extract_size(self, parser):
        assert parser._extract_size("结节大小约15mm") == 15.0
        assert parser._extract_size("肿块约2.5cm") == 25.0
        assert parser._extract_size("无明显病灶") is None

    def test_assess_severity(self, parser):
        assert parser._assess_severity("正常，未见异常") == FindingSeverity.NORMAL
        assert parser._assess_severity("恶性可能性大") == FindingSeverity.MALIGNANT
        assert parser._assess_severity("可疑") == FindingSeverity.SUSPICIOUS
        assert parser._assess_severity("良性病变") == FindingSeverity.BENIGN


class TestImagingTextAnalyzer:
    """影像-文本联合分析测试"""

    @pytest.fixture
    def analyzer(self):
        return ImagingTextAnalyzer()

    def test_analyze_correlation(self, analyzer):
        finding = ImagingFinding(
            finding_type="磨玻璃影",
            anatomy="右肺",
            severity=FindingSeverity.INDETERMINATE,
            confidence=0.7,
        )
        context = {"age": 55, "smoking_history": True}
        result = analyzer.analyze_finding_clinical_correlation(finding, context)
        assert result['finding'] == "磨玻璃影"
        assert len(result['differential_diagnosis']) > 0
        assert 'risk_assessment' in result

    def test_risk_assessment_high(self, analyzer):
        finding = ImagingFinding(
            finding_type="结节",
            size_mm=20,
            severity=FindingSeverity.MALIGNANT,
            confidence=0.9,
        )
        context = {"age": 70, "smoking_history": True, "family_history_cancer": True}
        risk = analyzer._assess_risk(finding, context)
        assert risk['level'] == "高"
        assert risk['score'] > 0.5

    def test_risk_assessment_low(self, analyzer):
        finding = ImagingFinding(
            finding_type="钙化",
            severity=FindingSeverity.BENIGN,
            confidence=0.8,
        )
        context = {"age": 30}
        risk = analyzer._assess_risk(finding, context)
        assert risk['level'] == "低"

    def test_generate_structured_description(self, analyzer):
        findings = [
            ImagingFinding(finding_type="结节", anatomy="右肺", size_mm=10),
            ImagingFinding(finding_type="积液", anatomy="胸腔"),
        ]
        desc = analyzer.generate_structured_description(findings)
        assert "右肺" in desc
        assert "结节" in desc
        assert "胸腔" in desc

    def test_empty_findings(self, analyzer):
        desc = analyzer.generate_structured_description([])
        assert desc == "未见明显异常。"


class TestImagingSignLibrary:
    """影像征象库测试"""

    @pytest.fixture
    def library(self):
        return ImagingSignLibrary()

    def test_lookup_sign(self, library):
        sign = library.get_sign("树芽征")
        assert sign is not None
        assert "细支气管" in sign['description']
        assert "CT" in sign['modalities']
        assert "肺部" in sign['anatomy']

    def test_lookup_ggo(self, library):
        sign = library.get_sign("磨玻璃影")
        assert sign is not None
        assert "CT" in sign['modalities']

    def test_lookup_nonexistent(self, library):
        sign = library.get_sign("不存在的征象")
        assert sign is None

    def test_search_by_modality(self, library):
        results = library.get_signs_by_modality("CT")
        assert len(results) > 0
        for sign in results:
            assert "CT" in sign['modalities']

    def test_search_by_anatomy(self, library):
        results = library.get_signs_by_anatomy("肺部")
        assert len(results) > 0

    def test_list_all_signs(self, library):
        signs = library.search_signs("")
        assert len(signs) > 0
        assert "树芽征" in [s['name'] for s in signs] or "磨玻璃影" in [s['name'] for s in signs]


class TestMedicalImagingToolkit:
    """影像工具箱集成测试"""

    def test_toolkit_initialization(self):
        toolkit = MedicalImagingToolkit()
        assert toolkit.dicom_reader is not None
        assert toolkit.report_parser is not None
        assert toolkit.text_analyzer is not None
        assert toolkit.sign_library is not None

    def test_parse_radiology_report(self):
        toolkit = MedicalImagingToolkit()
        report_text = """
        检查项目：胸部CT
        影像表现：右肺上叶见结节影，大小约12mm。
        诊断意见：右肺上叶结节，建议3个月复查。
        """
        report = toolkit.parse_radiology_report(report_text)
        assert isinstance(report, StructuredReport)
        assert report.modality == "CT"
        assert len(report.findings) > 0
