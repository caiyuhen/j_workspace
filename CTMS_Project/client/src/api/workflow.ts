<<<<<<< HEAD
<<<<<<< HEAD
import api from '@/api';
import type {
  WorkflowDefinition, CreateDefinitionParams,
  WorkflowInstance, StartInstanceParams,
  WorkflowTask, ProcessTaskParams,
  PaginatedResponse, ApiResponse
} from '@/types';

export const workflowApi = {
  // 流程定义
  listDefinitions: (params?: { page?: number; pageSize?: number; workflowType?: string }) =>
    api.get<ApiResponse<PaginatedResponse<WorkflowDefinition>>>('/workflow/definitions', { params }).then((r) => r.data.data),

  getDefinition: (id: string) =>
    api.get<ApiResponse<WorkflowDefinition>>(`/workflow/definitions/${id}`).then((r) => r.data.data),

  createDefinition: (data: CreateDefinitionParams) =>
    api.post<ApiResponse<WorkflowDefinition>>('/workflow/definitions', data).then((r) => r.data.data),

  updateDefinition: (id: string, data: Partial<CreateDefinitionParams>) =>
    api.put<ApiResponse<WorkflowDefinition>>(`/workflow/definitions/${id}`, data).then((r) => r.data.data),

  // 流程实例
  listInstances: (params?: { page?: number; pageSize?: number; status?: string }) =>
    api.get<ApiResponse<PaginatedResponse<WorkflowInstance>>>('/workflow/instances', { params }).then((r) => r.data.data),

  getInstance: (id: string) =>
    api.get<ApiResponse<WorkflowInstance>>(`/workflow/instances/${id}`).then((r) => r.data.data),

  startInstance: (data: StartInstanceParams) =>
    api.post<ApiResponse<WorkflowInstance>>('/workflow/instances/start', data).then((r) => r.data.data),

  cancelInstance: (id: string) =>
    api.post(`/workflow/instances/${id}/cancel`).then((r) => r.data.data),

  processTask: (taskId: string, data: ProcessTaskParams) =>
    api.post(`/workflow/instances/${taskId}/process`, data).then((r) => r.data.data),

  // 我的待办
  getMyTasks: (params?: { page?: number; pageSize?: number; status?: string }) =>
    api.get<ApiResponse<PaginatedResponse<WorkflowTask>>>('/workflow/my-tasks', { params }).then((r) => r.data.data),

  // 统计
  getStats: () =>
    api.get('/workflow/stats').then((r) => r.data.data),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
import api from '@/api';
import type {
  WorkflowDefinition, CreateDefinitionParams,
  WorkflowInstance, StartInstanceParams,
  WorkflowTask, ProcessTaskParams,
  PaginatedResponse, ApiResponse
} from '@/types';

export const workflowApi = {
  // 流程定义
  listDefinitions: (params?: { page?: number; pageSize?: number; workflowType?: string }) =>
    api.get<ApiResponse<PaginatedResponse<WorkflowDefinition>>>('/workflow/definitions', { params }).then((r) => r.data.data),

  getDefinition: (id: string) =>
    api.get<ApiResponse<WorkflowDefinition>>(`/workflow/definitions/${id}`).then((r) => r.data.data),

  createDefinition: (data: CreateDefinitionParams) =>
    api.post<ApiResponse<WorkflowDefinition>>('/workflow/definitions', data).then((r) => r.data.data),

  updateDefinition: (id: string, data: Partial<CreateDefinitionParams>) =>
    api.put<ApiResponse<WorkflowDefinition>>(`/workflow/definitions/${id}`, data).then((r) => r.data.data),

  // 流程实例
  listInstances: (params?: { page?: number; pageSize?: number; status?: string }) =>
    api.get<ApiResponse<PaginatedResponse<WorkflowInstance>>>('/workflow/instances', { params }).then((r) => r.data.data),

  getInstance: (id: string) =>
    api.get<ApiResponse<WorkflowInstance>>(`/workflow/instances/${id}`).then((r) => r.data.data),

  startInstance: (data: StartInstanceParams) =>
    api.post<ApiResponse<WorkflowInstance>>('/workflow/instances/start', data).then((r) => r.data.data),

  cancelInstance: (id: string) =>
    api.post(`/workflow/instances/${id}/cancel`).then((r) => r.data.data),

  processTask: (taskId: string, data: ProcessTaskParams) =>
    api.post(`/workflow/instances/${taskId}/process`, data).then((r) => r.data.data),

  // 我的待办
  getMyTasks: (params?: { page?: number; pageSize?: number; status?: string }) =>
    api.get<ApiResponse<PaginatedResponse<WorkflowTask>>>('/workflow/my-tasks', { params }).then((r) => r.data.data),

  // 统计
  getStats: () =>
    api.get('/workflow/stats').then((r) => r.data.data),
};
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
