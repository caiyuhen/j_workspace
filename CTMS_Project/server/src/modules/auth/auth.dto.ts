import { z } from 'zod';

// ========== 认证相关 DTO ==========

export const loginSchema = z.object({
  username: z.string().min(1, '用户名不能为空'),
  password: z.string().min(1, '密码不能为空'),
});
export type LoginInput = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  username: z.string().min(3, '用户名至少3个字符').max(50),
  email: z.string().email('邮箱格式不正确'),
  password: z.string().min(8, '密码至少8个字符').regex(
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    '密码必须包含大小写字母和数字'
  ),
  displayName: z.string().min(1, '显示名称不能为空'),
  phone: z.string().optional(),
});
export type RegisterInput = z.infer<typeof registerSchema>;

export const refreshTokenSchema = z.object({
  refreshToken: z.string().min(1, 'Refresh token 不能为空'),
});

export const changePasswordSchema = z.object({
  oldPassword: z.string().min(1),
  newPassword: z.string().min(8).regex(
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    '密码必须包含大小写字母和数字'
  ),
});
