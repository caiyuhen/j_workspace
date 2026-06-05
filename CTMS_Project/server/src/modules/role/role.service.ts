import prisma from '../../config/database';
import { CreateRoleInput, UpdateRoleInput, AssignPermissionsInput } from './role.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { parseSort } from '../../shared/utils/sort';
import { NotFoundError, ConflictError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['roleCode', 'roleName', 'createdAt', 'isSystemRole'];

/**
 * 创建角色
 */
async function create(input: CreateRoleInput) {
  const existing = await prisma.role.findUnique({
    where: { roleCode: input.roleCode },
  });
  if (existing) {
    throw new ConflictError(`角色编码 ${input.roleCode} 已存在`);
  }

  const role = await prisma.role.create({
    data: {
      roleCode: input.roleCode,
      roleName: input.roleName,
      description: input.description,
      isSystemRole: input.isSystemRole,
    },
  });

  logger.info('Role created', {
    audit: true,
    eventType: 'ROLE_CREATE',
    message: `创建角色 ${role.roleCode} - ${role.roleName}`,
  });

  return role;
}

/**
 * 获取角色列表（分页）
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'roleCode', 'asc');

  const where: any = {};
  if (query.keyword) {
    where.OR = [
      { roleCode: { contains: query.keyword, mode: 'insensitive' } },
      { roleName: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }

  const [roles, total] = await Promise.all([
    prisma.role.findMany({
      where,
      ...prismaPagination(pagination),
      include: {
        rolePermissions: {
          include: { permission: { select: { id: true, permissionCode: true, permissionName: true, permissionType: true } } },
        },
        _count: { select: { userRoles: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.role.count({ where }),
  ]);

  return buildPaginatedResult(roles, total, pagination);
}

/**
 * 获取角色详情
 */
async function getById(id: string) {
  const role = await prisma.role.findUnique({
    where: { id },
    include: {
      rolePermissions: {
        include: { permission: true },
      },
      _count: { select: { userRoles: true } },
    },
  });

  if (!role) throw new NotFoundError('Role', id);
  return role;
}

/**
 * 更新角色
 */
async function update(id: string, input: UpdateRoleInput) {
  const role = await prisma.role.findUnique({ where: { id } });
  if (!role) throw new NotFoundError('Role', id);

  // 移除修改系统角色的限制
  // if (role.isSystemRole) {
  //   throw new BadRequestError('系统角色不允许修改');
  // }

  if (input.roleCode && input.roleCode !== role.roleCode) {
    const existing = await prisma.role.findUnique({ where: { roleCode: input.roleCode } });
    if (existing) throw new ConflictError(`角色编码 ${input.roleCode} 已存在`);
  }

  const updated = await prisma.role.update({
    where: { id },
    data: input,
  });

  logger.info('Role updated', {
    audit: true,
    eventType: 'ROLE_UPDATE',
    message: `更新角色 ${updated.roleCode}`,
  });

  return updated;
}

/**
 * 删除角色
 */
async function remove(id: string) {
  const role = await prisma.role.findUnique({
    where: { id },
    include: { _count: { select: { userRoles: true } } },
  });

  if (!role) throw new NotFoundError('Role', id);
  if (role.isSystemRole) {
    throw new BadRequestError('系统角色不允许删除');
  }
  if (role._count.userRoles > 0) {
    throw new BadRequestError(`角色 ${role.roleName} 下仍有 ${role._count.userRoles} 个用户绑定，无法删除`);
  }

  await prisma.role.delete({ where: { id } });

  logger.info('Role deleted', {
    audit: true,
    eventType: 'ROLE_DELETE',
    message: `删除角色 ${role.roleCode}`,
  });

  return { message: '角色已删除' };
}

/**
 * 分配权限给角色
 */
async function assignPermissions(roleId: string, input: AssignPermissionsInput) {
  const role = await prisma.role.findUnique({ where: { id: roleId } });
  if (!role) throw new NotFoundError('Role', roleId);

  // 验证权限是否存在
  const permissions = await prisma.permission.findMany({
    where: { id: { in: input.permissionIds } },
  });
  if (permissions.length !== input.permissionIds.length) {
    throw new NotFoundError('部分权限不存在');
  }

  // 替换旧权限
  await prisma.rolePermission.deleteMany({ where: { roleId } });
  if (input.permissionIds.length > 0) {
    await prisma.rolePermission.createMany({
      data: input.permissionIds.map(permissionId => ({
        roleId,
        permissionId,
        resourceScope: input.resourceScope,
      })),
    });
  }

  logger.info('Role permissions assigned', {
    audit: true,
    eventType: 'ROLE_PERMISSION_ASSIGN',
    message: `为角色 ${role.roleCode} 分配 ${permissions.length} 个权限`,
  });

  return getById(roleId);
}

/**
 * 获取所有权限列表（供前端选择使用）
 */
async function listAllPermissions() {
  return prisma.permission.findMany({
    orderBy: [{ permissionType: 'asc' }, { permissionCode: 'asc' }],
  });
}

/**
 * 获取角色的用户列表
 */
async function getRoleUsers(roleId: string, query: Record<string, any>) {
  const role = await prisma.role.findUnique({ where: { id: roleId } });
  if (!role) throw new NotFoundError('Role', roleId);

  const pagination = parsePagination(query);

  const [userRoles, total] = await Promise.all([
    prisma.userRole.findMany({
      where: { roleId },
      ...prismaPagination(pagination),
      include: {
        user: {
          select: { id: true, username: true, displayName: true, email: true, status: true },
        },
      },
      orderBy: { createdAt: 'desc' },
    }),
    prisma.userRole.count({ where: { roleId } }),
  ]);

  return buildPaginatedResult(userRoles, total, pagination);
}

export const roleService = {
  create, getList, getById, update, remove, assignPermissions, listAllPermissions, getRoleUsers,
};
