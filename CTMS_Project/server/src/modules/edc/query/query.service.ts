import prisma from '../../../config/database';
import { CreateQueryInput, ReplyQueryInput } from './query.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['priority', 'status', 'queryType', 'createdAt', 'updatedAt'];

/**
 * 创建质疑
 */
async function create(input: CreateQueryInput, userId: string) {
  const query = await prisma.dataQuery.create({
    data: {
      ...input,
      raisedBy: userId,
      status: 'open',
    },
  });

  // 创建历史记录
  await prisma.dataQueryHistory.create({
    data: {
      queryId: query.id,
      actionType: 'created',
      actionBy: userId,
    },
  });

  logger.info('Data query created', {
    audit: true,
    eventType: 'DATA_QUERY_CREATE',
    projectId: input.projectId,
    message: `创建质疑: ${input.title}`,
  });

  return query;
}

/**
 * 获取质疑列表
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.subjectId) where.subjectId = query.subjectId;
  if (query.status) where.status = query.status;
  if (query.queryType) where.queryType = query.queryType;
  if (query.priority) where.priority = query.priority;
  if (query.assignedTo) where.assignedTo = query.assignedTo;
  if (query.raisedBy) where.raisedBy = query.raisedBy;

  const [queries, total] = await Promise.all([
    prisma.dataQuery.findMany({
      where, ...prismaPagination(pagination),
      include: {
        subject: { select: { id: true, subjectCode: true } },
        histories: { orderBy: { actionAt: 'asc' } },
        _count: { select: { histories: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.dataQuery.count({ where }),
  ]);

  return buildPaginatedResult(queries, total, pagination);
}

/**
 * 获取质疑详情
 */
async function getById(id: string) {
  const query = await prisma.dataQuery.findUnique({
    where: { id },
    include: {
      subject: { select: { id: true, subjectCode: true } },
      histories: { orderBy: { actionAt: 'asc' } },
    },
  });

  if (!query) throw new NotFoundError('DataQuery', id);
  return query;
}

/**
 * 回复质疑
 */
async function reply(id: string, input: ReplyQueryInput, userId: string) {
  const query = await prisma.dataQuery.findUnique({ where: { id } });
  if (!query) throw new NotFoundError('DataQuery', id);

  let newStatus = query.status;
  let oldStatus = query.status;

  if (input.action === 'close') {
    if (query.status === 'closed') throw new BadRequestError('质疑已关闭');
    newStatus = 'closed';
  } else if (input.action === 'escalate') {
    newStatus = 'escalated';
  }

  // 更新质疑状态
  await prisma.dataQuery.update({
    where: { id },
    data: { status: newStatus, updatedAt: new Date() },
  });

  // 创建回复记录
  const history = await prisma.dataQueryHistory.create({
    data: {
      queryId: id,
      actionType: input.action,
      actionBy: userId,
      oldValue: { status: oldStatus },
      newValue: { content: input.content, status: newStatus },
    },
  });

  logger.info(`Data query ${input.action}`, {
    audit: true,
    eventType: `DATA_QUERY_${input.action.toUpperCase()}`,
    message: `${input.action === 'reply' ? '回复' : input.action === 'close' ? '关闭' : '升级'}质疑 ${query.title}`,
  });

  return history;
}

/**
 * 重新分配质疑
 */
async function reassign(id: string, assignedTo: string, userId: string) {
  const query = await prisma.dataQuery.findUnique({ where: { id } });
  if (!query) throw new NotFoundError('DataQuery', id);

  const oldAssignedTo = query.assignedTo;
  const updated = await prisma.dataQuery.update({
    where: { id },
    data: { assignedTo, updatedAt: new Date() },
  });

  await prisma.dataQueryHistory.create({
    data: {
      queryId: id,
      actionType: 'reassigned',
      actionBy: userId,
      oldValue: { assignedTo: oldAssignedTo },
      newValue: { assignedTo },
    },
  });

  logger.info('Data query reassigned', {
    audit: true,
    eventType: 'DATA_QUERY_REASSIGN',
    message: `质疑 ${query.title} 重新分配`,
  });

  return updated;
}

export const queryService = {
  create, getList, getById, reply, reassign,
};
