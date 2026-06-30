"""
医学写作助手模块
Medical Writing Assistant Module
"""

from .medical_writing import (
    JournalType,
    PaperSection,
    Citation,
    PaperGenerator,
    ReferenceManager,
    FigureTableGenerator,
    MedicalWritingAssistant
)

from .paper_evaluator import (
    JournalTier,
    EvaluationDimension,
    JournalRecommendation,
    StudyTypeWeights,
    PaperQualityScorer,
    JournalRecommender,
    PaperEvaluator
)

from .paper_parser import (
    StudyDesignType,
    ParsedPaper,
    PaperTextParser
)

from .multilingual import (
    Language,
    MedicalTerm,
    I18nManager,
    MedicalTerminology,
    ChineseJournalDatabase,
    MultilingualAssistant,
)

from .peer_review import (
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

__all__ = [
    # 基础类
    'JournalType',
    'PaperSection',
    'Citation',
    # 论文生成
    'PaperGenerator',
    # 参考文献管理
    'ReferenceManager',
    # 图表生成
    'FigureTableGenerator',
    # 主类
    'MedicalWritingAssistant',
    # 论文评分和期刊推荐
    'JournalTier',
    'EvaluationDimension',
    'JournalRecommendation',
    'StudyTypeWeights',
    'PaperQualityScorer',
    'JournalRecommender',
    'PaperEvaluator',
    # 论文解析
    'StudyDesignType',
    'ParsedPaper',
    'PaperTextParser',
    # 多语言支持
    'Language',
    'MedicalTerm',
    'I18nManager',
    'MedicalTerminology',
    'ChineseJournalDatabase',
    'MultilingualAssistant',
    # 同行评审辅助
    'ReviewCommentType',
    'ResponseStrategy',
    'ReviewComment',
    'AuthorResponse',
    'ReviewCommentParser',
    'ResponseGenerator',
    'ResponseLetterWriter',
    'RevisionTracker',
    'PeerReviewAssistant',
]
