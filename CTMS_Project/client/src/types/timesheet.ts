// 工时管理
export type WorkType = 'monitoring' | 'site_management' | 'project_management' | 'data_review' | 'training' | 'meeting' | 'travel' | 'other';

export interface TimesheetEntry {
  workDate: string;
  hours: number;
  workType: WorkType;
  projectId?: string;
  siteId?: string;
  description?: string;
  isBillable?: boolean;
}

export interface Timesheet {
  id: string;
  userId: string;
  projectId?: string;
  weekStartDate: string;
  entries: TimesheetEntry[];
  status: string;
  totalHours?: number;
  createdAt: string;
  updatedAt: string;
}

export interface CreateTimesheetParams {
  userId: string;
  projectId?: string;
  weekStartDate: string;
  entries: TimesheetEntry[];
}

export interface SubmitTimesheetParams {
  comment?: string;
}

export interface ApproveTimesheetParams {
  action: 'approve' | 'reject';
  comment?: string;
}
