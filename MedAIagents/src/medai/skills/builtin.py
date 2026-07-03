"""
内置医学 Skills

预置的常用临床和科研工作流模板。
"""

from typing import Dict, List, Any
from loguru import logger

from .models import Skill, SkillStep, SkillParameter, StepType
from .registry import SkillRegistry


def register_builtin_skills(registry: SkillRegistry = None) -> List[Skill]:
    """注册所有内置 Skills
    
    Args:
        registry: SkillRegistry 实例，如提供则自动注册
    
    Returns:
        所有内置 Skill 列表
    """
    skills = [
        _build_lung_cancer_diagnosis_skill(),
        _build_meta_analysis_writing_skill(),
        _build_grant_proposal_skill(),
        _build_rct_protocol_skill(),
        _build_imaging_report_skill(),
        _build_literature_review_skill(),
        _build_survival_analysis_skill(),
        _build_response_letter_skill(),
        _build_medical_note_skill(),
        _build_drug_safety_check_skill(),
        _build_package_installer_skill(),
        _build_ecrf_designer_skill(),
    ]
    
    if registry:
        for skill in skills:
            registry.register(skill)
        logger.info(f"已注册 {len(skills)} 个内置 Skills")
    
    return skills


def _build_lung_cancer_diagnosis_skill() -> Skill:
    """肺癌诊断流程 Skill"""
    return Skill(
        name="lung_cancer_diagnosis_workflow",
        description="肺癌标准化诊断流程：从症状评估到分期诊断的完整工作流",
        version="1.0.0",
        parameters=[
            SkillParameter(name="symptoms", description="患者症状描述", type="string", required=True),
            SkillParameter(name="age", description="患者年龄", type="number", required=True),
            SkillParameter(name="smoking_history", description="吸烟史（包年）", type="number", required=False, default=0),
            SkillParameter(name="imaging_available", description="是否有影像资料", type="boolean", required=False, default=False),
        ],
        steps=[
            SkillStep(
                name="症状评估",
                step_type=StepType.LLM_CALL,
                description="评估肺癌相关症状",
                config={
                    "prompt_template": """请评估以下患者的肺癌风险症状：
年龄: ${age}岁
症状: ${symptoms}
吸烟史: ${smoking_history}包年

请评估：
1. 症状的警示性（1-10分）
2. 需要优先排查的肺癌类型
3. 建议的紧急程度""",
                    "system_prompt": "你是一位肺癌专科医生，擅长早期筛查和诊断。"
                },
                output_var="symptom_assessment"
            ),
            SkillStep(
                name="影像检查建议",
                step_type=StepType.CONDITION,
                description="根据症状评估决定影像检查",
                config={
                    "condition_expression": "${imaging_available} == False",
                },
                output_var="needs_imaging"
            ),
            SkillStep(
                name="推荐影像检查",
                step_type=StepType.LLM_CALL,
                description="推荐合适的影像检查",
                config={
                    "prompt_template": "基于症状评估: ${symptom_assessment}，请推荐最适合的影像学检查（CT/PET-CT/支气管镜等）及检查要点。"
                },
                output_var="imaging_recommendation"
            ),
            SkillStep(
                name="诊断方案",
                step_type=StepType.LLM_CALL,
                description="制定诊断方案",
                config={
                    "prompt_template": """综合以下信息，制定完整的肺癌诊断方案：
症状评估: ${symptom_assessment}
影像建议: ${imaging_recommendation}

请包括：
1. 推荐的诊断路径
2. 需要排除的鉴别诊断
3. 必要的实验室检查
4. 何时考虑活检"""
                },
                output_var="diagnosis_plan"
            ),
            SkillStep(
                name="输出诊断报告",
                step_type=StepType.OUTPUT,
                description="生成最终诊断报告",
                config={
                    "output_template": """# 肺癌诊断评估报告

## 症状评估
${symptom_assessment}

## 影像学建议
${imaging_recommendation}

## 诊断方案
${diagnosis_plan}

---
*本报告由AI辅助生成，仅供参考，最终诊断需由专科医生确认。*"""
                },
                output_var="output"
            ),
        ],
        tags=["clinical", "diagnosis", "lung_cancer", "oncology", "builtin"],
        is_builtin=True
    )


