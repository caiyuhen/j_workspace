import prisma from '../../../config/database';
import { CreateTimesheetInput, SubmitTimesheetInput, ApproveTimesheetInput } from './timesheet.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, BadRequestError, ConflictError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['weekStartDate', 'totalHours', 'status', 'createdAt'];

/**
 * 创建工时表
 */
async function create(input: CreateTimesheetInput, userId: string) {
  const weekStartDate = new Date(input.weekStartDate);

  // 检查该周是否已有工时表
  const existing = await prisma.timesheet.findFirst({
    where: {
      userId: input.userId,
      weekStartDate,
    },
  });
  if (existing) throw new ConflictError('该周的工时表已存在');

  const totalHours = input.entries.reduce((sum, e) => sum + e.hours, 0);

  const timesheet = await prisma.timesheet.create({
    data: {
      userId: input.userId,
      projectId: input.projectId,
      weekStartDate,
      totalHours,
      status: 'draft',
      entries: {
        create: input.entries.map(entry => ({
          workDate: new Date(entry.workDate),
          hours: entry.hours,
          workType: entry.workType,
          projectId: entry.projectId,
          siteId: entry.siteId,
          isBillable: entry.isBillable,
          description: entry.description,
        })),
      },
    },
    include: { entries: true },
  });

  logger.info('Timesheet created', {
    audit: true,
    userId: input.userId,
    eventType: 'TIMESHEET_CREATE',
    message: `创建工时表 - 周 ${input.weekStartDate}, ${totalHours}h`,
  });

  return timesheet;
}

/**
 * 获取工时表列表（分页）
 */
async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.userId) where.userId = query.userId;
  if (query.projectId) where.projectId = query.projectId;
  if (query.status) where.status = query.status;
  if (query.weekStartFrom && query.weekStartTo) {
    where.weekStartDate = {
      gte: new Date(query.weekStartFrom),
      lte: new Date(query.weekStartTo),
    };
  }

  const [timesheets, total] = await Promise.all([
    prisma.timesheet.findMany({
      where,
      ...prismaPagination(pagination),
      include: {
        entries: { orderBy: { workDate: 'asc' } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.timesheet.count({ where }),
  ]);

  return buildPaginatedResult(timesheets, total, pagination);
}

/**
 * 获取工时表详情
 */
async function getById(id: string) {
  const timesheet = await prisma.timesheet.findUnique({
    where: { id },
    include: {
      entries: { orderBy: { workDate: 'asc' } },
    },
  });

  if (!timesheet) throw new NotFoundError('Timesheet', id);
  return timesheet;
}

/**
 * 提交工时表（审批）
 */
async function submit(id: string, input: SubmitTimesheetInput, userId: string) {
  const timesheet = await prisma.timesheet.findUnique({ where: { id } });
  if (!timesheet) throw new NotFoundError('Timesheet', id);
  if (timesheet.status !== 'draft') throw new BadRequestError('只有草稿状态的工时表可以提交');

  const updated = await prisma.timesheet.update({
    where: { id },
    data: { status: 'submitted' },
    include: { entries: true },
  });

  logger.info('Timesheet submitted', {
    audit: true,
    userId,
    eventType: 'TIMESHEET_SUBMIT',
    message: `提交工时表 ${id}`,
  });

  return updated;
}

/**
 * 审批工时表
 */
async function approve(id: string, input: ApproveTimesheetInput, approverId: string) {
  const timesheet = await prisma.timesheet.findUnique({ where: { id } });
  if (!timesheet) throw new NotFoundError('Timesheet', id);
  if (timesheet.status !== 'submitted') throw new BadRequestError('只有已提交的工时表可以审批');

  const updated = await prisma.timesheet.update({
    where: { id },
    data: {
      status: input.action === 'approve' ? 'approved' : 'rejected',
      approvedBy: approverId,
      approvedAt: input.action === 'approve' ? new Date() : null,
    },
    include: { entries: true },
  });

  logger.info(`Timesheet ${input.action}`, {
    audit: true,
    userId: approverId,
    eventType: input.action === 'approve' ? 'TIMESHEET_APPROVE' : 'TIMESHEET_REJECT',
    message: `${input.action === 'approve' ? '批准' : '驳回'}工时表 ${id}`,
    details: { comment: input.comment },
  });

  return updated;
}

export const timesheetService = {
  create, getList, getById, submit, approve,
};
