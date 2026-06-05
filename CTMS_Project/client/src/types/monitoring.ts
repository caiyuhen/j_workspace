// ==================== 监察管理 ====================

export interface MonitoringPlan {
  id: string;
  projectId: string;
  siteId?: string;
  craId?: string;
  planName: string;
  visitType: 'SIV' | 'SMV' | 'COV' | 'PMV' | 'CLOSEOUT';
  scheduledDate: string;
  actualDate?: string;
  status: 'planned' | 'in_progress' | 'completed' | 'cancelled';
  scope?: string;
  findings?: string;
  remarks?: string;
  createdAt: string;
  updatedAt: string;
  project?: { id: string; name: string };
  site?: { id: string; name: string };
  cra?: { id: string; displayName: string };
}

export interface CreateMonitoringPlanParams {
  projectId: string;
  siteId?: string;
  craId?: string;
  planName: string;
  visitType: 'SIV' | 'SMV' | 'COV' | 'PMV' | 'CLOSEOUT';
  scheduledDate: string;
  scope?: string;
}

export interface MonitoringVisit {
  id: string;
  planId: string;
  visitDate: string;
  visitType: string;
  craId?: string;
  siteId?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  summary?: string;
  findings?: string;
  actionItems?: string;
  nextVisitDate?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateMonitoringVisitParams {
  planId: string;
  visitDate: string;
  visitType: string;
  craId?: string;
  siteId?: string;
  summary?: string;
}
