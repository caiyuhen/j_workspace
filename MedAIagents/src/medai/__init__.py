"""
MedAIagents - 专业级医学AI智能体框架
Professional Medical AI Agent Framework
"""

__version__ = "0.5.0"
__author__ = "MedAI Team"

# 配置管理
from .config import Config

# 临床决策支持
try:
    from .cdss import (
        DiagnosisEngine,
        DifferentialDiagnosis,
        MedicationSafetyChecker,
        GuidelineEngine,
        ClinicalDecisionSupportSystem
    )
except ImportError:
    pass

# 电子病历系统
try:
    from .emr import (
        EMRInformationExtractor,
        MedicalNoteGenerator,
        ICD10Coder,
        EMRNote
    )
except ImportError:
    pass

# 安全与合规
try:
    from .security import (
        DataEncryptor,
        DataDeidentifier,
        RBACManager,
        AuditLogger,
        SecurityManager
    )
except ImportError:
    pass

# 记忆系统
try:
    from .memory import MemoryManager, ConversationMemory, LongTermMemory
except ImportError:
    pass

# 知识检索
try:
    from .knowledge import MedicalKnowledgeBase, PubMedSearcher, SimpleVectorDB
except ImportError:
    pass

# 临床科研
try:
    from .research import (
        StudyPhase,
        StudyType,
        StudyDesign,
        SampleSizeCalculator,
        RCTProtocolGenerator,
        RWEAnalyzer,
        StudyReportGenerator,
        # Meta分析
        EffectMeasureType,
        StudyData,
        MetaAnalysisToolkit,
        # 基金申请
        GrantType,
        ResearchArea,
        GrantProposal,
        GrantProposalAssistant,
    )
except ImportError:
    pass

# 医学写作
try:
    from .writing import (
        JournalType,
        PaperSection,
        Citation,
        PaperGenerator,
        ReferenceManager,
        FigureTableGenerator,
        MedicalWritingAssistant,
        # 多语言支持
        Language,
        MedicalTerm,
        I18nManager,
        MedicalTerminology,
        ChineseJournalDatabase,
        MultilingualAssistant,
        # 同行评审辅助
        ReviewCommentType,
        ResponseStrategy,
        ReviewComment,
        AuthorResponse,
        ReviewCommentParser,
        ResponseGenerator,
        ResponseLetterWriter,
        RevisionTracker,
        PeerReviewAssistant,
    )
except ImportError:
    pass

# 大语言模型
try:
    from .llm import LLMProvider, OpenAIProvider, AnthropicProvider
except ImportError:
    pass

# 医学影像
try:
    from .imaging import (
        Modality,
        BodyPart,
        FindingSeverity,
        DICOMHeader,
        ImagingFinding,
        StructuredReport,
        ImagingStudy,
        DICOMReader,
        RadiologyReportParser,
        ImagingTextAnalyzer,
        ImagingSignLibrary,
        MedicalImagingToolkit,
    )
except ImportError:
    pass

# 生物信息学
try:
    from .bioinformatics import (
        SurvivalModelType,
        GenomicDataType,
        OmicsType,
        SurvivalRecord,
        KMResult,
        CoxResult,
        CompetingRiskResult,
        GeneMutation,
        GenomicSample,
        FeatureImportance,
        SHAPValue,
        OmicsDataset,
        SurvivalAnalyzer,
        GenomicVisualizer,
        ModelExplainer,
        MultiOmicsIntegrator,
        BioinformaticsToolkit,
    )
except ImportError:
    pass

# 桌面应用
try:
    from .desktop import MedAIDesktop
except ImportError:
    pass


def get_version():
    """获取版本信息"""
    return __version__


def print_version_info():
    """打印版本和功能信息"""
    print(f"🏥 MedAIagents v{__version__}")
    print("=" * 50)
    
    modules = {
        "临床决策支持 (CDSS)": True,
        "电子病历系统 (EMR)": True,
        "安全与合规引擎": True,
        "记忆管理系统": True,
        "医学知识检索": True,
        "临床科研工具": True,
        "医学写作助手": True,
        "多语言支持": True,
        "同行评审辅助": True,
        "医学影像AI分析": True,
        "生物信息学接口": True,
        "大语言模型集成": True,
        "桌面应用": True,
    }
    
    print("\n📦 可用模块：")
    for name, available in modules.items():
        status = "✅" if available else "⬜"
        print(f"  {status} {name}")
    
    print("\n" + "=" * 50)


__all__ = [
    "Config",
    # CDSS
    "DiagnosisEngine",
    "DifferentialDiagnosis",
    "MedicationSafetyChecker",
    "GuidelineEngine",
    "ClinicalDecisionSupportSystem",
    # EMR
    "EMRInformationExtractor",
    "MedicalNoteGenerator",
    "ICD10Coder",
    "EMRNote",
    # Security
    "DataEncryptor",
    "DataDeidentifier",
    "RBACManager",
    "AuditLogger",
    "SecurityManager",
    # Memory
    "MemoryManager",
    "ConversationMemory",
    "LongTermMemory",
    # Knowledge
    "MedicalKnowledgeBase",
    "PubMedSearcher",
    "SimpleVectorDB",
    # Research
    "StudyPhase",
    "StudyType",
    "StudyDesign",
    "SampleSizeCalculator",
    "RCTProtocolGenerator",
    "RWEAnalyzer",
    "StudyReportGenerator",
    # Meta分析
    "EffectMeasureType",
    "StudyData",
    "MetaAnalysisToolkit",
    # 基金申请
    "GrantType",
    "ResearchArea",
    "GrantProposal",
    "GrantProposalAssistant",
    # Writing
    "JournalType",
    "PaperSection",
    "Citation",
    "PaperGenerator",
    "ReferenceManager",
    "FigureTableGenerator",
    "MedicalWritingAssistant",
    # 多语言支持
    "Language",
    "MedicalTerm",
    "I18nManager",
    "MedicalTerminology",
    "ChineseJournalDatabase",
    "MultilingualAssistant",
    # 同行评审辅助
    "ReviewCommentType",
    "ResponseStrategy",
    "ReviewComment",
    "AuthorResponse",
    "ReviewCommentParser",
    "ResponseGenerator",
    "ResponseLetterWriter",
    "RevisionTracker",
    "PeerReviewAssistant",
    # LLM
    "LLMProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    # 医学影像
    "Modality",
    "BodyPart",
    "FindingSeverity",
    "DICOMHeader",
    "ImagingFinding",
    "StructuredReport",
    "ImagingStudy",
    "DICOMReader",
    "RadiologyReportParser",
    "ImagingTextAnalyzer",
    "ImagingSignLibrary",
    "MedicalImagingToolkit",
    # 生物信息学
    "SurvivalModelType",
    "GenomicDataType",
    "OmicsType",
    "SurvivalRecord",
    "KMResult",
    "CoxResult",
    "CompetingRiskResult",
    "GeneMutation",
    "GenomicSample",
    "FeatureImportance",
    "SHAPValue",
    "OmicsDataset",
    "SurvivalAnalyzer",
    "GenomicVisualizer",
    "ModelExplainer",
    "MultiOmicsIntegrator",
    "BioinformaticsToolkit",
    # Desktop
    "MedAIDesktop",
    # Utilities
    "get_version",
    "print_version_info",
]
