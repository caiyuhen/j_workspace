import prisma from '../../../config/database';
import { CreateSubjectInput, UpdateSubjectInput } from './subject.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, ConflictError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['subjectCode', 'screeningNumber', 'enrollmentStatus', 'enrolledAt', 'createdAt'];

/**
 * 登记受试者
 */
async function create(input: CreateSubjectInput, userId: string) {
  const project = await prisma.project.findUnique({ where: { id: input.projectId } });
  if (!project) throw new NotFoundError('Project', input.projectId);

  const existing = await prisma.subject.findFirst({
    where: { projectId: input.projectId, subjectCode: input.subjectCode },
  });
  if (existing) throw new ConflictError(`受试者编号 ${input.subjectCode} 在该项目中已存在`);

  if (input.screeningNumber) {
    const existingScreening = await prisma.subject.findFirst({
      where: { projectId: input.projectId, screeningNumber: input.screeningNumber },
    });
    if (existingScreening) throw new ConflictError(`筛选号 ${input.screeningNumber} 已存在`);
  }

  const subject = await prisma.subject.create({
    data: {
      ...input,
      enrolledAt: input.enrollmentStatus !== 'screening' ? new Date() : null,
    },
  });

  logger.info('Subject created', {
    audit: true,
    eventType: 'SUBJECT_CREATE',
    projectId: input.projectId,
    message: `登记受试者 ${input.subjectCode}`,
  });

  return subject;
}

/**
 * 获取受试者列表
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.siteId) where.siteId = query.siteId;
  if (query.enrollmentStatus) where.enrollmentStatus = query.enrollmentStatus;
  if (query.keyword) {
    where.OR = [
      { subjectCode: { contains: query.keyword, mode: 'insensitive' } },
      { screeningNumber: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }

  const [subjects, total] = await Promise.all([
    prisma.subject.findMany({
      where, ...prismaPagination(pagination),
      include: {
        site: { select: { id: true, siteCode: true, siteName: true } },
        project: { select: { id: true, projectCode: true, projectName: true } },
        visits: {
          select: { id: true, visitCode: true, visitName: true, isSDVCompleted: true, plannedDate: true },
          orderBy: { plannedDate: 'asc' },
        },
        _count: { select: { crfData: true, queries: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.subject.count({ where }),
  ]);

  return buildPaginatedResult(subjects, total, pagination);
}

/**
 * 获取受试者详情
 */
async function getById(id: string) {
  const subject = await prisma.subject.findUnique({
    where: { id },
    include: {
      site: { select: { id: true, siteCode: true, siteName: true } },
      project: { select: { id: true, projectCode: true, projectName: true } },
      visits: { orderBy: { plannedDate: 'asc' } },
      crfData: { take: 100 },
      queries: { orderBy: { createdAt: 'desc' }, take: 50 },
    },
  });

  if (!subject) throw new NotFoundError('Subject', id);
  return subject;
}

/**
 * 更新受试者信息
 */
async function update(id: string, input: UpdateSubjectInput) {
  const subject = await prisma.subject.findUnique({ where: { id } });
  if (!subject) throw new NotFoundError('Subject', id);

  const data: any = { ...input };

  // 入组时自动设置 enrolledAt
  if (input.enrollmentStatus && ['enrolled', 'randomized'].includes(input.enrollmentStatus) && !subject.enrolledAt) {
    data.enrolledAt = new Date();
  }

  // 退组时记录时间
  if (input.enrollmentStatus === 'discontinued' || input.enrollmentStatus === 'withdrawn') {
    data.discontinuedAt = new Date();
  }

  const updated = await prisma.subject.update({ where: { id }, data });

  logger.info('Subject updated', {
    audit: true,
    eventType: 'SUBJECT_UPDATE',
    message: `更新受试者 ${subject.subjectCode} 状态为 ${input.enrollmentStatus || '不变'}`,
  });

  return updated;
}

/**
 * 创建访视
 */
async function createVisit(subjectId: string, data: {
  visitCode: string;
  visitName: string;
  plannedDate: string;
  siteId?: string;
}) {
  const subject = await prisma.subject.findUnique({ where: { id: subjectId } });
  if (!subject) throw new NotFoundError('Subject', subjectId);

  const visit = await prisma.visit.create({
    data: {
      projectId: subject.projectId,
      subjectId,
      siteId: data.siteId || subject.siteId,
      visitCode: data.visitCode,
      visitName: data.visitName,
      plannedDate: new Date(data.plannedDate),
    },
  });

  return visit;
}

/**
 * 获取受试者的访视列表
 */
async function getVisits(subjectId: string) {
  const subject = await prisma.subject.findUnique({ where: { id: subjectId } });
  if (!subject) throw new NotFoundError('Subject', subjectId);

  return prisma.visit.findMany({
    where: { subjectId },
    orderBy: { plannedDate: 'asc' },
  });
}

export const subjectService = {
  create, getList, getById, update, createVisit, getVisits,
};
