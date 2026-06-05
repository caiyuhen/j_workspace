import prisma from '../../config/database';
import { CreateReportTemplateInput, UpdateReportTemplateInput, GenerateReportInput } from './report.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../shared/utils/pagination';
import { NotFoundError, ConflictError, BadRequestError } from '../../shared/errors/AppError';
import logger from '../../shared/utils/logger';

// ========== 报表数据查询引擎 ==========

/**
 * 工时明细报表：查询指定项目/时间范围内的工时记录
 * Timesheet 模型没有 user/project 正向关联，需手动查询
 */
async function queryTimesheetDetail(projectId: string, params: Record<string, any>): Promise<any[]> {
  const where: any = {};
  if (projectId) where.projectId = projectId;
  if (params.userId) where.userId = params.userId;
  if (params.status) where.status = params.status;
  if (params.weekStartFrom || params.weekStartTo) {
    where.weekStartDate = {};
    if (params.weekStartFrom) where.weekStartDate.gte = new Date(params.weekStartFrom);
    if (params.weekStartTo) where.weekStartDate.lte = new Date(params.weekStartTo);
  }

  const [timesheets, users, projects] = await Promise.all([
    prisma.timesheet.findMany({
      where,
      include: { entries: { select: { workDate: true, hours: true, workType: true, description: true, isBillable: true, projectId: true } } },
      orderBy: { weekStartDate: 'desc' },
    }),
    prisma.user.findMany({ select: { id: true, displayName: true, username: true, department: true } }),
    prisma.project.findMany({ select: { id: true, projectCode: true, projectName: true } }),
  ]);

  const userMap = new Map(users.map((u: any) => [u.id, u]));
  const projectMap = new Map(projects.map((p: any) => [p.id, p]));

  return timesheets.map((ts: any) => ({
    ...ts,
    _userDisplayName: userMap.get(ts.userId)?.displayName || '',
    _userUsername: userMap.get(ts.userId)?.username || '',
    _projectCode: projectMap.get(ts.projectId)?.projectCode || '',
    _projectName: projectMap.get(ts.projectId)?.projectName || '',
  }));
}

/**
 * 工时汇总报表：按用户汇总工时数据
 */
async function queryTimesheetSummary(projectId: string, params: Record<string, any>): Promise<any[]> {
  const where: any = {};
  if (projectId) where.projectId = projectId;
  if (params.userId) where.userId = params.userId;

  const [timesheets, users] = await Promise.all([
    prisma.timesheet.findMany({
      where,
      include: { entries: { select: { workType: true, hours: true, isBillable: true } } },
      orderBy: { weekStartDate: 'desc' },
    }),
    prisma.user.findMany({ select: { id: true, displayName: true, department: true } }),
  ]);

  const userMap = new Map(users.map((u: any) => [u.id, u]));

  // 按用户汇总
  const summaryMap = new Map<string, any>();
  for (const ts of timesheets as any[]) {
    const uid = ts.userId;
    if (!summaryMap.has(uid)) {
      const userInfo = userMap.get(uid);
      summaryMap.set(uid, {
        userId: uid,
        displayName: userInfo?.displayName || '',
        department: userInfo?.department || '',
        totalHours: 0, billableHours: 0, nonBillableHours: 0,
        workTypeBreakdown: {} as Record<string, number>,
        weekCount: 0,
      });
    }
    const summary = summaryMap.get(uid)!;
    summary.weekCount++;
    for (const entry of ts.entries) {
      summary.totalHours += entry.hours;
      if (entry.isBillable) summary.billableHours += entry.hours;
      else summary.nonBillableHours += entry.hours;
      summary.workTypeBreakdown[entry.workType] = (summary.workTypeBreakdown[entry.workType] || 0) + entry.hours;
    }
  }

  return Array.from(summaryMap.values()).map((s: any) => ({
    ...s,
    billableRate: s.totalHours > 0 ? ((s.billableHours / s.totalHours) * 100).toFixed(1) + '%' : '0%',
  }));
}

