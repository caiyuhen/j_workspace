// 角色管理服务

import prisma from '../utils/prisma';
import logger from '../utils/logger';
import { CreateRoleInput, UpdateRoleInput, AssignRoleInput } from '../dto/auth.dto';

export class RoleService {
  /**
   * 创建角色
   */
  async createRole(tenantId: string, data: CreateRoleInput, createdById: string) {
    try {
      // 检查角色代码是否已存在
      const existingRole = await prisma.role.findUnique({
        where: {
          tenantId_code: {
            tenantId,
            code: data.code,
          },
        },
      });

      if (existingRole) {
        throw new Error('Role code already exists');
      }

      const role = await prisma.role.create({
        data: {
          tenantId,
          name: data.name,
          code: data.code,
          description: data.description,
          permissions: data.permissions,
        },
      });

      // 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: createdById,
          action: 'CREATE_ROLE',
          resource: 'Role',
          resourceId: role.id,
          changes: { after: data },
        },
      });

      logger.info(`Role created: ${role.code} (ID: ${role.id})`);

      return role;
    } catch (error) {
      logger.error(`Create role failed: ${error}`);
      throw error;
    }
  }

  /**
   * 更新角色
   */
  async updateRole(roleId: string, data: UpdateRoleInput, updatedById: string) {
    try {
      const role = await prisma.role.update({
        where: { id: roleId },
        data,
      });

      // 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: updatedById,
          action: 'UPDATE_ROLE',
          resource: 'Role',
          resourceId: roleId,
          changes: { after: data },
        },
      });

      logger.info(`Role updated: ${roleId}`);

      return role;
    } catch (error) {
      logger.error(`Update role failed: ${error}`);
      throw error;
    }
  }

  /**
   * 获取角色列表
   */
  async getRoles(tenantId?: string) {
    try {
      const where: any = {};

      if (tenantId) {
        where.tenantId = tenantId;
      }

      const roles = await prisma.role.findMany({
        where,
        orderBy: { createdAt: 'asc' },
      });

      return roles;
    } catch (error) {
      logger.error(`Get roles failed: ${error}`);
      throw error;
    }
  }

  /**
   * 为用户分配角色
   */
  async assignRole(data: AssignRoleInput, assignedBy: string) {
    try {
      const userRole = await prisma.userRole.create({
        data: {
          userId: data.userId,
          roleId: data.roleId,
          assignedBy,
          expiresAt: data.expiresAt ? new Date(data.expiresAt) : null,
        },
        include: {
          user: {
            select: {
              id: true,
              username: true,
              email: true,
            },
          },
          role: true,
        },
      });

      // 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: assignedBy,
          action: 'ASSIGN_ROLE',
          resource: 'UserRole',
          resourceId: userRole.id,
          changes: {
            after: {
              userId: data.userId,
              roleId: data.roleId,
            },
          },
        },
      });

      logger.info(`Role assigned: ${data.roleId} to user ${data.userId}`);

      return userRole;
    } catch (error) {
      logger.error(`Assign role failed: ${error}`);
      throw error;
    }
  }

  /**
   * 移除用户角色
   */
  async revokeRole(userId: string, roleId: string, revokedBy: string) {
    try {
      await prisma.userRole.deleteMany({
        where: {
          userId,
          roleId,
        },
      });

      // 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: revokedBy,
          action: 'REVOKE_ROLE',
          resource: 'UserRole',
          changes: {
            after: {
              userId,
              roleId,
            },
          },
        },
      });

      logger.info(`Role revoked: ${roleId} from user ${userId}`);

      return { success: true };
    } catch (error) {
      logger.error(`Revoke role failed: ${error}`);
      throw error;
    }
  }

  /**
   * 获取用户的角色
   */
  async getUserRoles(userId: string) {
    try {
      const userRoles = await prisma.userRole.findMany({
        where: { userId },
        include: {
          role: true,
        },
      });

      return userRoles;
    } catch (error) {
      logger.error(`Get user roles failed: ${error}`);
      throw error;
    }
  }
}

export default new RoleService();