def _build_meta_analysis_writing_skill() -> Skill:
    """Meta 分析写作 Skill"""
    return Skill(
        name="meta_analysis_writing_workflow",
        description="Meta 分析论文结构化写作工作流：从文献检索到结果解读",
        version="1.0.0",
        parameters=[
            SkillParameter(name="topic", description="研究主题/问题", type="string", required=True),
            SkillParameter(name="effect_measure", description="效应指标(OR/RR/MD/SMD)", type="string", required=True, enum=["OR", "RR", "MD", "SMD"]),
            SkillParameter(name="num_studies", description="纳入研究数量", type="number", required=False, default=10),
            SkillParameter(name="language", description="写作语言", type="string", required=False, default="chinese", enum=["chinese", "english"]),
        ],
        steps=[
            SkillStep(
                name="撰写检索策略",
                step_type=StepType.LLM_CALL,
                description="生成文献检索策略",
                config={
                    "prompt_template": """请为以下Meta分析主题设计系统的文献检索策略：
主题: ${topic}

请提供：
1. PubMed/Medline 检索式
2. Embase 检索式  
3. Cochrane Library 检索式
4. 中文数据库检索式（CNKI/WanFang）"""
                },
                output_var="search_strategy"
            ),
            SkillStep(
                name="撰写方法学",
                step_type=StepType.LLM_CALL,
                description="撰写方法学部分",
                config={
                    "prompt_template": """请撰写Meta分析的方法学部分（Methods）：
主题: ${topic}
效应指标: ${effect_measure}
预计纳入研究数: ${num_studies}

请包括：
1. 纳入排除标准
2. 文献筛选流程
3. 数据提取方法
4. 质量评价工具
5. 统计分析方法
6. 异质性处理策略"""
                },
                output_var="methods_section"
            ),
            SkillStep(
                name="撰写结果框架",
                step_type=StepType.LLM_CALL,
                description="撰写结果部分框架",
                config={
                    "prompt_template": """请撰写Meta分析的结果部分框架（Results）：
主题: ${topic}
效应指标: ${effect_measure}

请包括：
1. 文献筛选流程（PRISMA）
2. 纳入研究基本特征表
3. 质量评价结果
4. 主要结果（森林图描述）
5. 异质性分析
6. 发表偏倚评估
7. 亚组分析框架"""
                },
                output_var="results_section"
            ),
            SkillStep(
                name="撰写讨论",
                step_type=StepType.LLM_CALL,
                description="撰写讨论部分",
                config={
                    "prompt_template": """请撰写Meta分析的讨论部分（Discussion）：
主题: ${topic}
方法学: ${methods_section}
结果框架: ${results_section}

请按结构撰写：
1. 主要发现总结
2. 与现有证据的比较
3. 研究优势
4. 研究局限性
5. 临床意义
6. 未来研究方向"""
                },
                output_var="discussion_section"
            ),
            SkillStep(
                name="生成完整论文框架",
                step_type=StepType.OUTPUT,
                description="组装完整论文",
                config={
                    "output_template": """# Meta分析论文框架

## 检索策略
${search_strategy}

## 方法学 (Methods)
${methods_section}

## 结果 (Results)
${results_section}

## 讨论 (Discussion)
${discussion_section}

---
*请根据实际数据填充具体数值和图表。本框架遵循PRISMA指南。*"""
                },
                output_var="output"
            ),
        ],
        tags=["research", "writing", "meta_analysis", "builtin"],
        is_builtin=True
    )


