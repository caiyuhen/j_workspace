import prisma from '../../../config/database';
import { CreateVendorInput, UpdateVendorInput } from './vendor.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, ConflictError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['vendorCode', 'vendorName', 'vendorType', 'rating', 'status', 'createdAt'];

async function create(input: CreateVendorInput, userId: string) {
  const existing = await prisma.vendor.findUnique({ where: { vendorCode: input.vendorCode } });
  if (existing) throw new ConflictError(`供应商编码 ${input.vendorCode} 已存在`);

  const vendor = await prisma.vendor.create({
    data: { ...input, status: 'active', createdBy: userId },
  });

  logger.info('Vendor created', { audit: true, eventType: 'VENDOR_CREATE', vendorId: vendor.id, message: `创建供应商 ${vendor.vendorCode}` });
  return vendor;
}

async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'vendorCode', 'asc');

  const where: any = {};
  if (query.keyword) {
    where.OR = [
      { vendorCode: { contains: query.keyword, mode: 'insensitive' } },
      { vendorName: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }
  if (query.vendorType) where.vendorType = query.vendorType;
  if (query.status) where.status = query.status;

  const [vendors, total] = await Promise.all([
    prisma.vendor.findMany({
      where, ...prismaPagination(pagination),
      include: { _count: { select: { contracts: true } } },
      orderBy: sort.orderBy,
    }),
    prisma.vendor.count({ where }),
  ]);

  return buildPaginatedResult(vendors, total, pagination);
}

async function getById(id: string) {
  const vendor = await prisma.vendor.findUnique({
    where: { id },
    include: { contracts: { orderBy: { createdAt: 'desc' } } },
  });
  if (!vendor) throw new NotFoundError('Vendor', id);
  return vendor;
}

async function update(id: string, input: UpdateVendorInput) {
  const vendor = await prisma.vendor.findUnique({ where: { id } });
  if (!vendor) throw new NotFoundError('Vendor', id);

  if (input.vendorCode && input.vendorCode !== vendor.vendorCode) {
    const existing = await prisma.vendor.findUnique({ where: { vendorCode: input.vendorCode } });
    if (existing) throw new ConflictError(`供应商编码 ${input.vendorCode} 已存在`);
  }

  const updated = await prisma.vendor.update({ where: { id }, data: input });
  logger.info('Vendor updated', { audit: true, eventType: 'VENDOR_UPDATE', vendorId: id });
  return updated;
}

async function remove(id: string) {
  const vendor = await prisma.vendor.findUnique({ where: { id } });
  if (!vendor) throw new NotFoundError('Vendor', id);

  await prisma.vendor.update({ where: { id }, data: { status: 'inactive' } });
  logger.info('Vendor deactivated', { audit: true, eventType: 'VENDOR_DELETE', vendorId: id });
  return { message: '供应商已停用' };
}

/** 更新供应商评分 */
async function updateRating(id: string, score: number, comment?: string) {
  const vendor = await prisma.vendor.findUnique({ where: { id } });
  if (!vendor) throw new NotFoundError('Vendor', id);
  if (score < 0 || score > 5) throw new BadRequestError('评分必须在 0-5 之间');

  const updated = await prisma.vendor.update({
    where: { id },
    data: { rating: score },
  });

  logger.info('Vendor rating updated', {
    audit: true,
    eventType: 'VENDOR_RATING_UPDATE',
    vendorId: id,
    message: `供应商 ${vendor.vendorName} 评分更新: ${vendor.rating} → ${score}`,
    details: { comment },
  });

  return updated;
}

/** 加入/移出黑名单 */
async function toggleBlacklist(id: string, reason?: string) {
  const vendor = await prisma.vendor.findUnique({ where: { id } });
  if (!vendor) throw new NotFoundError('Vendor', id);

  const newStatus = vendor.status === 'blacklisted' ? 'active' : 'blacklisted';

  const updated = await prisma.vendor.update({
    where: { id },
    data: { status: newStatus },
  });

  logger.info('Vendor blacklist toggled', {
    audit: true,
    eventType: newStatus === 'blacklisted' ? 'VENDOR_BLACKLIST' : 'VENDOR_UNBLACKLIST',
    vendorId: id,
    message: `供应商 ${vendor.vendorName} ${newStatus === 'blacklisted' ? '加入' : '移出'}黑名单`,
    details: { reason },
  });

  return updated;
}

/** 供应商统计 */
async function getStats() {
  const [total, active, byType, blacklisted] = await Promise.all([
    prisma.vendor.count(),
    prisma.vendor.count({ where: { status: 'active' } }),
    prisma.vendor.groupBy({ by: ['vendorType'], _count: true }),
    prisma.vendor.count({ where: { status: 'blacklisted' } }),
  ]);

  // 平均评分
  const avgRating = await prisma.vendor.aggregate({
    _avg: { rating: true },
    where: { rating: { not: null } },
  });

  return {
    total,
    active,
    blacklisted,
    byType: byType.map(t => ({ type: t.vendorType, count: t._count })),
    averageRating: avgRating._avg.rating?.toFixed(1) || 'N/A',
  };
}

/** 获取供应商的合同统计 */
async function getContractStats(vendorId: string) {
  const vendor = await prisma.vendor.findUnique({ where: { id: vendorId } });
  if (!vendor) throw new NotFoundError('Vendor', vendorId);

  const contracts = await prisma.contract.findMany({
    where: { vendorId },
    select: { id: true, contractCode: true, contractName: true, signStatus: true, amount: true },
  });

  const totalAmount = contracts.reduce((sum, c) => sum + (c.amount || 0), 0);
  const byStatus = contracts.reduce((acc, c) => {
    acc[c.signStatus] = (acc[c.signStatus] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return {
    vendorId,
    totalContracts: contracts.length,
    totalAmount,
    byStatus,
    contracts,
  };
}

export const vendorService = {
  create, getList, getById, update, remove,
  updateRating, toggleBlacklist, getStats, getContractStats,
};
