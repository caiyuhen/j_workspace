import { z } from 'zod';

// ========== 用户管理 DTO ==========

export const createUserSchema = z.object({
  username: z.string().min(3, '用户名至少3个字符').max(50, '用户名最多50个字符'),
  email: z.string().email('邮箱格式不正确'),
  password: z.string().min(8, '密码至少8个字符').regex(
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    '密码必须包含大小写字母和数字'
  ),
  displayName: z.string().min(1, '显示名称不能为空'),
  phone: z.string().optional().nullable().or(z.literal('')),
  title: z.string().optional().nullable().or(z.literal('')),
  department: z.string().optional().nullable().or(z.literal('')),
  organization: z.string().optional().nullable().or(z.literal('')),
  roleIds: z.array(z.string().uuid()).optional(),
});
export type CreateUserInput = z.infer<typeof createUserSchema>;

export const updateUserSchema = createUserSchema.partial().omit({ password: true }).extend({
  status: z.enum(['active', 'inactive', 'locked']).optional(),
});
export type UpdateUserInput = z.infer<typeof updateUserSchema>;

export const listUsersQuerySchema = z.object({
  page: z.string().optional(),
  pageSize: z.string().optional(),
  keyword: z.string().optional(),
  status: z.enum(['active', 'inactive', 'locked']).optional(),
  department: z.string().optional(),
  organization: z.string().optional(),
  sortField: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).optional(),
});
export type ListUsersQuery = z.infer<typeof listUsersQuerySchema>;

export const assignRolesSchema = z.object({
  roleIds: z.array(z.string().uuid()).min(1, '至少选择一个角色'),
  projectId: z.string().uuid().optional(),
  siteId: z.string().uuid().optional(),
});
export type AssignRolesInput = z.infer<typeof assignRolesSchema>;

export const changeUserPasswordSchema = z.object({
  newPassword: z.string().min(8, '密码至少8个字符').regex(
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    '密码必须包含大小写字母和数字'
  ),
});
export type ChangeUserPasswordInput = z.infer<typeof changeUserPasswordSchema>;