/**
 * 工时异常报表：超时/未提交/被拒绝的工时记录
 */
async function queryTimesheetAnomaly(projectId: string, params: Record<string, any>): Promise<any[]> {
  const where: any = {};
  if (projectId) where.projectId = projectId;
  const twoWeeksAgo = new Date();
  twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14);
  where.OR = [
    { status: 'rejected' },
    { status: 'submitted', submittedAt: { lt: twoWeeksAgo }, approvedAt: null },
  ];

  const [timesheets, users, projects] = await Promise.all([
    prisma.timesheet.findMany({ where, orderBy: { weekStartDate: 'asc' } }),
    prisma.user.findMany({ select: { id: true, displayName: true, username: true } }),
    prisma.project.findMany({ select: { id: true, projectCode: true, projectName: true } }),
  ]);

  const userMap = new Map(users.map((u: any) => [u.id, u]));
  const projectMap = new Map(projects.map((p: any) => [p.id, p]));

  return timesheets.map((ts: any) => ({
    ...ts,
    _userDisplayName: userMap.get(ts.userId)?.displayName || '',
    _projectCode: projectMap.get(ts.projectId)?.projectCode || '',
    _projectName: projectMap.get(ts.projectId)?.projectName || '',
  }));
}

/**
 * 财务预算报表：按项目汇总预算与实际收支
 * Project 模型没有 incomes/expenses 正向关联，需分别查询
 */
async function queryFinancialPL(projectId: string, params: Record<string, any>): Promise<any[]> {
  const projectWhere: any = {};
  if (projectId) projectWhere.id = projectId;

  const projects = await prisma.project.findMany({
    where: projectWhere,
    select: { id: true, projectCode: true, projectName: true, totalBudget: true, currency: true },
  });

  const projectIds = projects.map(p => p.id);
  const [incomes, expenses] = await Promise.all([
    prisma.financialIncome.findMany({
      where: { projectId: { in: projectIds } },
      select: { projectId: true, amount: true, incomeType: true, status: true, receivedDate: true },
    }),
    prisma.financialExpense.findMany({
      where: { projectId: { in: projectIds } },
      select: { projectId: true, amount: true, expenseType: true, status: true, expenseDate: true },
    }),
  ]);

  // 按 projectId 分组
  const incomeByProject = new Map<string, any[]>();
  const expenseByProject = new Map<string, any[]>();
  for (const i of incomes) {
    if (i.projectId && !incomeByProject.has(i.projectId)) incomeByProject.set(i.projectId, []);
    if (i.projectId) incomeByProject.get(i.projectId)!.push(i);
  }
  for (const e of expenses) {
    if (e.projectId && !expenseByProject.has(e.projectId)) expenseByProject.set(e.projectId, []);
    if (e.projectId) expenseByProject.get(e.projectId)!.push(e);
  }

  return projects.map(p => {
    const pIncomes = incomeByProject.get(p.id) || [];
    const pExpenses = expenseByProject.get(p.id) || [];
    const totalIncome = pIncomes.filter((i: any) => i.status === 'received').reduce((s: number, i: any) => s + Number(i.amount), 0);
    const pendingIncome = pIncomes.filter((i: any) => i.status === 'pending').reduce((s: number, i: any) => s + Number(i.amount), 0);
    const totalExpense = pExpenses.filter((e: any) => e.status === 'approved').reduce((s: number, e: any) => s + Number(e.amount), 0);
    const pendingExpense = pExpenses.filter((e: any) => e.status === 'pending').reduce((s: number, e: any) => s + Number(e.amount), 0);
    const budget = Number(p.totalBudget) || 0;

    return {
      projectId: p.id, projectCode: p.projectCode, projectName: p.projectName,
      currency: p.currency, totalBudget: budget,
      totalIncome, pendingIncome, totalExpense, pendingExpense,
      netIncome: totalIncome - totalExpense,
      budgetUtilization: budget > 0 ? ((totalExpense / budget) * 100).toFixed(1) + '%' : 'N/A',
      remainingBudget: budget - totalExpense,
    };
  });
}

