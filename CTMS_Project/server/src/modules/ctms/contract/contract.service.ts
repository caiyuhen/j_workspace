import prisma from '../../../config/database';
import { CreateContractInput, UpdateContractInput } from './contract.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, ConflictError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['contractCode', 'contractName', 'contractType', 'signStatus', 'createdAt'];

/** 合同状态流转 */
const STATUS_TRANSITIONS: Record<string, string[]> = {
  draft: ['pending_sign', 'terminated'],
  pending_sign: ['signed', 'draft', 'terminated'],
  signed: ['expired', 'terminated'],
  expired: [],
  terminated: [],
};

async function create(input: CreateContractInput, userId: string) {
  const existing = await prisma.contract.findUnique({ where: { contractCode: input.contractCode } });
  if (existing) throw new ConflictError(`合同编码 ${input.contractCode} 已存在`);

  const contract = await prisma.contract.create({
    data: {
      ...input,
      startDate: input.startDate ? new Date(input.startDate) : null,
      endDate: input.endDate ? new Date(input.endDate) : null,
      signStatus: 'draft',
      createdBy: userId,
    },
    include: { vendor: { select: { id: true, vendorName: true } } },
  });

  logger.info('Contract created', { audit: true, eventType: 'CONTRACT_CREATE', contractId: contract.id, message: `创建合同 ${contract.contractCode}` });
  return contract;
}

async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'contractCode', 'asc');

  const where: any = {};
  if (query.keyword) {
    where.OR = [
      { contractCode: { contains: query.keyword, mode: 'insensitive' } },
      { contractName: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }
  if (query.contractType) where.contractType = query.contractType;
  if (query.signStatus) where.signStatus = query.signStatus;
  if (query.projectId) where.projectId = query.projectId;
  if (query.vendorId) where.vendorId = query.vendorId;

  const [contracts, total] = await Promise.all([
    prisma.contract.findMany({
      where, ...prismaPagination(pagination),
      include: { vendor: { select: { id: true, vendorName: true } } },
      orderBy: sort.orderBy,
    }),
    prisma.contract.count({ where }),
  ]);

  return buildPaginatedResult(contracts, total, pagination);
}

async function getById(id: string) {
  const contract = await prisma.contract.findUnique({
    where: { id },
    include: { vendor: true },
  });
  if (!contract) throw new NotFoundError('Contract', id);
  return contract;
}

async function update(id: string, input: UpdateContractInput) {
  const contract = await prisma.contract.findUnique({ where: { id } });
  if (!contract) throw new NotFoundError('Contract', id);

  if (input.contractCode && input.contractCode !== contract.contractCode) {
    const existing = await prisma.contract.findUnique({ where: { contractCode: input.contractCode } });
    if (existing) throw new ConflictError(`合同编码 ${input.contractCode} 已存在`);
  }

  const data: any = { ...input };
  if (input.startDate) data.startDate = new Date(input.startDate);
  if (input.endDate) data.endDate = new Date(input.endDate);

  const updated = await prisma.contract.update({ where: { id }, data });
  logger.info('Contract updated', { audit: true, eventType: 'CONTRACT_UPDATE', contractId: id });
  return updated;
}

async function remove(id: string) {
  const contract = await prisma.contract.findUnique({ where: { id } });
  if (!contract) throw new NotFoundError('Contract', id);

  await prisma.contract.update({ where: { id }, data: { signStatus: 'terminated' } });
  logger.info('Contract terminated', { audit: true, eventType: 'CONTRACT_DELETE', contractId: id });
  return { message: '合同已终止' };
}

/** 合同状态流转 */
async function transitionStatus(id: string, newStatus: string, userId: string) {
  const contract = await prisma.contract.findUnique({ where: { id } });
  if (!contract) throw new NotFoundError('Contract', id);

  const allowed = STATUS_TRANSITIONS[contract.signStatus];
  if (!allowed || !allowed.includes(newStatus)) {
    throw new BadRequestError(
      `不允许从 ${contract.signStatus} 变更为 ${newStatus}`
    );
  }

  const updated = await prisma.contract.update({
    where: { id },
    data: { signStatus: newStatus },
  });

  logger.info('Contract status transition', {
    audit: true,
    eventType: 'CONTRACT_STATUS_CHANGE',
    contractId: id,
    message: `合同 ${contract.contractCode}: ${contract.signStatus} → ${newStatus}`,
  });

  return updated;
}

/** 合同到期预警 */
async function getExpiringSoon(days: number = 30) {
  const now = new Date();
  const threshold = new Date(now.getTime() + days * 24 * 60 * 60 * 1000);

  return prisma.contract.findMany({
    where: {
      signStatus: 'signed',
      endDate: { lte: threshold, gte: now },
    },
    include: { vendor: { select: { id: true, vendorName: true } } },
    orderBy: { endDate: 'asc' },
  });
}

/** 合同统计 */
async function getStats(projectId?: string) {
  const where: any = {};
  if (projectId) where.projectId = projectId;

  const [total, byStatus, byType, totalAmount] = await Promise.all([
    prisma.contract.count({ where }),
    prisma.contract.groupBy({ by: ['signStatus'], where, _count: true }),
    prisma.contract.groupBy({ by: ['contractType'], where, _count: true }),
    prisma.contract.aggregate({
      _sum: { amount: true },
      where,
    }),
  ]);

  return {
    total,
    totalAmount: totalAmount._sum.amount || 0,
    byStatus: byStatus.map(s => ({ status: s.signStatus, count: s._count })),
    byType: byType.map(t => ({ type: t.contractType, count: t._count })),
  };
}

export const contractService = {
  create, getList, getById, update, remove,
  transitionStatus, getExpiringSoon, getStats,
};