def _build_grant_proposal_skill() -> Skill:
    """基金申请书撰写 Skill"""
    return Skill(
        name="grant_proposal_writing_workflow",
        description="基金申请书结构化撰写工作流",
        version="1.0.0",
        parameters=[
            SkillParameter(name="title", description="研究题目", type="string", required=True),
            SkillParameter(name="grant_type", description="基金类型", type="string", required=True, enum=["NSFC", "provincial", "hospital"]),
            SkillParameter(name="research_area", description="研究领域", type="string", required=True),
            SkillParameter(name="budget", description="预算金额（万元）", type="number", required=False, default=50),
        ],
        steps=[
            SkillStep(
                name="撰写立项依据",
                step_type=StepType.LLM_CALL,
                description="生成立项依据框架",
                config={
                    "prompt_template": """请为以下基金申请撰写立项依据框架：
题目: ${title}
领域: ${research_area}
基金类型: ${grant_type}

请包括：
1. 研究背景与意义
2. 国内外研究现状
3. 现有研究的不足
4. 本研究的创新点
5. 前期研究基础"""
                },
                output_var="rationale"
            ),
            SkillStep(
                name="设计研究方案",
                step_type=StepType.LLM_CALL,
                description="设计研究方案",
                config={
                    "prompt_template": """请设计详细的研究方案：
题目: ${title}
立项依据: ${rationale}

请包括：
1. 研究目标
2. 研究内容
3. 技术路线
4. 预期成果
5. 年度计划"""
                },
                output_var="research_plan"
            ),
            SkillStep(
                name="编制预算",
                step_type=StepType.LLM_CALL,
                description="编制经费预算",
                config={
                    "prompt_template": """请编制${grant_type}基金的经费预算（${budget}万元）：

按以下类别分配：
1. 设备费
2. 材料费
3. 测试化验加工费
4. 差旅/会议费
5. 出版/文献费
6. 劳务费
7. 专家咨询费
8. 间接费用

请给出具体金额和占比。"""
                },
                output_var="budget_plan"
            ),
            SkillStep(
                name="输出申请书框架",
                step_type=StepType.OUTPUT,
                description="组装完整申请书",
                config={
                    "output_template": """# 基金申请书框架

## 题目
${title}

## 立项依据
${rationale}

## 研究方案
${research_plan}

## 经费预算
${budget_plan}

---
*请根据实际研究内容补充详细数据和参考文献。*"""
                },
                output_var="output"
            ),
        ],
        tags=["research", "grant", "writing", "builtin"],
        is_builtin=True
    )


