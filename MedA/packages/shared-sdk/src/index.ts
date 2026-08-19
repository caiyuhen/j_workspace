export { createBrowserSessionStore, createMemorySessionStore, createClient, ApiError } from "./client";
export type {
  ProjectSummary,
  WorkspaceHeroAction,
  WorkspaceStageSummary,
  WorkspaceItemSummary,
  StageEntryAction,
  StageEntryCardSummary,
  StageEntryGuidanceNote,
  WorkspaceAssistantSummary,
  WorkspaceProjectSummary,
  WorkspaceHomeSummary,
  StageEntrySummary,
  SessionContext,
  CreateProjectRequest,
  ProjectResponse,
  SearchTermSummary,
  SearchTermGroupSummary,
  SearchExpressionBlock,
  SearchValidationMessage,
  SearchPreviewSummary,
  SearchQueryEditorSummary,
  SaveSearchQueryDraftPayload,
  DeriveSearchQueryDraftPayload,
  SourceCatalogItem,
  CatalogOption,
  SearchSourceCatalog,
  AvailableSource,
  SourceImpactSummary,
  SearchSourceConfigSummary,
  SaveSearchSourceConfigPayload,
  LiteratureRecordSummary,
  LiteratureSourceCount,
  LiteratureStats,
  LiteratureBatchSummary,
  ImportResultSummary,
  LiteratureLibrarySummary,
  ImportLiteraturePayload,
  CreateLiteratureRecordPayload,
  DevLoginPayload,
  SearchRunStatus,
  SearchRunSourceStatus,
  PicoStatus,
  LibrarySortKey,
  SearchSourceBreakdown,
  PrismaReport,
  SearchRunSummary,
  SearchRunSourceSummary,
  SearchRunDetail,
  SearchRunCreatePayload,
  SearchRunStatusPoll,
  LiteraturePicoResponse,
  BatchPicoPayload,
  BatchPicoResult,
  PicoAutofillDraft,
  ScreeningStage,
  ScreeningDecision,
  ExcludeReasonJson,
  PrismaOverride,
  LiteratureStatsW82B,
} from "./client";

export function getSearchRunCsvUrl(baseUrl: string, projectId: number, runId: number): string {
  return `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs/${runId}/export.csv`;
}

import type {
  WorkspaceProjectSummary as _WPS,
  SearchRunSummary as _SRS,
  SearchRunStatus as _SRS_STATUS,
} from "./client";
export type SearchRunListResponse = {
  project: _WPS;
  stage_key: string;
  items: _SRS[];
  runs: _SRS[];
  total: number;
  page: number;
  page_size: number;
  pageSize: number;
};

export type SearchRunListItem = {
  id: number;
  status: _SRS_STATUS;
  created_at: string;
  sources: Array<{
    key: string;
    retrieved: number;
    imported: number;
  }>;
  prisma: {
    identification: number;
    screening: number;
  };
  progress_percent: number | null;
};

export {
  DEMO_PRESETS,
  DEMO_PRESET_BY_KEY,
  type DemoPreset,
  type DemoPresetKey,
} from "./presets";
export {
  build_grouped_terms_from_pico,
  build_expression_from_boolean_text,
  ensureDemoProjectAndQuery,
  type EnsureDemoResult,
  type EnsureDemoOptions,
  type MedaClient,
} from "./utils/demoSeedings";

// ============================================================
// WAVE 8.3 T7 BLOCK: extraction + analysis 类型导出
// 15 symbols (12 核心 + 3 辅助)
// ============================================================

export type PicoBindingW83 =
  | "P"
  | "I"
  | "C"
  | "O"
  | "S"
  | "StudyType"
  | "OutcomeMeasure"
  | "Other";

export type ExtractionFieldType =
  | "text"
  | "textarea"
  | "select"
  | "multiselect"
  | "number"
  | "boolean"
  | "date";

export interface ExtractionTemplateField {
  key: string;
  label: string;
  pico_binding: PicoBindingW83;
  required: boolean;
  field_type?: ExtractionFieldType;
  options?: string[];
  description?: string;
}

export interface ExtractionTemplate {
  template_id: number;
  name: string;
  description?: string;
  fields_json: ExtractionTemplateField[];
  created_at: string;
  updated_at?: string;
}

export interface ExtractionCell {
  cell_id: number;
  record_id: number;
  field_key: string;
  value_raw: string | null;
  value_number: number | null;
  value_boolean: boolean | null;
  extracted_by: "human" | "ai" | "import";
  extracted_at: string | null;
  confidence: number | null;
}

export type OutcomeDefinitionMeasure = "RR" | "OR" | "RD" | "MD" | "SMD";

export interface OutcomeDefinition {
  outcome_id: number;
  name: string;
  description?: string;
  measure: OutcomeDefinitionMeasure;
  time_point?: string;
  direction_higher_is_better?: boolean;
}

