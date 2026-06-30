"""
医学影像AI分析模块 (v0.5.0)
Medical Imaging AI Analysis Module

功能:
- DICOM文件元数据读取与基础解析
- 影像报告结构化提取 (放射学报告)
- 影像-文本联合分析接口
- 常见影像征象智能识别模板库
"""

import re
import struct
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class Modality(Enum):
    """影像模态"""
    CT = "CT"
    MRI = "MRI"
    XRAY = "X-Ray"
    ULTRASOUND = "Ultrasound"
    MAMMOGRAPHY = "Mammography"
    PET = "PET"
    NM = "Nuclear Medicine"
    ANGIOGRAPHY = "Angiography"
    DX = "Digital Radiography"
    UNKNOWN = "Unknown"


class BodyPart(Enum):
    """检查部位"""
    HEAD = "头部"
    CHEST = "胸部"
    ABDOMEN = "腹部"
    PELVIS = "盆腔"
    SPINE = "脊柱"
    EXTREMITY = "四肢"
    NECK = "颈部"
    WHOLE_BODY = "全身"
    BREAST = "乳腺"
    HEART = "心脏"
    UNKNOWN = "未知"


class FindingSeverity(Enum):
    """征象严重程度"""
    NORMAL = "正常"
    BENIGN = "良性"
    LIKELY_BENIGN = "可能良性"
    INDETERMINATE = "性质待定"
    SUSPICIOUS = "可疑恶性"
    MALIGNANT = "恶性"
    CRITICAL = "危急"


@dataclass
class DICOMHeader:
    """DICOM文件头信息"""
    patient_id: str = ""
    patient_name: str = ""
    patient_birth_date: str = ""
    patient_sex: str = ""
    study_instance_uid: str = ""
    study_date: str = ""
    study_time: str = ""
    study_description: str = ""
    series_instance_uid: str = ""
    series_number: int = 0
    series_description: str = ""
    modality: str = ""
    body_part_examined: str = ""
    institution_name: str = ""
    manufacturer: str = ""
    rows: int = 0
    columns: int = 0
    slice_thickness: float = 0.0
    pixel_spacing: List[float] = field(default_factory=list)
    window_center: float = 0.0
    window_width: float = 0.0
    bits_allocated: int = 16
    bits_stored: int = 16
    photometric_interpretation: str = ""


@dataclass
class ImagingFinding:
    """影像征象发现"""
    finding_id: str = ""
    anatomy: str = ""           # 解剖部位
    finding_type: str = ""      # 征象类型
    description: str = ""       # 描述
    size_mm: Optional[float] = None
    location: str = ""          # 具体位置
    severity: FindingSeverity = FindingSeverity.NORMAL
    confidence: float = 0.0     # 置信度 0-1
    comparison: str = ""        # 与既往对比
    recommendations: str = ""   # 建议


@dataclass
class StructuredReport:
    """结构化影像报告"""
    report_id: str = ""
    patient_id: str = ""
    exam_type: str = ""         # 检查类型
    modality: str = ""          # 模态
    body_part: str = ""         # 部位
    clinical_indication: str = ""  # 临床指征
    technique: str = ""         # 技术方法
    findings: List[ImagingFinding] = field(default_factory=list)
    impression: str = ""        # 诊断意见
    recommendations: str = ""   # 建议
    radiologist: str = ""       # 报告医师
    report_date: str = ""
    comparison_studies: str = ""  # 对比检查


