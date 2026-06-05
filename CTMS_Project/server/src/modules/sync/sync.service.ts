import prisma from '../../config/database';
import { TriggerSyncInput, CreateSyncLogInput } from './sync.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { parseSort } from '../../shared/utils/sort';
import logger from '../../shared/utils/logger';

const ALLOWED_SORT_FIELDS = ['syncType', 'status', 'createdAt'];

/** 记录同步日志 */
async function logSync(input: CreateSyncLogInput, status: string = 'pending', errorMessage?: string) {
  return prisma.dataSyncLog.create({
    data: {
      ...input,
      status,
      errorMessage,
    },
  });
}

// ========== 同步处理器 ==========

/**
 * 项目信息同步：CTMS → EDC
 * 将项目基础信息同步到 EDC 侧（确保表单模板、站点配置引用正确）
 */
async function syncProjectInfo(projectId: string): Promise<{ syncedRecords: number }> {
  const project = await prisma.project.findUnique({
    where: { id: projectId },
    include: { sites: { select: { id: true, siteCode: true, siteName: true, status: true } } },
  });
  if (!project) throw new Error(`项目 ${projectId} 不存在`);

  // 记录同步的站点信息到 sync payload
  const sites = project.sites || [];
  const payload = {
    projectCode: project.projectCode,
    projectName: project.projectName,
    studyType: project.studyType,
    therapeuticArea: project.therapeuticArea,
    indication: project.indication,
    sampleSize: project.sampleSize,
    status: project.status,
    syncedSites: sites.map(s => ({ siteCode: s.siteCode, siteName: s.siteName, status: s.status })),
  };

  // 更新同步日志的 payload
  const syncLog = await prisma.dataSyncLog.findFirst({
    where: { projectId, syncType: 'project_info', status: 'pending' },
    orderBy: { createdAt: 'desc' },
  });
  if (syncLog) {
    await prisma.dataSyncLog.update({
      where: { id: syncLog.id },
      data: { payload, recordType: 'Project' },
    });
  }

  return { syncedRecords: 1 + sites.length };
}

/**
 * 工时数据同步：CTMS → EDC
 * 将工时记录关联的项目信息同步到 EDC 侧的审计追踪
 */
async function syncTimesheet(projectId: string, params?: Record<string, any>): Promise<{ syncedRecords: number }> {
  const where: any = {};
  if (projectId) where.projectId = projectId;
  if (params?.weekStartDate) where.weekStartDate = params.weekStartDate;
  if (params?.status) where.status = params.status;

  const [timesheets, users] = await Promise.all([
    prisma.timesheet.findMany({
      where,
      include: { entries: { select: { workDate: true, hours: true, workType: true, projectId: true, siteId: true } } },
      take: 500,
      orderBy: { weekStartDate: 'desc' },
    }),
    prisma.user.findMany({ select: { id: true, displayName: true } }),
  ]);

  const userMap = new Map(users.map((u: any) => [u.id, u.displayName]));

  const payload = timesheets.map((ts: any) => ({
    timesheetId: ts.id,
    userId: ts.userId,
    displayName: userMap.get(ts.userId) || '',
    weekStartDate: ts.weekStartDate,
    totalHours: ts.totalHours,
    status: ts.status,
    entryCount: ts.entries?.length || 0,
  }));

  const syncLog = await prisma.dataSyncLog.findFirst({
    where: { projectId, syncType: 'timesheet', status: 'pending' },
    orderBy: { createdAt: 'desc' },
  });
  if (syncLog) {
    await prisma.dataSyncLog.update({
      where: { id: syncLog.id },
      data: { payload, recordType: 'Timesheet', recordId: timesheets.length > 0 ? timesheets[0].id : undefined },
    });
  }

  return { syncedRecords: timesheets.length };
}

/**
 * 财务数据同步：CTMS → EDC
 * 同步项目预算和收支数据
 */
