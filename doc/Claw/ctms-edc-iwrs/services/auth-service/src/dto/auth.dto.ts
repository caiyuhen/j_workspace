// 认证相关 DTO（Zod 验证 Schema）

import { z } from 'zod';

// ==================== 用户注册 ====================

export const registerSchema = z.object({
  tenantCode: z.string().min(2).max(50),
  username: z.string().min(3).max(50).regex(/^[a-zA-Z0-9_]+$/),
  email: z.string().email('Invalid email address'),
  password: z
    .string()
    .min(12, 'Password must be at least 12 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),
  firstName: z.string().max(50).optional(),
  lastName: z.string().max(50).optional(),
  phone: z.string().max(20).optional(),
});

export type RegisterInput = z.infer<typeof registerSchema>;

// ==================== 用户登录 ====================

export const loginSchema = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
  rememberMe: z.boolean().optional(),
});

export type LoginInput = z.infer<typeof loginSchema>;

// ==================== 刷新令牌 ====================

export const refreshTokenSchema = z.object({
  refreshToken: z.string().min(1),
});

export type RefreshTokenInput = z.infer<typeof refreshTokenSchema>;

// ==================== 修改密码 ====================

export const changePasswordSchema = z.object({
  currentPassword: z.string().min(1),
  newPassword: z
    .string()
    .min(12, 'New password must be at least 12 characters')
    .regex(/[A-Z]/, 'New password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'New password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'New password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'New password must contain at least one special character'),
});

export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;

// ==================== 忘记密码 ====================

export const forgotPasswordSchema = z.object({
  email: z.string().email('Invalid email address'),
});

export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;

export const resetPasswordSchema = z.object({
  token: z.string().min(1),
  newPassword: z
    .string()
    .min(12, 'New password must be at least 12 characters')
    .regex(/[A-Z]/, 'New password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'New password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'New password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'New password must contain at least one special character'),
});

export type ResetPasswordInput = z.infer<typeof resetPasswordSchema>;

// ==================== 用户资料 ====================

export const updateProfileSchema = z.object({
  firstName: z.string().max(50).optional(),
  lastName: z.string().max(50).optional(),
  phone: z.string().max(20).optional(),
  email: z.string().email('Invalid email address').optional(),
});

export type UpdateProfileInput = z.infer<typeof updateProfileSchema>;

// ==================== 角色管理 ====================

export const createRoleSchema = z.object({
  name: z.string().min(1).max(100),
  code: z.string().min(1).max(50).regex(/^[A-Z_]+$/),
  description: z.string().max(500).optional(),
  permissions: z.array(z.string()).optional(),
});

export type CreateRoleInput = z.infer<typeof createRoleSchema>;

export const updateRoleSchema = createRoleSchema.partial();

export type UpdateRoleInput = z.infer<typeof updateRoleSchema>;

// ==================== 用户角色分配 ====================

export const assignRoleSchema = z.object({
  userId: z.string().uuid('Invalid user ID'),
  roleId: z.string().uuid('Invalid role ID'),
  expiresAt: z.string().datetime().optional(),
});

export type AssignRoleInput = z.infer<typeof assignRoleSchema>;

// ==================== 查询参数 ====================

export const paginationSchema = z.object({
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('asc'),
});

export type PaginationInput = z.infer<typeof paginationSchema>;

export const userFilterSchema = z.object({
  tenantId: z.string().uuid().optional(),
  status: z.enum(['ACTIVE', 'INACTIVE', 'LOCKED', 'SUSPENDED', 'PENDING']).optional(),
  search: z.string().optional(),
});

export type UserFilterInput = z.infer<typeof userFilterSchema>;
