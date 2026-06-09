<<<<<<< HEAD
<<<<<<< HEAD
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  MonitoringPlan,
  CreateMonitoringPlanParams,
  MonitoringVisit,
  CreateMonitoringVisitParams,
} from '@/types';

export const monitoringApi = {
  // 计划
  listPlans: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<MonitoringPlan>>>('/monitoring/plans', { params }).then((r) => r.data.data),

  createPlan: (data: CreateMonitoringPlanParams) =>
    api.post<ApiResponse<MonitoringPlan>>('/monitoring/plans', data).then((r) => r.data.data),

  getPlanById: (id: string) =>
    api.get<ApiResponse<MonitoringPlan>>(`/monitoring/plans/${id}`).then((r) => r.data.data),

  updatePlan: (id: string, data: Partial<CreateMonitoringPlanParams>) =>
    api.put<ApiResponse<MonitoringPlan>>(`/monitoring/plans/${id}`, data).then((r) => r.data.data),

  deletePlan: (id: string) =>
    api.delete(`/monitoring/plans/${id}`).then((r) => r.data),

  // 访视
  listVisits: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<MonitoringVisit>>>('/monitoring/visits', { params }).then((r) => r.data.data),

  createVisit: (data: CreateMonitoringVisitParams) =>
    api.post<ApiResponse<MonitoringVisit>>('/monitoring/visits', data).then((r) => r.data.data),

  getVisitById: (id: string) =>
    api.get<ApiResponse<MonitoringVisit>>(`/monitoring/visits/${id}`).then((r) => r.data.data),

  updateVisit: (id: string, data: Partial<CreateMonitoringVisitParams>) =>
    api.put<ApiResponse<MonitoringVisit>>(`/monitoring/visits/${id}`, data).then((r) => r.data.data),

  deleteVisit: (id: string) =>
    api.delete(`/monitoring/visits/${id}`).then((r) => r.data),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  MonitoringPlan,
  CreateMonitoringPlanParams,
  MonitoringVisit,
  CreateMonitoringVisitParams,
} from '@/types';

export const monitoringApi = {
  // 计划
  listPlans: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<MonitoringPlan>>>('/monitoring/plans', { params }).then((r) => r.data.data),

  createPlan: (data: CreateMonitoringPlanParams) =>
    api.post<ApiResponse<MonitoringPlan>>('/monitoring/plans', data).then((r) => r.data.data),

  getPlanById: (id: string) =>
    api.get<ApiResponse<MonitoringPlan>>(`/monitoring/plans/${id}`).then((r) => r.data.data),

  updatePlan: (id: string, data: Partial<CreateMonitoringPlanParams>) =>
    api.put<ApiResponse<MonitoringPlan>>(`/monitoring/plans/${id}`, data).then((r) => r.data.data),

  deletePlan: (id: string) =>
    api.delete(`/monitoring/plans/${id}`).then((r) => r.data),

  // 访视
  listVisits: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<MonitoringVisit>>>('/monitoring/visits', { params }).then((r) => r.data.data),

  createVisit: (data: CreateMonitoringVisitParams) =>
    api.post<ApiResponse<MonitoringVisit>>('/monitoring/visits', data).then((r) => r.data.data),

  getVisitById: (id: string) =>
    api.get<ApiResponse<MonitoringVisit>>(`/monitoring/visits/${id}`).then((r) => r.data.data),

  updateVisit: (id: string, data: Partial<CreateMonitoringVisitParams>) =>
    api.put<ApiResponse<MonitoringVisit>>(`/monitoring/visits/${id}`, data).then((r) => r.data.data),

  deleteVisit: (id: string) =>
    api.delete(`/monitoring/visits/${id}`).then((r) => r.data),
};
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
