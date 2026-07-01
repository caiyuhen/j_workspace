"""
医学工具集合
Medical Tools Collection

将现有医学功能封装为标准工具接口。
"""

import os
from typing import Dict, Any, List, Optional

from .registry import ToolRegistry


# ============================================================
# 工具函数实现
# ============================================================

def diagnose(symptoms: List[str], age: int, gender: str) -> Dict[str, Any]:
    """医学诊断工具
    
    基于症状、年龄和性别进行诊断推理。
    
    Args:
        symptoms: 症状列表（如 ["头痛", "发热"]）
        age: 患者年龄
        gender: 患者性别（"男" 或 "女"）
    
    Returns:
        诊断结果，包含主要诊断、鉴别诊断和建议检查
    """
    from ..cdss.diagnosis import ClinicalDecisionSupport
    
    cdss = ClinicalDecisionSupport()
    result = cdss.diagnose(symptoms=symptoms, lab_results={"年龄": str(age), "性别": gender})
    
    # 添加患者基本信息
    result["patient_info"] = {"age": age, "gender": gender}
    
    return result


def analyze_imaging(report_text: str) -> Dict[str, Any]:
    """影像报告解析工具
    
    将自由文本影像报告解析为结构化数据。
    
    Args:
        report_text: 影像报告文本
    
    Returns:
        结构化报告数据，包含检查类型、发现征象、诊断印象等
    """
    from ..imaging import MedicalImagingToolkit
    
    toolkit = MedicalImagingToolkit()
    report = toolkit.parse_radiology_report(report_text)
    
    # 转换为可序列化的字典
    findings = []
    for f in report.findings:
        findings.append({
            "finding_id": f.finding_id,
            "anatomy": f.anatomy,
            "finding_type": f.finding_type,
            "description": f.description,
            "size_mm": f.size_mm,
            "location": f.location,
            "severity": f.severity.value,
            "confidence": f.confidence,
        })
    
    return {
        "report_id": report.report_id,
        "exam_type": report.exam_type,
        "modality": report.modality,
        "body_part": report.body_part,
        "clinical_indication": report.clinical_indication,
        "findings": findings,
        "impression": report.impression,
        "recommendations": report.recommendations,
        "report_date": report.report_date,
    }


