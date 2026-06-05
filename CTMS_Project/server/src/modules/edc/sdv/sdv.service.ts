import prisma from '../../../config/database';
import {
  CreateSdvRecordInput, UpdateSdvRecordInput,
  CreateSdvItemInput, UpdateSdvItemInput, CompleteSdvInput,
} from './sdv.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['sdvDate', 'percentage', 'status', 'createdAt', 'updatedAt'];

/**
 * 创建 SDV 记录
 */
async function create(input: CreateSdvRecordInput, userId: string) {
  const project = await prisma.project.findUnique({ where: { id: input.projectId } });
  if (!project) throw new NotFoundError('Project', input.projectId);

  const record = await prisma.sdvRecord.create({
    data: {
      ...input,
      craUserId: userId,
      sdvDate: new Date(input.sdvDate),
      status: 'in_progress',
    },
  });

  logger.info('SDV record created', {
    audit: true, eventType: 'SDV_CREATE', projectId: input.projectId,
    message: `创建SDV记录: 受试者 ${input.subjectId}`,
  });

  return record;
}

/**
 * 获取 SDV 记录列表
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.siteId) where.siteId = query.siteId;
  if (query.subjectId) where.subjectId = query.subjectId;
  if (query.craUserId) where.craUserId = query.craUserId;
  if (query.status) where.status = query.status;
  if (query.monitoringVisitId) where.monitoringVisitId = query.monitoringVisitId;

  const [records, total] = await Promise.all([
    prisma.sdvRecord.findMany({
      where, ...prismaPagination(pagination),
      include: {
        items: true,
        _count: { select: { items: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.sdvRecord.count({ where }),
  ]);

  return buildPaginatedResult(records, total, pagination);
}

/**
 * 获取 SDV 记录详情
 */
async function getById(id: string) {
  const record = await prisma.sdvRecord.findUnique({
    where: { id },
    include: {
      items: { orderBy: { createdAt: 'asc' } },
    },
  });

  if (!record) throw new NotFoundError('SdvRecord', id);
  return record;
}

/**
 * 更新 SDV 记录
 */
async function updateRecord(id: string, input: UpdateSdvRecordInput) {
  const record = await prisma.sdvRecord.findUnique({ where: { id } });
  if (!record) throw new NotFoundError('SdvRecord', id);
  if (record.status === 'completed') throw new BadRequestError('已完成的SDV记录不能修改');

  return prisma.sdvRecord.update({
    where: { id },
    data: input,
  });
}

/**
 * 添加 SDV 核查项
 */
async function addItems(recordId: string, items: CreateSdvItemInput[], userId: string) {
  const record = await prisma.sdvRecord.findUnique({ where: { id: recordId } });
  if (!record) throw new NotFoundError('SdvRecord', recordId);
  if (record.status === 'completed') throw new BadRequestError('已完成的SDV记录不能添加核查项');

  const createdItems = await prisma.sdvItem.createMany({
    data: items.map(item => ({ sdvRecordId: recordId, ...item })),
  });

  // 重新计算完成率
  await recalculatePercentage(recordId);

  logger.info('SDV items added', {
    audit: true, eventType: 'SDV_ITEM_ADD',
    message: `添加 ${items.length} 个SDV核查项`,
  });

  return { createdCount: createdItems.count };
}

/**
 * 更新 SDV 核查项
 */
async function updateItem(recordId: string, itemId: string, input: UpdateSdvItemInput) {
  const item = await prisma.sdvItem.findFirst({ where: { id: itemId, sdvRecordId: recordId } });
  if (!item) throw new NotFoundError('SdvItem', itemId);

  const updated = await prisma.sdvItem.update({
    where: { id: itemId },
    data: input,
  });

  // 重新计算完成率
  await recalculatePercentage(recordId);

  return updated;
}

/**
 * 批量更新 SDV 核查项
 */
async function batchUpdateItems(recordId: string, updates: { itemId: string; data: UpdateSdvItemInput }[]) {
  const record = await prisma.sdvRecord.findUnique({ where: { id: recordId } });
  if (!record) throw new NotFoundError('SdvRecord', recordId);

  const results = await Promise.all(
    updates.map(({ itemId, data }) =>
      prisma.sdvItem.updateMany({
        where: { id: itemId, sdvRecordId: recordId },
        data,
      })
    )
  );

  await recalculatePercentage(recordId);

  return { updatedCount: results.reduce((sum: number, r: any) => sum + r.count, 0) };
}

/**
 * 完成 SDV 记录
 */
async function complete(id: string, input: CompleteSdvInput, userId: string) {
  const record = await prisma.sdvRecord.findUnique({
    where: { id },
    include: { items: true },
  });
  if (!record) throw new NotFoundError('SdvRecord', id);
  if (record.status === 'completed') throw new BadRequestError('SDV记录已完成');

  const updated = await prisma.sdvRecord.update({
    where: { id },
    data: {
      status: 'completed',
      completedAt: new Date(),
      notes: input.notes || record.notes,
    },
  });

  logger.info('SDV record completed', {
    audit: true, eventType: 'SDV_COMPLETE', projectId: record.projectId,
    message: `完成SDV核查: 完成率 ${record.percentage}%`,
  });

  return updated;
}

/**
 * SDV 统计
 */
async function getStatistics(query: Record<string, any>) {
  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.siteId) where.siteId = query.siteId;

  const [totalRecords, completedRecords, inProgressRecords] = await Promise.all([
    prisma.sdvRecord.count({ where }),
    prisma.sdvRecord.count({ where: { ...where, status: 'completed' } }),
    prisma.sdvRecord.count({ where: { ...where, status: 'in_progress' } }),
  ]);

  // 平均完成率
  const avgResult = await prisma.sdvRecord.aggregate({
    where,
    _avg: { percentage: true },
  });

  // 差异统计
  const discrepancyStats = await prisma.sdvItem.groupBy({
    by: ['discrepancyType'],
    where: {
      sdvRecord: { ...where },
      discrepancyType: { not: null },
    },
    _count: true,
  });

  return {
    totalRecords,
    completedRecords,
    inProgressRecords,
    averagePercentage: avgResult._avg.percentage || 0,
    discrepancyBreakdown: discrepancyStats,
  };
}

/**
 * 重新计算 SDV 完成率
 */
async function recalculatePercentage(recordId: string) {
  const items = await prisma.sdvItem.findMany({
    where: { sdvRecordId: recordId },
  });

  const totalItems = items.length;
  const verifiedItems = items.filter((i: any) => i.isVerified).length;
  const discrepancyItems = items.filter((i: any) => i.discrepancyType !== null).length;
  const percentage = totalItems > 0 ? (verifiedItems / totalItems) * 100 : 0;

  await prisma.sdvRecord.update({
    where: { id: recordId },
    data: {
      totalItems,
      verifiedItems,
      discrepancyItems,
      percentage: Math.round(percentage * 100) / 100,
    },
  });
}

export const sdvService = {
  create, getList, getById, updateRecord,
  addItems, updateItem, batchUpdateItems,
  complete, getStatistics,
};
