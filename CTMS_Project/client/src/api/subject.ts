import api from '@/api';
import type {
  Subject, CreateSubjectParams, UpdateSubjectParams,
  Visit, CreateVisitParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const subjectApi = {
  list: (params?: FilterParams & { page?: number; pageSize?: number; projectId?: string; siteId?: string }) =>
    api.get<ApiResponse<PaginatedResponse<Subject>>>('/edc/subjects', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<Subject>>(`/edc/subjects/${id}`).then((r) => r.data.data),

  create: (data: CreateSubjectParams) =>
    api.post<ApiResponse<Subject>>('/edc/subjects', data).then((r) => r.data.data),

  update: (id: string, data: UpdateSubjectParams) =>
    api.put<ApiResponse<Subject>>(`/edc/subjects/${id}`, data).then((r) => r.data.data),

  // 访视
  getVisits: (subjectId: string) =>
    api.get<ApiResponse<Visit[]>>(`/edc/subjects/${subjectId}/visits`).then((r) => r.data.data),

  createVisit: (subjectId: string, data: CreateVisitParams) =>
    api.post<ApiResponse<Visit>>(`/edc/subjects/${subjectId}/visits`, data).then((r) => r.data.data),
};