@dataclass
class ImagingStudy:
    """影像检查完整信息"""
    study_id: str = ""
    dicom_header: Optional[DICOMHeader] = None
    structured_report: Optional[StructuredReport] = None
    file_paths: List[str] = field(default_factory=list)
    preview_available: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class DICOMReader:
    """DICOM文件读取器 (基础解析，支持外部pydicom增强)"""

    # DICOM标准标签 (group, element) -> name
    DICOM_TAGS = {
        (0x0010, 0x0010): "PatientName",
        (0x0010, 0x0020): "PatientID",
        (0x0010, 0x0030): "PatientBirthDate",
        (0x0010, 0x0040): "PatientSex",
        (0x0008, 0x0060): "Modality",
        (0x0008, 0x0070): "Manufacturer",
        (0x0008, 0x0080): "InstitutionName",
        (0x0008, 0x1030): "StudyDescription",
        (0x0008, 0x103E): "SeriesDescription",
        (0x0008, 0x0020): "StudyDate",
        (0x0008, 0x0030): "StudyTime",
        (0x0020, 0x000D): "StudyInstanceUID",
        (0x0020, 0x000E): "SeriesInstanceUID",
        (0x0020, 0x0011): "SeriesNumber",
        (0x0018, 0x0015): "BodyPartExamined",
        (0x0028, 0x0010): "Rows",
        (0x0028, 0x0011): "Columns",
        (0x0028, 0x0030): "PixelSpacing",
        (0x0028, 0x0100): "BitsAllocated",
        (0x0028, 0x0101): "BitsStored",
        (0x0028, 0x0004): "PhotometricInterpretation",
        (0x0018, 0x0050): "SliceThickness",
        (0x0028, 0x1050): "WindowCenter",
        (0x0028, 0x1051): "WindowWidth",
    }

    def __init__(self):
        self._has_pydicom = False
        try:
            import pydicom
            self._has_pydicom = True
        except ImportError:
            pass

    def read_file(self, file_path: str) -> DICOMHeader:
        """读取DICOM文件元数据"""
        if self._has_pydicom:
            return self._read_with_pydicom(file_path)
        return self._read_basic(file_path)

    def _read_with_pydicom(self, file_path: str) -> DICOMHeader:
        """使用pydicom读取完整DICOM信息"""
        import pydicom
        ds = pydicom.dcmread(file_path)
        header = DICOMHeader()
        header.patient_name = str(getattr(ds, 'PatientName', ''))
        header.patient_id = str(getattr(ds, 'PatientID', ''))
        header.patient_birth_date = str(getattr(ds, 'PatientBirthDate', ''))
        header.patient_sex = str(getattr(ds, 'PatientSex', ''))
        header.study_instance_uid = str(getattr(ds, 'StudyInstanceUID', ''))
        header.study_date = str(getattr(ds, 'StudyDate', ''))
        header.study_time = str(getattr(ds, 'StudyTime', ''))
        header.study_description = str(getattr(ds, 'StudyDescription', ''))
        header.series_instance_uid = str(getattr(ds, 'SeriesInstanceUID', ''))
        header.series_number = int(getattr(ds, 'SeriesNumber', 0))
        header.series_description = str(getattr(ds, 'SeriesDescription', ''))
        header.modality = str(getattr(ds, 'Modality', ''))
        header.body_part_examined = str(getattr(ds, 'BodyPartExamined', ''))
        header.institution_name = str(getattr(ds, 'InstitutionName', ''))
        header.manufacturer = str(getattr(ds, 'Manufacturer', ''))
        header.rows = int(getattr(ds, 'Rows', 0))
        header.columns = int(getattr(ds, 'Columns', 0))
        header.slice_thickness = float(getattr(ds, 'SliceThickness', 0.0) or 0.0)
        header.bits_allocated = int(getattr(ds, 'BitsAllocated', 16))
        header.bits_stored = int(getattr(ds, 'BitsStored', 16))
        header.photometric_interpretation = str(getattr(ds, 'PhotometricInterpretation', ''))
        try:
            header.window_center = float(getattr(ds, 'WindowCenter', 0.0) or 0.0)
            header.window_width = float(getattr(ds, 'WindowWidth', 0.0) or 0.0)
        except (ValueError, TypeError):
            pass
        try:
            ps = getattr(ds, 'PixelSpacing', None)
            if ps:
                header.pixel_spacing = [float(x) for x in ps]
        except (ValueError, TypeError):
            pass
        return header

    def _read_basic(self, file_path: str) -> DICOMHeader:
        """基础DICOM解析（不依赖pydicom）"""
        header = DICOMHeader()
        try:
            with open(file_path, 'rb') as f:
                data = f.read(32768)  # 读取前32KB

            # 检查DICOM前缀
            if b'DICM' in data[:132]:
                preamble_end = data.index(b'DICM') + 4
            else:
                preamble_end = 0

            # 简单解析关键标签（隐式VR，Little Endian）
            for tag, name in self.DICOM_TAGS.items():
                tag_bytes = struct.pack('<HH', tag[0], tag[1])
                pos = data.find(tag_bytes, preamble_end)
                if pos >= 0 and pos + 8 < len(data):
                    # 读取值长度
                    try:
                        vr = data[pos+4:pos+6].decode('ascii', errors='ignore')
                        if vr in ('OB', 'OW', 'OF', 'SQ', 'UT', 'UN'):
                            length = struct.unpack('<I', data[pos+8:pos+12])[0]
                            value_start = pos + 12
                        else:
                            length = struct.unpack('<H', data[pos+6:pos+8])[0]
                            value_start = pos + 8
                        value = data[value_start:value_start+length].decode('utf-8', errors='ignore').strip('\x00')
                        self._set_header_field(header, name, value)
                    except Exception:
                        pass
        except Exception:
            pass
        return header

    def _set_header_field(self, header: DICOMHeader, name: str, value: str):
        """设置DICOM头字段"""
        field_map = {
            "PatientName": "patient_name",
            "PatientID": "patient_id",
            "PatientBirthDate": "patient_birth_date",
            "PatientSex": "patient_sex",
            "StudyInstanceUID": "study_instance_uid",
            "StudyDate": "study_date",
            "StudyTime": "study_time",
            "StudyDescription": "study_description",
            "SeriesInstanceUID": "series_instance_uid",
            "SeriesNumber": "series_number",
            "SeriesDescription": "series_description",
            "Modality": "modality",
            "BodyPartExamined": "body_part_examined",
            "InstitutionName": "institution_name",
            "Manufacturer": "manufacturer",
            "Rows": "rows",
            "Columns": "columns",
            "BitsAllocated": "bits_allocated",
            "BitsStored": "bits_stored",
            "PhotometricInterpretation": "photometric_interpretation",
            "SliceThickness": "slice_thickness",
            "WindowCenter": "window_center",
            "WindowWidth": "window_width",
        }
        if name in field_map:
            attr = field_map[name]
            try:
                current = getattr(header, attr)
                if isinstance(current, int):
                    setattr(header, attr, int(value) if value else 0)
                elif isinstance(current, float):
                    setattr(header, attr, float(value) if value else 0.0)
                else:
                    setattr(header, attr, value)
            except (ValueError, TypeError):
                setattr(header, attr, value)

    def is_dicom(self, file_path: str) -> bool:
        """检查文件是否为DICOM格式"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(132)
            return b'DICM' in header[:132] or header[128:132] == b'DICM'
        except Exception:
            return False


class RadiologyReportParser:
    """放射学报告结构化提取器"""

    # 征象关键词库
    FINDING_PATTERNS = {
        "结节": [r"结节[，、]?(?:大小约?)?(\d+(?:\.\d+)?)\s*(cm|mm)?",
                r"([\w\u4e00-\u9fff]+)见.*?结节"],
        "肿块": [r"肿块[，、]?(?:大小约?)?(\d+(?:\.\d+)?)\s*(cm|mm)?",
                r"占位性病变"],
        "积液": [r"(?:胸腔|腹腔|心包)?积液",
                r"液性暗区"],
        "钙化": [r"钙化[灶点]?(?:影)?",
                r"高密度影.*?钙化"],
        "梗死": [r"梗死[灶区]",
                r"脑梗死|心肌梗死"],
        "出血": [r"出血[灶区]?",
                r"高密度影.*?出血"],
        "骨折": [r"骨折[线]?",
                r"骨质中断|骨皮质不连"],
        "淋巴结肿大": [r"淋巴结.*?肿大",
                      r"肿大淋巴结"],
        "肺气肿": [r"肺气肿",
                 r"肺大疱|肺含气量增多"],
        "纤维化": [r"纤维化",
                 r"纤维灶|纤维条索影"],
        "磨玻璃影": [r"磨玻璃[样]?[密度]?影",
                   r"GGO|ground glass"],
        "实变": [r"实变[影区]?",
               r"大片状高密度影"],
    }

    # 解剖部位关键词
    ANATOMY_KEYWORDS = [
        "右肺", "左肺", "右上肺", "左上肺", "右下肺", "左下肺",
        "右肺中叶", "右肺上叶", "右肺下叶", "左肺上叶", "左肺下叶",
        "肝脏", "胆囊", "胰腺", "脾脏", "肾脏", "右肾", "左肾",
        "肾上腺", "胃", "肠道", "膀胱", "前列腺", "子宫", "卵巢",
        "大脑", "小脑", "脑干", "丘脑", "基底节", "脑室",
        "颈椎", "胸椎", "腰椎", "骶椎", "骨盆",
        "右侧", "左侧", "双侧",
    ]

    # 严重程度关键词
    SEVERITY_MAP = {
        FindingSeverity.CRITICAL: ["危急", "严重", "大面积", "急性期", "危重"],
        FindingSeverity.MALIGNANT: ["恶性", "癌", "肿瘤", "转移"],
        FindingSeverity.SUSPICIOUS: ["可疑", "不能排除", "待排除", "性质待定"],
        FindingSeverity.INDETERMINATE: ["建议随访", "建议复查", "建议进一步检查"],
        FindingSeverity.BENIGN: ["良性", "囊肿", "血管瘤", "错构瘤"],
        FindingSeverity.NORMAL: ["正常", "未见异常", "未见明显异常"],
    }

    def parse_report(self, report_text: str, report_id: str = "",
                     patient_id: str = "") -> StructuredReport:
        """
        解析自由文本影像报告为结构化数据
        """
        report = StructuredReport(
            report_id=report_id,
            patient_id=patient_id,
            report_date=datetime.now().strftime("%Y-%m-%d")
        )

        # 提取检查类型和部位
        report.exam_type, report.modality, report.body_part = \
            self._extract_exam_info(report_text)

        # 提取临床指征
        report.clinical_indication = self._extract_indication(report_text)

        # 分离Findings和Impression
        findings_text, impression_text = self._split_sections(report_text)
        report.impression = impression_text

        # 提取征象
        report.findings = self._extract_findings(findings_text)

        # 提取建议
        report.recommendations = self._extract_recommendations(report_text)

        # 提取对比检查
        report.comparison_studies = self._extract_comparison(report_text)

        return report

    def _extract_exam_info(self, text: str) -> Tuple[str, str, str]:
        """提取检查信息"""
        modality_map = {
            "CT": ["CT", "计算机断层"],
            "MRI": ["MRI", "MR", "磁共振"],
            "DR": ["DR", "X线", "X光", "胸片"],
            "超声": ["超声", "B超", "彩超"],
            "MAMMO": ["钼靶", "乳腺X线"],
        }
        modality = ""
        for mod, keywords in modality_map.items():
            if any(kw in text for kw in keywords):
                modality = mod
                break

        body_part = ""
        for anatomy in self.ANATOMY_KEYWORDS:
            if anatomy in text:
                body_part = anatomy
                break

        exam_type = f"{modality}{body_part}检查" if modality and body_part else modality or "影像检查"
        return exam_type, modality, body_part

    def _extract_indication(self, text: str) -> str:
        """提取临床指征"""
        patterns = [
            r"临床诊断[：:]\s*(.+?)(?:\n|$)",
            r"检查目的[：:]\s*(.+?)(?:\n|$)",
            r"因(.+?)行.*?检查",
            r"主诉[：:]\s*(.+?)(?:\n|$)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        return ""

    def _split_sections(self, text: str) -> Tuple[str, str]:
        """分离影像表现和诊断意见"""
        # 常见报告结构
        impression_markers = ["诊断意见", "诊断结论", "印象", "IMPRESSION",
                             "Conclusion", "诊断", "报告意见"]
        findings_markers = ["影像表现", "检查所见", "描述", "FINDINGS",
                           "Description", "所见"]

        impression_text = ""
        findings_text = text

        for marker in impression_markers:
            idx = text.rfind(marker)
            if idx >= 0:
                findings_text = text[:idx]
                impression_text = text[idx:]
                break

        return findings_text, impression_text

    def _extract_findings(self, text: str) -> List[ImagingFinding]:
        """从文本中提取征象"""
        findings = []
        finding_id = 0

        for finding_type, patterns in self.FINDING_PATTERNS.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text):
                    finding_id += 1
                    # 提取上下文
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end]

                    # 确定解剖部位
                    anatomy = self._find_anatomy(context)

                    # 提取大小
                    size = self._extract_size(context)

                    # 确定严重程度
                    severity = self._assess_severity(context)

                    finding = ImagingFinding(
                        finding_id=f"F{finding_id:03d}",
                        anatomy=anatomy,
                        finding_type=finding_type,
                        description=context.strip(),
                        size_mm=size,
                        location=anatomy,
                        severity=severity,
                        confidence=0.7
                    )
                    findings.append(finding)

        # 如果没有发现征象，检查是否有正常描述
        if not findings:
            if any(kw in text for kw in ["正常", "未见异常", "未见明显异常"]):
                findings.append(ImagingFinding(
                    finding_id="F001",
                    finding_type="正常",
                    description="未见明显异常",
                    severity=FindingSeverity.NORMAL,
                    confidence=0.9
                ))

        return findings

    def _find_anatomy(self, text: str) -> str:
        """在文本中查找解剖部位"""
        for anatomy in self.ANATOMY_KEYWORDS:
            if anatomy in text:
                return anatomy
        return "未明确"

    def _extract_size(self, text: str) -> Optional[float]:
        """提取病灶大小"""
        patterns = [
            r"(?:大小约?|约|直径|长径)\s*(\d+(?:\.\d+)?)\s*(cm|mm|厘米|毫米)",
            r"(\d+(?:\.\d+)?)\s*(cm|mm|厘米|毫米)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                size = float(m.group(1))
                unit = m.group(2)
                if unit in ('cm', '厘米'):
                    size *= 10
                return round(size, 1)
        return None

    def _assess_severity(self, text: str) -> FindingSeverity:
        """评估严重程度"""
        for severity, keywords in self.SEVERITY_MAP.items():
            if any(kw in text for kw in keywords):
                return severity
        return FindingSeverity.INDETERMINATE

    def _extract_recommendations(self, text: str) -> str:
        """提取建议"""
        patterns = [
            r"建议[：:]\s*(.+?)(?:\n|$)",
            r"请[：:]\s*(.+?)(?:\n|$)",
        ]
        recommendations = []
        for p in patterns:
            for m in re.finditer(p, text):
                recommendations.append(m.group(1).strip())
        return "；".join(recommendations) if recommendations else ""

    def _extract_comparison(self, text: str) -> str:
        """提取对比检查信息"""
        patterns = [
            r"与(.+?)对比",
            r"对比(.+?)检查",
            r"较前[片次]?(.+?)(?:变化|好转|进展|增大|缩小)",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        return ""


class ImagingTextAnalyzer:
    """影像-文本联合分析接口"""

    # 影像征象与临床疾病关联知识库
    FINDING_DISEASE_MAP = {
        "磨玻璃影": {"diseases": ["早期肺腺癌", "非典型腺瘤样增生", "炎症", "出血"],
                    "follow_up": "建议3-6个月复查CT"},
        "结节": {"diseases": ["肺癌", "肺结核", "炎性假瘤", "错构瘤"],
                "follow_up": "根据结节大小和密度决定随访间隔"},
        "实变": {"diseases": ["肺炎", "肺不张", "肺水肿"],
                "follow_up": "抗感染治疗后复查"},
        "胸腔积液": {"diseases": ["心力衰竭", "恶性肿瘤", "结核", "低蛋白血症"],
                     "follow_up": "建议胸腔穿刺明确性质"},
        "脑梗死": {"diseases": ["缺血性脑卒中", "脑栓塞", "腔隙性脑梗死"],
                   "follow_up": "神经内科进一步诊治"},
        "脑出血": {"diseases": ["高血压性脑出血", "动脉瘤破裂", "血管畸形"],
                   "follow_up": "神经外科/神经内科紧急处理"},
        "骨折": {"diseases": ["外伤性骨折", "病理性骨折", "骨质疏松性骨折"],
                 "follow_up": "骨科进一步处理"},
        "钙化": {"diseases": ["陈旧性病变", "良性肿瘤", "动脉硬化"],
                 "follow_up": "通常无需特殊处理"},
        "淋巴结肿大": {"diseases": ["炎症", "结核", "淋巴瘤", "转移瘤"],
                      "follow_up": "建议活检或PET-CT进一步检查"},
    }

    def analyze_finding_clinical_correlation(
        self,
        finding: ImagingFinding,
        clinical_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析影像征象与临床背景的关联

        Args:
            finding: 影像征象
            clinical_context: 临床信息 (年龄、性别、症状、病史等)

        Returns:
            关联分析结果
        """
        result = {
            "finding": finding.finding_type,
            "anatomy": finding.anatomy,
            "severity": finding.severity.value,
            "differential_diagnosis": [],
            "risk_assessment": {},
            "recommendations": finding.recommendations or "",
            "confidence": finding.confidence,
        }

        # 查找征象-疾病关联
        if finding.finding_type in self.FINDING_DISEASE_MAP:
            info = self.FINDING_DISEASE_MAP[finding.finding_type]
            result["differential_diagnosis"] = info["diseases"]
            if not result["recommendations"]:
                result["recommendations"] = info["follow_up"]

        # 基于临床背景的风险评估
        result["risk_assessment"] = self._assess_risk(
            finding, clinical_context
        )

        return result

    def _assess_risk(self, finding: ImagingFinding,
                     context: Dict[str, Any]) -> Dict[str, Any]:
        """风险评估"""
        risk_score = 0.0
        factors = []

        age = context.get("age", 0)
        if age > 60:
            risk_score += 0.2
            factors.append("年龄>60岁")
        if age > 40 and finding.finding_type in ("结节", "磨玻璃影", "肿块"):
            risk_score += 0.15
            factors.append("中年以上+占位病变")

        if context.get("smoking_history"):
            risk_score += 0.25
            factors.append("吸烟史")

        if context.get("family_history_cancer"):
            risk_score += 0.15
            factors.append("肿瘤家族史")

        if finding.size_mm and finding.size_mm > 10:
            risk_score += 0.2
            factors.append("病灶>10mm")

        if finding.severity == FindingSeverity.MALIGNANT:
            risk_score = min(1.0, risk_score + 0.5)
        elif finding.severity == FindingSeverity.SUSPICIOUS:
            risk_score = min(1.0, risk_score + 0.3)

        risk_level = "低"
        if risk_score > 0.7:
            risk_level = "高"
        elif risk_score > 0.4:
            risk_level = "中"

        return {
            "score": round(min(1.0, risk_score), 2),
            "level": risk_level,
            "factors": factors
        }

    def generate_structured_description(
        self,
        findings: List[ImagingFinding]
    ) -> str:
        """生成结构化影像描述文本"""
        sections = []

        # 按部位分组
        by_anatomy = {}
        for f in findings:
            by_anatomy.setdefault(f.anatomy, []).append(f)

        for anatomy, items in by_anatomy.items():
            section = f"{anatomy}: "
            descs = []
            for item in items:
                size_str = f"，大小约{item.size_mm}mm" if item.size_mm else ""
                descs.append(f"{item.finding_type}{size_str}")
            section += "；".join(descs) + "。"
            sections.append(section)

        return "\n".join(sections) if sections else "未见明显异常。"


