<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
import api from '@/api';
import type {
  AdverseEvent, CreateAEParams, UpdateAEParams,
  SaeReport, CreateSaeReportParams, ReviewSaeReportParams, SubmitSaeReportParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const aeApi = {
  list: (params?: FilterParams & { page?: number; pageSize?: number; projectId?: string; eventType?: string; severity?: string }) =>
    api.get<ApiResponse<PaginatedResponse<AdverseEvent>>>('/edc/ae', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<AdverseEvent>>(`/edc/ae/${id}`).then((r) => r.data.data),

  create: (data: CreateAEParams) =>
    api.post<ApiResponse<AdverseEvent>>('/edc/ae', data).then((r) => r.data.data),

  update: (id: string, data: UpdateAEParams) =>
    api.put<ApiResponse<AdverseEvent>>(`/edc/ae/${id}`, data).then((r) => r.data.data),

  close: (id: string) =>
    api.post(`/edc/ae/${id}/close`).then((r) => r.data.data),

  statistics: (params?: { projectId?: string }) =>
    api.get('/edc/ae/statistics', { params }).then((r) => r.data.data),

  // SAE 报告
  getReports: (aeId: string) =>
    api.get<ApiResponse<SaeReport[]>>(`/edc/ae/${aeId}/reports`).then((r) => r.data.data),

  createReport: (aeId: string, data: CreateSaeReportParams) =>
    api.post<ApiResponse<SaeReport>>(`/edc/ae/${aeId}/reports`, data).then((r) => r.data.data),

  updateReport: (aeId: string, reportId: string, data: Partial<CreateSaeReportParams>) =>
    api.put<ApiResponse<SaeReport>>(`/edc/ae/${aeId}/reports/${reportId}`, data).then((r) => r.data.data),

  reviewReport: (aeId: string, reportId: string, data: ReviewSaeReportParams) =>
    api.post(`/edc/ae/${aeId}/reports/${reportId}/review`, data).then((r) => r.data.data),

  submitReport: (aeId: string, reportId: string, data: SubmitSaeReportParams) =>
    api.post(`/edc/ae/${aeId}/reports/${reportId}/submit`, data).then((r) => r.data.data),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
import api from '@/api';
import type {
  AdverseEvent, CreateAEParams, UpdateAEParams,
  SaeReport, CreateSaeReportParams, ReviewSaeReportParams, SubmitSaeReportParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const aeApi = {
  list: (params?: FilterParams & { page?: number; pageSize?: number; projectId?: string; eventType?: string; severity?: string }) =>
    api.get<ApiResponse<PaginatedResponse<AdverseEvent>>>('/edc/ae', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<AdverseEvent>>(`/edc/ae/${id}`).then((r) => r.data.data),

  create: (data: CreateAEParams) =>
    api.post<ApiResponse<AdverseEvent>>('/edc/ae', data).then((r) => r.data.data),

  update: (id: string, data: UpdateAEParams) =>
    api.put<ApiResponse<AdverseEvent>>(`/edc/ae/${id}`, data).then((r) => r.data.data),

  close: (id: string) =>
    api.post(`/edc/ae/${id}/close`).then((r) => r.data.data),

  statistics: (params?: { projectId?: string }) =>
    api.get('/edc/ae/statistics', { params }).then((r) => r.data.data),

  // SAE 报告
  getReports: (aeId: string) =>
    api.get<ApiResponse<SaeReport[]>>(`/edc/ae/${aeId}/reports`).then((r) => r.data.data),

  createReport: (aeId: string, data: CreateSaeReportParams) =>
    api.post<ApiResponse<SaeReport>>(`/edc/ae/${aeId}/reports`, data).then((r) => r.data.data),

  updateReport: (aeId: string, reportId: string, data: Partial<CreateSaeReportParams>) =>
    api.put<ApiResponse<SaeReport>>(`/edc/ae/${aeId}/reports/${reportId}`, data).then((r) => r.data.data),

  reviewReport: (aeId: string, reportId: string, data: ReviewSaeReportParams) =>
    api.post(`/edc/ae/${aeId}/reports/${reportId}/review`, data).then((r) => r.data.data),

  submitReport: (aeId: string, reportId: string, data: SubmitSaeReportParams) =>
    api.post(`/edc/ae/${aeId}/reports/${reportId}/submit`, data).then((r) => r.data.data),
};
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
