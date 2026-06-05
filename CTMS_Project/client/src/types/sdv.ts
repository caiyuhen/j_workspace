// ==================== SDV 源数据核查 ====================

export interface SdvRecord {
  id: string;
  projectId: string;
  siteId: string;
  subjectId: string;
  visitName: string;
  formName?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  craId?: string;
  completedAt?: string;
  totalItems: number;
  verifiedItems: number;
  failedItems: number;
  findings?: string;
  createdAt: string;
  updatedAt: string;
  cra?: { id: string; displayName: string };
}

export interface CreateSdvParams {
  projectId: string;
  siteId: string;
  subjectId: string;
  visitName: string;
  formName?: string;
  craId?: string;
}

export interface SdvItem {
  id: string;
  sdvRecordId: string;
  fieldName: string;
  crfValue: any;
  sourceValue: any;
  status: 'pending' | 'verified' | 'discrepancy';
  notes?: string;
  verifiedAt?: string;
  verifiedById?: string;
}

export interface SdvStatistics {
  totalRecords: number;
  completedRecords: number;
  inProgressRecords: number;
  overallRate: number;
  bySite: { siteId: string; siteName: string; total: number; verified: number; rate: number }[];
  byVisit: { visitName: string; total: number; verified: number; rate: number }[];
}