class ImagingSignLibrary:
    """常见影像征象智能识别模板库"""

    SIGNS = {
        "树芽征": {
            "description": "细支气管及其周围炎症，呈树芽状分布",
            "modalities": ["CT"],
            "anatomy": ["肺部"],
            "diseases": ["肺结核", "支气管肺炎", "囊性纤维化"],
            "severity": FindingSeverity.INDETERMINATE,
        },
        "磨玻璃影": {
            "description": "肺内局灶性密度增高影，但不掩盖肺纹理",
            "modalities": ["CT"],
            "anatomy": ["肺部"],
            "diseases": ["早期肺腺癌", "非典型腺瘤样增生", "炎症", "肺水肿"],
            "severity": FindingSeverity.INDETERMINATE,
        },
        "反晕征": {
            "description": "中央磨玻璃影伴外周实变环",
            "modalities": ["CT"],
            "anatomy": ["肺部"],
            "diseases": ["隐源性机化性肺炎", "副球孢子菌病"],
            "severity": FindingSeverity.INDETERMINATE,
        },
        "空气新月征": {
            "description": "坏死病灶内出现新月形气体影",
            "modalities": ["CT", "X-Ray"],
            "anatomy": ["肺部"],
            "diseases": ["曲霉菌感染", "肺脓肿", "肺结核"],
            "severity": FindingSeverity.SUSPICIOUS,
        },
        "D字征": {
            "description": "胸腔积液压迫肺组织呈D字形",
            "modalities": ["CT", "X-Ray"],
            "anatomy": ["胸腔"],
            "diseases": ["恶性胸腔积液", "脓胸"],
            "severity": FindingSeverity.SUSPICIOUS,
        },
        "新月形坏死": {
            "description": "病灶边缘呈新月形坏死",
            "modalities": ["MRI", "CT"],
            "anatomy": ["肝脏", "脾脏"],
            "diseases": ["肝脓肿", "转移瘤"],
            "severity": FindingSeverity.SUSPICIOUS,
        },
        "牛眼征": {
            "description": "转移瘤中心坏死呈靶样改变",
            "modalities": ["CT", "MRI"],
            "anatomy": ["肝脏"],
            "diseases": ["肝转移瘤"],
            "severity": FindingSeverity.MALIGNANT,
        },
        "脑回样强化": {
            "description": "脑皮质呈脑回样强化",
            "modalities": ["MRI"],
            "anatomy": ["大脑"],
            "diseases": ["脑梗死亚急性期", "脑炎", "线粒体脑病"],
            "severity": FindingSeverity.CRITICAL,
        },
        "盔甲脑": {
            "description": "硬脑膜广泛增厚强化",
            "modalities": ["MRI"],
            "anatomy": ["颅脑"],
            "diseases": ["低颅压综合征", "肥厚性硬脑膜炎"],
            "severity": FindingSeverity.CRITICAL,
        },
    }

    def get_sign(self, sign_name: str) -> Optional[Dict[str, Any]]:
        """获取征象信息"""
        return self.SIGNS.get(sign_name)

    def search_signs(self, keyword: str) -> List[Dict[str, Any]]:
        """搜索征象"""
        results = []
        keyword_lower = keyword.lower()
        for name, info in self.SIGNS.items():
            searchable = (name + info["description"] +
                         "".join(info["diseases"]) +
                         "".join(info["anatomy"]))
            if keyword_lower in searchable.lower():
                results.append({"name": name, **info})
        return results

    def get_signs_by_modality(self, modality: str) -> List[Dict[str, Any]]:
        """按模态获取征象"""
        return [{"name": name, **info}
                for name, info in self.SIGNS.items()
                if modality in info["modalities"]]

    def get_signs_by_anatomy(self, anatomy: str) -> List[Dict[str, Any]]:
        """按部位获取征象"""
        return [{"name": name, **info}
                for name, info in self.SIGNS.items()
                if any(anatomy in a for a in info["anatomy"])]


