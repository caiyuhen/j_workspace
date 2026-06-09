<<<<<<< HEAD
<<<<<<< HEAD
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  SdvRecord,
  CreateSdvParams,
  SdvItem,
  SdvStatistics,
} from '@/types';

export const sdvApi = {
  // SDV 记录
  list: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<SdvRecord>>>('/edc/sdv', { params }).then((r) => r.data.data),

  getStatistics: (params?: Record<string, any>) =>
    api.get<ApiResponse<SdvStatistics>>('/edc/sdv/statistics', { params }).then((r) => r.data.data),

  create: (data: CreateSdvParams) =>
    api.post<ApiResponse<SdvRecord>>('/edc/sdv', data).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<SdvRecord>>(`/edc/sdv/${id}`).then((r) => r.data.data),

  updateRecord: (id: string, data: Partial<CreateSdvParams>) =>
    api.put<ApiResponse<SdvRecord>>(`/edc/sdv/${id}`, data).then((r) => r.data.data),

  // SDV 核查项
  addItems: (id: string, items: Partial<SdvItem>[]) =>
    api.post<ApiResponse<SdvItem[]>>(`/edc/sdv/${id}/items`, { items }).then((r) => r.data.data),

  updateItem: (id: string, itemId: string, data: Partial<SdvItem>) =>
    api.put<ApiResponse<SdvItem>>(`/edc/sdv/${id}/items/${itemId}`, data).then((r) => r.data.data),

  batchUpdateItems: (id: string, data: { items: { itemId: string; status: string; notes?: string }[] }) =>
    api.post<ApiResponse<{ updated: number }>>(`/edc/sdv/${id}/items/batch`, data).then((r) => r.data.data),

  // 完成 SDV
  complete: (id: string) =>
    api.post<ApiResponse<SdvRecord>>(`/edc/sdv/${id}/complete`).then((r) => r.data.data),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  SdvRecord,
  CreateSdvParams,
  SdvItem,
  SdvStatistics,
} from '@/types';

export const sdvApi = {
  // SDV 记录
  list: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<SdvRecord>>>('/edc/sdv', { params }).then((r) => r.data.data),

  getStatistics: (params?: Record<string, any>) =>
    api.get<ApiResponse<SdvStatistics>>('/edc/sdv/statistics', { params }).then((r) => r.data.data),

  create: (data: CreateSdvParams) =>
    api.post<ApiResponse<SdvRecord>>('/edc/sdv', data).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<SdvRecord>>(`/edc/sdv/${id}`).then((r) => r.data.data),

  updateRecord: (id: string, data: Partial<CreateSdvParams>) =>
    api.put<ApiResponse<SdvRecord>>(`/edc/sdv/${id}`, data).then((r) => r.data.data),

  // SDV 核查项
  addItems: (id: string, items: Partial<SdvItem>[]) =>
    api.post<ApiResponse<SdvItem[]>>(`/edc/sdv/${id}/items`, { items }).then((r) => r.data.data),

  updateItem: (id: string, itemId: string, data: Partial<SdvItem>) =>
    api.put<ApiResponse<SdvItem>>(`/edc/sdv/${id}/items/${itemId}`, data).then((r) => r.data.data),

  batchUpdateItems: (id: string, data: { items: { itemId: string; status: string; notes?: string }[] }) =>
    api.post<ApiResponse<{ updated: number }>>(`/edc/sdv/${id}/items/batch`, data).then((r) => r.data.data),

  // 完成 SDV
  complete: (id: string) =>
    api.post<ApiResponse<SdvRecord>>(`/edc/sdv/${id}/complete`).then((r) => r.data.data),
};
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