def search_literature(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """医学文献搜索工具
    
    搜索 PubMed 等医学文献数据库。
    
    Args:
        query: 搜索查询词
        max_results: 最大返回结果数量（默认 5）
    
    Returns:
        文献列表，每项包含标题、摘要、作者、期刊等信息
    """
    from ..knowledge.base import PubMedSearcher
    
    try:
        searcher = PubMedSearcher()
        results = searcher.search(query, max_results=max_results)
        return results
    except Exception as e:
        return [{"error": f"文献搜索失败: {str(e)}", "query": query}]


def calculate_sample_size(
    study_type: str,
    alpha: float = 0.05,
    power: float = 0.8,
    **kwargs
) -> Dict[str, Any]:
    """样本量计算工具
    
    根据研究类型和参数计算所需样本量。
    
    Args:
        study_type: 研究类型，可选 "proportion"（率比较）、"mean"（均数比较）、"survival"（生存分析）
        alpha: 显著性水平（默认 0.05）
        power: 检验效能（默认 0.8）
        **kwargs: 额外参数，根据 study_type 不同：
            - proportion: p1, p2, ratio
            - mean: mean1, mean2, std_dev, ratio
            - survival: median_survival_control, median_survival_treatment, hazard_ratio, ratio
    
    Returns:
        样本量计算结果
    """
    from ..research.rct import SampleSizeCalculator
    
    calculator = SampleSizeCalculator()
    
    if study_type == "proportion":
        p1 = kwargs.get("p1", 0.3)
        p2 = kwargs.get("p2", 0.5)
        ratio = kwargs.get("ratio", 1.0)
        return calculator.calculate_proportion(
            p1=p1, p2=p2, alpha=alpha, power=power, ratio=ratio
        )
    elif study_type == "mean":
        mean1 = kwargs.get("mean1", 50)
        mean2 = kwargs.get("mean2", 60)
        std_dev = kwargs.get("std_dev", 15)
        ratio = kwargs.get("ratio", 1.0)
        return calculator.calculate_mean(
            mean1=mean1, mean2=mean2, std_dev=std_dev,
            alpha=alpha, power=power, ratio=ratio
        )
    elif study_type == "survival":
        median_survival_control = kwargs.get("median_survival_control", 12)
        median_survival_treatment = kwargs.get("median_survival_treatment", 18)
        hazard_ratio = kwargs.get("hazard_ratio", 0.75)
        ratio = kwargs.get("ratio", 1.0)
        return calculator.calculate_survival(
            median_survival_control=median_survival_control,
            median_survival_treatment=median_survival_treatment,
            hazard_ratio=hazard_ratio,
            alpha=alpha, power=power, ratio=ratio
        )
    else:
        raise ValueError(f"不支持的研究类型: {study_type}，可选: proportion, mean, survival")


def generate_medical_note(note_type: str, patient_info: Dict[str, Any]) -> str:
    """病历生成工具
    
    根据模板类型和患者信息生成结构化病历。
    
    Args:
        note_type: 病历类型，可选 "admission_note"（入院记录）、"progress_note"（病程记录）、"discharge_note"（出院记录）
        patient_info: 患者信息字典，字段根据 note_type 不同：
            - admission_note: patient_name, gender, age, chief_complaint, diagnosis, ...
            - progress_note: subjective, temperature, pulse, respiration, blood_pressure, ...
            - discharge_note: patient_name, gender, age, admission_diagnosis, discharge_diagnosis, discharge_orders, ...
    
    Returns:
        生成的病历文本
    """
    from ..emr.automation import EMRNoteGenerator
    
    generator = EMRNoteGenerator()
    
    if note_type == "admission_note":
        return generator.generate_admission_note(
            patient_name=patient_info.get("patient_name", "不详"),
            gender=patient_info.get("gender", "男"),
            age=patient_info.get("age", 0),
            chief_complaint=patient_info.get("chief_complaint", ""),
            diagnosis=patient_info.get("diagnosis", "待查"),
            **{k: v for k, v in patient_info.items() if k not in [
                "patient_name", "gender", "age", "chief_complaint", "diagnosis"
            ]}
        )
    elif note_type == "progress_note":
        return generator.generate_progress_note(
            subjective=patient_info.get("subjective", "无特殊不适"),
            temperature=patient_info.get("temperature", 36.5),
            pulse=patient_info.get("pulse", 72),
            respiration=patient_info.get("respiration", 18),
            blood_pressure=patient_info.get("blood_pressure", "120/80"),
            **{k: v for k, v in patient_info.items() if k not in [
                "subjective", "temperature", "pulse", "respiration", "blood_pressure"
            ]}
        )
    elif note_type == "discharge_note":
        return generator.generate_discharge_note(
            patient_name=patient_info.get("patient_name", "不详"),
            gender=patient_info.get("gender", "男"),
            age=patient_info.get("age", 0),
            admission_diagnosis=patient_info.get("admission_diagnosis", ""),
            discharge_diagnosis=patient_info.get("discharge_diagnosis", ""),
            discharge_orders=patient_info.get("discharge_orders", ""),
            **{k: v for k, v in patient_info.items() if k not in [
                "patient_name", "gender", "age", "admission_diagnosis", "discharge_diagnosis", "discharge_orders"
            ]}
        )
    else:
        raise ValueError(f"不支持的病历类型: {note_type}，可选: admission_note, progress_note, discharge_note")


def check_medication_safety(
    medications: List[str],
    patient_conditions: Dict[str, Any]
) -> Dict[str, Any]:
    """用药安全检查工具
    
    检查药物相互作用、过敏史和剂量安全性。
    
    Args:
        medications: 药物名称列表（如 ["阿司匹林", "二甲双胍"]）
        patient_conditions: 患者情况字典，可包含：
            - allergies: 过敏药物列表
            - doses: 各药物日剂量字典（如 {"阿司匹林": 100}）
    
    Returns:
        用药安全检查结果，包含警告列表和安全评估
    """
    from ..cdss.diagnosis import MedicationSafetyChecker
    
    checker = MedicationSafetyChecker()
    
    allergies = patient_conditions.get("allergies", [])
    doses = patient_conditions.get("doses", {})
    
    return checker.comprehensive_check(
        medications=medications,
        allergies=allergies,
        doses=doses
    )


def export_document(doc_type: str, data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
    """文档导出工具
    
    将数据导出为 Office 文档。
    
    Args:
        doc_type: 文档类型，可选 "paper"（论文）、"proposal"（基金申请）、"response_letter"（回复信）、"protocol"（试验方案）
        data: 文档数据字典
        file_path: 输出文件路径
    
    Returns:
        导出结果，包含文件路径和状态
    """
    from ..export.document_exporter import PaperExporter, GrantProposalExporter, ResponseLetterExporter, ProtocolExporter
    
    exporters = {
        "paper": PaperExporter,
        "proposal": GrantProposalExporter,
        "response_letter": ResponseLetterExporter,
        "protocol": ProtocolExporter,
    }
    
    if doc_type not in exporters:
        raise ValueError(f"不支持的文档类型: {doc_type}，可选: {', '.join(exporters.keys())}")
    
    exporter_class = exporters[doc_type]
    exporter = exporter_class()
    
    export_methods = {
        "paper": "export_paper",
        "proposal": "export_proposal",
        "response_letter": "export_response_letter",
        "protocol": "export_protocol",
    }
    
    method_name = export_methods[doc_type]
    method = getattr(exporter, method_name)
    
    # 确保目录存在
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    
    saved_path = method(data, file_path)
    
    return {
        "success": True,
        "file_path": saved_path,
        "doc_type": doc_type,
    }


# ============================================================
# JSON Schema 定义
# ============================================================

DIAGNOSE_SCHEMA = {
    "type": "object",
    "properties": {
        "symptoms": {
            "type": "array",
            "items": {"type": "string"},
            "description": "症状列表，如 [\"头痛\", \"发热\"]"
        },
        "age": {
            "type": "integer",
            "description": "患者年龄"
        },
        "gender": {
            "type": "string",
            "enum": ["男", "女"],
            "description": "患者性别"
        }
    },
    "required": ["symptoms", "age", "gender"]
}

ANALYZE_IMAGING_SCHEMA = {
    "type": "object",
    "properties": {
        "report_text": {
            "type": "string",
            "description": "影像报告自由文本"
        }
    },
    "required": ["report_text"]
}

SEARCH_LITERATURE_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "搜索查询词"
        },
        "max_results": {
            "type": "integer",
            "default": 5,
            "description": "最大返回结果数量"
        }
    },
    "required": ["query"]
}