def _build_rct_protocol_skill() -> Skill:
    """RCT 方案设计 Skill"""
    return Skill(
        name="rct_protocol_design_workflow",
        description="随机对照试验(RCT)方案设计工作流",
        version="1.0.0",
        parameters=[
            SkillParameter(name="intervention", description="干预措施", type="string", required=True),
            SkillParameter(name="condition", description="研究疾病/条件", type="string", required=True),
            SkillParameter(name="primary_endpoint", description="主要终点指标", type="string", required=True),
            SkillParameter(name="sample_size", description="计划样本量", type="number", required=False, default=100),
        ],
        steps=[
            SkillStep(
                name="设计研究方案",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请设计RCT研究方案：
干预措施: ${intervention}
研究疾病: ${condition}
主要终点: ${primary_endpoint}
计划样本量: ${sample_size}

请包括：
1. 研究设计类型
2. 纳入排除标准
3. 随机化方法
4. 盲法设计
5. 干预方案
6. 终点指标"""
                },
                output_var="protocol_design"
            ),
            SkillStep(
                name="计算样本量",
                step_type=StepType.TOOL_CALL,
                config={
                    "tool_name": "calculate_sample_size",
                    "arguments": {
                        "effect_size": "${primary_endpoint}",
                        "alpha": 0.05,
                        "power": 0.8
                    }
                },
                output_var="sample_size_result"
            ),
            SkillStep(
                name="输出方案",
                step_type=StepType.OUTPUT,
                config={
                    "output_template": """# RCT研究方案

## 设计方案
${protocol_design}

## 样本量计算
${sample_size_result}

---
*请根据伦理审查要求补充知情同意和安全性监测内容。*"""
                },
                output_var="output"
            ),
        ],
        tags=["research", "rct", "protocol", "builtin"],
        is_builtin=True
    )


def _build_imaging_report_skill() -> Skill:
    """影像报告结构化 Skill"""
    return Skill(
        name="imaging_report_structuring_workflow",
        description="将自由文本影像报告转换为结构化报告",
        version="1.0.0",
        parameters=[
            SkillParameter(name="report_text", description="原始影像报告文本", type="string", required=True),
            SkillParameter(name="modality", description="影像模态", type="string", required=True, enum=["CT", "MRI", "X-ray", "Ultrasound", "PET-CT"]),
            SkillParameter(name="body_part", description="检查部位", type="string", required=True),
        ],
        steps=[
            SkillStep(
                name="提取关键发现",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请从以下${modality}影像报告中提取关键发现：
检查部位: ${body_part}

报告内容:
${report_text}

请提取：
1. 主要征象
2. 病变位置
3. 病变大小
4. 密度/信号特征
5. 强化特征（如适用）"""
                },
                output_var="findings"
            ),
            SkillStep(
                name="生成结构化报告",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请基于以下发现生成结构化影像报告：

发现: ${findings}
模态: ${modality}
部位: ${body_part}

请按以下格式输出：
【检查信息】
【技术方法】
【影像所见】
【影像诊断/印象】
【建议】"""
                },
                output_var="structured_report"
            ),
            SkillStep(
                name="输出结果",
                step_type=StepType.OUTPUT,
                config={
                    "output_template": """# 结构化影像报告

${structured_report}

---
*原始报告已结构化处理*"""
                },
                output_var="output"
            ),
        ],
        tags=["imaging", "clinical", "report", "builtin"],
        is_builtin=True
    )


def _build_literature_review_skill() -> Skill:
    """文献综述 Skill"""
    return Skill(
        name="literature_review_workflow",
        description="系统性文献综述撰写工作流",
        version="1.0.0",
        parameters=[
            SkillParameter(name="topic", description="综述主题", type="string", required=True),
            SkillParameter(name="num_papers", description="计划综述文献数", type="number", required=False, default=30),
            SkillParameter(name="focus_areas", description="重点关注领域（逗号分隔）", type="string", required=False, default=""),
        ],
        steps=[
            SkillStep(
                name="制定检索策略",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请为以下主题制定文献检索策略：
主题: ${topic}
重点关注: ${focus_areas}

请提供：
1. 检索词组合
2. 数据库选择
3. 纳入排除标准
4. 筛选流程"""
                },
                output_var="search_strategy"
            ),
            SkillStep(
                name="撰写综述框架",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请撰写文献综述的详细框架：
主题: ${topic}
检索策略: ${search_strategy}

请按以下结构：
1. 引言
2. 检索方法
3. 结果分类（按主题/时间/方法学）
4. 主要发现总结
5. 研究空白
6. 未来方向
7. 结论"""
                },
                output_var="review_outline"
            ),
            SkillStep(
                name="输出综述",
                step_type=StepType.OUTPUT,
                config={
                    "output_template": """# 文献综述框架

## 检索策略
${search_strategy}

## 综述大纲
${review_outline}

---
*请根据实际检索结果填充具体内容。*"""
                },
                output_var="output"
            ),
        ],
        tags=["research", "writing", "literature", "builtin"],
        is_builtin=True
    )


def _build_survival_analysis_skill() -> Skill:
    """生存分析 Skill"""
    return Skill(
        name="survival_analysis_workflow",
        description="生存分析统计工作流：KM曲线、Cox回归、竞争风险",
        version="1.0.0",
        parameters=[
            SkillParameter(name="data_description", description="数据描述", type="string", required=True),
            SkillParameter(name="time_variable", description="时间变量名", type="string", required=True),
            SkillParameter(name="event_variable", description="事件变量名", type="string", required=True),
            SkillParameter(name="group_variable", description="分组变量名", type="string", required=False, default=""),
            SkillParameter(name="covariates", description="协变量列表（逗号分隔）", type="string", required=False, default=""),
        ],
        steps=[
            SkillStep(
                name="分析方案设计",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请为以下生存数据设计分析方案：
数据: ${data_description}
时间变量: ${time_variable}
事件变量: ${event_variable}
分组变量: ${group_variable}
协变量: ${covariates}

请设计：
1. 描述性统计
2. KM曲线分析
3. 对数秩检验
4. Cox回归模型
5. 竞争风险分析（如适用）"""
                },
                output_var="analysis_plan"
            ),
            SkillStep(
                name="生成分析代码",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请生成R语言生存分析代码：
分析方案: ${analysis_plan}

请生成完整可运行的R代码，包括：
1. 数据导入和预处理
2. 描述性统计
3. KM曲线绘制
4. Cox回归
5. 结果输出"""
                },
                output_var="analysis_code"
            ),
            SkillStep(
                name="输出分析方案",
                step_type=StepType.OUTPUT,
                config={
                    "output_template": """# 生存分析方案

## 分析计划
${analysis_plan}

## R代码
```r
${analysis_code}
```

---
*请根据实际数据调整代码。*"""
                },
                output_var="output"
            ),
        ],
        tags=["research", "statistics", "survival", "bioinformatics", "builtin"],
        is_builtin=True
    )


def _build_response_letter_skill() -> Skill:
    """Response Letter 撰写 Skill"""
    return Skill(
        name="response_letter_writing_workflow",
        description="同行评审回复信撰写工作流",
        version="1.0.0",
        parameters=[
            SkillParameter(name="reviewer_comments", description="审稿意见文本", type="string", required=True),
            SkillParameter(name="paper_title", description="论文题目", type="string", required=True),
            SkillParameter(name="journal_name", description="期刊名称", type="string", required=False, default=""),
        ],
        steps=[
            SkillStep(
                name="分类审稿意见",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请将以下审稿意见分类整理：
论文: ${paper_title}
期刊: ${journal_name}

审稿意见:
${reviewer_comments}

请按以下分类：
1. 主要意见（Major）
2. 次要意见（Minor）
3. 方法学问题
4. 统计学问题
5. 语言问题"""
                },
                output_var="classified_comments"
            ),
            SkillStep(
                name="撰写回复",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请为以下分类意见撰写逐条回复：

分类意见:
${classified_comments}

每条回复请包括：
1. 感谢审稿人
2. 逐点回复
3. 具体修改说明
4. 修改位置标注"""
                },
                output_var="responses"
            ),
            SkillStep(
                name="输出回复信",
                step_type=StepType.OUTPUT,
                config={
                    "output_template": """# Response Letter

## 论文信息
题目: ${paper_title}
期刊: ${journal_name}

## 审稿意见分类
${classified_comments}

## 逐条回复
${responses}

---
*请根据实际修改情况调整具体内容。*"""
                },
                output_var="output"
            ),
        ],
        tags=["writing", "peer_review", "response_letter", "builtin"],
        is_builtin=True
    )


def _build_medical_note_skill() -> Skill:
    """医学文书生成 Skill"""
    return Skill(
        name="medical_note_generation_workflow",
        description="根据临床数据自动生成各类医学文书",
        version="1.0.0",
        parameters=[
            SkillParameter(name="note_type", description="文书类型", type="string", required=True, enum=["admission", "progress", "discharge", "consultation", "operative"]),
            SkillParameter(name="patient_info", description="患者基本信息（JSON格式）", type="string", required=True),
            SkillParameter(name="clinical_data", description="临床数据（JSON格式）", type="string", required=True),
        ],
        steps=[
            SkillStep(
                name="解析患者信息",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请解析以下患者信息并整理为标准格式：
${patient_info}

请输出：姓名、性别、年龄、主诉、现病史、既往史等。"""
                },
                output_var="parsed_patient"
            ),
            SkillStep(
                name="生成文书",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请生成${note_type}医学文书：

患者信息:
${parsed_patient}

临床数据:
${clinical_data}

请按照标准格式生成完整文书。"""
                },
                output_var="medical_note"
            ),
            SkillStep(
                name="输出文书",
                step_type=StepType.OUTPUT,
                config={
                    "output_template": """${medical_note}

---
*本文书由AI辅助生成，请医生审核后使用。*"""
                },
                output_var="output"
            ),
        ],
        tags=["clinical", "emr", "writing", "builtin"],
        is_builtin=True
    )


def _build_drug_safety_check_skill() -> Skill:
    """用药安全检查 Skill"""
    return Skill(
        name="drug_safety_check_workflow",
        description="多药物联合用药安全性检查工作流",
        version="1.0.0",
        parameters=[
            SkillParameter(name="medications", description="药物列表（逗号分隔）", type="string", required=True),
            SkillParameter(name="patient_age", description="患者年龄", type="number", required=True),
            SkillParameter(name="allergies", description="过敏史（逗号分隔）", type="string", required=False, default=""),
            SkillParameter(name="conditions", description="合并疾病（逗号分隔）", type="string", required=False, default=""),
        ],
        steps=[
            SkillStep(
                name="检查药物相互作用",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请检查以下药物的相互作用：
药物: ${medications}
患者年龄: ${patient_age}岁

请分析：
1. 药物-药物相互作用
2. 潜在不良反应
3. 需要监测的指标"""
                },
                output_var="ddi_check"
            ),
            SkillStep(
                name="检查禁忌症",
                step_type=StepType.LLM_CALL,
                config={
                    "prompt_template": """请检查以下用药禁忌：
药物: ${medications}
过敏史: ${allergies}
合并疾病: ${conditions}

请分析：
1. 过敏风险
2. 疾病禁忌
3. 年龄相关注意事项"""
                },
                output_var="contraindication_check"
            ),
            SkillStep(
                name="输出安全报告",
                step_type=StepType.OUTPUT,
                config={
                    "output_template": """# 用药安全检查报告

## 药物相互作用
${ddi_check}

## 禁忌症检查
${contraindication_check}

---
*本报告仅供参考，最终用药决策请遵医嘱。*"""
                },
                output_var="output"
            ),
        ],
        tags=["clinical", "medication", "safety", "builtin"],
        is_builtin=True
    )


