import { z } from 'zod';

// ========== 角色管理 DTO ==========

export const createRoleSchema = z.object({
  roleCode: z.string().min(1, '角色编码不能为空').max(50),
  roleName: z.string().min(1, '角色名称不能为空').max(100),
  description: z.string().optional(),
  isSystemRole: z.boolean().optional().default(false),
});
export type CreateRoleInput = z.infer<typeof createRoleSchema>;

export const updateRoleSchema = createRoleSchema.partial();
export type UpdateRoleInput = z.infer<typeof updateRoleSchema>;

export const assignPermissionsSchema = z.object({
  permissionIds: z.array(z.string().uuid()).min(1, '至少选择一个权限'),
  resourceScope: z.enum(['all', 'own', 'project', 'site']).optional().default('all'),
});
export type AssignPermissionsInput = z.infer<typeof assignPermissionsSchema>;

export const listRolesQuerySchema = z.object({
  page: z.string().optional(),
  pageSize: z.string().optional(),
  keyword: z.string().optional(),
  permissionType: z.string().optional(),
  sortField: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).optional(),
});
