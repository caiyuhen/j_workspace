from sqlmodel import Session, select, func

from app.models import (
    AnalysisRun,
    ArtifactRecord,
    ExtractionCell,
    ExtractionTemplate,
    LiteratureRecord,
    OutcomeDefinition,
    ResearchProject,
    ResearchTaskRecord,
)
from app.schemas import (
    StageEntryAction,
    StageEntryCardSummary,
    StageEntryGuidanceNote,
    StageEntryResponse,
    WorkspaceItemSummary,
    WorkspaceProjectSummary,
)

ARTIFACT_STAGE_MAP = {
    "protocol": "topic",
    "search_strategy": "search",
    "screening_log": "screening",
    "extraction_sheet": "extraction",
    "analysis_output": "analysis",
    "report": "output",
}

STAGE_ENTRY_CONFIG = {
    "topic": {
        "label": "选题",
        "status": "done",
        "goal": "明确研究问题与研究边界",
        "primary_action": StageEntryAction(
            label="进入研究问题定义",
            target="/workspace/stage/topic/problem-definition",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="problem-definition",
                title="研究问题定义",
                description="明确研究对象、暴露和结局边界",
                status="ready",
                target="/workspace/stage/topic/problem-definition",
            ),
            StageEntryCardSummary(
                key="pico",
                title="PICO 结构",
                description="梳理人群、干预、对照与结局",
                status="ready",
                target="/workspace/stage/topic/pico",
            ),
            StageEntryCardSummary(
                key="design-draft",
                title="研究设计草案",
                description="沉淀方案草稿和关键设计约束",
                status="ready",
                target="/workspace/stage/topic/design-draft",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="先明确研究终点定义",
                subtitle="优先统一研究对象、终点与比较关系",
                target="/workspace/stage/topic/problem-definition",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要明确研究场景、研究对象和核心终点。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成研究问题草案、PICO 结构和设计草案。",
            ),
        ],
    },
    "search": {
        "label": "检索",
        "status": "done",
        "goal": "完成检索式与来源配置",
        "primary_action": StageEntryAction(
            label="进入检索式管理",
            target="/workspace/stage/search/query-builder",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="query-builder",
                title="检索式管理",
                description="维护主题词、自由词和组合策略",
                status="ready",
                target="/workspace/stage/search/query-builder",
            ),
            StageEntryCardSummary(
                key="sources",
                title="数据库来源",
                description="配置 PubMed、Embase 等来源",
                status="ready",
                target="/workspace/stage/search/sources",
            ),
            StageEntryCardSummary(
                key="literature",
                title="文献条目库",
                description="导入与去重项目文献集合",
                status="ready",
                target="/workspace/stage/search/literature",
            ),
            StageEntryCardSummary(
                key="search-log",
                title="检索记录",
                description="查看已执行检索和时间线",
                status="ready",
                target="/workspace/stage/search/search-log",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="补全数据库来源",
                subtitle="优先确认核心医学数据库清单",
                target="/workspace/stage/search/sources",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要主题词、自由词与数据库范围。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成检索式与检索记录。",
            ),
        ],
    },
    "screening": {
        "label": "筛选",
        "status": "in_progress",
        "goal": "完成文献纳入排除判断",
        "primary_action": StageEntryAction(
            label="进入标题摘要筛选",
            target="/workspace/stage/screening/title-abstract",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="title-abstract",
                title="标题摘要筛选",
                description="先完成标题摘要轮的纳入排除判断",
                status="ready",
                target="/workspace/stage/screening/title-abstract",
            ),
            StageEntryCardSummary(
                key="full-text",
                title="全文筛选",
                description="进入全文核查与纳入排除判断",
                status="ready",
                target="/workspace/stage/screening/full-text",
            ),
            StageEntryCardSummary(
                key="prisma",
                title="PRISMA 流程图承接",
                description="同步筛选结果和流程图状态",
                status="ready",
                target="/workspace/stage/screening/prisma",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="先完成标题摘要筛选",
                subtitle="保证排除理由结构化记录",
                target="/workspace/stage/screening/title-abstract",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要纳入排除标准和待筛文献集合。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成筛选结果、排除原因和流程图承接。",
            ),
        ],
    },
    "extraction": {
        "label": "抽取",
        "status": "pending",
        "goal": "把非结构化内容转成结构化证据",
        "primary_action": StageEntryAction(
            label="进入抽取字段模板",
            target="/workspace/stage/extraction/template",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="template",
                title="抽取字段模板",
                description="定义抽取字段、口径和结构",
                status="ready",
                target="/workspace/stage/extraction/template",
            ),
            StageEntryCardSummary(
                key="dual-review",
                title="双人抽取",
                description="进入双人抽取和差异处理承接页",
                status="ready",
                target="/workspace/stage/extraction/dual-review",
            ),
            StageEntryCardSummary(
                key="evidence-table",
                title="证据表",
                description="查看结构化抽取结果和证据字段",
                status="ready",
                target="/workspace/stage/extraction/evidence-table",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="先确认抽取字段模板",
                subtitle="减少后续双人抽取差异",
                target="/workspace/stage/extraction/template",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要抽取字段定义和文献全文内容。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成抽取模板和结构化证据表。",
            ),
        ],
    },
    "analysis": {
        "label": "分析",
        "status": "pending",
        "goal": "组织变量、方法和结果表达",
        "primary_action": StageEntryAction(
            label="进入分析变量",
            target="/workspace/stage/analysis/variables",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="variables",
                title="分析变量",
                description="整理变量定义、分组和统计口径",
                status="ready",
                target="/workspace/stage/analysis/variables",
            ),
            StageEntryCardSummary(
                key="results",
                title="结果摘要",
                description="查看分析结果与结论摘要",
                status="ready",
                target="/workspace/stage/analysis/results",
            ),
            StageEntryCardSummary(
                key="charts",
                title="图表产出",
                description="承接核心图表与结果展示",
                status="ready",
                target="/workspace/stage/analysis/charts",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="先整理分析变量",
                subtitle="先统一变量口径再进入结果表达",
                target="/workspace/stage/analysis/variables",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要变量定义、分析方法和可追溯证据数据。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成分析变量表、结果摘要和图表承接。",
            ),
        ],
    },
    "output": {
        "label": "产出",
        "status": "pending",
        "goal": "形成最终交付产物",
        "primary_action": StageEntryAction(
            label="进入方案文档",
            target="/workspace/stage/output/protocol",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="protocol",
                title="方案文档",
                description="进入方案、报告和主文档承接入口",
                status="ready",
                target="/workspace/stage/output/protocol",
            ),
            StageEntryCardSummary(
                key="attachments",
                title="图表附件",
                description="承接图表、附表和补充材料",
                status="ready",
                target="/workspace/stage/output/attachments",
            ),
            StageEntryCardSummary(
                key="exports",
                title="导出与版本",
                description="查看导出记录和版本快照",
                status="ready",
                target="/workspace/stage/output/exports",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="先整理最终输出结构",
                subtitle="确认主文档与附件列表后再导出",
                target="/workspace/stage/output/protocol",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要上游阶段确认后的分析结果和草稿内容。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成主文档入口、附件承接和导出版本入口。",
            ),
        ],
    },
}


