import prisma from '../../../config/database';
import { CreateSiteInput, UpdateSiteInput, AddSiteStaffInput, UpdateSiteStaffInput } from './site.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, ConflictError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['siteCode', 'siteName', 'status', 'ethicsStatus', 'contractStatus', 'createdAt'];

/**
 * 创建中心
 */
async function create(input: CreateSiteInput) {
  // 验证项目存在
  if (input.projectId) {
    const project = await prisma.project.findUnique({ where: { id: input.projectId } });
    if (!project) throw new NotFoundError('Project', input.projectId);
  }

  // 检查中心编码唯一性
  const existing = await prisma.site.findFirst({
    where: { projectId: input.projectId || null, siteCode: input.siteCode },
  });
  if (existing) throw new ConflictError(`中心编码 ${input.siteCode} 已存在`);

  const site = await prisma.site.create({
    data: {
      ...input,
      status: 'active',
    },
    include: {
      siteStaff: {
        include: { user: { select: { id: true, username: true, displayName: true } } },
      },
    },
  });

  logger.info('Site created', {
    audit: true,
    eventType: 'SITE_CREATE',
    projectId: input.projectId,
    message: `创建中心 ${input.siteCode} - ${input.siteName}`,
  });

  return site;
}

/**
 * 获取中心列表（分页）
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.keyword) {
    where.OR = [
      { siteCode: { contains: query.keyword, mode: 'insensitive' } },
      { siteName: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }
  if (query.status) where.status = query.status;
  if (query.ethicsStatus) where.ethicsStatus = query.ethicsStatus;
  if (query.contractStatus) where.contractStatus = query.contractStatus;

  const [sites, total] = await Promise.all([
    prisma.site.findMany({
      where,
      ...prismaPagination(pagination),
      include: {
        siteStaff: {
          include: { user: { select: { id: true, username: true, displayName: true } } },
        },
        project: { select: { id: true, projectCode: true, projectName: true } },
        _count: { select: { subjects: true, monitoringVisits: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.site.count({ where }),
  ]);

  return buildPaginatedResult(sites, total, pagination);
}

/**
 * 获取中心详情
 */
async function getById(id: string) {
  const site = await prisma.site.findUnique({
    where: { id },
    include: {
      siteStaff: {
        include: { 
          user: { 
            select: { 
              id: true, 
              username: true, 
              displayName: true, 
              email: true, 
              phone: true,
              userRoles: { include: { role: true } }
            } 
          } 
        },
        orderBy: { joinedAt: 'desc' },
      },
      project: { select: { id: true, projectCode: true, projectName: true } },
      _count: { select: { subjects: true, monitoringVisits: true } },
    },
  });

  if (!site) throw new NotFoundError('Site', id);
  return site;
}

/**
 * 更新中心
 */
async function update(id: string, input: UpdateSiteInput) {
  const site = await prisma.site.findUnique({ where: { id } });
  if (!site) throw new NotFoundError('Site', id);

  const updated = await prisma.site.update({
    where: { id },
    data: input,
  });

  logger.info('Site updated', {
    audit: true,
    eventType: 'SITE_UPDATE',
    message: `更新中心 ${site.siteCode}`,
  });

  return updated;
}

/**
 * 删除中心（软删除 → closed）
 */
async function remove(id: string) {
  const site = await prisma.site.findUnique({ where: { id } });
  if (!site) throw new NotFoundError('Site', id);

  await prisma.site.update({
    where: { id },
    data: { status: 'closed' },
  });

  logger.info('Site closed', {
    audit: true,
    eventType: 'SITE_CLOSE',
    message: `关闭中心 ${site.siteCode}`,
  });

  return { message: '中心已关闭' };
}

// ========== 中心人员管理 ==========

/**
 * 添加中心人员
 */
async function addStaff(siteId: string, input: AddSiteStaffInput) {
  const site = await prisma.site.findUnique({ where: { id: siteId } });
  if (!site) throw new NotFoundError('Site', siteId);

  const user = await prisma.user.findUnique({ where: { id: input.userId } });
  if (!user) throw new NotFoundError('User', input.userId);

  // 检查是否已在中心中
  const existing = await prisma.siteStaff.findFirst({
    where: { siteId, userId: input.userId, status: 'active' },
  });
  if (existing) throw new ConflictError('该用户已在此中心中');

  const staff = await prisma.siteStaff.create({
    data: {
      siteId,
      userId: input.userId,
      roleAtSite: input.roleAtSite,
      joinedAt: input.joinedAt ? new Date(input.joinedAt) : new Date(),
      status: 'active',
    },
    include: { user: { select: { id: true, username: true, displayName: true } } },
  });

  logger.info('Site staff added', {
    audit: true,
    eventType: 'SITE_STAFF_ADD',
    message: `为中心 ${site.siteCode} 添加人员 ${user.displayName} (${input.roleAtSite})`,
  });

  return staff;
}

/**
 * 更新中心人员信息
 */
async function updateStaff(siteId: string, staffId: string, input: UpdateSiteStaffInput) {
  const staff = await prisma.siteStaff.findFirst({
    where: { id: staffId, siteId },
  });
  if (!staff) throw new NotFoundError('SiteStaff', staffId);

  const data: any = { ...input };
  if (input.joinedAt) data.joinedAt = new Date(input.joinedAt);
  if (input.leftAt) data.leftAt = new Date(input.leftAt);

  const updated = await prisma.siteStaff.update({
    where: { id: staffId },
    data,
    include: { user: { select: { id: true, username: true, displayName: true } } },
  });

  logger.info('Site staff updated', {
    audit: true,
    eventType: 'SITE_STAFF_UPDATE',
    message: `更新中心人员信息`,
  });

  return updated;
}

/**
 * 移除中心人员
 */
async function removeStaff(siteId: string, staffId: string) {
  const staff = await prisma.siteStaff.findFirst({
    where: { id: staffId, siteId },
  });
  if (!staff) throw new NotFoundError('SiteStaff', staffId);

  await prisma.siteStaff.update({
    where: { id: staffId },
    data: { status: 'inactive', leftAt: new Date() },
  });

  logger.info('Site staff removed', {
    audit: true,
    eventType: 'SITE_STAFF_REMOVE',
    message: `移除中心人员`,
  });

  return { message: '人员已移除' };
}

export const siteService = {
  create, getList, getById, update, remove,
  addStaff, updateStaff, removeStaff,
};
