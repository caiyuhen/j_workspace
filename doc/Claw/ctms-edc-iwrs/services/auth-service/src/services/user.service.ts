// 用户管理服务

import prisma from '../utils/prisma';
import logger from '../utils/logger';
import { UserFilterInput, PaginationInput } from '../dto/auth.dto';

export class UserService {
  /**
   * 获取用户列表（分页）
   */
  async getUsers(filters: UserFilterInput, pagination: PaginationInput) {
    try {
      const { page, limit, sortBy = 'createdAt', sortOrder } = pagination;
      const skip = (page - 1) * limit;

      const whereClauses: any = {};

      if (filters.tenantId) {
        whereClauses.tenantId = filters.tenantId;
      }

      if (filters.status) {
        whereClauses.status = filters.status;
      }

      if (filters.search) {
        whereClauses.OR = [
          { username: { contains: filters.search, mode: 'insensitive' } },
          { email: { contains: filters.search, mode: 'insensitive' } },
          { firstName: { contains: filters.search, mode: 'insensitive' } },
          { lastName: { contains: filters.search, mode: 'insensitive' } },
        ];
      }

      const [users, total] = await Promise.all([
        prisma.user.findMany({
          where: whereClauses,
          skip,
          take: limit,
          orderBy: { [sortBy]: sortOrder },
          select: {
            id: true,
            tenantId: true,
            username: true,
            email: true,
            firstName: true,
            lastName: true,
            phone: true,
            status: true,
            lastLoginAt: true,
            createdAt: true,
            updatedAt: true,
            userRoles: {
              select: {
                role: {
                  select: {
                    name: true,
                    code: true,
                  },
                },
              },
            },
          },
        }),
        prisma.user.count({ where: whereClauses }),
      ]);

      return {
        data: users,
        pagination: {
          total,
          page,
          limit,
          totalPages: Math.ceil(total / limit),
        },
      };
    } catch (error) {
      logger.error(`Get users failed: ${error}`);
      throw error;
    }
  }

  /**
   * 根据 ID 获取用户
   */
  async getUserById(userId: string) {
    try {
      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: {
          userRoles: {
            include: {
              role: true,
            },
          },
          tenant: {
            select: {
              id: true,
              name: true,
              code: true,
            },
          },
        },
      });

      if (!user) {
        throw new Error('User not found');
      }

      // 移除敏感字段
      const { passwordHash, mfaSecret, ...userWithoutSecrets } = user;

      return userWithoutSecrets;
    } catch (error) {
      logger.error(`Get user by ID failed: ${error}`);
      throw error;
    }
  }

  /**
   * 更新用户状态
   */
  async updateUserStatus(userId: string, status: string, assignedBy: string) {
    try {
      const user = await prisma.user.update({
        where: { id: userId },
        data: { status },
      });

      // 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: assignedBy,
          action: 'UPDATE_USER_STATUS',
          resource: 'User',
          resourceId: userId,
          changes: {
            after: { status },
          },
        },
      });

      logger.info(`User status updated: ${userId} -> ${status}`);

      return user;
    } catch (error) {
      logger.error(`Update user status failed: ${error}`);
      throw error;
    }
  }

  /**
   * 删除用户（软删除 - 设置为 INACTIVE）
   */
  async deleteUser(userId: string, deletedBy: string) {
    try {
      const user = await prisma.user.update({
        where: { id: userId },
        data: { status: 'INACTIVE' },
      });

      // 记录审计日志
      await prisma.auditLog.create({
        data: {
          userId: deletedBy,
          action: 'DELETE_USER',
          resource: 'User',
          resourceId: userId,
        },
      });

      logger.info(`User deleted (soft): ${userId}`);

      return user;
    } catch (error) {
      logger.error(`Delete user failed: ${error}`);
      throw error;
    }
  }
}

export default new UserService();
