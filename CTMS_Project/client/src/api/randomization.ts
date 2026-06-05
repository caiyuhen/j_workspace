import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  RandomizationRecord,
  CreateRandomizationParams,
  RandomizationStats,
  NumberPoolStatus,
} from '@/types';

export const randomizationApi = {
  // 随机化记录
  list: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<RandomizationRecord>>>('/edc/randomization', { params }).then((r) => r.data.data),

  getRecordById: (id: string) =>
    api.get<ApiResponse<RandomizationRecord>>(`/edc/randomization/${id}`).then((r) => r.data.data),

  getRecordBySubject: (subjectId: string) =>
    api.get<ApiResponse<RandomizationRecord>>(`/edc/randomization/subject/${subjectId}`).then((r) => r.data.data),

  createRecord: (data: CreateRandomizationParams) =>
    api.post<ApiResponse<RandomizationRecord>>('/edc/randomization', data).then((r) => r.data.data),

  // 紧急揭盲
  emergencyUnblind: (subjectId: string, reason: string) =>
    api.post<ApiResponse<RandomizationRecord>>(`/edc/randomization/emergency-unblind/${subjectId}`, { reason }).then((r) => r.data.data),

  // 统计
  getRandomizationStats: (projectId: string) =>
    api.get<ApiResponse<RandomizationStats>>(`/edc/randomization/stats/${projectId}`).then((r) => r.data.data),

  // 号池状态
  getNumberPoolStatus: (projectId: string) =>
    api.get<ApiResponse<NumberPoolStatus>>(`/edc/randomization/pool/${projectId}`).then((r) => r.data.data),

  // 导出
  exportList: (projectId: string) =>
    api.get(`/edc/randomization/export/${projectId}`, { responseType: 'blob' }).then((r) => r.data),
};
