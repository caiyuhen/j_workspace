"""
专科 Agent
Specialized Agents
"""

from typing import Any

from .base import BaseAgent
from ..tools.medical_tools import register_medical_tools


class ClinicalAgent(BaseAgent):
    """临床 Agent

    专注于临床诊断、用药安全和病历生成。
    """

    def __init__(self, llm_router: Any):
        super().__init__(
            name="临床Agent",
            role="clinical",
            system_prompt="""你是资深临床医生，拥有20年以上临床经验。

你的专业领域包括：
1. 疾病诊断与鉴别诊断
2. 用药方案制定与安全检查
3. 病历文书撰写
4. 临床指南解读

请用专业、严谨、清晰的语言回答临床问题。
在给出任何诊断或治疗建议时，务必提醒用户这仅为辅助参考，最终决策应由主治医师做出。""",
            llm_router=llm_router,
        )
        # 预注册临床相关工具
        register_medical_tools(self.tools)


class ImagingAgent(BaseAgent):
    """影像 Agent

    专注于医学影像报告解析和影像诊断辅助。
    """

    def __init__(self, llm_router: Any):
        super().__init__(
            name="影像Agent",
            role="imaging",
            system_prompt="""你是放射科医生，擅长各类医学影像的解读与分析。

你的专业领域包括：
1. CT、MRI、X光、超声等影像报告解析
2. 影像征象识别与描述
3. 影像诊断与鉴别诊断
4. 影像随访建议

请用专业的放射学术语描述影像表现，并给出清晰的诊断印象。""",
            llm_router=llm_router,
        )
        # 预注册影像相关工具
        from ..tools.medical_tools import ANALYZE_IMAGING_SCHEMA, analyze_imaging
        self.tools.register(
            name="analyze_imaging",
            description="将自由文本影像报告解析为结构化数据，提取征象、部位和诊断印象",
            parameters=ANALYZE_IMAGING_SCHEMA,
            func=analyze_imaging,
        )


class ResearchAgent(BaseAgent):
    """科研 Agent

    专注于临床研究设计、文献检索和统计分析。
    """

    def __init__(self, llm_router: Any):
        super().__init__(
            name="科研Agent",
            role="research",
            system_prompt="""你是临床科研人员，精通临床研究设计与统计分析。

你的专业领域包括：
1. 临床试验设计（RCT、队列研究、病例对照研究）
2. 样本量计算与统计效能分析
3. 文献检索与系统评价
4. 统计分析方法选择

请基于循证医学原则给出科研建议，并推荐合适的统计方法。""",
            llm_router=llm_router,
        )
        # 预注册科研相关工具
        from ..tools.medical_tools import (
            CALCULATE_SAMPLE_SIZE_SCHEMA,
            SEARCH_LITERATURE_SCHEMA,
            calculate_sample_size,
            search_literature,
        )
        self.tools.register(
            name="calculate_sample_size",
            description="根据研究类型和统计参数计算临床试验所需样本量",
            parameters=CALCULATE_SAMPLE_SIZE_SCHEMA,
            func=calculate_sample_size,
        )
        self.tools.register(
            name="search_literature",
            description="搜索 PubMed 医学文献数据库，返回文献标题、摘要和作者信息",
            parameters=SEARCH_LITERATURE_SCHEMA,
            func=search_literature,
        )


class WritingAgent(BaseAgent):
    """写作 Agent

    专注于医学论文撰写、基金申请和学术写作。
    """

    def __init__(self, llm_router: Any):
        super().__init__(
            name="写作Agent",
            role="writing",
            system_prompt="""你是医学写作专家，擅长各类医学学术文书的撰写。

你的专业领域包括：
1. SCI论文撰写与润色
2. 基金申请书撰写
3. 临床试验方案撰写
4. 伦理审查申请文书
5. 学术回复信（Response Letter）

请使用规范的学术语言，确保逻辑清晰、表述准确。""",
            llm_router=llm_router,
        )
        # 预注册写作相关工具
        from ..tools.medical_tools import EXPORT_DOCUMENT_SCHEMA, export_document
        self.tools.register(
            name="export_document",
            description="将数据导出为 Office 文档（论文、基金申请、回复信、试验方案）",
            parameters=EXPORT_DOCUMENT_SCHEMA,
            func=export_document,
        )


class BioinformaticsAgent(BaseAgent):
    """生信 Agent

    专注于生物信息学分析、基因组学和生存分析。
    """

    def __init__(self, llm_router: Any):
        super().__init__(
            name="生信Agent",
            role="bioinformatics",
            system_prompt="""你是生物信息学专家，精通多组学数据分析。

你的专业领域包括：
1. 基因组学/转录组学数据分析
2. 生存分析与预后模型构建
3. 差异表达分析与通路富集
4. 机器学习在生物医学中的应用
5. 数据可视化与报告生成

请使用专业的生物信息学术语，并给出可执行的分析建议。""",
            llm_router=llm_router,
        )
        # 生信 Agent 暂时注册通用工具（未来可扩展为生信专用工具）
        from ..tools.medical_tools import EXPORT_DOCUMENT_SCHEMA, export_document
        self.tools.register(
            name="export_document",
            description="将分析结果导出为 Office 文档",
            parameters=EXPORT_DOCUMENT_SCHEMA,
            func=export_document,
        )
