<<<<<<< HEAD
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type { AuditLog, AuditLogQuery, AuditStats, RecordChange } from '@/types';

export const auditApi = {
  // 审计日志查询
  query: (params?: AuditLogQuery) =>
    api.get<ApiResponse<PaginatedResponse<AuditLog>>>('/audit', { params }).then((r) => r.data.data),

  // 审计统计
  getStats: (params?: Record<string, any>) =>
    api.get<ApiResponse<AuditStats>>('/audit/stats', { params }).then((r) => r.data.data),

  // 详情
  getById: (id: string) =>
    api.get<ApiResponse<AuditLog>>(`/audit/${id}`).then((r) => r.data.data),

  // 记录变更历史
  getRecordHistory: (tableName: string, recordId: string) =>
    api.get<ApiResponse<RecordChange[]>>(`/audit/record/${tableName}/${recordId}`).then((r) => r.data.data),
};
=======
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type { AuditLog, AuditLogQuery, AuditStats, RecordChange } from '@/types';

export const auditApi = {
  // 审计日志查询
  query: (params?: AuditLogQuery) =>
    api.get<ApiResponse<PaginatedResponse<AuditLog>>>('/audit', { params }).then((r) => r.data.data),

  // 审计统计
  getStats: (params?: Record<string, any>) =>
    api.get<ApiResponse<AuditStats>>('/audit/stats', { params }).then((r) => r.data.data),

  // 详情
  getById: (id: string) =>
    api.get<ApiResponse<AuditLog>>(`/audit/${id}`).then((r) => r.data.data),

  // 记录变更历史
  getRecordHistory: (tableName: string, recordId: string) =>
    api.get<ApiResponse<RecordChange[]>>(`/audit/record/${tableName}/${recordId}`).then((r) => r.data.data),
};
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