def build_stage_entry(
    session: Session, project: ResearchProject, stage_key: str
) -> StageEntryResponse | None:
    config = STAGE_ENTRY_CONFIG.get(stage_key)
    if config is None:
        return None

    project_id = project.id or 0
    tasks = session.exec(
        select(ResearchTaskRecord).where(
            ResearchTaskRecord.project_id == project_id,
            ResearchTaskRecord.stage_key == stage_key,
        )
    ).all()
    artifacts = session.exec(
        select(ArtifactRecord).where(ArtifactRecord.project_id == project_id)
    ).all()

    recent_tasks = [
        WorkspaceItemSummary(
            title=task.title,
            subtitle="进入该阶段任务承接页",
            target=f"/workspace/stage/{stage_key}/tasks",
        )
        for task in tasks[:2]
    ]
    if not recent_tasks:
        recent_tasks = [
            WorkspaceItemSummary(
                title=f"继续推进{config['label']}阶段任务",
                subtitle="进入该阶段任务承接页",
                target=f"/workspace/stage/{stage_key}/tasks",
            )
        ]

    recent_artifacts = [
        WorkspaceItemSummary(
            title=artifact.title,
            subtitle="进入该阶段产物承接页",
            target=f"/workspace/stage/{stage_key}/artifacts",
        )
        for artifact in artifacts
        if ARTIFACT_STAGE_MAP.get(artifact.artifact_type) == stage_key
    ][:2]
    if not recent_artifacts:
        recent_artifacts = [
            WorkspaceItemSummary(
                title=f"{config['label']}阶段产物承接",
                subtitle="进入该阶段产物承接页",
                target=f"/workspace/stage/{stage_key}/artifacts",
            )
        ]

    primary_action = config["primary_action"]
    entry_cards = config["entry_cards"]

    if stage_key == "search":
        primary_action = primary_action.model_copy(
            update={"target": f"/workspace/projects/{project_id}/stages/search/query-builder"}
        )
        project_deep_page_keys = {"query-builder", "sources", "literature"}
        entry_cards = [
            card.model_copy(
                update={
                    "target": (
                        f"/workspace/projects/{project_id}/stages/search/{card.key}"
                        if card.key in project_deep_page_keys
                        else card.target
                    )
                }
            )
            for card in config["entry_cards"]
        ]

    if stage_key == "screening":
        from app.services.screening_engine import compute_prisma_counts
        import dataclasses
        p_counts = compute_prisma_counts(session, project_id)
        p_base = dataclasses.asdict(p_counts)
        ta_included_q = select(func.count(LiteratureRecord.id)).where(
            LiteratureRecord.project_id == project_id,
            LiteratureRecord.screening_stage == "ta",
            LiteratureRecord.screening_decision == "include",
        )
        ta_included = int(session.exec(ta_included_q).one())
        fulltext_included = int(p_base.get("included") or 0)
        p_dict = {
            "identification": int(p_base.get("identification") or 0),
            "screening": int(p_base.get("screening") or 0),
            "eligibility": int(p_base.get("eligibility") or 0),
            "ta_included": ta_included,
            "ta_excluded": int(p_base.get("ta_excluded") or 0),
            "fulltext_included": fulltext_included,
            "fulltext_excluded": int(p_base.get("fulltext_excluded") or 0),
            "duplicate_excluded": int(p_base.get("duplicate_excluded") or 0),
            "included": fulltext_included,
            "manual_override_applied": bool(p_base.get("override_applied") or False),
            "diff_percent": p_base.get("diff_percent"),
        }
        locked_cards_keys = set()
        if ta_included <= 0:
            locked_cards_keys.add("full-text")
        entry_cards = [
            card.model_copy(update={"status": "locked"})
            if card.key in locked_cards_keys else card
            for card in entry_cards
        ]
    else:
        p_dict = None

    extraction_stage_cards = None
    if stage_key == "extraction":
        tpl_q = select(ExtractionTemplate).where(ExtractionTemplate.project_id == project_id)
        tpl = session.exec(tpl_q).first()

        fields_count = len(tpl.fields_json) if tpl and tpl.fields_json else 0
        template_locked = (
            tpl is None or (tpl.locked is False and fields_count < 3)
        )
        template_status = "locked" if template_locked else "ready"

        n4_q = select(func.count(LiteratureRecord.id)).where(
            LiteratureRecord.project_id == project_id,
            LiteratureRecord.screening_stage == "fulltext",
            LiteratureRecord.screening_decision == "include",
        )
        n4 = int(session.exec(n4_q).one())

        cells_q = select(func.count()).select_from(ExtractionCell).where(
            ExtractionCell.project_id == project_id,
        )
        total_cells = int(session.exec(cells_q).one())

        evidence_locked = total_cells < (n4 * 1)
        evidence_status = "locked" if evidence_locked else "ready"

        extraction_stage_cards = [
            {
                "key": "template",
                "title": "抽取字段模板",
                "description": "定义抽取字段、口径和结构",
                "status": template_status,
                "target": "/workspace/stage/extraction/template",
            },
            {
                "key": "dual-review",
                "title": "双人抽取",
                "description": "进入双人抽取和差异处理承接页",
                "status": "locked",
                "target": "/workspace/stage/extraction/dual-review",
            },
            {
                "key": "evidence-table",
                "title": "证据表",
                "description": "查看结构化抽取结果和证据字段",
                "status": evidence_status,
                "target": "/workspace/stage/extraction/evidence-table",
            },
        ]

    analysis_stage_cards = None
    if stage_key == "analysis":
        outcome_q = select(func.count(OutcomeDefinition.id)).where(
            OutcomeDefinition.project_id == project_id,
        )
        outcome_count = int(session.exec(outcome_q).one())

        ar_q = select(func.count(AnalysisRun.id)).where(
            AnalysisRun.project_id == project_id,
        )
        analysisrun_count = int(session.exec(ar_q).one())

        variables_status = "locked" if outcome_count < 1 else "ready"
        results_charts_status = "locked" if analysisrun_count == 0 else "ready"

        analysis_stage_cards = [
            {
                "key": "variables",
                "title": "分析变量",
                "description": "整理变量定义、分组和统计口径",
                "status": variables_status,
                "target": "/workspace/stage/analysis/variables",
            },
            {
                "key": "results",
                "title": "结果摘要",
                "description": "查看分析结果与结论摘要",
                "status": results_charts_status,
                "target": "/workspace/stage/analysis/results",
            },
            {
                "key": "charts",
                "title": "图表产出",
                "description": "承接核心图表与结果展示",
                "status": results_charts_status,
                "target": "/workspace/stage/analysis/charts",
            },
        ]

    return StageEntryResponse(
        project=WorkspaceProjectSummary(
            id=project_id,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage=config["label"],
            updated_at_label="刚刚更新",
        ),
        stage_key=stage_key,
        stage_label=config["label"],
        stage_status=config["status"],
        stage_goal=config["goal"],
        primary_action=primary_action,
        entry_cards=entry_cards,
        recent_tasks=recent_tasks,
        recent_artifacts=recent_artifacts,
        assistant_suggestions=config["assistant_suggestions"],
        prisma_counts=p_dict,
        guidance_notes=config["guidance_notes"],
        extraction_stage_cards=extraction_stage_cards,
        analysis_stage_cards=analysis_stage_cards,
    )
