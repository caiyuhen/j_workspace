<<<<<<< HEAD
<<<<<<< HEAD
import api from '@/api';
import type {
  Project, CreateProjectParams, UpdateProjectParams,
  Milestone, CreateMilestoneParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const projectApi = {
  // 项目列表
  list: (params?: FilterParams & { page?: number; pageSize?: number }) =>
    api.get<ApiResponse<PaginatedResponse<Project>>>('/projects', { params }).then((r) => r.data.data),

  // 项目详情
  getById: (id: string) =>
    api.get<ApiResponse<Project>>(`/projects/${id}`).then((r) => r.data.data),

  // 创建项目
  create: (data: CreateProjectParams) =>
    api.post<ApiResponse<Project>>('/projects', data).then((r) => r.data.data),

  // 更新项目
  update: (id: string, data: UpdateProjectParams) =>
    api.put<ApiResponse<Project>>(`/projects/${id}`, data).then((r) => r.data.data),

  // 删除项目
  delete: (id: string) =>
    api.delete(`/projects/${id}`).then((r) => r.data.data),

  // 里程碑列表
  getMilestones: (projectId: string) =>
    api.get<ApiResponse<Milestone[]>>(`/projects/${projectId}/milestones`).then((r) => r.data.data),

  // 创建里程碑
  createMilestone: (projectId: string, data: CreateMilestoneParams) =>
    api.post<ApiResponse<Milestone>>(`/projects/${projectId}/milestones`, data).then((r) => r.data.data),

  // 更新里程碑
  updateMilestone: (projectId: string, milestoneId: string, data: Partial<CreateMilestoneParams> & { actualDate?: string; status?: string }) =>
    api.put<ApiResponse<Milestone>>(`/projects/${projectId}/milestones/${milestoneId}`, data).then((r) => r.data.data),

  // 删除里程碑
  deleteMilestone: (projectId: string, milestoneId: string) =>
    api.delete(`/projects/${projectId}/milestones/${milestoneId}`).then((r) => r.data.data),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
import api from '@/api';
import type {
  Project, CreateProjectParams, UpdateProjectParams,
  Milestone, CreateMilestoneParams,
  PaginatedResponse, FilterParams, ApiResponse
} from '@/types';

export const projectApi = {
  // 项目列表
  list: (params?: FilterParams & { page?: number; pageSize?: number }) =>
    api.get<ApiResponse<PaginatedResponse<Project>>>('/projects', { params }).then((r) => r.data.data),

  // 项目详情
  getById: (id: string) =>
    api.get<ApiResponse<Project>>(`/projects/${id}`).then((r) => r.data.data),

  // 创建项目
  create: (data: CreateProjectParams) =>
    api.post<ApiResponse<Project>>('/projects', data).then((r) => r.data.data),

  // 更新项目
  update: (id: string, data: UpdateProjectParams) =>
    api.put<ApiResponse<Project>>(`/projects/${id}`, data).then((r) => r.data.data),

  // 删除项目
  delete: (id: string) =>
    api.delete(`/projects/${id}`).then((r) => r.data.data),

  // 里程碑列表
  getMilestones: (projectId: string) =>
    api.get<ApiResponse<Milestone[]>>(`/projects/${projectId}/milestones`).then((r) => r.data.data),

  // 创建里程碑
  createMilestone: (projectId: string, data: CreateMilestoneParams) =>
    api.post<ApiResponse<Milestone>>(`/projects/${projectId}/milestones`, data).then((r) => r.data.data),

  // 更新里程碑
  updateMilestone: (projectId: string, milestoneId: string, data: Partial<CreateMilestoneParams> & { actualDate?: string; status?: string }) =>
    api.put<ApiResponse<Milestone>>(`/projects/${projectId}/milestones/${milestoneId}`, data).then((r) => r.data.data),

  // 删除里程碑
  deleteMilestone: (projectId: string, milestoneId: string) =>
    api.delete(`/projects/${projectId}/milestones/${milestoneId}`).then((r) => r.data.data),
};
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
