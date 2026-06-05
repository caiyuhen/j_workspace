import prisma from '../../config/database';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { parseSort } from '../../shared/utils/sort';
import { ForbiddenError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['eventType', 'tableName', 'action', 'eventTimestamp', 'userId'];

/**
 * 查询审计日志列表
 */
async function queryLogs(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'eventTimestamp', 'desc');

  const where: any = {};
  if (query.userId) where.userId = query.userId;
  if (query.eventType) where.eventType = query.eventType;
  if (query.tableName) where.tableName = query.tableName;
  if (query.recordId) where.recordId = query.recordId;
  if (query.action) where.action = query.action;
  if (query.systemCode) where.systemCode = query.systemCode;

  if (query.startTime || query.endTime) {
    where.eventTimestamp = {};
    if (query.startTime) where.eventTimestamp.gte = new Date(query.startTime);
    if (query.endTime) where.eventTimestamp.lte = new Date(query.endTime);
  }

  if (query.keyword) {
    where.OR = [
      { eventType: { contains: query.keyword, mode: 'insensitive' } },
      { action: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }

  const [logs, total] = await Promise.all([
    prisma.auditLog.findMany({
      where, ...prismaPagination(pagination),
      include: {
        user: { select: { id: true, username: true, displayName: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.auditLog.count({ where }),
  ]);

  return buildPaginatedResult(logs, total, pagination);
}

/**
 * 获取审计日志详情
 */
async function getById(id: string) {
  const log = await prisma.auditLog.findUnique({
    where: { id },
    include: {
      user: { select: { id: true, username: true, displayName: true } },
    },
  });

  if (!log) {
    throw new ForbiddenError('审计日志不存在');
  }

  return log;
}

/**
 * 获取记录变更历史（根据表名和记录ID）
 */
async function getRecordHistory(tableName: string, recordId: string) {
  return prisma.auditLog.findMany({
    where: { tableName, recordId },
    orderBy: { eventTimestamp: 'desc' },
    include: {
      user: { select: { id: true, username: true, displayName: true } },
    },
  });
}

/**
 * 审计日志统计（按事件类型分组）
 */
async function getStats(query: Record<string, any>) {
  const where: any = {};
  if (query.startTime || query.endTime) {
    where.eventTimestamp = {};
    if (query.startTime) where.eventTimestamp.gte = new Date(query.startTime);
    if (query.endTime) where.eventTimestamp.lte = new Date(query.endTime);
  }

  const stats = await prisma.auditLog.groupBy({
    by: ['eventType'],
    where,
    _count: true,
    _max: { eventTimestamp: true },
    orderBy: { _count: { eventType: 'desc' } },
  });

  const total = await prisma.auditLog.count({ where });

  return { stats, total };
}

export const auditService = {
  queryLogs, getById, getRecordHistory, getStats,
};
