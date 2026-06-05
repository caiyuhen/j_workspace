import prisma from '../../../config/database';
import {
  CreateAdverseEventInput, UpdateAdverseEventInput,
  CreateSaeReportInput, SubmitSaeReportInput, ReviewSaeReportInput,
} from './ae.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, BadRequestError, ConflictError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['onsetDate', 'severity', 'seriousness', 'eventType', 'status', 'createdAt', 'updatedAt'];

// ========== 不良事件管理 ==========

async function create(input: CreateAdverseEventInput, userId: string) {
  const project = await prisma.project.findUnique({ where: { id: input.projectId } });
  if (!project) throw new NotFoundError('Project', input.projectId);

  // 生成报告编码
  const aeCount = await prisma.adverseEvent.count({ where: { projectId: input.projectId } });
  const reportCode = `${project.projectCode}-AE-${String(aeCount + 1).padStart(4, '0')}`;

  const event = await prisma.adverseEvent.create({
    data: {
      ...input,
      reportCode,
      onsetDate: new Date(input.onsetDate),
      endDate: input.endDate ? new Date(input.endDate) : null,
      seriousnessCriteria: input.seriousnessCriteria || [],
      actionTaken: input.actionTaken || [],
      reporterId: userId,
      status: 'open',
    },
  });

  // SAE 自动创建初始报告
  if (input.eventType === 'sae') {
    await prisma.saeReport.create({
      data: {
        adverseEventId: event.id,
        reportType: 'initial',
        reportVersion: '1.0',
        reportDate: new Date(),
        reviewStatus: 'pending',
        status: 'draft',
        reportContent: {},
      },
    });

    // SAE 24小时紧急上报截止日期
    await prisma.adverseEvent.update({
      where: { id: event.id },
      data: {
        status: 'reporting',
      },
    });
  }

  logger.info('Adverse event created', {
    audit: true,
    eventType: input.eventType === 'sae' ? 'SAE_CREATE' : 'AE_CREATE',
    projectId: input.projectId,
    message: `创建${input.eventType === 'sae' ? '严重不良事件' : '不良事件'}: ${input.termPreferred}`,
  });

  return event;
}

async function getList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.subjectId) where.subjectId = query.subjectId;
  if (query.eventType) where.eventType = query.eventType;
  if (query.severity) where.severity = query.severity;
  if (query.seriousness) where.seriousness = query.seriousness;
  if (query.status) where.status = query.status;
  if (query.siteId) where.siteId = query.siteId;
  if (query.reporterId) where.reporterId = query.reporterId;
  if (query.keyword) {
    where.OR = [
      { termPreferred: { contains: query.keyword, mode: 'insensitive' } },
      { reportCode: { contains: query.keyword, mode: 'insensitive' } },
      { description: { contains: query.keyword, mode: 'insensitive' } },
    ];
  }

  const [events, total] = await Promise.all([
    prisma.adverseEvent.findMany({
      where, ...prismaPagination(pagination),
      include: {
        reports: { orderBy: { reportDate: 'desc' } },
        _count: { select: { reports: true } },
      },
      orderBy: sort.orderBy,
    }),
    prisma.adverseEvent.count({ where }),
  ]);

  return buildPaginatedResult(events, total, pagination);
}

async function getById(id: string) {
  const event = await prisma.adverseEvent.findUnique({
    where: { id },
    include: {
      reports: { orderBy: { reportDate: 'desc' } },
    },
  });

  if (!event) throw new NotFoundError('AdverseEvent', id);
  return event;
}

async function update(id: string, input: UpdateAdverseEventInput) {
  const event = await prisma.adverseEvent.findUnique({ where: { id } });
  if (!event) throw new NotFoundError('AdverseEvent', id);

  const updated = await prisma.adverseEvent.update({
    where: { id },
    data: {
      ...input,
      endDate: input.endDate ? new Date(input.endDate) : undefined,
      onsetDate: input.onsetDate ? new Date(input.onsetDate) : undefined,
    },
  });

  logger.info('Adverse event updated', {
    audit: true,
    eventType: 'AE_UPDATE',
    projectId: event.projectId,
    message: `更新不良事件: ${event.termPreferred}`,
  });

  return updated;
}

async function close(id: string, reason: string) {
  const event = await prisma.adverseEvent.findUnique({ where: { id } });
  if (!event) throw new NotFoundError('AdverseEvent', id);
  if (event.status === 'closed') throw new BadRequestError('事件已关闭');

  const updated = await prisma.adverseEvent.update({
    where: { id },
    data: { status: 'closed' },
  });

  logger.info('Adverse event closed', {
    audit: true, eventType: 'AE_CLOSE', projectId: event.projectId,
    message: `关闭不良事件: ${event.termPreferred}, 原因: ${reason}`,
  });

  return updated;
}

// ========== SAE 报告管理 ==========