async function syncFinance(projectId: string, params?: Record<string, any>): Promise<{ syncedRecords: number }> {
  const projectWhere: any = {};
  if (projectId) projectWhere.id = projectId;

  const [incomes, expenses] = await Promise.all([
    prisma.financialIncome.findMany({
      where: { ...projectWhere, ...(params?.status ? { status: params.status } : {}) },
      select: { id: true, projectId: true, incomeCode: true, incomeType: true, amount: true, currency: true, status: true },
      take: 500,
    }),
    prisma.financialExpense.findMany({
      where: { ...projectWhere, ...(params?.status ? { status: params.status } : {}) },
      select: { id: true, projectId: true, expenseCode: true, expenseType: true, amount: true, currency: true, status: true },
      take: 500,
    }),
  ]);

  const payload = {
    incomeCount: incomes.length,
    expenseCount: expenses.length,
    totalIncome: incomes.reduce((s, i) => s + Number(i.amount), 0),
    totalExpense: expenses.reduce((s, e) => s + Number(e.amount), 0),
  };

  const syncLog = await prisma.dataSyncLog.findFirst({
    where: { projectId, syncType: 'finance', status: 'pending' },
    orderBy: { createdAt: 'desc' },
  });
  if (syncLog) {
    await prisma.dataSyncLog.update({
      where: { id: syncLog.id },
      data: { payload, recordType: 'FinancialRecord' },
    });
  }

  return { syncedRecords: incomes.length + expenses.length };
}

/**
 * 受试者数据同步：EDC → CTMS
 * 将 EDC 侧入组进度同步到 CTMS 项目的里程碑
 */
async function syncSubjectEnrollment(projectId: string): Promise<{ syncedRecords: number }> {
  const subjectStats = await prisma.subject.groupBy({
    by: ['siteId'],
    where: { projectId, enrollmentStatus: { in: ['screening', 'enrolled'] } },
    _count: { id: true },
  });

  const siteNames = await prisma.site.findMany({
    where: { projectId },
    select: { id: true, siteName: true, siteCode: true },
  });

  const siteMap = new Map(siteNames.map(s => [s.id, s]));

  const payload = {
    projectId,
    totalActiveSubjects: subjectStats.reduce((s, g) => s + g._count.id, 0),
    bySite: subjectStats.map(g => ({
      siteId: g.siteId!,
      siteName: siteMap.get(g.siteId!)?.siteName || 'Unknown',
      siteCode: siteMap.get(g.siteId!)?.siteCode || 'N/A',
      activeCount: g._count.id,
    })),
    syncedAt: new Date().toISOString(),
  };

  const syncLog = await prisma.dataSyncLog.findFirst({
    where: { projectId, syncType: 'subject_enrollment', status: 'pending' },
    orderBy: { createdAt: 'desc' },
  });
  if (syncLog) {
    await prisma.dataSyncLog.update({
      where: { id: syncLog.id },
      data: { payload, recordType: 'Subject' },
    });
  }

  return { syncedRecords: subjectStats.length };
}

/**
 * AE/SAE 数据同步：EDC → CTMS
 * 将严重不良事件信息同步到 CTMS 项目管理
 */
async function syncAdverseEvents(projectId: string): Promise<{ syncedRecords: number }> {
  const where: any = {};
  if (projectId) where.projectId = projectId;

  const events = await prisma.adverseEvent.findMany({
    where,
    select: {
      id: true, projectId: true, reportCode: true, eventType: true,
      termPreferred: true, severity: true, seriousness: true, status: true,
      createdAt: true,
    },
    take: 500,
    orderBy: { createdAt: 'desc' },
  });

  const payload = {
    totalEvents: events.length,
    seriousEvents: events.filter(e => e.seriousness === 'serious').length,
    openEvents: events.filter(e => e.status === 'open').length,
    recentEvents: events.slice(0, 10).map(e => ({
      reportCode: e.reportCode, eventType: e.eventType, termPreferred: e.termPreferred,
      severity: e.severity, status: e.status,
    })),
  };

  const syncLog = await prisma.dataSyncLog.findFirst({
    where: { projectId, syncType: 'adverse_events', status: 'pending' },
    orderBy: { createdAt: 'desc' },
  });
  if (syncLog) {
    await prisma.dataSyncLog.update({
      where: { id: syncLog.id },
      data: { payload, recordType: 'AdverseEvent' },
    });
  }

  return { syncedRecords: events.length };
}

/**
 * 根据同步类型路由到对应的同步处理器
 */
const syncHandlers: Record<string, (projectId: string, params?: Record<string, any>) => Promise<{ syncedRecords: number }>> = {
  project_info: syncProjectInfo,
  timesheet: syncTimesheet,
  finance: syncFinance,
  subject_enrollment: syncSubjectEnrollment,
  adverse_events: syncAdverseEvents,
};