/**
 * 财务现金流报表：按月汇总收入支出时间线
 */
async function queryFinancialCashflow(projectId: string, params: Record<string, any>): Promise<any[]> {
  const incomeWhere: any = {};
  const expenseWhere: any = {};
  if (projectId) {
    incomeWhere.projectId = projectId;
    expenseWhere.projectId = projectId;
  }
  if (params.dateFrom) {
    incomeWhere.receivedDate = { gte: new Date(params.dateFrom) };
    expenseWhere.expenseDate = { gte: new Date(params.dateFrom) };
  }
  if (params.dateTo) {
    incomeWhere.receivedDate = { ...incomeWhere.receivedDate, lte: new Date(params.dateTo) };
    expenseWhere.expenseDate = { ...expenseWhere.expenseDate, lte: new Date(params.dateTo) };
  }

  const [incomes, expenses] = await Promise.all([
    prisma.financialIncome.findMany({
      where: incomeWhere,
      select: { amount: true, incomeType: true, receivedDate: true, status: true },
      orderBy: { receivedDate: 'asc' },
    }),
    prisma.financialExpense.findMany({
      where: expenseWhere,
      select: { amount: true, expenseType: true, expenseDate: true, status: true },
      orderBy: { expenseDate: 'asc' },
    }),
  ]);

  // 按月汇总
  const monthlyMap = new Map<string, { month: string; income: number; expense: number; net: number }>();
  const addToMonth = (date: Date | null, amount: number, isInflow: boolean) => {
    if (!date) return;
    const key = date.toISOString().slice(0, 7); // YYYY-MM
    if (!monthlyMap.has(key)) monthlyMap.set(key, { month: key, income: 0, expense: 0, net: 0 });
    const entry = monthlyMap.get(key)!;
    if (isInflow) entry.income += amount; else entry.expense += amount;
  };

  for (const i of incomes) addToMonth(i.receivedDate, Number(i.amount), true);
  for (const e of expenses) addToMonth(e.expenseDate, Number(e.amount), false);

  return Array.from(monthlyMap.values())
    .sort((a, b) => a.month.localeCompare(b.month))
    .map(m => ({ ...m, net: m.income - m.expense }));
}

/**
 * 财务成本报表：按费用类型汇总支出明细
 * FinancialExpense 没有 project/submitter 关联，需手动查询
 */
async function queryFinancialCost(projectId: string, params: Record<string, any>): Promise<any[]> {
  const where: any = {};
  if (projectId) where.projectId = projectId;
  if (params.expenseType) where.expenseType = params.expenseType;
  if (params.status) where.status = params.status;

  const [expenses, projects] = await Promise.all([
    prisma.financialExpense.findMany({
      where,
      orderBy: { expenseDate: 'desc' },
    }),
    prisma.project.findMany({ select: { id: true, projectCode: true, projectName: true } }),
  ]);

  const projectMap = new Map(projects.map((p: any) => [p.id, p]));

  // 按费用类型汇总
  const typeMap = new Map<string, { expenseType: string; total: number; count: number; items: any[] }>();
  for (const e of expenses as any[]) {
    if (!typeMap.has(e.expenseType)) {
      typeMap.set(e.expenseType, { expenseType: e.expenseType, total: 0, count: 0, items: [] });
    }
    const entry = typeMap.get(e.expenseType)!;
    entry.total += Number(e.amount);
    entry.count++;
    entry.items.push({
      id: e.id, amount: Number(e.amount), expenseDate: e.expenseDate,
      description: e.description, status: e.status,
      projectName: projectMap.get(e.projectId)?.projectName || '',
    });
  }

  return Array.from(typeMap.values()).sort((a, b) => b.total - a.total);
}