export interface BinaryArmInputs {
  arm_label: string;
  events: number | null;
  total: number | null;
}

export interface ContinuousArmInputs {
  arm_label: string;
  mean: number | null;
  sd: number | null;
  n: number | null;
}

export type OutcomeArmAnyInputs = BinaryArmInputs | ContinuousArmInputs;

export interface OutcomeArmData {
  outcome_id: number;
  record_id: number;
  arms: OutcomeArmAnyInputs[];
  measure: OutcomeDefinitionMeasure;
  study_weight?: number | null;
}

export interface PooledHeterogeneity {
  i_squared: number | null;
  tau_squared: number | null;
  q_statistic: number | null;
  q_p_value: number | null;
  df: number | null;
}

export interface AnalysisRun {
  analysis_id: number;
  outcome_id: number;
  model: "fixed_effect" | "random_effect";
  method: "Mantel-Haenszel" | "Paule-Mandel" | "DerSimonian-Laird" | "Inverse-Variance";
  measure: OutcomeDefinitionMeasure;
  n_studies: number;
  pooled_estimate: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  p_value: number | null;
  heterogeneity: PooledHeterogeneity;
  status: "pending" | "running" | "completed" | "failed";
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
}

export interface MetaRunRequest {
  outcome_id: number;
  measure: OutcomeDefinitionMeasure;
  model: "fixed_effect" | "random_effect";
  method?:
    | "Mantel-Haenszel"
    | "Paule-Mandel"
    | "DerSimonian-Laird"
    | "Inverse-Variance";
  include_record_ids?: number[];
  exclude_record_ids?: number[];
  subgroup_key?: string;
}

export interface EvidenceTableWideRow {
  record_id: number;
  study_name: string;
  year: number | null;
  authors: string | null;
  population: string | null;
  intervention: string | null;
  comparison: string | null;
  outcome: string | null;
  study_type: string | null;
  outcome_measure: string | null;
  effect_estimate: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  n_total: number | null;
  risk_of_bias: string | null;
  kappa_status: "ok" | "low_agreement" | "unassessed";
}

export type KappaWarningLevel = "low_agreement" | "ok";

export interface KappaFieldSummary {
  field_key: string;
  kappa: number | null;
  n_pairs: number;
  pct_agree?: number | null;
  warning_level: KappaWarningLevel;
  flagged_cells?: number[];
}

// ─────────────────────────────────────────────────────────────────────
// WAVE 8.4 OUTPUT STAGE (GRADE + PRISMA2020 REPORT) 12 TYPE EXPORTS
// (append only; W82B + W83 blocks MUST NOT be modified)
// ─────────────────────────────────────────────────────────────────────
export type GradeDomainLevel =
  | "no_concerns"
  | "some_concerns"
  | "major_concerns";

export type GradeCertaintyFinal =
  | "High"
  | "Moderate"
  | "Low"
  | "VeryLow";

export type ReportFormat =
  | "md"
  | "html"
  | "txt";

export type Prisma2020ItemIndex = 1|2|3|4|5|6|7|8|9|10
  |11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27;

export type Grade5Domains = {
  risk_of_bias: GradeDomainLevel;
  indirectness: GradeDomainLevel;
  inconsistency: GradeDomainLevel;
  imprecision: GradeDomainLevel;
  publication_bias: GradeDomainLevel;
};

export type Grade3Upgrades = {
  large_effect: boolean;
  dose_response: boolean;
  confounders_reduce: boolean;
};

export type GradeAssessment<IdT = number> = {
  id: IdT;
  project_id: IdT;
  outcome_id: IdT;
  reviewer_id: IdT;
  domains_5: Grade5Domains;
  upgrades_3: Grade3Upgrades;
  certainty_final: GradeCertaintyFinal;
  note?: string;
  locked: boolean;
  created_at: string;
};

export type SofRow<IdT = number> = {
  id?: IdT;
  project_id: IdT;
  outcome_id: IdT;
  outcome_label: string;
  participants_n: number;
  studies_k: number;
  effect_measure_label: string;
  risk_of_bias: GradeDomainLevel;
  indirectness: GradeDomainLevel;
  inconsistency: GradeDomainLevel;
  imprecision: GradeDomainLevel;
  publication_bias: GradeDomainLevel;
  certainty: GradeCertaintyFinal;
  absolute_risk_intervention?: string;
  absolute_risk_control?: string;
  comments?: string;
};

export type ReportSnapshot<IdT = number> = {
  id: IdT;
  project_id: IdT;
  sha256_grade: string;
  sha256_analysis: string;
  version_label: string;
  md_content: string;
  html_content: string;
  txt_content: string;
  created_at: string;
};

