<<<<<<< HEAD
<<<<<<< HEAD
import api from '@/api';
import type {
  EdcTemplate, CreateTemplateParams, UpdateTemplateParams, CloneTemplateParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const templateApi = {
  list: (params?: FilterParams & { page?: number; pageSize?: number; templateType?: string; status?: string }) =>
    api.get<ApiResponse<PaginatedResponse<EdcTemplate>>>('/edc/templates', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<EdcTemplate>>(`/edc/templates/${id}`).then((r) => r.data.data),

  create: (data: CreateTemplateParams) =>
    api.post<ApiResponse<EdcTemplate>>('/edc/templates', data).then((r) => r.data.data),

  update: (id: string, data: UpdateTemplateParams) =>
    api.put<ApiResponse<EdcTemplate>>(`/edc/templates/${id}`, data).then((r) => r.data.data),

  publish: (id: string) =>
    api.post(`/edc/templates/${id}/publish`).then((r) => r.data.data),

  deprecate: (id: string) =>
    api.post(`/edc/templates/${id}/deprecate`).then((r) => r.data.data),

  clone: (id: string, data: CloneTemplateParams) =>
    api.post(`/edc/templates/${id}/clone`, data).then((r) => r.data.data),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
import api from '@/api';
import type {
  EdcTemplate, CreateTemplateParams, UpdateTemplateParams, CloneTemplateParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const templateApi = {
  list: (params?: FilterParams & { page?: number; pageSize?: number; templateType?: string; status?: string }) =>
    api.get<ApiResponse<PaginatedResponse<EdcTemplate>>>('/edc/templates', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<EdcTemplate>>(`/edc/templates/${id}`).then((r) => r.data.data),

  create: (data: CreateTemplateParams) =>
    api.post<ApiResponse<EdcTemplate>>('/edc/templates', data).then((r) => r.data.data),

  update: (id: string, data: UpdateTemplateParams) =>
    api.put<ApiResponse<EdcTemplate>>(`/edc/templates/${id}`, data).then((r) => r.data.data),

  publish: (id: string) =>
    api.post(`/edc/templates/${id}/publish`).then((r) => r.data.data),

  deprecate: (id: string) =>
    api.post(`/edc/templates/${id}/deprecate`).then((r) => r.data.data),

  clone: (id: string, data: CloneTemplateParams) =>
    api.post(`/edc/templates/${id}/clone`, data).then((r) => r.data.data),
};
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
