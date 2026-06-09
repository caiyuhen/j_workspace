<<<<<<< HEAD
<<<<<<< HEAD
import api from '@/api';
import type {
  Timesheet, CreateTimesheetParams,
  SubmitTimesheetParams, ApproveTimesheetParams,
  PaginatedResponse, ApiResponse
} from '@/types';

export const timesheetApi = {
  list: (params?: { page?: number; pageSize?: number; status?: string; userId?: string; projectId?: string }) =>
    api.get<ApiResponse<PaginatedResponse<Timesheet>>>('/timesheets', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<Timesheet>>(`/timesheets/${id}`).then((r) => r.data.data),

  create: (data: CreateTimesheetParams) =>
    api.post<ApiResponse<Timesheet>>('/timesheets', data).then((r) => r.data.data),

  submit: (id: string, data?: SubmitTimesheetParams) =>
    api.post(`/timesheets/${id}/submit`, data).then((r) => r.data.data),

  approve: (id: string, data: ApproveTimesheetParams) =>
    api.post(`/timesheets/${id}/approve`, data).then((r) => r.data.data),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
import api from '@/api';
import type {
  Timesheet, CreateTimesheetParams,
  SubmitTimesheetParams, ApproveTimesheetParams,
  PaginatedResponse, ApiResponse
} from '@/types';

export const timesheetApi = {
  list: (params?: { page?: number; pageSize?: number; status?: string; userId?: string; projectId?: string }) =>
    api.get<ApiResponse<PaginatedResponse<Timesheet>>>('/timesheets', { params }).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<Timesheet>>(`/timesheets/${id}`).then((r) => r.data.data),

  create: (data: CreateTimesheetParams) =>
    api.post<ApiResponse<Timesheet>>('/timesheets', data).then((r) => r.data.data),

  submit: (id: string, data?: SubmitTimesheetParams) =>
    api.post(`/timesheets/${id}/submit`, data).then((r) => r.data.data),

  approve: (id: string, data: ApproveTimesheetParams) =>
    api.post(`/timesheets/${id}/approve`, data).then((r) => r.data.data),
};
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