export type Prisma2020Checklist<IdT = number> = {
  id: IdT;
  project_id: IdT;
  reviewer_id: IdT;
  item_1: boolean;
  item_2: boolean;
  item_3: boolean;
  item_4: boolean;
  item_5: boolean;
  item_6: boolean;
  item_7: boolean;
  item_8: boolean;
  item_9: boolean;
  item_10: boolean;
  item_11: boolean;
  item_12: boolean;
  item_13: boolean;
  item_14: boolean;
  item_15: boolean;
  item_16: boolean;
  item_17: boolean;
  item_18: boolean;
  item_19: boolean;
  item_20: boolean;
  item_21: boolean;
  item_22: boolean;
  item_23: boolean;
  item_24: boolean;
  item_25: boolean;
  item_26: boolean;
  item_27: boolean;
  note?: string;
  locked: boolean;
  created_at: string;
};

export type OutputStageCardKey =
  | "protocol_report_draft"
  | "sof_attachments_ready"
  | "export_version_snapshots_ready";

export type OutputStageCard = {
  card_key: OutputStageCardKey;
  ready: boolean;
  locked_reason:
    | "protocol_requires_grade_and_prisma_5_items"
    | "attachments_requires_sof_row_and_forest_3_studies"
    | "exports_requires_at_least_one_report_snapshot"
    | null;
};

// ─────────────────────────────────────────────────────────────────────
// WAVE 8.4 CLOSURE · Report8ChaptersDraft + ReportGeneratePayload
// (append only；绝不修改上方任何已有类型定义或字段)
// ─────────────────────────────────────────────────────────────────────
export type Report8ChaptersDraft<IdT = number> = {
  ch1_background: string;
  ch2_methods: string;
  ch3_pico: string;
  ch4_results: string;
  ch5_grade_assessment: string;
  ch6_summary_of_findings: string;
  ch7_discussion: string;
  ch8_appendices: string;
  source_snapshot_id?: IdT | null;
};

export type ReportGeneratePayload<IdT = number> = {
  version_label?: string;
  override_ch1_background?: string;
  override_ch2_methods?: string;
  override_ch3_pico?: string;
  override_ch4_results?: string;
  override_ch5_grade_assessment?: string;
  override_ch6_summary_of_findings?: string;
  override_ch7_discussion?: string;
  override_ch8_appendices?: string;
};

// ─────────────────────────────────────────────────────────────────────
// WAVE 9 · Evidence Artifact 共享引擎 + 三模块 (9a/9b/9c) 12 TYPE EXPORTS
// (append only；绝不修改上方任何已有类型定义或字段)
// ─────────────────────────────────────────────────────────────────────

export type EvidenceStage =
  | 'screening_ta' | 'screening_fulltext'
  | 'quality_ro'   | 'quality_nrsi'
  | 'data_abstractor';

export type EvidenceDecision = 'include' | 'exclude' | 'review';

export interface EvidenceArtifact {
  id: string;
  literature_record_id: string;
  stage: EvidenceStage;
  decision: EvidenceDecision;
  confidence?: number;
  exclude_reason_ids?: number[];
  meta_json?: Record<string, unknown>;
  created_by?: string;
  override_by_user_id?: string;
  created_at: string;
}

export type ExcludeReasonId = 2|3|4|5|6|7|8|9;

export interface FunnelStepStat {
  key: 'N1'|'N2'|'N3'|'N4'|'E1'|'E2'|'E3'|'E4'|'E5'|'E6';
  label: string;
  count: number;
  locked: boolean;
}

export type TrafficLightRating = 'low' | 'some_concerns' | 'high' | 'critical' | 'ni';

export interface RoB2DomainRating {
  domain: 'D1_randomization'|'D2_deviations'|'D3_missing'|'D4_measurement'|'D5_reporting';
  rating: TrafficLightRating;
  signal_answers: Record<string, 'Y'|'N'|'NA'>;
  rationale: string;
}

export interface RoB2Overall {
  study_id: string;
  study_type: 'RCT' | 'NRSI';
  domains: RoB2DomainRating[];
  overall: TrafficLightRating;
}

export type RobinsIDomain =
  | 'D1_confounding'|'D2_selection'|'D3_classification'
  | 'D4_deviations' |'D5_missing'  |'D6_measurement'|'D7_reporting';

export type TriageDecision = 'include' | 'exclude' | 'review';

export interface StructuredPICO {
  p: { text: string; n?: number; condition?: string; age_min?:number; age_max?:number };
  i: { drug?: string; dose?: string; duration?: string; n?: number };
  c: { comparator: string; type?: 'active'|'placebo'|'other' };
  o: Array<{ name: string; mean_diff?: number; rr?: number; ci_low?:number; ci_high?:number; p_value?: number }>;
}

export interface TriageResult {
  record_id: string;
  pico?: StructuredPICO;
  decision: TriageDecision;
  confidence: number;
  reasons: string[];
  exclude_reason_ids?: ExcludeReasonId[];
  failed_steps?: string[];
}