/**
 * SAE 汇总报表：严重不良事件统计
 * AdverseEvent 没有 subject/reports 关联，需手动查询
 */
async function querySaeSummary(projectId: string, params: Record<string, any>): Promise<any[]> {
  const where: any = { seriousness: 'serious' };
  if (projectId) where.projectId = projectId;
  if (params.siteId) where.siteId = params.siteId;
  if (params.severity) where.severity = params.severity;

  const [aeList, subjects, reports] = await Promise.all([
    prisma.adverseEvent.findMany({ where, orderBy: { createdAt: 'desc' } }),
    prisma.subject.findMany({
      where: { projectId: projectId || undefined },
      select: { id: true, subjectCode: true, siteId: true },
    }),
    prisma.saeReport.findMany({
      select: { adverseEventId: true, reportType: true, status: true, submissionDeadline: true, actualSubmissionDate: true },
    }),
  ]);

  const subjectMap = new Map(subjects.map((s: any) => [s.id, s.subjectCode]));
  const reportsByAe = new Map<string, any[]>();
  for (const r of reports) {
    if (!reportsByAe.has(r.adverseEventId)) reportsByAe.set(r.adverseEventId, []);
    reportsByAe.get(r.adverseEventId)!.push(r);
  }

  return aeList.map((ae: any) => ({
    ...ae,
    _subjectCode: subjectMap.get(ae.subjectId) || '',
    _saeReports: reportsByAe.get(ae.id) || [],
  }));
}

/**
 * 入组进度报表：按中心/月汇总入组统计
 */
async function queryEnrollment(projectId: string, params: Record<string, any>): Promise<any[]> {
  if (!projectId) throw new BadRequestError('入组报表需要指定项目 ID');

  const subjects = await prisma.subject.findMany({
    where: { projectId },
    include: { site: { select: { siteCode: true, siteName: true } } },
    orderBy: { enrolledAt: 'asc' },
  });

  // 按中心汇总
  const siteMap = new Map<string, any>();
  for (const s of subjects) {
    const sid = s.siteId || 'unknown';
    if (!siteMap.has(sid)) {
      siteMap.set(sid, {
        siteId: sid,
        siteCode: s.site?.siteCode || 'N/A',
        siteName: s.site?.siteName || '未分配中心',
        total: 0, screening: 0, screenFailed: 0, enrolled: 0, discontinued: 0,
        monthlyEnrollment: {} as Record<string, number>,
      });
    }
    const entry = siteMap.get(sid)!;
    entry.total++;
    if (s.enrollmentStatus === 'screening') entry.screening++;
    if (s.enrollmentStatus === 'screen_failed') entry.screenFailed++;
    if (s.enrollmentStatus === 'enrolled') entry.enrolled++;
    if (s.enrollmentStatus === 'discontinued') entry.discontinued++;
    if (s.enrolledAt) {
      const month = s.enrolledAt.toISOString().slice(0, 7);
      entry.monthlyEnrollment[month] = (entry.monthlyEnrollment[month] || 0) + 1;
    }
  }

  return Array.from(siteMap.values());
}

/**
 * 数据质量报表：质疑统计与数据完整性
 */
