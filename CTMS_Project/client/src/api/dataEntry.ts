<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  VisitFormData,
  FieldDefinition,
  ChangeHistory,
  DataEntrySummary,
} from '@/types';

export const dataEntryApi = {
  // 数据表单列表
  list: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<VisitFormData>>>('/edc/subjects', { params }).then((r) => r.data.data),

  // 受试者访视数据
  getVisits: (subjectId: string) =>
    api.get<ApiResponse<any[]>>(`/edc/subjects/${subjectId}/visits`).then((r) => r.data.data),

  // 创建/更新数据
  saveData: (subjectId: string, visitId: string, data: Record<string, any>) =>
    api.post<ApiResponse<VisitFormData>>(`/edc/subjects/${subjectId}/visits`, {
      visitId,
      data,
    }).then((r) => r.data.data),

  // 变更历史
  getChangeHistory: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<ChangeHistory>>>('/audit', {
      params: { ...params, tableName: 'VisitFormData' },
    }).then((r) => r.data.data),

  // 字段定义（通过模板）
  getFieldDefinitions: (formId: string) =>
    api.get<ApiResponse<FieldDefinition[]>>(`/edc/forms/${formId}`).then((r) => r.data.data),

  // 数据录入汇总
  getSummary: (params?: Record<string, any>) =>
    api.get<ApiResponse<DataEntrySummary>>('/edc/forms', { params }).then((r) => r.data.data as DataEntrySummary),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  VisitFormData,
  FieldDefinition,
  ChangeHistory,
  DataEntrySummary,
} from '@/types';

export const dataEntryApi = {
  // 数据表单列表
  list: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<VisitFormData>>>('/edc/subjects', { params }).then((r) => r.data.data),

  // 受试者访视数据
  getVisits: (subjectId: string) =>
    api.get<ApiResponse<any[]>>(`/edc/subjects/${subjectId}/visits`).then((r) => r.data.data),

  // 创建/更新数据
  saveData: (subjectId: string, visitId: string, data: Record<string, any>) =>
    api.post<ApiResponse<VisitFormData>>(`/edc/subjects/${subjectId}/visits`, {
      visitId,
      data,
    }).then((r) => r.data.data),

  // 变更历史
  getChangeHistory: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<ChangeHistory>>>('/audit', {
      params: { ...params, tableName: 'VisitFormData' },
    }).then((r) => r.data.data),

  // 字段定义（通过模板）
  getFieldDefinitions: (formId: string) =>
    api.get<ApiResponse<FieldDefinition[]>>(`/edc/forms/${formId}`).then((r) => r.data.data),

  // 数据录入汇总
  getSummary: (params?: Record<string, any>) =>
    api.get<ApiResponse<DataEntrySummary>>('/edc/forms', { params }).then((r) => r.data.data as DataEntrySummary),
};
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
