import prisma from '../../../config/database';
import { CreateEthicsInput, UpdateEthicsInput } from './ethics.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['ethicsCommittee', 'approvalType', 'approvalStatus', 'submissionDate', 'createdAt'];

/** 伦理审批状态流转定义 */
const STATUS_TRANSITIONS: Record<string, string[]> = {
  pending: ['under_review', 'withdrawn'],
  under_review: ['approved', 'conditionally_approved', 'rejected', 'pending'],
  approved: ['under_review'],
  conditionally_approved: ['approved', 'rejected', 'under_review'],
  rejected: ['pending'],
  withdrawn: ['pending'],
};

async function create(input: CreateEthicsInput, userId: string) {
  const ethics = await prisma.ethicsApproval.create({
    data: {
      ...input,
      submissionDate: input.submissionDate ? new Date(input.submissionDate) : null,
      approvalDate: input.approvalDate ? new Date(input.approvalDate) : null,
      expiryDate: input.expiryDate ? new Date(input.expiryDate) : null,
      approvalStatus: input.approvalStatus || 'pending',
      createdBy: userId,
    },
  });

  logger.info('Ethics approval created', {
    audit: true,
    eventType: 'ETHICS_CREATE',
    projectId: input.projectId,
    message: `创建伦理审批 ${ethics.ethicsCommittee}`,
  });

  return ethics;
}

async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'createdAt', 'desc');

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.siteId) where.siteId = query.siteId;
  if (query.approvalType) where.approvalType = query.approvalType;
  if (query.approvalStatus) where.approvalStatus = query.approvalStatus;

  const [items, total] = await Promise.all([
    prisma.ethicsApproval.findMany({
      where, ...prismaPagination(pagination),
      orderBy: sort.orderBy,
    }),
    prisma.ethicsApproval.count({ where }),
  ]);

  return buildPaginatedResult(items, total, pagination);
}

async function getById(id: string) {
  const ethics = await prisma.ethicsApproval.findUnique({
    where: { id },
    include: { project: { select: { id: true, projectCode: true, projectName: true } } },
  });
  if (!ethics) throw new NotFoundError('EthicsApproval', id);
  return ethics;
}

async function update(id: string, input: UpdateEthicsInput) {
  const ethics = await prisma.ethicsApproval.findUnique({ where: { id } });
  if (!ethics) throw new NotFoundError('EthicsApproval', id);

  const data: any = { ...input };
  if (input.submissionDate) data.submissionDate = new Date(input.submissionDate);
  if (input.approvalDate) data.approvalDate = new Date(input.approvalDate);
  if (input.expiryDate) data.expiryDate = new Date(input.expiryDate);

  const updated = await prisma.ethicsApproval.update({ where: { id }, data: data });

  logger.info('Ethics approval updated', { audit: true, eventType: 'ETHICS_UPDATE', ethicsId: id });
  return updated;
}

/** 伦理审批状态流转 */
async function transitionStatus(id: string, newStatus: string, userId: string, comment?: string) {
  const ethics = await prisma.ethicsApproval.findUnique({ where: { id } });
  if (!ethics) throw new NotFoundError('EthicsApproval', id);

  const allowed = STATUS_TRANSITIONS[ethics.approvalStatus];
  if (!allowed || !allowed.includes(newStatus)) {
    throw new BadRequestError(
      `不允许从 ${ethics.approvalStatus} 变更为 ${newStatus}，允许的状态为: ${allowed?.join(', ')}`
    );
  }

  const updated = await prisma.ethicsApproval.update({
    where: { id },
    data: {
      approvalStatus: newStatus,
      approvalDate: newStatus === 'approved' ? new Date() : ethics.approvalDate,
    },
  });

  logger.info('Ethics status transition', {
    audit: true,
    eventType: 'ETHICS_STATUS_CHANGE',
    ethicsId: id,
    message: `伦理审批 ${ethics.ethicsCommittee}: ${ethics.approvalStatus} → ${newStatus}`,
    details: { comment },
  });

  return updated;
}

/** 伦理到期预警 */
async function getExpiringSoon(days: number = 60) {
  const now = new Date();
  const threshold = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);

  return prisma.ethicsApproval.findMany({
    where: {
      approvalStatus: 'approved',
      expiryDate: { lte: threshold, gte: now },
    },
    include: {
      project: { select: { projectCode: true, projectName: true } },
      site: { select: { siteCode: true, siteName: true } },
    },
    orderBy: { expiryDate: 'asc' },
  });
}

/** 获取伦理审批统计 */
async function getStats(projectId?: string) {
  const where: any = {};
  if (projectId) where.projectId = projectId;

  const [total, byStatus, byType] = await Promise.all([
    prisma.ethicsApproval.count({ where }),
    prisma.ethicsApproval.groupBy({
      by: ['approvalStatus'],
      where,
      _count: true,
    }),
    prisma.ethicsApproval.groupBy({
      by: ['approvalType'],
      where,
      _count: true,
    }),
  ]);

  return {
    total,
    byStatus: byStatus.map(s => ({ status: s.approvalStatus, count: s._count })),
    byType: byType.map(t => ({ type: t.approvalType, count: t._count })),
  };
}

/** 获取项目伦理审批时间线 */
async function getTimeline(projectId: string) {
  const records = await prisma.ethicsApproval.findMany({
    where: { projectId },
    orderBy: { createdAt: 'asc' },
    include: {
      site: { select: { siteCode: true, siteName: true } },
    },
  });

  return records.map(r => ({
    id: r.id,
    ethicsCommittee: r.ethicsCommittee,
    approvalType: r.approvalType,
    approvalStatus: r.approvalStatus,
    submissionDate: r.submissionDate,
    approvalDate: r.approvalDate,
    expiryDate: r.expiryDate,
    approvalNumber: r.approvalNumber,
    site: r.site,
    createdAt: r.createdAt,
  }));
}

export const ethicsService = {
  create, getList, getById, update, transitionStatus,
  getExpiringSoon, getStats, getTimeline,
};
