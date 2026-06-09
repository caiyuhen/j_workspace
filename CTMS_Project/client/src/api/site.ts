<<<<<<< HEAD
import api from '@/api';
import type {
  Site, CreateSiteParams, UpdateSiteParams,
  SiteStaff, AddSiteStaffParams, UpdateSiteStaffParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const siteApi = {
  list: (params?: FilterParams & { page?: number; pageSize?: number; projectId?: string }) =>
    api.get<ApiResponse<PaginatedResponse<Site>>>('/sites', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<Site>>(`/sites/${id}`).then((r) => r.data.data),

  create: (data: CreateSiteParams) =>
    api.post<ApiResponse<Site>>('/sites', data).then((r) => r.data.data),

  update: (id: string, data: UpdateSiteParams) =>
    api.put<ApiResponse<Site>>(`/sites/${id}`, data).then((r) => r.data.data),

  delete: (id: string) =>
    api.delete(`/sites/${id}`).then((r) => r.data.data),

  // 中心工作人员
  addStaff: (siteId: string, data: AddSiteStaffParams) =>
    api.post<ApiResponse<SiteStaff>>(`/sites/${siteId}/staff`, data).then((r) => r.data.data),

  updateStaff: (siteId: string, staffId: string, data: UpdateSiteStaffParams) =>
    api.put<ApiResponse<SiteStaff>>(`/sites/${siteId}/staff/${staffId}`, data).then((r) => r.data.data),

  deleteStaff: (siteId: string, staffId: string) =>
    api.delete(`/sites/${siteId}/staff/${staffId}`).then((r) => r.data.data),
};
=======
import api from '@/api';
import type {
  Site, CreateSiteParams, UpdateSiteParams,
  SiteStaff, AddSiteStaffParams, UpdateSiteStaffParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const siteApi = {
  list: (params?: FilterParams & { page?: number; pageSize?: number; projectId?: string }) =>
    api.get<ApiResponse<PaginatedResponse<Site>>>('/sites', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<Site>>(`/sites/${id}`).then((r) => r.data.data),

  create: (data: CreateSiteParams) =>
    api.post<ApiResponse<Site>>('/sites', data).then((r) => r.data.data),

  update: (id: string, data: UpdateSiteParams) =>
    api.put<ApiResponse<Site>>(`/sites/${id}`, data).then((r) => r.data.data),

  delete: (id: string) =>
    api.delete(`/sites/${id}`).then((r) => r.data.data),

  // 中心工作人员
  addStaff: (siteId: string, data: AddSiteStaffParams) =>
    api.post<ApiResponse<SiteStaff>>(`/sites/${siteId}/staff`, data).then((r) => r.data.data),

  updateStaff: (siteId: string, staffId: string, data: UpdateSiteStaffParams) =>
    api.put<ApiResponse<SiteStaff>>(`/sites/${siteId}/staff/${staffId}`, data).then((r) => r.data.data),

  deleteStaff: (siteId: string, staffId: string) =>
    api.delete(`/sites/${siteId}/staff/${staffId}`).then((r) => r.data.data),
};
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
