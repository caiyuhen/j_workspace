// lock.service.ts - 数据锁定业务逻辑

import prisma from '../../../config/database';
import { AppError } from '../../../shared/errors/AppError';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { CreateLockDto, UnlockDto, LockQueryDto } from './lock.dto';

const VALID_LOCK_TYPES = ['subject', 'visit', 'project', 'form'];

export async function createLock(data: CreateLockDto, userId: string) {
  if (!VALID_LOCK_TYPES.includes(data.lockType)) {
    throw new AppError(`无效的锁定类型，允许值：${VALID_LOCK_TYPES.join(', ')}`, 400, 'INVALID_LOCK_TYPE');
  }

  // 检查是否已存在该目标的有效锁
  const existingLock = await prisma.edcLockRecord.findFirst({
    where: {
      targetId: data.targetId,
      lockType: data.lockType,
      status: 'locked',
    },
  });
  if (existingLock) {
    throw new AppError('该数据已处于锁定状态', 409, 'ALREADY_LOCKED');
  }

  const lock = await prisma.edcLockRecord.create({
    data: {
      projectId: data.projectId,
      lockType: data.lockType,
      targetId: data.targetId,
      lockReason: data.lockReason,
      lockedBy: userId,
      status: 'locked',
      esigRecords: data.esigRecords ?? undefined,
    },
    include: {
      project: { select: { id: true, projectName: true } },
    },
  });
  return lock;
}

export async function listLocks(query: LockQueryDto) {
  const pagination = parsePagination(query as Record<string, any>);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.lockType) where.lockType = query.lockType;
  if (query.status) where.status = query.status;

  const [total, items] = await Promise.all([
    prisma.edcLockRecord.count({ where }),
    prisma.edcLockRecord.findMany({
      where,
      ...prismaPagination(pagination),
      orderBy: { lockedAt: 'desc' },
      include: {
        project: { select: { id: true, projectName: true } },
      },
    }),
  ]);

  return buildPaginatedResult(items, total, pagination);
}

export async function getLockById(id: string) {
  const lock = await prisma.edcLockRecord.findUnique({
    where: { id },
    include: {
      project: { select: { id: true, projectName: true } },
    },
  });
  if (!lock) throw new AppError('锁定记录不存在', 404, 'LOCK_NOT_FOUND');
  return lock;
}

export async function checkLockStatus(lockType: string, targetId: string) {
  const lock = await prisma.edcLockRecord.findFirst({
    where: {
      targetId,
      lockType,
      status: 'locked',
    },
  });

  return {
    isLocked: !!lock,
    lockRecord: lock ?? null,
  };
}

export async function unlockRecord(id: string, data: UnlockDto, userId: string) {
  const lock = await prisma.edcLockRecord.findUnique({ where: { id } });
  if (!lock) throw new AppError('锁定记录不存在', 404, 'LOCK_NOT_FOUND');
  if (lock.status !== 'locked') throw new AppError('该记录当前未处于锁定状态', 400, 'NOT_LOCKED');

  return prisma.edcLockRecord.update({
    where: { id },
    data: {
      status: 'unlocked',
      unlockApprovedBy: data.unlockApprovedBy ?? userId,
      unlockAt: new Date(),
    },
    include: {
      project: { select: { id: true, projectName: true } },
    },
  });
}

export async function getLockStats(projectId: string) {
  const [total, byStatus, byType] = await Promise.all([
    prisma.edcLockRecord.count({ where: { projectId } }),
    prisma.edcLockRecord.groupBy({
      by: ['status'],
      where: { projectId },
      _count: { id: true },
    }),
    prisma.edcLockRecord.groupBy({
      by: ['lockType'],
      where: { projectId },
      _count: { id: true },
    }),
  ]);

  const statusBreakdown: Record<string, number> = {};
  for (const row of byStatus) {
    statusBreakdown[row.status] = row._count.id;
  }

  const typeBreakdown: Record<string, number> = {};
  for (const row of byType) {
    typeBreakdown[row.lockType] = row._count.id;
  }

  return { total, byStatus: statusBreakdown, byType: typeBreakdown };
}