class MedicalImagingToolkit:
    """医学影像分析工具箱主类"""

    def __init__(self):
        self.dicom_reader = DICOMReader()
        self.report_parser = RadiologyReportParser()
        self.text_analyzer = ImagingTextAnalyzer()
        self.sign_library = ImagingSignLibrary()

    def analyze_dicom(self, file_path: str) -> ImagingStudy:
        """分析DICOM文件"""
        if not self.dicom_reader.is_dicom(file_path):
            raise ValueError(f"文件不是DICOM格式: {file_path}")

        header = self.dicom_reader.read_file(file_path)
        study = ImagingStudy(
            study_id=header.study_instance_uid,
            dicom_header=header,
            file_paths=[file_path],
            preview_available=header.rows > 0 and header.columns > 0,
            metadata={
                "file_size_kb": 0,
                "parse_method": "pydicom" if self.dicom_reader._has_pydicom else "basic"
            }
        )
        return study

    def parse_radiology_report(self, report_text: str, **kwargs) -> StructuredReport:
        """解析放射学报告"""
        return self.report_parser.parse_report(report_text, **kwargs)

    def correlate_finding_with_clinical(
        self,
        finding: ImagingFinding,
        clinical_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """影像-临床关联分析"""
        return self.text_analyzer.analyze_finding_clinical_correlation(
            finding, clinical_context
        )

    def get_sign_info(self, sign_name: str) -> Optional[Dict[str, Any]]:
        """查询影像征象信息"""
        return self.sign_library.get_sign(sign_name)

    def generate_report_summary(self, report: StructuredReport) -> str:
        """生成报告摘要"""
        lines = [
            f"检查类型: {report.exam_type}",
            f"检查部位: {report.body_part}",
            f"临床指征: {report.clinical_indication or '未提供'}",
            f"发现征象数: {len(report.findings)}",
        ]

        if report.findings:
            lines.append("\n主要发现:")
            for f in report.findings[:5]:
                size_str = f" ({f.size_mm}mm)" if f.size_mm else ""
                lines.append(f"  • [{f.severity.value}] {f.anatomy}{size_str}: {f.finding_type}")

        lines.append(f"\n诊断印象: {report.impression or '见报告原文'}")

        if report.recommendations:
            lines.append(f"建议: {report.recommendations}")

        return "\n".join(lines)
