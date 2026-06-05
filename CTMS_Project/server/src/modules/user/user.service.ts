import prisma from '../../config/database';
import { CreateUserInput, UpdateUserInput, AssignRolesInput } from './user.dto';
import { hashPassword } from '../../shared/utils/hash';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { parseSort } from '../../shared/utils/sort';
import { NotFoundError, ConflictError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['username', 'displayName', 'email', 'status', 'department', 'createdAt', 'lastLoginAt'];

/**
 * 创建用户
 */
async function create(input: CreateUserInput) {
  const { username, email, password, displayName, phone, title, department, organization, roleIds } = input;

  // 检查用户名/邮箱唯一性
  const existing = await prisma.user.findFirst({
    where: { OR: [{ username }, { email }] },
  });
  if (existing) {
    throw new ConflictError('用户名或邮箱已存在');
  }

  const passwordHash = await hashPassword(password);

  const user = await prisma.user.create({
    data: {
      username, email, passwordHash, displayName, phone,
      title, department, organization, status: 'active',
    },
  });

  // 分配角色
  if (roleIds && roleIds.length > 0) {
    await prisma.userRole.createMany({
      data: roleIds.map(roleId => ({ userId: user.id, roleId })),
    });
  }

  // 审计日志
  logger.info('User created', {
    audit: true,
    userId: user.id,
    eventType: 'USER_CREATE',
    message: `创建用户 ${user.username}`,
  });

  return getUserById(user.id);
}

/**
 * 获取用户列表（分页+筛选）
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.keyword) {
    where.OR = [
      { username: { contains: query.keyword, mode: 'insensitive' } },
      { displayName: { contains: query.keyword, mode: 'insensitive' } },
      { email: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }
  if (query.status) where.status = query.status;
  if (query.department) where.department = query.department;
  if (query.organization) where.organization = query.organization;

  const [users, total] = await Promise.all([
    prisma.user.findMany({
      where,
      ...prismaPagination(pagination),
      select: {
        id: true, username: true, email: true, displayName: true,
        phone: true, title: true, department: true, organization: true,
        status: true, lastLoginAt: true, createdAt: true,
        userRoles: {
          select: {
            role: { select: { id: true, roleCode: true, roleName: true } },
            projectId: true, siteId: true,
          },
        },
      },
      orderBy: sort.orderBy,
    }),
    prisma.user.count({ where }),
  ]);

  return buildPaginatedResult(users, total, pagination);
}

/**
 * 获取单个用户详情
 */
async function getUserById(id: string) {
  const user = await prisma.user.findUnique({
    where: { id },
    include: {
      userRoles: {
        include: {
          role: { include: { rolePermissions: { include: { permission: true } } } },
        },
      },
    },
  });

  if (!user) throw new NotFoundError('User', id);

  // 不返回密码
  const { passwordHash, ...safeUser } = user;
  return safeUser;
}

/**
 * 更新用户
 */
async function update(id: string, input: UpdateUserInput) {
  const user = await prisma.user.findUnique({ where: { id } });
  if (!user) throw new NotFoundError('User', id);

  const { roleIds, ...updateData } = input;

  // 使用事务确保更新用户和角色是一致的
  const updated = await prisma.$transaction(async (tx) => {
    const updatedUser = await tx.user.update({
      where: { id },
      data: updateData,
    });

    if (roleIds !== undefined) {
      // 先删除现有的主要角色关联（这里简单处理，删除该用户所有的角色关联，再重新创建）
      await tx.userRole.deleteMany({
        where: { userId: id }
      });
      
      if (roleIds.length > 0) {
        await tx.userRole.createMany({
          data: roleIds.map(roleId => ({ userId: id, roleId })),
        });
      }
    }
    
    return updatedUser;
  });

  logger.info('User updated', {
    audit: true,
    userId: id,
    eventType: 'USER_UPDATE',
    message: `更新用户 ${user.username}`,
  });

  const { passwordHash, ...safeUser } = updated;
  return safeUser;
}

/**
 * 删除用户（硬删除）
 */
async function remove(id: string) {
  const user = await prisma.user.findUnique({ where: { id } });
  if (!user) throw new NotFoundError('User', id);

  await prisma.user.delete({
    where: { id },
  });

  logger.info('User deactivated', {
    audit: true,
    userId: id,
    eventType: 'USER_DEACTIVATE',
    message: `停用用户 ${user.username}`,
  });

  return { message: '用户已停用' };
}

/**
 * 分配角色给用户
 */
async function assignRoles(userId: string, input: AssignRolesInput) {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) throw new NotFoundError('User', userId);

  // 验证角色是否存在
  const roles = await prisma.role.findMany({
    where: { id: { in: input.roleIds } },
  });
  if (roles.length !== input.roleIds.length) {
    throw new NotFoundError('部分角色不存在');
  }

  // 先删除旧角色，再分配新角色（全局角色绑定）
  await prisma.userRole.deleteMany({
    where: { userId, projectId: null, siteId: null },
  });

  await prisma.userRole.createMany({
    data: input.roleIds.map(roleId => ({
      userId,
      roleId,
      projectId: input.projectId || null,
      siteId: input.siteId || null,
    })),
  });

  logger.info('User roles assigned', {
    audit: true,
    userId,
    eventType: 'USER_ROLE_ASSIGN',
    message: `为用户 ${user.username} 分配角色: ${roles.map(r => r.roleName).join(', ')}`,
  });

  return getUserById(userId);
}

/**
 * 重置用户密码（管理员操作）
 */
async function resetPassword(userId: string, newPassword: string) {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  if (!user) throw new NotFoundError('User', userId);

  const passwordHash = await hashPassword(newPassword);
  await prisma.user.update({
    where: { id: userId },
    data: { passwordHash, passwordChangedAt: new Date() },
  });

  logger.info('User password reset by admin', {
    audit: true,
    userId,
    eventType: 'USER_PASSWORD_RESET',
    message: `管理员重置用户 ${user.username} 的密码`,
  });

  return { message: '密码重置成功' };
}

export const userService = {
  create, getList, getUserById, update, remove, assignRoles, resetPassword,
};
