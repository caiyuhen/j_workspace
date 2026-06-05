import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  Document,
  CreateDocumentParams,
  DocumentVersion,
  DocumentStats,
} from '@/types';

export const documentApi = {
  // 文档 CRUD
  list: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<Document>>>('/documents', { params }).then((r) => r.data.data),

  create: (data: CreateDocumentParams) =>
    api.post<ApiResponse<Document>>('/documents', data).then((r) => r.data.data),

  getById: (id: string) =>
    api.get<ApiResponse<Document>>(`/documents/${id}`).then((r) => r.data.data),

  update: (id: string, data: Partial<CreateDocumentParams>) =>
    api.put<ApiResponse<Document>>(`/documents/${id}`, data).then((r) => r.data.data),

  remove: (id: string) =>
    api.delete(`/documents/${id}`).then((r) => r.data),

  // 统计
  getCompletionStats: (params?: Record<string, any>) =>
    api.get<ApiResponse<DocumentStats>>('/documents/stats', { params }).then((r) => r.data.data),

  // 版本管理
  getVersions: (documentId: string) =>
    api.get<ApiResponse<DocumentVersion[]>>(`/documents/${documentId}/versions`).then((r) => r.data.data),

  uploadVersion: (documentId: string, data: { fileUrl: string; fileSize?: number; mimeType?: string; changeLog?: string }) =>
    api.post<ApiResponse<DocumentVersion>>(`/documents/${documentId}/versions`, data).then((r) => r.data.data),

  getVersionDetail: (documentId: string, version: number) =>
    api.get<ApiResponse<DocumentVersion>>(`/documents/${documentId}/versions/${version}`).then((r) => r.data.data),

  // 状态审批
  updateStatus: (id: string, data: { status: string; comment?: string }) =>
    api.put<ApiResponse<Document>>(`/documents/${id}/status`, data).then((r) => r.data.data),

  bulkUpdateStatus: (data: { ids: string[]; status: string; comment?: string }) =>
    api.post<ApiResponse<{ updated: number }>>('/documents/bulk-status', data).then((r) => r.data.data),
};
