// 项目管理
export type StudyType = 'interventional' | 'observational' | 'post_marketing';
export type BlindType = 'open' | 'single_blind' | 'double_blind' | 'triple_blind';
export type ProjectPhase = 'phase_i' | 'phase_ii' | 'phase_iii' | 'phase_iv' | 'ind_enabling' | 'other';
export type ProjectStatus = 'planning' | 'recruiting' | 'active' | 'paused' | 'completed' | 'terminated';

export interface Project {
  id: string;
  projectCode: string;
  projectName: string;
  studyType?: StudyType;
  therapeuticArea?: string;
  blindType?: BlindType;
  phase?: ProjectPhase;
  sampleSize?: number;
  totalBudget?: number;
  startDate?: string;
  endDate?: string;
  description?: string;
  status?: ProjectStatus;
  sponsorOrgId?: string;
  croOrgId?: string;
  sites?: any[];
  createdAt: string;
  updatedAt: string;
}

export interface CreateProjectParams {
  projectCode: string;
  projectName: string;
  studyType?: StudyType;
  therapeuticArea?: string;
  blindType?: BlindType;
  phase?: ProjectPhase;
  sampleSize?: number;
  totalBudget?: number;
  startDate?: string;
  endDate?: string;
  description?: string;
  sponsorOrgId?: string;
  croOrgId?: string;
  sites?: {
    siteCode: string;
    siteName: string;
    plannedSampleSize?: number;
  }[];
}

export type UpdateProjectParams = Partial<CreateProjectParams> & {
  status?: ProjectStatus;
};

// 里程碑
export type MilestoneType = 'project_start' | 'site_init' | 'first_patient' | 'last_patient' | 'db_lock' | 'study_close' | 'other';
export type MilestoneStatus = 'planned' | 'in_progress' | 'completed' | 'overdue' | 'cancelled';

export interface Milestone {
  id: string;
  projectId: string;
  milestoneName: string;
  milestoneType: MilestoneType;
  plannedDate: string;
  actualDate?: string;
  status?: MilestoneStatus;
  description?: string;
}

export interface CreateMilestoneParams {
  milestoneName: string;
  milestoneType: MilestoneType;
  plannedDate: string;
  description?: string;
}