def _build_package_installer_skill() -> Skill:
    """包安装管理 Skill"""
    return Skill(
        name="package_installer_workflow",
        description="安全安装Python包的工作流：验证包安全性、预检查依赖、执行安装、确认结果",
        version="1.0.0",
        parameters=[
            SkillParameter(name="package_name", description="要安装的包名", type="string", required=True),
            SkillParameter(name="version", description="指定版本（可选）", type="string", required=False, default=""),
            SkillParameter(name="purpose", description="安装目的说明", type="string", required=True),
        ],
        steps=[
            SkillStep(
                name="安全检查",
                step_type=StepType.TOOL_CALL,
                config={
                    "tool_name": "check_package",
                    "arguments": {"package_name": "${package_name}"}
                },
                output_var="safety_check"
            ),
            SkillStep(
                name="确认安装",
                step_type=StepType.LLM_CALL,
                description="基于安全检查结果，确认是否继续安装",
                config={
                    "prompt_template": """请审核以下包安装请求：

包名: ${package_name}
版本: ${version}
安装目的: ${purpose}

安全检查结果: ${safety_check}

请给出以下信息：
1. 安全性评估（安全/警告/危险）
2. 是否建议安装（是/否）
3. 安装后需要做的配置或验证
4. 潜在风险说明"""
                },
                output_var="install_decision"
            ),
            SkillStep(
                name="执行安装",
                step_type=StepType.TOOL_CALL,
                config={
                    "tool_name": "install_package",
                    "arguments": {
                        "package_name": "${package_name}",
                        "version": "${version}"
                    }
                },
                output_var="install_result"
            ),
            SkillStep(
                name="输出安装报告",
                step_type=StepType.OUTPUT,
                config={
                    "output_template": """# 包安装报告

## 安装请求
- 包名: ${package_name}
- 版本: ${version}
- 目的: ${purpose}

## 安全检查
${safety_check}

## 安装决策
${install_decision}

## 安装结果
${install_result}

---
*安装完成后，可能需要重启服务以使新包生效。*"""
                },
                output_var="output"
            ),
        ],
        tags=["system", "package", "install", "builtin"],
        is_builtin=True
    )


