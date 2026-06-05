import prisma from '../../config/database';
import { CreateOrgInput, UpdateOrgInput } from './organization.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { parseSort } from '../../shared/utils/sort';
import { NotFoundError, ConflictError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['orgCode', 'orgName', 'orgType', 'status', 'createdAt'];

/**
 * 创建组织机构
 */
async function create(input: CreateOrgInput, userId: string) {
  const existing = await prisma.organization.findUnique({
    where: { orgCode: input.orgCode },
  });
  if (existing) {
    throw new ConflictError(`组织编码 ${input.orgCode} 已存在`);
  }

  const org = await prisma.organization.create({
    data: input,
  });

  logger.info('Organization created', {
    audit: true,
    eventType: 'ORG_CREATE',
    orgId: org.id,
    message: `创建组织 ${org.orgCode} - ${org.orgName}`,
  });

  return org;
}

/**
 * 获取组织列表（分页+筛选）
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'orgCode', 'asc');

  const where: any = {};
  if (query.keyword) {
    where.OR = [
      { orgCode: { contains: query.keyword, mode: 'insensitive' } },
      { orgName: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }
  if (query.orgType) where.orgType = query.orgType;
  if (query.status) where.status = query.status;
  if (query.parentId !== undefined) {
    where.parentId = query.parentId || null;
  }

  const [orgs, total] = await Promise.all([
    prisma.organization.findMany({
      where,
      ...prismaPagination(pagination),
      orderBy: sort.orderBy,
    }),
    prisma.organization.count({ where }),
  ]);

  return buildPaginatedResult(orgs, total, pagination);
}

/**
 * 获取组织详情
 */
async function getById(id: string) {
  const org = await prisma.organization.findUnique({ where: { id } });
  if (!org) throw new NotFoundError('Organization', id);
  return org;
}

/**
 * 更新组织机构
 */
async function update(id: string, input: UpdateOrgInput) {
  const org = await prisma.organization.findUnique({ where: { id } });
  if (!org) throw new NotFoundError('Organization', id);

  if (input.orgCode && input.orgCode !== org.orgCode) {
    const existing = await prisma.organization.findUnique({ where: { orgCode: input.orgCode } });
    if (existing) throw new ConflictError(`组织编码 ${input.orgCode} 已存在`);
  }

  const updated = await prisma.organization.update({
    where: { id },
    data: input,
  });

  logger.info('Organization updated', {
    audit: true,
    eventType: 'ORG_UPDATE',
    orgId: id,
    message: `更新组织 ${org.orgCode}`,
  });

  return updated;
}

/**
 * 获取组织树形结构
 */
async function getTree(orgType?: string) {
  const where: any = {};
  if (orgType) where.orgType = orgType;

  const orgs = await prisma.organization.findMany({
    where: { ...where, status: 'active' },
    orderBy: [{ sortOrder: 'asc' }, { orgCode: 'asc' }],
  });

  // 构建树形结构
  const map = new Map<string, any>();
  const roots: any[] = [];

  for (const org of orgs) {
    map.set(org.id, { ...org, children: [] });
  }

  for (const org of orgs) {
    const node = map.get(org.id)!;
    if (org.parentId && map.has(org.parentId)) {
      map.get(org.parentId)!.children.push(node);
    } else {
      roots.push(node);
    }
  }

  return roots;
}

/**
 * 删除组织机构（硬删除）
 */
async function remove(id: string) {
  const org = await prisma.organization.findUnique({ where: { id } });
  if (!org) throw new NotFoundError('Organization', id);

  // 检查是否有子组织
  const childCount = await prisma.organization.count({
    where: { parentId: id },
  });
  if (childCount > 0) {
    throw new ConflictError('该组织下有子组织，无法删除');
  }

  await prisma.organization.delete({
    where: { id },
  });

  logger.info('Organization deleted', {
    audit: true,
    eventType: 'ORG_DELETE',
    orgId: id,
    message: `删除组织 ${org.orgCode}`,
  });

  return { message: '组织已删除' };
}

export const organizationService = {
  create, getList, getById, update, getTree, remove,
};