async function queryDataQuality(projectId: string, params: Record<string, any>): Promise<any[]> {
  if (!projectId) throw new BadRequestError('数据质量报表需要指定项目 ID');

  const [queries, subjects] = await Promise.all([
    prisma.dataQuery.findMany({
      where: { projectId },
      select: { id: true, status: true, priority: true, queryType: true, createdAt: true, subjectId: true, dueDate: true },
    }),
    prisma.subject.count({ where: { projectId } }),
  ]);

  // 按状态汇总
  const byStatus: Record<string, number> = {};
  const byPriority: Record<string, number> = {};
  const byType: Record<string, number> = {};
  for (const q of queries) {
    byStatus[q.status] = (byStatus[q.status] || 0) + 1;
    byPriority[q.priority] = (byPriority[q.priority] || 0) + 1;
    byType[q.queryType] = (byType[q.queryType] || 0) + 1;
  }

  const openCount = queries.filter(q => q.status === 'open').length;
  const totalQueryRate = subjects > 0 ? ((queries.length / subjects) * 100).toFixed(1) : '0';

  return [{
    projectId,
    totalSubjects: subjects,
    totalQueries: queries.length,
    openQueries: openCount,
    closedQueries: byStatus['closed'] || 0,
    overdueQueries: queries.filter(q => q.status === 'open' && q.dueDate && q.dueDate < new Date()).length,
    queriesPerSubject: totalQueryRate,
    breakdownByStatus: byStatus,
    breakdownByPriority: byPriority,
    breakdownByType: byType,
  }];
}

/**
 * 审计合规报表：系统审计日志统计
 */
async function queryAuditCompliance(projectId: string, params: Record<string, any>): Promise<any[]> {
  const where: any = {};
  if (projectId) where.projectId = projectId;
  if (params.eventType) where.eventType = params.eventType;
  if (params.dateFrom || params.dateTo) {
    where.eventTimestamp = {};
    if (params.dateFrom) where.eventTimestamp.gte = new Date(params.dateFrom);
    if (params.dateTo) where.eventTimestamp.lte = new Date(params.dateTo);
  }

  const [logs, total] = await Promise.all([
    prisma.auditLog.findMany({
      where,
      include: {
        user: { select: { displayName: true, username: true } },
      },
      orderBy: { eventTimestamp: 'desc' },
      take: params.limit ? parseInt(params.limit) : 500,
    }),
    prisma.auditLog.count({ where }),
  ]);

  // 按事件类型分组
  const byEventType: Record<string, number> = {};
  const byCategory: Record<string, number> = {};
  const byUser: Record<string, { displayName: string; count: number }> = {};
  for (const log of logs as any[]) {
    byEventType[log.eventType] = (byEventType[log.eventType] || 0) + 1;
    if (log.eventCategory) byCategory[log.eventCategory] = (byCategory[log.eventCategory] || 0) + 1;
    const uid = log.userId;
    if (log.user && !byUser[uid]) byUser[uid] = { displayName: log.user.displayName, count: 0 };
    if (log.user) byUser[uid].count++;
  }

  return [{
    totalEvents: total,
    returnedEvents: logs.length,
    breakdownByEventType: byEventType,
    breakdownByCategory: byCategory,
    topUsers: Object.entries(byUser).sort((a: any, b: any) => b[1].count - a[1].count).slice(0, 10).map(([uid, info]: any) => ({ userId: uid, ...info })),
    recentEvents: logs.slice(0, 20).map((log: any) => ({
      id: log.id, eventType: log.eventType, eventCategory: log.eventCategory,
      action: log.action, tableName: log.tableName, eventTimestamp: log.eventTimestamp,
      userId: log.userId, displayName: log.user?.displayName || '',
    })),
  }];
}

/**
 * 根据报告类型执行对应的数据查询
 */
const reportQueryHandlers: Record<string, (projectId: string, params: Record<string, any>) => Promise<any[]>> = {
  timesheet_detail: queryTimesheetDetail,
  timesheet_summary: queryTimesheetSummary,
  timesheet_anomaly: queryTimesheetAnomaly,
  financial_pl: queryFinancialPL,
  financial_cashflow: queryFinancialCashflow,
  financial_cost: queryFinancialCost,
  sae_summary: querySaeSummary,
  enrollment: queryEnrollment,
  data_quality: queryDataQuality,
  audit_compliance: queryAuditCompliance,
};

