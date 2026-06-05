import { Request, Response, NextFunction } from 'express';
import { authService } from './auth.service';
import { loginSchema, registerSchema, refreshTokenSchema, changePasswordSchema } from './auth.dto';
import { UnauthorizedError } from '../../shared/errors/AppError';

/**
 * 登录
 * POST /api/auth/login
 */
async function login(req: Request, res: Response, next: NextFunction) {
  try {
    const input = loginSchema.parse(req.body);
    const ip = req.ip || req.socket.remoteAddress || 'unknown';
    const result = await authService.login(input, ip);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

/**
 * 注册
 * POST /api/auth/register
 */
async function register(req: Request, res: Response, next: NextFunction) {
  try {
    const input = registerSchema.parse(req.body);
    const result = await authService.register(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

/**
 * 刷新 Token
 * POST /api/auth/refresh
 */
async function refresh(req: Request, res: Response, next: NextFunction) {
  try {
    const { refreshToken } = refreshTokenSchema.parse(req.body);
    const result = await authService.refreshTokens(refreshToken);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

/**
 * 获取当前用户信息
 * GET /api/auth/me
 */
async function getMe(req: Request, res: Response, next: NextFunction) {
  try {
    const user = (req as any).user;
    if (!user) throw new UnauthorizedError();
    const result = await authService.getCurrentUser(user.userId);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

/**
 * 修改密码
 * PUT /api/auth/password
 */
async function changePassword(req: Request, res: Response, next: NextFunction) {
  try {
    const user = (req as any).user;
    if (!user) throw new UnauthorizedError();
    const input = changePasswordSchema.parse(req.body);
    await authService.changePassword(user.userId, input.oldPassword, input.newPassword);
    res.json({ success: true, message: '密码修改成功' });
  } catch (err) {
    next(err);
  }
}

export const authController = {
  login,
  register,
  refresh,
  getMe,
  changePassword,
};