def _build_ecrf_designer_skill() -> Skill:
    """eCRF Designer Skill（移植自 ClawHub @aipoch-ai/ecrf-designer）

    设计临床试验病例报告表(CRF)，支持CDISC SDTM合规、字段验证规则和逻辑跳转。
    """
    return Skill(
        name="ecrf_designer_workflow",
        description="临床试验eCRF设计工作流：设计病例报告表、字段验证规则、逻辑跳转模式，支持CDISC SDTM合规",
        version="1.0.0",
        parameters=[
            SkillParameter(name="study_title", description="研究标题", type="string", required=True),
            SkillParameter(name="visit_schedule", description="访视时间点列表（如：筛选期、基线、第4周、第8周、随访期）", type="string", required=True),
            SkillParameter(name="data_elements", description="需要收集的数据元素列表（如：人口统计学、生命体征、实验室检查、不良事件）", type="string", required=True),
            SkillParameter(name="cdisc_domain", description="CDISC SDTM领域代码（如：DM=人口统计学, VS=生命体征, LB=实验室检查, AE=不良事件）", type="string", required=False, default=""),
            SkillParameter(name="target_population", description="目标人群描述（如：晚期非小细胞肺癌患者）", type="string", required=False, default=""),
        ],
        steps=[
            SkillStep(
                name="设计CRF整体结构",
                step_type=StepType.LLM_CALL,
                description="基于研究信息和访视计划，设计CRF的整体模块结构",
                config={
                    "prompt_template": """你是一名临床试验数据管理专家。请为以下研究设计eCRF（电子病例报告表）结构：

## 研究信息
- 研究标题：${study_title}
- 目标人群：${target_population}
- 访视时间点：${visit_schedule}
- 数据收集领域：${data_elements}
- CDISC SDTM领域：${cdisc_domain}

## 设计要求
1. 每个访视点需要收集哪些CRF页面
2. 每个页面的字段清单（字段名、标签、数据类型、是否必填）
3. 字段间的逻辑关系（如：如果"是否怀孕"=是，则显示"末次月经日期"）
4. CDISC SDTM映射（每个字段对应的标准变量名）

请输出结构化的CRF设计方案，使用表格形式。"""
                },
                output_var="crf_structure"
            ),
            SkillStep(
                name="设计字段验证规则",
                step_type=StepType.LLM_CALL,
                description="为每个字段设计数据验证规则",
                config={
                    "prompt_template": """基于以下CRF结构，为每个字段设计详细的验证规则：

${crf_structure}

## 验证规则要求
1. 范围检查（如：年龄 18-100岁，收缩压 90-200 mmHg）
2. 格式检查（如：日期格式、受试者编号格式）
3. 逻辑一致性（如：入组日期 <= 首次给药日期 <= 末次给药日期）
4. 缺失值处理规则
5. 严重异常值标记规则

请按CRF页面分组输出验证规则。"""
                },
                output_var="validation_rules"
            ),
            SkillStep(
                name="设计逻辑跳转模式",
                step_type=StepType.LLM_CALL,
                description="设计CRF页面间的逻辑跳转和条件显示",
                config={
                    "prompt_template": """基于以下CRF结构和验证规则，设计逻辑跳转模式：

## CRF结构
${crf_structure}

## 验证规则
${validation_rules}

## 逻辑跳转要求
1. 条件显示：哪些字段在特定条件下才显示
2. 页面跳转：根据回答跳转到不同页面
3. 必填/可选动态切换
4. 重复测量模块的处理（如：多次访视的同一检查）
5. 早期终止/退出流程

请以伪代码或流程图描述的形式输出。"""
                },
                output_var="skip_patterns"
            ),
            SkillStep(
                name="生成数据字典",
                step_type=StepType.LLM_CALL,
                description="生成CDISC SDTM兼容的数据字典",
                config={
                    "prompt_template": """基于以下CRF设计，生成CDISC SDTM兼容的数据字典：

## CRF结构
${crf_structure}

## 验证规则
${validation_rules}

## 逻辑跳转
${skip_patterns}

## 数据字典要求
1. 变量名（SDTM标准变量名或自定义变量名）
2. 变量标签
3. 数据类型（Char/Num/Date）
4. 长度
5. 受控术语/代码列表（如：性别：M=男, F=女）
6. 来源/派生规则
7. 注释

请以表格形式输出，按SDTM领域分组。"""
                },
                output_var="data_dictionary"
            ),
            SkillStep(
                name="汇总输出CRF规范",
                step_type=StepType.OUTPUT,
                config={
                    "output_template": """# eCRF 设计规范报告

## 研究信息
- **研究标题**：${study_title}
- **目标人群**：${target_population}
- **访视计划**：${visit_schedule}
- **数据领域**：${data_elements}
- **CDISC领域**：${cdisc_domain}

---

## 一、CRF整体结构
${crf_structure}

---

## 二、字段验证规则
${validation_rules}

---

## 三、逻辑跳转模式
${skip_patterns}

---

## 四、数据字典（CDISC SDTM兼容）
${data_dictionary}

---

*本报告由 eCRF Designer Skill 自动生成（来源：ClawHub @aipoch-ai/ecrf-designer）*
"""
                },
                output_var="output"
            ),
        ],
        tags=["clinical", "crf", "cdisc", "edc", "data-management", "builtin", "clawhub"],
        is_builtin=True
    )
