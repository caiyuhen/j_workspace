"""
临床科研自动化模块
Clinical Research Automation Module
"""

from .rct import (
    StudyPhase,
    StudyType,
    StudyDesign,
    SampleSizeCalculator,
    RCTProtocolGenerator,
    RWEAnalyzer,
    StudyReportGenerator
)

from .meta_analysis import (
    EffectMeasureType,
    StudyData,
    EffectSizeResult,
    HeterogeneityResult,
    PublicationBiasResult,
    MetaAnalysisResult,
    EffectSizeCalculator,
    MetaAnalyzer,
    PublicationBiasAnalyzer,
    PRISMAGenerator,
    ForestPlotGenerator,
    MetaAnalysisToolkit,
)

from .grant_writer import (
    GrantType,
    ResearchArea,
    BudgetItem,
    GrantProposal,
    GrantTemplateGenerator,
    LiteratureReviewGenerator,
    ResearchPlanOptimizer,
    BudgetPlanner,
    GrantProposalAssistant,
)

__all__ = [
    # RCT模块
    'StudyPhase',
    'StudyType',
    'StudyDesign',
    'SampleSizeCalculator',
    'RCTProtocolGenerator',
    'RWEAnalyzer',
    'StudyReportGenerator',
    # Meta分析模块
    'EffectMeasureType',
    'StudyData',
    'EffectSizeResult',
    'HeterogeneityResult',
    'PublicationBiasResult',
    'MetaAnalysisResult',
    'EffectSizeCalculator',
    'MetaAnalyzer',
    'PublicationBiasAnalyzer',
    'PRISMAGenerator',
    'ForestPlotGenerator',
    'MetaAnalysisToolkit',
    # 基金申请模块
    'GrantType',
    'ResearchArea',
    'BudgetItem',
    'GrantProposal',
    'GrantTemplateGenerator',
    'LiteratureReviewGenerator',
    'ResearchPlanOptimizer',
    'BudgetPlanner',
    'GrantProposalAssistant',
]
