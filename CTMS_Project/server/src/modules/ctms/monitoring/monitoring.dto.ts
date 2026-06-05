// monitoring.dto.ts - 监察管理数据传输对象

export interface CreateMonitoringPlanDto {
  projectId: string;
  planName: string;
  frequency?: string;
  description?: string;
  status?: string;
}

export interface UpdateMonitoringPlanDto {
  planName?: string;
  frequency?: string;
  description?: string;
  status?: string;
}

export interface CreateMonitoringVisitDto {
  planId?: string;
  projectId: string;
  siteId?: string;
  craUserId: string;
  visitType: string;
  plannedDate: string; // ISO date string
  actualDate?: string;
  status?: string;
  sdvPercentage?: number;
  reportId?: string;
}

export interface UpdateMonitoringVisitDto {
  planId?: string;
  siteId?: string;
  craUserId?: string;
  visitType?: string;
  plannedDate?: string;
  actualDate?: string;
  status?: string;
  sdvPercentage?: number;
  reportId?: string;
}

export interface MonitoringQueryDto {
  projectId?: string;
  siteId?: string;
  craUserId?: string;
  status?: string;
  visitType?: string;
  page?: number;
  pageSize?: number;
}