CALCULATE_SAMPLE_SIZE_SCHEMA = {
    "type": "object",
    "properties": {
        "study_type": {
            "type": "string",
            "enum": ["proportion", "mean", "survival"],
            "description": "研究类型：proportion（率比较）、mean（均数比较）、survival（生存分析）"
        },
        "alpha": {
            "type": "number",
            "default": 0.05,
            "description": "显著性水平"
        },
        "power": {
            "type": "number",
            "default": 0.8,
            "description": "检验效能"
        },
        "p1": {
            "type": "number",
            "description": "对照组阳性率（proportion 类型时必填）"
        },
        "p2": {
            "type": "number",
            "description": "试验组阳性率（proportion 类型时必填）"
        },
        "mean1": {
            "type": "number",
            "description": "对照组均值（mean 类型时可用）"
        },
        "mean2": {
            "type": "number",
            "description": "试验组均值（mean 类型时可用）"
        },
        "std_dev": {
            "type": "number",
            "description": "标准差（mean 类型时可用）"
        },
        "hazard_ratio": {
            "type": "number",
            "description": "风险比（survival 类型时可用）"
        },
        "ratio": {
            "type": "number",
            "default": 1.0,
            "description": "试验组/对照组样本量比例"
        }
    },
    "required": ["study_type", "alpha", "power"]
}

