// 认证控制器

import { Request, Response, NextFunction } from 'express';
import authService from '../services/auth.service';
import {
  registerSchema,
  loginSchema,
  refreshTokenSchema,
  changePasswordSchema,
  forgotPasswordSchema,
  resetPasswordSchema,
  updateProfileSchema,
} from '../dto/auth.dto';
import logger from '../utils/logger';

export class AuthController {
  /**
   * POST /api/v1/auth/register
   * 用户注册
   */
  async register(req: Request, res: Response, next: NextFunction) {
    try {
      // 验证请求数据
      const data = registerSchema.parse(req.body);

      const user = await authService.register(data);

      res.status(201).json({
        success: true,
        message: 'User registered successfully',
        data: user,
      });
    } catch (error: any) {
      logger.error(`Register error: ${error.message}`);

      if (error instanceof Error && error.message.includes('ZodError')) {
        res.status(400).json({
          success: false,
          message: 'Validation error',
          error: error.message,
        });
        return;
      }

      res.status(400).json({
        success: false,
        message: error.message || 'Registration failed',
        error: 'REGISTRATION_FAILED',
      });
    }
  }

  /**
   * POST /api/v1/auth/login
   * 用户登录
   */
  async login(req: Request, res: Response, next: NextFunction) {
    try {
      // 验证请求数据
      const data = loginSchema.parse(req.body);

      const result = await authService.login(data);

      res.json({
        success: true,
        message: 'Login successful',
        data: result,
      });
    } catch (error: any) {
      logger.error(`Login error: ${error.message}`);

      if (error instanceof Error && error.message.includes('ZodError')) {
        res.status(400).json({
          success: false,
          message: 'Validation error',
          error: error.message,
        });
        return;
      }

      res.status(401).json({
        success: false,
        message: error.message || 'Login failed',
        error: 'LOGIN_FAILED',
      });
    }
  }

  /**
   * POST /api/v1/auth/refresh
   * 刷新令牌
   */
  async refreshToken(req: Request, res: Response, next: NextFunction) {
    try {
      const data = refreshTokenSchema.parse(req.body);

      const result = await authService.refreshToken(data.refreshToken);

      res.json({
        success: true,
        message: 'Token refreshed',
        data: result,
      });
    } catch (error: any) {
      logger.error(`Refresh token error: ${error.message}`);

      res.status(401).json({
        success: false,
        message: error.message || 'Refresh failed',
        error: 'REFRESH_FAILED',
      });
    }
  }

  /**
   * POST /api/v1/auth/logout
   * 用户登出
   */
  async logout(req: Request, res: Response, next: NextFunction) {
    try {
      const userId = req.user?.userId;

      if (!userId) {
        res.status(401).json({
          success: false,
          message: 'Unauthorized',
          error: 'UNAUTHORIZED',
        });
        return;
      }

      const refreshToken = req.body.refreshToken;

      const result = await authService.logout(userId, refreshToken);

      res.json({
        success: true,
        message: result.message,
      });
    } catch (error: any) {
      logger.error(`Logout error: ${error.message}`);

      res.status(500).json({
        success: false,
        message: 'Logout failed',
        error: 'INTERNAL_ERROR',
      });
    }
  }

  /**
   * GET /api/v1/auth/profile
   * 获取用户资料
   */
  async getProfile(req: Request, res: Response, next: NextFunction) {
    try {
      const userId = req.user?.userId;

      if (!userId) {
        res.status(401).json({
          success: false,
          message: 'Unauthorized',
          error: 'UNAUTHORIZED',
        });
        return;
      }

      const profile = await authService.getProfile(userId);

      res.json({
        success: true,
        data: profile,
      });
    } catch (error: any) {
      logger.error(`Get profile error: ${error.message}`);

      res.status(404).json({
        success: false,
        message: error.message || 'Profile not found',
        error: 'PROFILE_NOT_FOUND',
      });
    }
  }

  /**
   * PUT /api/v1/auth/profile
   * 更新用户资料
   */
  async updateProfile(req: Request, res: Response, next: NextFunction) {
    try {
      const userId = req.user?.userId;

      if (!userId) {
        res.status(401).json({
          success: false,
          message: 'Unauthorized',
          error: 'UNAUTHORIZED',
        });
        return;
      }

      const data = updateProfileSchema.parse(req.body);

      const profile = await authService.updateProfile(userId, data);

      res.json({
        success: true,
        message: 'Profile updated',
        data: profile,
      });
    } catch (error: any) {
      logger.error(`Update profile error: ${error.message}`);

      if (error instanceof Error && error.message.includes('ZodError')) {
        res.status(400).json({
          success: false,
          message: 'Validation error',
          error: error.message,
        });
        return;
      }

      res.status(400).json({
        success: false,
        message: error.message || 'Update failed',
        error: 'UPDATE_FAILED',
      });
    }
  }

  /**
   * POST /api/v1/auth/change-password
   * 修改密码
   */
  async changePassword(req: Request, res: Response, next: NextFunction) {
    try {
      const userId = req.user?.userId;

      if (!userId) {
        res.status(401).json({
          success: false,
          message: 'Unauthorized',
          error: 'UNAUTHORIZED',
        });
        return;
      }

      const data = changePasswordSchema.parse(req.body);

      const result = await authService.changePassword(userId, data);

      res.json({
        success: true,
        message: result.message,
      });
    } catch (error: any) {
      logger.error(`Change password error: ${error.message}`);

      if (error instanceof Error && error.message.includes('ZodError')) {
        res.status(400).json({
          success: false,
          message: 'Validation error',
          error: error.message,
        });
        return;
      }

      res.status(400).json({
        success: false,
        message: error.message || 'Password change failed',
        error: 'PASSWORD_CHANGE_FAILED',
      });
    }
  }

  /**
   * POST /api/v1/auth/forgot-password
   * 忘记密码
   */
  async forgotPassword(req: Request, res: Response, next: NextFunction) {
    try {
      const data = forgotPasswordSchema.parse(req.body);

      const result = await authService.forgotPassword(data);

      res.json({
        success: true,
        message: result.message,
      });
    } catch (error: any) {
      logger.error(`Forgot password error: ${error.message}`);

      if (error instanceof Error && error.message.includes('ZodError')) {
        res.status(400).json({
          success: false,
          message: 'Validation error',
          error: error.message,
        });
        return;
      }

      res.status(500).json({
        success: false,
        message: 'Request failed',
        error: 'INTERNAL_ERROR',
      });
    }
  }

  /**
   * POST /api/v1/auth/reset-password
   * 重置密码
   */
  async resetPassword(req: Request, res: Response, next: NextFunction) {
    try {
      const { token, newPassword } = req.body;

      if (!token || !newPassword) {
        res.status(400).json({
          success: false,
          message: 'Token and new password are required',
          error: 'BAD_REQUEST',
        });
        return;
      }

      const result = await authService.resetPassword(token, newPassword);

      res.json({
        success: true,
        message: result.message,
      });
    } catch (error: any) {
      logger.error(`Reset password error: ${error.message}`);

      res.status(400).json({
        success: false,
        message: error.message || 'Password reset failed',
        error: 'PASSWORD_RESET_FAILED',
      });
    }
  }
}

export default new AuthController();
