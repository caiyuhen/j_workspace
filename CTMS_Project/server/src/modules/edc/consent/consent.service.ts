import prisma from '../../../config/database';
import { CreateConsentInput, UpdateConsentInput } from './consent.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['consentDate', 'signeeName', 'status', 'createdAt'];

async function create(input: CreateConsentInput) {
  // 检查是否有之前的同意记录需要标记为 reconsented
  const existing = await prisma.consentRecord.findFirst({
    where: {
      projectId: input.projectId,
      siteId: input.siteId,
      subjectId: input.subjectId,
      status: 'active',
    },
  });

  if (existing && existing.consentVersion !== input.consentVersion) {
    await prisma.consentRecord.update({
      where: { id: existing.id },
      data: { status: 'reconsented' },
    });
  }

  const consent = await prisma.consentRecord.create({
    data: {
      ...input,
      consentDate: new Date(input.consentDate),
      status: 'active',
    },
  });

  logger.info('Consent record created', {
    audit: true,
    eventType: 'CONSENT_CREATE',
    projectId: input.projectId,
    subjectId: input.subjectId,
    message: `知情同意签署: ${input.signeeName} (${input.consentVersion})`,
  });

  return consent;
}

async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'consentDate', 'desc');

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.siteId) where.siteId = query.siteId;
  if (query.subjectId) where.subjectId = query.subjectId;
  if (query.status) where.status = query.status;
  if (query.consentVersion) where.consentVersion = query.consentVersion;

  const [items, total] = await Promise.all([
    prisma.consentRecord.findMany({ where, ...prismaPagination(pagination), orderBy: sort.orderBy }),
    prisma.consentRecord.count({ where }),
  ]);

  return buildPaginatedResult(items, total, pagination);
}

async function getById(id: string) {
  const consent = await prisma.consentRecord.findUnique({ where: { id } });
  if (!consent) throw new NotFoundError('ConsentRecord', id);
  return consent;
}

async function update(id: string, input: UpdateConsentInput) {
  const consent = await prisma.consentRecord.findUnique({ where: { id } });
  if (!consent) throw new NotFoundError('ConsentRecord', id);

  const data: any = { ...input };
  if (input.consentDate) data.consentDate = new Date(input.consentDate);

  const updated = await prisma.consentRecord.update({ where: { id }, data });
  logger.info('Consent record updated', { audit: true, eventType: 'CONSENT_UPDATE', consentId: id });
  return updated;
}

/** 获取受试者的完整知情同意历史 */
async function getSubjectHistory(projectId: string, siteId: string, subjectId: string) {
  return prisma.consentRecord.findMany({
    where: { projectId, siteId, subjectId },
    orderBy: { consentDate: 'asc' },
  });
}

/** 撤回知情同意 */
async function withdraw(id: string, reason: string, userId: string) {
  const consent = await prisma.consentRecord.findUnique({ where: { id } });
  if (!consent) throw new NotFoundError('ConsentRecord', id);
  if (consent.status !== 'active') {
    throw new BadRequestError('只能撤回状态为 active 的知情同意记录');
  }

  const updated = await prisma.consentRecord.update({
    where: { id },
    data: { status: 'withdrawn' },
  });

  // 同步更新受试者入组状态
  await prisma.subject.updateMany({
    where: {
      id: consent.subjectId,
      enrollmentStatus: { in: ['screening', 'enrolled'] },
    },
    data: {
      enrollmentStatus: 'discontinued',
      discontinuationReason: `知情同意撤回: ${reason}`,
      discontinuedAt: new Date(),
    },
  });

  logger.info('Consent withdrawn', {
    audit: true,
    eventType: 'CONSENT_WITHDRAW',
    consentId: id,
    subjectId: consent.subjectId,
    message: `受试者 ${consent.subjectId} 知情同意撤回: ${reason}`,
    details: { withdrawnBy: userId },
  });

  return updated;
}

/** 知情同意版本统计 */
async function getConsentStats(projectId?: string) {
  const where: any = {};
  if (projectId) where.projectId = projectId;

  const [total, active, byVersion, byStatus] = await Promise.all([
    prisma.consentRecord.count({ where }),
    prisma.consentRecord.count({ where: { ...where, status: 'active' } }),
    prisma.consentRecord.groupBy({ by: ['consentVersion'], where, _count: true }),
    prisma.consentRecord.groupBy({ by: ['status'], where, _count: true }),
  ]);

  return {
    total,
    active,
    byVersion: byVersion.map(v => ({ version: v.consentVersion, count: v._count })),
    byStatus: byStatus.map(s => ({ status: s.status, count: s._count })),
  };
}

/** 获取项目的知情同意版本列表 */
async function getVersions(projectId: string) {
  const records = await prisma.consentRecord.findMany({
    where: { projectId },
    select: { consentVersion: true },
    distinct: ['consentVersion'],
    orderBy: { consentVersion: 'desc' },
  });

  return records.map(r => r.consentVersion);
}

export const consentService = {
  create, getList, getById, update, getSubjectHistory,
  withdraw, getConsentStats, getVersions,
};