async function createSaeReport(eventId: string, input: CreateSaeReportInput, userId: string) {
  const event = await prisma.adverseEvent.findUnique({ where: { id: eventId } });
  if (!event) throw new NotFoundError('AdverseEvent', eventId);
  if (event.eventType !== 'sae') throw new BadRequestError('仅 SAE 可创建报告');

  const existingReports = await prisma.saeReport.findMany({
    where: { adverseEventId: eventId },
    orderBy: { createdAt: 'desc' },
    select: { reportVersion: true },
    take: 1,
  });

  const lastVersion = existingReports[0]?.reportVersion || '0.0';
  const parts = lastVersion.split('.');
  const newVersion = `${parseInt(parts[0] || '0')}.${parseInt(parts[1] || '0') + 1}`;

  const report = await prisma.saeReport.create({
    data: {
      adverseEventId: eventId,
      ...input,
      reportVersion: newVersion,
      reportDate: new Date(input.reportDate),
      reportContent: input.reportContent || {},
      reviewStatus: 'pending',
      status: 'draft',
    },
  });

  logger.info('SAE report created', {
    audit: true, eventType: 'SAE_REPORT_CREATE', projectId: event.projectId,
    message: `创建SAE报告: ${event.reportCode} ${input.reportType}`,
  });

  return report;
}

async function getSaeReports(eventId: string) {
  const event = await prisma.adverseEvent.findUnique({ where: { id: eventId } });
  if (!event) throw new NotFoundError('AdverseEvent', eventId);

  return prisma.saeReport.findMany({
    where: { adverseEventId: eventId },
    orderBy: { reportDate: 'desc' },
  });
}

async function updateSaeReport(eventId: string, reportId: string, content: Record<string, any>) {
  const report = await prisma.saeReport.findFirst({
    where: { id: reportId, adverseEventId: eventId },
  });
  if (!report) throw new NotFoundError('SaeReport', reportId);
  if (report.status !== 'draft') throw new BadRequestError('仅草稿状态的报告可编辑');

  return prisma.saeReport.update({
    where: { id: reportId },
    data: { reportContent: content },
  });
}

async function reviewSaeReport(eventId: string, reportId: string, input: ReviewSaeReportInput, userId: string) {
  const report = await prisma.saeReport.findFirst({
    where: { id: reportId, adverseEventId: eventId },
  });
  if (!report) throw new NotFoundError('SaeReport', reportId);

  const updated = await prisma.saeReport.update({
    where: { id: reportId },
    data: {
      reviewStatus: input.reviewStatus,
      reviewComments: input.reviewComments,
      reviewedBy: userId,
      reviewedAt: new Date(),
    },
  });

  logger.info('SAE report reviewed', {
    audit: true, eventType: 'SAE_REPORT_REVIEW',
    message: `SAE报告审核: ${input.reviewStatus}`,
  });

  return updated;
}

async function submitSaeReport(eventId: string, reportId: string, input: SubmitSaeReportInput, userId: string) {
  const report = await prisma.saeReport.findFirst({
    where: { id: reportId, adverseEventId: eventId },
  });
  if (!report) throw new NotFoundError('SaeReport', reportId);
  if (report.status === 'submitted') throw new BadRequestError('报告已提交');

  const updated = await prisma.saeReport.update({
    where: { id: reportId },
    data: {
      status: 'submitted',
      submittedTo: input.submittedTo,
      submissionRef: input.submissionRef,
      actualSubmissionDate: new Date(),
      submittedBy: userId,
    },
  });

  logger.info('SAE report submitted', {
    audit: true, eventType: 'SAE_REPORT_SUBMIT',
    message: `提交SAE报告至: ${input.submittedTo}`,
  });

  return updated;
}

// ========== 统计 ==========

async function getStatistics(projectId: string) {
  const project = await prisma.project.findUnique({ where: { id: projectId } });
  if (!project) throw new NotFoundError('Project', projectId);

  const [
    totalEvents, aeCount, saeCount, openCount, closedCount, reportingCount,
  ] = await Promise.all([
    prisma.adverseEvent.count({ where: { projectId } }),
    prisma.adverseEvent.count({ where: { projectId, eventType: 'ae' } }),
    prisma.adverseEvent.count({ where: { projectId, eventType: 'sae' } }),
    prisma.adverseEvent.count({ where: { projectId, status: 'open' } }),
    prisma.adverseEvent.count({ where: { projectId, status: 'closed' } }),
    prisma.adverseEvent.count({ where: { projectId, status: 'reporting' } }),
  ]);

  // 严重程度分布
  const severityStats = await prisma.adverseEvent.groupBy({
    by: ['severity'],
    where: { projectId },
    _count: true,
  });

  // SAE 报告提交状态
  const reportStats = await prisma.saeReport.groupBy({
    by: ['status'],
    where: { adverseEvent: { projectId } },
    _count: true,
  });

  return {
    totalEvents, aeCount, saeCount, openCount, closedCount, reportingCount,
    severityBreakdown: severityStats.map((s: any) => ({ severity: s.severity, count: s._count })),
    reportStatusBreakdown: reportStats.map((s: any) => ({ status: s.status, count: s._count })),
  };
}

export const aeService = {
  create, getList, getById, update, close,
  createSaeReport, getSaeReports, updateSaeReport, reviewSaeReport, submitSaeReport,
  getStatistics,
};
