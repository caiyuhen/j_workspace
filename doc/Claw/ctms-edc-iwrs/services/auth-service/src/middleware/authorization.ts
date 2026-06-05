// RBAC 权限控制中间件

import { Request, Response, NextFunction } from 'express';
import prisma from '../utils/prisma';
import logger from '../utils/logger';

export interface Permission {
  resource: string;
  action: string;
}

/**
 * 权限检查中间件
 * 检查用户是否有特定资源的特定操作权限
 */
export const authorize = (...requiredPermissions: Permission[]) => {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      if (!req.user) {
        res.status(401).json({
          success: false,
          message: 'Unauthorized',
          error: 'UNAUTHORIZED',
        });
        return;
      }

      // 获取用户的角色
      const userRoles = await prisma.userRole.findMany({
        where: { userId: req.user.userId },
        include: {
          role: {
            select: {
              permissions: true,
              code: true,
            },
          },
        },
      });

      // 收集用户的所有权限
      const userPermissions: string[] = [];
      userRoles.forEach((ur) => {
        if (ur.role.permissions && Array.isArray(ur.role.permissions)) {
          userPermissions.push(...ur.role.permissions);
        }
      });

      // 检查是否有超级管理员角色（绕过权限检查）
      const hasSuperAdmin = userRoles.some((ur) => ur.role.code === 'SUPER_ADMIN');
      if (hasSuperAdmin) {
        next();
        return;
      }

      // 检查是否拥有所有必需的权限
      const hasAllPermissions = requiredPermissions.every((permission) => {
        const permissionString = `${permission.resource}:${permission.action}`;
        return userPermissions.includes(permissionString) || userPermissions.includes(`${permission.resource}:*`);
      });

      if (!hasAllPermissions) {
        logger.warn(
          `Permission denied for user ${req.user.userId}. Required: ${requiredPermissions.map((p) => `${p.resource}:${p.action}`).join(', ')}`
        );

        res.status(403).json({
          success: false,
          message: 'Insufficient permissions',
          error: 'FORBIDDEN',
          required: requiredPermissions.map((p) => `${p.resource}:${p.action}`),
        });
        return;
      }

      next();
    } catch (error) {
      logger.error(`Authorization check failed: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
        error: 'INTERNAL_ERROR',
      });
    }
  };
};

/**
 * 角色检查中间件
 * 检查用户是否有特定角色
 */
export const requireRole = (...allowedRoles: string[]) => {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      if (!req.user) {
        res.status(401).json({
          success: false,
          message: 'Unauthorized',
          error: 'UNAUTHORIZED',
        });
        return;
      }

      // 获取用户的角色代码
      const userRoles = await prisma.userRole.findMany({
        where: { userId: req.user.userId },
        include: {
          role: {
            select: {
              code: true,
            },
          },
        },
      });

      const userRoleCodes = userRoles.map((ur) => ur.role.code);

      // 检查是否有允许的角色
      const hasAllowedRole = userRoleCodes.some((roleCode) => allowedRoles.includes(roleCode));

      if (!hasAllowedRole) {
        logger.warn(
          `Role requirement failed for user ${req.user.userId}. Required: ${allowedRoles.join(', ')}`
        );

        res.status(403).json({
          success: false,
          message: 'Insufficient role privileges',
          error: 'FORBIDDEN',
          required: allowedRoles,
        });
        return;
      }

      next();
    } catch (error) {
      logger.error(`Role check failed: ${error}`);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
        error: 'INTERNAL_ERROR',
      });
    }
  };
};