async function createTemplate(input: CreateReportTemplateInput, userId: string) {
  const existing = await prisma.reportTemplate.findUnique({ where: { templateCode: input.templateCode } });
  if (existing) throw new ConflictError(`报表模板编码 ${input.templateCode} 已存在`);

  const template = await prisma.reportTemplate.create({
    data: {
      ...input,
      columnConfig: input.columnConfig || [],
      createdBy: userId,
    },
  });

  logger.info('Report template created', { audit: true, eventType: 'REPORT_TEMPLATE_CREATE', templateId: template.id });
  return template;
}

async function getTemplateList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const where: any = {};
  if (query.reportType) where.reportType = query.reportType;
  if (query.isActive !== undefined) where.isActive = query.isActive === 'true';

  const [templates, total] = await Promise.all([
    prisma.reportTemplate.findMany({ where, ...prismaPagination(pagination), orderBy: { createdAt: 'desc' } }),
    prisma.reportTemplate.count({ where }),
  ]);

  return buildPaginatedResult(templates, total, pagination);
}

async function getTemplateById(id: string) {
  const template = await prisma.reportTemplate.findUnique({ where: { id } });
  if (!template) throw new NotFoundError('ReportTemplate', id);
  return template;
}

async function updateTemplate(id: string, input: UpdateReportTemplateInput) {
  const template = await prisma.reportTemplate.findUnique({ where: { id } });
  if (!template) throw new NotFoundError('ReportTemplate', id);

  if (input.templateCode && input.templateCode !== template.templateCode) {
    const existing = await prisma.reportTemplate.findUnique({ where: { templateCode: input.templateCode } });
    if (existing) throw new ConflictError(`报表模板编码 ${input.templateCode} 已存在`);
  }

  return prisma.reportTemplate.update({ where: { id }, data: input });
}

/** 生成报表 */
async function generate(input: GenerateReportInput, userId: string) {
  const template = await prisma.reportTemplate.findUnique({ where: { id: input.templateId } });
  if (!template) throw new NotFoundError('ReportTemplate', input.templateId);

  // 根据模板 reportType 调用对应的数据查询引擎
  const handler = reportQueryHandlers[template.reportType];
  let reportDataRows: any[] = [];

  if (handler) {
    const projectId = input.projectId || '';
    const queryConfigParams = template.queryConfig as Record<string, any> | null;
    const params = { ...(input.parameters || {}), ...(queryConfigParams?.params || {}) };
    try {
      reportDataRows = await handler(projectId, params);
    } catch (err) {
      logger.error('Report query execution failed', { templateId: template.id, reportType: template.reportType, error: err });
      reportDataRows = [];
    }
  } else {
    logger.warn('No query handler for report type', { reportType: template.reportType });
  }

  const reportData = {
    templateCode: template.templateCode,
    templateName: template.templateName,
    reportType: template.reportType,
    generatedAt: new Date().toISOString(),
    parameters: input.parameters || {},
    recordCount: reportDataRows.length,
    data: reportDataRows,
  };

  const instance = await prisma.reportInstance.create({
    data: {
      templateId: template.id,
      projectId: input.projectId,
      reportName: input.reportName || `${template.templateName}_${new Date().toISOString().split('T')[0]}`,
      parameters: input.parameters || {},
      format: input.format || template.format,
      generatedBy: userId,
    },
  });

  logger.info('Report generated', {
    audit: true,
    eventType: 'REPORT_GENERATE',
    templateId: template.id,
    instanceId: instance.id,
    reportType: template.reportType,
  });

  return { instance, data: reportData };
}

async function getInstanceList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const where: any = {};
  if (query.templateId) where.templateId = query.templateId;
  if (query.projectId) where.projectId = query.projectId;

  const [instances, total] = await Promise.all([
    prisma.reportInstance.findMany({
      where, ...prismaPagination(pagination),
      include: { template: { select: { templateCode: true, templateName: true } } },
      orderBy: { generatedAt: 'desc' },
    }),
    prisma.reportInstance.count({ where }),
  ]);

  return buildPaginatedResult(instances, total, pagination);
}

export const reportService = { createTemplate, getTemplateList, getTemplateById, updateTemplate, generate, getInstanceList };
