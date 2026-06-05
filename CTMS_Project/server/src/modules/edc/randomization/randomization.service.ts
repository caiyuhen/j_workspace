// randomization.service.ts - 随机化管理业务逻辑

import prisma from '../../../config/database';
import { AppError, NotFoundError, BadRequestError } from '../../../shared/errors/AppError';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { CreateRandomizationDto, RandomizationQueryDto } from './randomization.dto';
import logger from '../../../shared/utils/logger';

export async function createRecord(data: CreateRandomizationDto, userId: string) {
  // 检查受试者是否存在
  const subject = await prisma.subject.findUnique({ where: { id: data.subjectId } });
  if (!subject) throw new AppError('受试者不存在', 404, 'SUBJECT_NOT_FOUND');

  // 检查该受试者是否已有随机化记录
  const existing = await prisma.edcRandomizationRecord.findUnique({
    where: { subjectId: data.subjectId },
  });
  if (existing) throw new AppError('该受试者已完成随机化', 409, 'ALREADY_RANDOMIZED');

  // 检查随机号是否重复
  const dupNumber = await prisma.edcRandomizationRecord.findUnique({
    where: { randomizationNumber: data.randomizationNumber },
  });
  if (dupNumber) throw new AppError('随机号已被使用', 409, 'DUPLICATE_RANDOMIZATION_NUMBER');

  const record = await prisma.edcRandomizationRecord.create({
    data: {
      subjectId: data.subjectId,
      projectId: data.projectId,
      randomizationNumber: data.randomizationNumber,
      treatmentArm: data.treatmentArm,
      randomizationDate: new Date(data.randomizationDate),
      method: data.method,
      stratifiedFactors: data.stratifiedFactors ?? undefined,
      drugBatch: data.drugBatch,
      drugExpiryDate: data.drugExpiryDate ? new Date(data.drugExpiryDate) : undefined,
      randomizedBy: userId,
    },
    include: {
      subject: { select: { id: true, subjectCode: true } },
      project: { select: { id: true, projectName: true } },
    },
  });

  logger.info('Randomization record created', {
    audit: true,
    eventType: 'RANDOMIZATION_CREATE',
    projectId: data.projectId,
    subjectId: data.subjectId,
    randomizationNumber: data.randomizationNumber,
    treatmentArm: data.treatmentArm,
    message: `受试者 ${subject.subjectCode} 随机化: ${data.randomizationNumber} (${data.treatmentArm || '未分配'})`,
  });

  return record;
}

export async function listRecords(query: RandomizationQueryDto) {
  const pagination = parsePagination(query as Record<string, any>);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.treatmentArm) where.treatmentArm = query.treatmentArm;
  if (query.method) where.method = query.method;

  const [total, items] = await Promise.all([
    prisma.edcRandomizationRecord.count({ where }),
    prisma.edcRandomizationRecord.findMany({
      where,
      ...prismaPagination(pagination),
      orderBy: { createdAt: 'desc' },
      include: {
        subject: { select: { id: true, subjectCode: true } },
        project: { select: { id: true, projectName: true } },
      },
    }),
  ]);

  return buildPaginatedResult(items, total, pagination);
}

export async function getRecordById(id: string) {
  const record = await prisma.edcRandomizationRecord.findUnique({
    where: { id },
    include: {
      subject: { select: { id: true, subjectCode: true } },
      project: { select: { id: true, projectName: true } },
    },
  });
  if (!record) throw new AppError('随机化记录不存在', 404, 'RECORD_NOT_FOUND');
  return record;
}

export async function getRecordBySubject(subjectId: string) {
  const record = await prisma.edcRandomizationRecord.findUnique({
    where: { subjectId },
    include: {
      subject: { select: { id: true, subjectCode: true } },
      project: { select: { id: true, projectName: true } },
    },
  });
  if (!record) throw new AppError('该受试者暂无随机化记录', 404, 'RECORD_NOT_FOUND');
  return record;
}

export async function getRandomizationStats(projectId: string) {
  const [total, byArm, byMethod] = await Promise.all([
    prisma.edcRandomizationRecord.count({ where: { projectId } }),
    prisma.edcRandomizationRecord.groupBy({
      by: ['treatmentArm'],
      where: { projectId },
      _count: { id: true },
    }),
    prisma.edcRandomizationRecord.groupBy({
      by: ['method'],
      where: { projectId },
      _count: { id: true },
    }),
  ]);

  const armBreakdown: Record<string, number> = {};
  for (const row of byArm) {
    armBreakdown[row.treatmentArm ?? 'unknown'] = row._count.id;
  }

  const methodBreakdown: Record<string, number> = {};
  for (const row of byMethod) {
    methodBreakdown[row.method ?? 'unknown'] = row._count.id;
  }

  return { total, byTreatmentArm: armBreakdown, byMethod: methodBreakdown };
}

/** 紧急揭盲 */
export async function emergencyUnblind(subjectId: string, reason: string, userId: string) {
  const record = await prisma.edcRandomizationRecord.findUnique({
    where: { subjectId },
  });
  if (!record) throw new NotFoundError('EdcRandomizationRecord', subjectId);

  logger.warn('Emergency unblinding', {
    audit: true,
    eventType: 'EMERGENCY_UNBLIND',
    subjectId,
    projectId: record.projectId,
    randomizationNumber: record.randomizationNumber,
    treatmentArm: record.treatmentArm,
    message: `紧急揭盲: 受试者 ${subjectId} → ${record.treatmentArm}`,
    details: { reason, unblindedBy: userId },
  });

  return {
    subjectId,
    randomizationNumber: record.randomizationNumber,
    treatmentArm: record.treatmentArm,
    randomizationDate: record.randomizationDate,
    drugBatch: record.drugBatch,
    drugExpiryDate: record.drugExpiryDate,
    method: record.method,
    stratifiedFactors: record.stratifiedFactors,
    unblindedAt: new Date(),
    unblindedBy: userId,
    reason,
  };
}

/** 获取随机号池状态（已用/未用） */
export async function getNumberPoolStatus(projectId: string) {
  const usedNumbers = await prisma.edcRandomizationRecord.findMany({
    where: { projectId },
    select: { randomizationNumber: true, treatmentArm: true, createdAt: true },
    orderBy: { randomizationNumber: 'asc' },
  });

  const usedSet = new Set(usedNumbers.map(n => n.randomizationNumber));

  return {
    projectId,
    totalUsed: usedNumbers.length,
    usedNumbers: usedNumbers.map(n => ({
      number: n.randomizationNumber,
      treatmentArm: n.treatmentArm,
      assignedAt: n.createdAt,
    })),
  };
}

/** 导出随机化清单 */
export async function exportRandomizationList(projectId: string) {
  const records = await prisma.edcRandomizationRecord.findMany({
    where: { projectId },
    orderBy: { randomizationNumber: 'asc' },
    include: {
      subject: { select: { subjectCode: true, enrollmentStatus: true } },
    },
  });

  return {
    projectId,
    generatedAt: new Date().toISOString(),
    total: records.length,
    records: records.map(r => ({
      randomizationNumber: r.randomizationNumber,
      subjectCode: r.subject.subjectCode,
      treatmentArm: r.treatmentArm,
      randomizationDate: r.randomizationDate,
      method: r.method,
      stratifiedFactors: r.stratifiedFactors,
      drugBatch: r.drugBatch,
      drugExpiryDate: r.drugExpiryDate,
      enrollmentStatus: r.subject.enrollmentStatus,
    })),
  };
}
