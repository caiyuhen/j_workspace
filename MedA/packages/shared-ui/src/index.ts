export {
  LiteratureLibraryScreen,
  type LiteratureLibraryScreenProps,
  type LiteratureLibrarySortKey,
  type LiteratureLibraryInitialFilter,
  SORT_OPTIONS,
} from "./LiteratureLibraryScreen";
export {
  SearchSourceConfigScreen,
  type SearchSourceConfigScreenProps,
} from "./SearchSourceConfigScreen";
export {
  PrismaChart,
  type PrismaChartProps,
  type PrismaSourceBreakdown,
  calculatePrismaWidths,
} from "./PrismaChart";
export {
  SearchRunListScreen,
  type SearchRunListScreenProps,
  type SearchRunStatus,
  type SearchRunListItem,
  STATUS_CHIP_STYLES,
  formatRelativeTime,
} from "./SearchRunListScreen";
export {
  SearchRunDetailScreen,
  type SearchRunDetailScreenProps,
} from "./SearchRunDetailScreen";
export {
  PicoPanel,
  type PicoPanelProps,
  type PicoFieldValues,
} from "./PicoPanel";
export {
  WorkspaceOneClickPubmedDemo,
  type WorkspaceOneClickPubmedDemoProps,
} from "./WorkspaceOneClickPubmedDemo";

export { serializeRIS } from "./export/serializeRIS";
export { serializeBibTeX } from "./export/serializeBibTeX";
export { exportPRISMA } from "./export/exportPRISMA";
export {
  downloadBlob,
  downloadDataUrl,
  downloadDiagnosticText,
} from "./export/downloadDiagnosticText";
export { sanitizeFilename } from "./export/sanitizeFilename";
export { ExportPanel, type ExportPanelProps } from "./export/ExportPanel";

// WAVE82B_INSERT_SCREENING_EXPORT
export {
  ScreeningTable,
  type ScreeningTableProps,
  type ScreeningTableRow,
  type DedupeStatus,
  SCREENING_TABLE_COL_WIDTHS,
} from "./screening/ScreeningTable";
export {
  ScreeningProgressHeader,
  type ScreeningProgressHeaderProps,
  type StatsWithPrisma as StatsWithPrismaT9,
  ScreeningToolbar,
  type ScreeningToolbarProps,
  type FilterState,
  ExcludeReasonDialog,
  type ExcludeReasonDialogProps,
  COCHRANE_PRESET_REASONS_9,
  type CochranePreset,
} from "./screening/ScreeningTrio";
// WAVE82B_T10_PAGES_EXPORT
export {
  DashboardScreeningPage,
  type DashboardScreeningPageProps,
  TAScreeningPage,
  type TAScreeningPageProps,
  FulltextScreeningPage,
  type FulltextScreeningPageProps,
  computeNavigation,
  type NavResult as T10NavResult,
  type ScreeningRouteKey,
  type ScreeningPageStats,
} from "./screening/ScreeningPagesT10";
export {
  PrismaOverrideEditor as PrismaOverrideEditorT11,
  type PrismaOverrideEditorT11Props,
} from "./screening/PrismaOverrideEditorT11";

// ---- W8.3 BLOCK ----
export { ExtractionTemplatePage } from "./extraction/ExtractionTemplatePage";
export type { ExtractionTemplatePageProps } from "./extraction/ExtractionTemplatePage";
export { SingleRecordExtractionPage } from "./extraction/SingleRecordExtractionPage";
export type { SingleRecordExtractionPageProps } from "./extraction/SingleRecordExtractionPage";
export { EvidenceTablePage } from "./extraction/EvidenceTablePage";
export type { EvidenceTablePageProps } from "./extraction/EvidenceTablePage";
export { AnalysisMetaPage } from "./analysis/AnalysisMetaPage";
export type { AnalysisMetaPageProps } from "./analysis/AnalysisMetaPage";
export { OutcomeArmInputs } from "./analysis/OutcomeArmInputs";
export type { OutcomeArmInputsProps } from "./analysis/OutcomeArmInputs";
export { ForestPlotW83 } from "./charts/ForestPlotW83";
export type { ForestPlotW83Props } from "./charts/ForestPlotW83";

// ══════════════════════════════════════════════════════════════════════════════
// WAVE 8.4 OUTPUT STAGE BARREL EXPORTS (GRADE 4 + REPORT 4)
// EOF APPEND ONLY; ABOVE W8.2B/W8.3 EXPORTS 0 bytes modified
// ══════════════════════════════════════════════════════════════════════════════
export {
  GradeDomainScorer5,
  GradeUpgradeScorer3,
  GradeAssessmentCard,
  GradeSoFTable,
} from "./grade";
export {
  ReportExportMenu3Formats,
  Prisma2020Checklist27,
  ReportSnapshotList,
  DashboardOutputCards,
} from "./report";
export { DashboardOutputsW84 } from "./dashboard/DashboardOutputsW84";
