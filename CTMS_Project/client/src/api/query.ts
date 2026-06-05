import api from '@/api';
import type {
  DataQuery, CreateQueryParams, ReplyQueryParams, ReassignQueryParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const queryApi = {
  list: (params?: FilterParams & { page?: number; pageSize?: number; projectId?: string; priority?: string; status?: string }) =>
    api.get<ApiResponse<PaginatedResponse<DataQuery>>>('/edc/queries', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<DataQuery>>(`/edc/queries/${id}`).then((r) => r.data.data),

  create: (data: CreateQueryParams) =>
    api.post<ApiResponse<DataQuery>>('/edc/queries', data).then((r) => r.data.data),

  reply: (id: string, data: ReplyQueryParams) =>
    api.post(`/edc/queries/${id}/reply`, data).then((r) => r.data.data),

  reassign: (id: string, data: ReassignQueryParams) =>
    api.post(`/edc/queries/${id}/reassign`, data).then((r) => r.data.data),
};
