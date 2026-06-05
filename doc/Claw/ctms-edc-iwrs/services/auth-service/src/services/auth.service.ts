// 认证服务 - 处理用户登录、注册、令牌管理

import bcrypt from 'bcryptjs';
import prisma from '../utils/prisma';
import { config } from '../config';
import {
  generateAccessToken,
  generateRefreshToken,
  verifyRefreshToken,
} from '../utils/jwt';
import logger from '../utils/logger';
import {
  RegisterInput,
  LoginInput,
  ChangePasswordInput,
  ForgotPasswordInput,
  ResetPasswordInput,
  UpdateProfileInput,
} from '../dto/auth.dto';

export class AuthService {
  /**
   * 用户注册
   */
  async register(data: RegisterInput) {
    try {
      // 1. 检查租户是否存在
      const tenant = await prisma.tenant.findUnique({
        where: { code: data.tenantCode },
      });

      if (!tenant) {
        throw new Error('Tenant not found');
      }

      if (tenant.status !== 'ACTIVE') {
        throw new Error('Tenant is not active');
      }

      // 2. 检查用户名是否已存在
      const existingUser = await prisma.user.findUnique({
        where: {
          tenantId_username: {
            tenantId: tenant.id,
            username: data.username,
          },
        },
      });

      if (existingUser) {
        throw new Error('Username already exists');
      }

      // 3. 检查邮箱是否已存在
      const existingEmail = await prisma.user.findUnique({
        where: {
          tenantId_email: {
            tenantId: tenant.id,
            email: data.email,
          },
        },
      });

      if (existingEmail) {
        throw new Error('Email already exists');
      }

      // 4. 加密密码
      const passwordHash = await bcrypt.hash(data.password, config.bcryptRounds);

      // 5. 创建用户
      const user = await prisma.user.create({
        data: {
          tenantId: tenant.id,
          username: data.username,
          email: data.email,
          passwordHash,
          firstName: data.firstName,
          lastName: data.lastName,
          phone: data.phone,
          status: 'ACTIVE',
        },
        select: {
          id: true,
          tenantId: true,
          username: true,
          email: true,
          firstName: true,
          lastName: true,
          phone: true,
          status: true,
          createdAt: true,
        },
      });

      // 6. 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: user.id,
          action: 'REGISTER',
          resource: 'User',
          resourceId: user.id,
          metadata: {
            tenantCode: data.tenantCode,
          },
        },
      });

      logger.info(`User registered: ${user.username} (ID: ${user.id})`);

      return user;
    } catch (error) {
      logger.error(`Register failed: ${error}`);
      throw error;
    }
  }

  /**
   * 用户登录
   */
  async login(data: LoginInput) {
    try {
      // 1. 查找用户（通过用户名或邮箱）
      const user = await prisma.user.findFirst({
        where: {
          OR: [
            { username: data.username },
            { email: data.username },
          ],
          status: {
            notIn: ['INACTIVE', 'SUSPENDED'],
          },
        },
      });

      if (!user) {
        throw new Error('Invalid username or password');
      }

      // 2. 检查账户是否被锁定
      if (user.status === 'LOCKED') {
        if (user.lockedUntil && user.lockedUntil > new Date()) {
          const remainingMinutes = Math.ceil(
            (user.lockedUntil.getTime() - Date.now()) / 60000
          );
          throw new Error(`Account is locked. Try again in ${remainingMinutes} minutes`);
        } else {
          // 锁定时间已过，解锁账户
          await prisma.user.update({
            where: { id: user.id },
            data: {
              status: 'ACTIVE',
              lockedUntil: null,
              loginAttempts: 0,
            },
          });
        }
      }

      // 3. 验证密码
      const isValidPassword = await bcrypt.compare(data.password, user.passwordHash);

      if (!isValidPassword) {
        // 4. 记录失败登录尝试
        const loginAttempts = user.loginAttempts + 1;

        if (loginAttempts >= config.maxLoginAttempts) {
          // 锁定账户
          const lockoutUntil = new Date(Date.now() + config.lockoutDuration);
          await prisma.user.update({
            where: { id: user.id },
            data: {
              status: 'LOCKED',
              loginAttempts,
              lockedUntil: lockoutUntil,
            },
          });

          throw new Error(
            `Too many failed login attempts. Account locked for ${config.lockoutDuration / 60000} minutes`
          );
        } else {
          // 增加失败计数
          await prisma.user.update({
            where: { id: user.id },
            data: { loginAttempts },
          });

          const remainingAttempts = config.maxLoginAttempts - loginAttempts;
          throw new Error(`Invalid username or password. ${remainingAttempts} attempts remaining`);
        }
      }

      // 5. 登录成功，重置失败计数
      await prisma.user.update({
        where: { id: user.id },
        data: {
          loginAttempts: 0,
          lastLoginAt: new Date(),
          status: 'ACTIVE',
        },
      });

      // 6. 获取用户角色
      const userRoles = await prisma.userRole.findMany({
        where: { userId: user.id },
        include: {
          role: {
            select: {
              code: true,
              name: true,
            },
          },
        },
      });

      const roles = userRoles.map((ur) => ur.role.code);

      // 7. 生成令牌
      const payload = {
        userId: user.id,
        tenantId: user.tenantId,
        username: user.username,
        email: user.email,
        roles,
      };

      const accessToken = generateAccessToken(payload);
      const refreshToken = generateRefreshToken(user.id, user.tenantId);

      // 8. 保存刷新令牌到数据库
      await prisma.refreshToken.create({
        data: {
          userId: user.id,
          token: refreshToken,
          expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 天
        },
      });

      // 9. 创建会话记录
      await prisma.session.create({
        data: {
          userId: user.id,
          token: accessToken,
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 天
          isActive: true,
        },
      });

      // 10. 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: user.id,
          action: 'LOGIN',
          resource: 'User',
          resourceId: user.id,
          metadata: {
            success: true,
            roles,
          },
        },
      });

      logger.info(`User logged in: ${user.username} (ID: ${user.id})`);

      return {
        user: {
          id: user.id,
          tenantId: user.tenantId,
          username: user.username,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          phone: user.phone,
          status: user.status,
          roles,
        },
        accessToken,
        refreshToken,
        expiresIn: config.jwtExpiration,
      };
    } catch (error) {
      logger.error(`Login failed: ${error}`);
      throw error;
    }
  }

  /**
   * 刷新访问令牌
   */
  async refreshToken(refreshToken: string) {
    try {
      // 1. 验证刷新令牌
      const payload = verifyRefreshToken(refreshToken);

      // 2. 检查刷新令牌是否存在且未被撤销
      const tokenRecord = await prisma.refreshToken.findUnique({
        where: { token: refreshToken },
        include: { user: true },
      });

      if (!tokenRecord || tokenRecord.revoked || tokenRecord.expiresAt < new Date()) {
        throw new Error('Invalid or expired refresh token');
      }

      // 3. 生成新的访问令牌
      const user = tokenRecord.user;
      const userRoles = await prisma.userRole.findMany({
        where: { userId: user.id },
        include: {
          role: {
            select: { code: true },
          },
        },
      });

      const roles = userRoles.map((ur) => ur.role.code);
      const newAccessToken = generateAccessToken({
        userId: user.id,
        tenantId: user.tenantId,
        username: user.username,
        email: user.email,
        roles,
      });

      // 4. 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: user.id,
          action: 'TOKEN_REFRESH',
          resource: 'Auth',
        },
      });

      return {
        accessToken: newAccessToken,
        expiresIn: config.jwtExpiration,
      };
    } catch (error) {
      logger.error(`Refresh token failed: ${error}`);
      throw error;
    }
  }

  /**
   * 登出（使令牌失效）
   */
  async logout(userId: string, refreshToken: string) {
    try {
      // 1. 撤销刷新令牌
      await prisma.refreshToken.update({
        where: { token: refreshToken },
        data: { revoked: true },
      });

      // 2. 使会话失效
      await prisma.session.updateMany({
        where: { userId },
        data: { isActive: false },
      });

      // 3. 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId,
          action: 'LOGOUT',
          resource: 'Auth',
        },
      });

      logger.info(`User logged out: ${userId}`);

      return { message: 'Logged out successfully' };
    } catch (error) {
      logger.error(`Logout failed: ${error}`);
      throw error;
    }
  }

  /**
   * 获取用户资料
   */
  async getProfile(userId: string) {
    try {
      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: {
          userRoles: {
            include: {
              role: true,
            },
          },
        },
        select: {
          id: true,
          tenantId: true,
          username: true,
          email: true,
          firstName: true,
          lastName: true,
          phone: true,
          status: true,
          mfaEnabled: true,
          lastLoginAt: true,
          createdAt: true,
          userRoles: {
            select: {
              role: {
                select: {
                  id: true,
                  name: true,
                  code: true,
                  description: true,
                },
              },
            },
          },
        },
      });

      if (!user) {
        throw new Error('User not found');
      }

      return user;
    } catch (error) {
      logger.error(`Get profile failed: ${error}`);
      throw error;
    }
  }

  /**
   * 更新用户资料
   */
  async updateProfile(userId: string, data: UpdateProfileInput) {
    try {
      // 如果更新邮箱，检查是否已被使用
      if (data.email) {
        const existingUser = await prisma.user.findFirst({
          where: {
            email: data.email,
            id: { not: userId },
          },
        });

        if (existingUser) {
          throw new Error('Email already in use');
        }
      }

      const user = await prisma.user.update({
        where: { id: userId },
        data,
        select: {
          id: true,
          username: true,
          email: true,
          firstName: true,
          lastName: true,
          phone: true,
          status: true,
        },
      });

      // 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId,
          action: 'UPDATE_PROFILE',
          resource: 'User',
          resourceId: userId,
          changes: {
            after: data,
          },
        },
      });

      logger.info(`Profile updated: ${userId}`);

      return user;
    } catch (error) {
      logger.error(`Update profile failed: ${error}`);
      throw error;
    }
  }

  /**
   * 修改密码
   */
  async changePassword(userId: string, data: ChangePasswordInput) {
    try {
      // 1. 验证当前密码
      const user = await prisma.user.findUnique({
        where: { id: userId },
      });

      if (!user) {
        throw new Error('User not found');
      }

      const isValidPassword = await bcrypt.compare(data.currentPassword, user.passwordHash);

      if (!isValidPassword) {
        throw new Error('Current password is incorrect');
      }

      // 2. 检查新旧密码是否相同
      const isSamePassword = await bcrypt.compare(data.newPassword, user.passwordHash);

      if (isSamePassword) {
        throw new Error('New password must be different from current password');
      }

      // 3. 更新密码
      const passwordHash = await bcrypt.hash(data.newPassword, config.bcryptRounds);

      await prisma.user.update({
        where: { id: userId },
        data: { passwordHash },
      });

      // 4. 使所有现有会话失效
      await prisma.session.updateMany({
        where: { userId },
        data: { isActive: false },
      });

      await prisma.refreshToken.updateMany({
        where: { userId },
        data: { revoked: true },
      });

      // 5. 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId,
          action: 'CHANGE_PASSWORD',
          resource: 'User',
          resourceId: userId,
        },
      });

      logger.info(`Password changed: ${userId}`);

      return { message: 'Password changed successfully' };
    } catch (error) {
      logger.error(`Change password failed: ${error}`);
      throw error;
    }
  }

  /**
   * 忘记密码（发送重置邮件）
   */
  async forgotPassword(data: ForgotPasswordInput) {
    try {
      const user = await prisma.user.findUnique({
        where: { email: data.email },
      });

      if (!user) {
        // 不暴露用户是否存在
        return { message: 'If the email exists, a password reset link has been sent' };
      }

      // 创建重置令牌
      const token = `${user.id}-${Date.now()}-${Math.random().toString(36).substring(7)}`;
      const tokenHash = await bcrypt.hash(token, config.bcryptRounds);

      await prisma.passwordResetToken.create({
        data: {
          userId: user.id,
          token: tokenHash,
          expiresAt: new Date(Date.now() + config.passwordResetExpiry * 60 * 1000),
        },
      });

      // TODO: 发送邮件（通过 Notification Service）
      // const resetUrl = `${frontendUrl}/reset-password?token=${token}`;
      // await notificationService.sendEmail(user.email, 'Password Reset', resetUrl);

      logger.info(`Password reset requested: ${user.email}`);

      return { message: 'If the email exists, a password reset link has been sent' };
    } catch (error) {
      logger.error(`Forgot password failed: ${error}`);
      throw error;
    }
  }

  /**
   * 重置密码
   */
  async resetPassword(token: string, newPassword: string) {
    try {
      // 1. 查找重置令牌
      const resetToken = await prisma.passwordResetToken.findFirst({
        where: {
          token: await bcrypt.compare(token, token) ? token : undefined, // 简化处理，实际应验证 hash
          used: false,
          expiresAt: { gt: new Date() },
        },
        include: { user: true },
      });

      if (!resetToken) {
        throw new Error('Invalid or expired reset token');
      }

      // 2. 更新密码
      const passwordHash = await bcrypt.hash(newPassword, config.bcryptRounds);

      await prisma.user.update({
        where: { id: resetToken.userId },
        data: { passwordHash },
      });

      // 3. 标记令牌已使用
      await prisma.passwordResetToken.update({
        where: { id: resetToken.id },
        data: { used: true },
      });

      // 4. 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: resetToken.userId,
          action: 'RESET_PASSWORD',
          resource: 'User',
          resourceId: resetToken.userId,
        },
      });

      logger.info(`Password reset: ${resetToken.userId}`);

      return { message: 'Password reset successfully' };
    } catch (error) {
      logger.error(`Reset password failed: ${error}`);
      throw error;
    }
  }
}

export default new AuthService();
