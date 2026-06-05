import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type { User, CreateUserParams, UpdateUserParams, Role, CreateRoleParams, Organization } from '@/types';

export const settingsApi = {
  // 用户管理
  listUsers: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<User>>>('/users', { params }).then((r) => r.data.data),

  createUser: (data: CreateUserParams) =>
    api.post<ApiResponse<User>>('/users', data).then((r) => r.data.data),

  getUserById: (id: string) =>
    api.get<ApiResponse<User>>(`/users/${id}`).then((r) => r.data.data),

  updateUser: (id: string, data: UpdateUserParams) =>
    api.put<ApiResponse<User>>(`/users/${id}`, data).then((r) => r.data.data),

  deleteUser: (id: string) =>
    api.delete(`/users/${id}`).then((r) => r.data),

  // 角色管理
  listRoles: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<Role>>>('/roles', { params }).then((r) => r.data.data),

  createRole: (data: CreateRoleParams) =>
    api.post<ApiResponse<Role>>('/roles', data).then((r) => r.data.data),

  getRoleById: (id: string) =>
    api.get<ApiResponse<Role>>(`/roles/${id}`).then((r) => r.data.data),

  updateRole: (id: string, data: Partial<CreateRoleParams>) =>
    api.put<ApiResponse<Role>>(`/roles/${id}`, data).then((r) => r.data.data),

  deleteRole: (id: string) =>
    api.delete(`/roles/${id}`).then((r) => r.data),

  // 组织机构
  listOrganizations: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<Organization>>>('/organizations', { params }).then((r) => r.data.data),

  createOrganization: (data: Partial<Organization>) =>
    api.post<ApiResponse<Organization>>('/organizations', data).then((r) => r.data.data),

  updateOrganization: (id: string, data: Partial<Organization>) =>
    api.put<ApiResponse<Organization>>(`/organizations/${id}`, data).then((r) => r.data.data),

  deleteOrganization: (id: string) =>
    api.delete(`/organizations/${id}`).then((r) => r.data),
};