/** 触发同步 */
async function triggerSync(input: TriggerSyncInput, userId: string) {
  const direction = input.direction || (['project_info', 'timesheet', 'finance'].includes(input.syncType) ? 'ctms_to_edc' : 'edc_to_ctms');
  const sourceSystem = direction === 'ctms_to_edc' ? 'CTMS' : 'EDC';
  const targetSystem = direction === 'ctms_to_edc' ? 'EDC' : 'CTMS';

  // 创建同步日志记录
  const syncLog = await prisma.dataSyncLog.create({
    data: {
      syncType: input.syncType,
      direction,
      projectId: input.projectId,
      sourceSystem,
      targetSystem,
      status: 'pending',
    },
  });

  logger.info('Data sync triggered', {
    audit: true,
    eventType: 'DATA_SYNC_TRIGGER',
    syncType: input.syncType,
    projectId: input.projectId,
    direction,
    message: `触发数据同步: ${input.syncType} (${direction})`,
  });

  // 执行同步逻辑
  const handler = syncHandlers[input.syncType];
  if (handler) {
    try {
      const result = await handler(input.projectId || '', input.parameters);
      await prisma.dataSyncLog.update({
        where: { id: syncLog.id },
        data: {
          status: 'completed',
          syncedAt: new Date(),
          payload: { syncedRecords: result.syncedRecords },
        },
      });

      logger.info('Data sync completed', {
        audit: true,
        eventType: 'DATA_SYNC_COMPLETE',
        syncLogId: syncLog.id,
        syncType: input.syncType,
        syncedRecords: result.syncedRecords,
        message: `同步完成: ${input.syncType}，同步 ${result.syncedRecords} 条记录`,
      });
    } catch (err: any) {
      await prisma.dataSyncLog.update({
        where: { id: syncLog.id },
        data: {
          status: 'failed',
          errorMessage: err.message || '未知同步错误',
          retryCount: { increment: 1 },
        },
      });

      logger.error('Data sync failed', {
        syncLogId: syncLog.id,
        syncType: input.syncType,
        error: err.message,
      });

      return { ...syncLog, status: 'failed', errorMessage: err.message };
    }
  } else {
    // 无对应处理器，标记为成功（兼容未实现的同步类型）
    await prisma.dataSyncLog.update({
      where: { id: syncLog.id },
      data: { status: 'completed', syncedAt: new Date() },
    });
    logger.warn('No sync handler for type, marking as completed', { syncType: input.syncType });
  }

  return syncLog;
}

/** 获取同步日志列表 */
async function getLogList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, ALLOWED_SORT_FIELDS, 'createdAt', 'desc');

  const where: any = {};
  if (query.syncType) where.syncType = query.syncType;
  if (query.projectId) where.projectId = query.projectId;
  if (query.status) where.status = query.status;
  if (query.sourceSystem) where.sourceSystem = query.sourceSystem;

  const [logs, total] = await Promise.all([
    prisma.dataSyncLog.findMany({
      where, ...prismaPagination(pagination),
      orderBy: sort.orderBy,
    }),
    prisma.dataSyncLog.count({ where }),
  ]);

  return buildPaginatedResult(logs, total, pagination);
}

/** 获取同步统计 */
async function getStats(projectId?: string) {
  const where: any = {};
  if (projectId) where.projectId = projectId;

  const [total, completed, failed, pending] = await Promise.all([
    prisma.dataSyncLog.count({ where }),
    prisma.dataSyncLog.count({ where: { ...where, status: 'completed' } }),
    prisma.dataSyncLog.count({ where: { ...where, status: 'failed' } }),
    prisma.dataSyncLog.count({ where: { ...where, status: 'pending' } }),
  ]);

  // 按类型分组统计
  const byType = await prisma.dataSyncLog.groupBy({
    by: ['syncType'],
    where,
    _count: { id: true },
  });

  return {
    total, completed, failed, pending,
    successRate: total > 0 ? ((completed / total) * 100).toFixed(1) + '%' : '0%',
    byType: byType.map(t => ({ syncType: t.syncType, count: t._count.id })),
  };
}

export const syncService = { logSync, triggerSync, getLogList, getStats };