GENERATE_MEDICAL_NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "note_type": {
            "type": "string",
            "enum": ["admission_note", "progress_note", "discharge_note"],
            "description": "病历类型"
        },
        "patient_info": {
            "type": "object",
            "description": "患者信息字典，字段根据病历类型不同"
        }
    },
    "required": ["note_type", "patient_info"]
}

CHECK_MEDICATION_SAFETY_SCHEMA = {
    "type": "object",
    "properties": {
        "medications": {
            "type": "array",
            "items": {"type": "string"},
            "description": "药物名称列表"
        },
        "patient_conditions": {
            "type": "object",
            "properties": {
                "allergies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "过敏药物列表"
                },
                "doses": {
                    "type": "object",
                    "description": "药物日剂量字典，如 {\"阿司匹林\": 100}"
                }
            },
            "description": "患者情况"
        }
    },
    "required": ["medications", "patient_conditions"]
}

EXPORT_DOCUMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "doc_type": {
            "type": "string",
            "enum": ["paper", "proposal", "response_letter", "protocol"],
            "description": "文档类型"
        },
        "data": {
            "type": "object",
            "description": "文档数据字典"
        },
        "file_path": {
            "type": "string",
            "description": "输出文件路径"
        }
    },
    "required": ["doc_type", "data", "file_path"]
}


# ============================================================
# 工具注册函数
# ============================================================

def register_medical_tools(registry: ToolRegistry) -> ToolRegistry:
    """注册所有医学工具到注册表
    
    Args:
        registry: 工具注册表实例
    
    Returns:
        注册表实例（便于链式调用）
    """
    registry.register(
        name="diagnose",
        description="基于症状、年龄和性别进行医学诊断推理，返回可能的诊断列表和建议检查",
        parameters=DIAGNOSE_SCHEMA,
        func=diagnose
    )
    
    registry.register(
        name="analyze_imaging",
        description="将自由文本影像报告解析为结构化数据，提取征象、部位和诊断印象",
        parameters=ANALYZE_IMAGING_SCHEMA,
        func=analyze_imaging
    )
    
    registry.register(
        name="search_literature",
        description="搜索 PubMed 医学文献数据库，返回文献标题、摘要和作者信息",
        parameters=SEARCH_LITERATURE_SCHEMA,
        func=search_literature
    )
    
    registry.register(
        name="calculate_sample_size",
        description="根据研究类型和统计参数计算临床试验所需样本量",
        parameters=CALCULATE_SAMPLE_SIZE_SCHEMA,
        func=calculate_sample_size
    )
    
    registry.register(
        name="generate_medical_note",
        description="根据病历类型和患者信息生成结构化病历文本（入院记录、病程记录、出院记录）",
        parameters=GENERATE_MEDICAL_NOTE_SCHEMA,
        func=generate_medical_note
    )
    
    registry.register(
        name="check_medication_safety",
        description="检查药物相互作用、过敏史和剂量安全性，返回用药安全警告",
        parameters=CHECK_MEDICATION_SAFETY_SCHEMA,
        func=check_medication_safety
    )
    
    registry.register(
        name="export_document",
        description="将数据导出为 Office 文档（论文、基金申请、回复信、试验方案）",
        parameters=EXPORT_DOCUMENT_SCHEMA,
        func=export_document
    )
    
    return registry
