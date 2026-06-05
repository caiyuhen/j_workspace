import { Request, Response, NextFunction } from 'express';
import { ForbiddenError } from '../errors/AppError';
import logger from '../utils/logger';
import { PrismaClient, UserRole as PrismaUserRole } from '@prisma/client';
import prisma from '../../config/database';

/**
 * RBAC 权限中间件工厂
 * @param permissionCodes 需要的权限码数组（满足任一即可）
 */
export function requirePermission(...permissionCodes: string[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const user = (req as any).user;
      if (!user || !user.userId) {
        throw new ForbiddenError('User not authenticated');
      }

      // 获取用户所有权限
      const userRoles = await prisma.userRole.findMany({
        where: { userId: user.userId },
        include: { role: { include: { rolePermissions: { include: { permission: true } } } } },
      });

      // 收集所有权限码
      const userPermissionCodes = new Set<string>();
      for (const ur of userRoles) {
        for (const rp of ur.role.rolePermissions) {
          userPermissionCodes.add(rp.permission.permissionCode);
        }
      }

      // 检查是否拥有任一所需权限
      const hasPermission = permissionCodes.some(code => userPermissionCodes.has(code));
      
      if (!hasPermission) {
        logger.warn('Permission denied', {
          userId: user.userId,
          required: permissionCodes,
          has: Array.from(userPermissionCodes),
          path: req.path,
        });
        throw new ForbiddenError(`Missing required permission: ${permissionCodes.join(' or ')}`);
      }

      next();
    } catch (err) {
      next(err);
    }
  };
}

/**
 * 角色检查中间件（简化版，仅检查角色）
 */
export function requireRole(...roleCodes: string[]) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const user = (req as any).user;
      if (!user || !user.roles) {
        throw new ForbiddenError('User not authenticated');
      }

      const hasRole = roleCodes.some((code: string) => user.roles.includes(code));
      if (!hasRole) {
        throw new ForbiddenError(`Missing required role: ${roleCodes.join(' or ')}`);
      }

      next();
    } catch (err) {
      next(err);
    }
  };
}

/**
 * 数据范围过滤（根据角色限制数据范围）
 * 在 Service 层使用
 */
export async function applyDataScope(
  userId: string,
  userRoles: string[],
  query: any,
  scopeField: 'siteId' | 'projectId' | 'createdBy',
  scopeValue: string | string[]
): Promise<any> {
  // SUPER_ADMIN 可看全部
  if (userRoles.includes('SUPER_ADMIN')) {
    return query;
  }

  // 根据角色确定数据范围
  if (userRoles.includes('SPONSOR') || userRoles.includes('PM')) {
    // Sponsor/PM 可看所属项目数据
    return query;
  }

  if (userRoles.includes('PI') || userRoles.includes('SUB_I') || userRoles.includes('CRC')) {
    // PI/CRC 只看本中心数据
    return query.where({ siteId: { in: scopeValue as string[] } });
  }

  if (userRoles.includes('CRA')) {
    // CRA 看分配的中心
    return query.where({ siteId: { in: scopeValue as string[] } });
  }

  // 默认只看自己的数据
  return query.where({ createdBy: userId });
}
