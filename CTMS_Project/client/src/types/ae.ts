// 不良事件
export type EventType = 'ae' | 'sae';
export type AESeverity = 'mild' | 'moderate' | 'severe';
export type AESSeriousness = 'non_serious' | 'serious';
export type AECausality = 'not_related' | 'unlikely' | 'possible' | 'probable' | 'definite';
export type AEOutcome = 'resolved' | 'resolving' | 'not_resolved' | 'fatal' | 'unknown';
export type AERelationship = 'unrelated' | 'unlikely_related' | 'possibly_related' | 'probably_related' | 'definitely_related';

export interface AdverseEvent {
  id: string;
  projectId: string;
  subjectId: string;
  eventType: EventType;
  termPreferred: string;
  termCode?: string;
  meddraCode?: string;
  onsetDate: string;
  endDate?: string;
  isOngoing?: boolean;
  severity: AESeverity;
  seriousness: AESSeriousness;
  seriousnessCriteria?: string[];
  causality?: AECausality;
  causalityMethod?: string;
  relationship?: AERelationship;
  description: string;
  actionTaken?: string[];
  outcome?: AEOutcome;
  status: string;
  siteId?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateAEParams {
  projectId: string;
  subjectId: string;
  eventType: EventType;
  termPreferred: string;
  termCode?: string;
  meddraCode?: string;
  onsetDate: string;
  endDate?: string;
  isOngoing?: boolean;
  severity: AESeverity;
  seriousness: AESSeriousness;
  seriousnessCriteria?: string[];
  causality?: AECausality;
  causalityMethod?: string;
  relationship?: AERelationship;
  description: string;
  actionTaken?: string[];
  outcome?: AEOutcome;
  siteId?: string;
}

export type UpdateAEParams = Partial<Omit<CreateAEParams, 'projectId' | 'subjectId' | 'eventType'>>;

// SAE 报告
export interface SaeReport {
  id: string;
  adverseEventId: string;
  reportType: 'initial' | 'follow_up' | 'final' | 'death' | 'expedited' | 'annual';
  reportVersion?: string;
  regulatoryBody?: string;
  reportDate: string;
  reportContent?: Record<string, any>;
  reviewStatus?: string;
  submissionStatus?: string;
  submittedTo?: string;
  submissionRef?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateSaeReportParams {
  reportType: SaeReport['reportType'];
  reportVersion?: string;
  regulatoryBody?: string;
  reportDate: string;
  reportContent?: Record<string, any>;
}

export interface ReviewSaeReportParams {
  reviewStatus: 'approved' | 'rejected' | 'revision_required';
  reviewComments?: string;
}

export interface SubmitSaeReportParams {
  submittedTo: string;
  submissionRef?: string;
}
