// monitoring.service.ts - 监察管理业务逻辑

import prisma from '../../../config/database';
import { AppError, NotFoundError } from '../../../shared/errors/AppError';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import {
  CreateMonitoringPlanDto,
  UpdateMonitoringPlanDto,
  CreateMonitoringVisitDto,
  UpdateMonitoringVisitDto,
  MonitoringQueryDto,
} from './monitoring.dto';

// ==================== 监察计划 ====================

export async function createPlan(data: CreateMonitoringPlanDto, userId: string) {
  const project = await prisma.project.findUnique({ where: { id: data.projectId } });
  if (!project) throw new AppError('项目不存在', 404, 'PROJECT_NOT_FOUND');

  const plan = await prisma.monitoringPlan.create({
    data: {
      projectId: data.projectId,
      planName: data.planName,
      frequency: data.frequency,
      description: data.description,
      status: data.status ?? 'draft',
      createdBy: userId,
    },
    include: {
      project: { select: { id: true, projectName: true } },
    },
  });
  return plan;
}

export async function listPlans(query: MonitoringQueryDto) {
  const pagination = parsePagination(query as Record<string, any>);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.status) where.status = query.status;

  const [total, items] = await Promise.all([
    prisma.monitoringPlan.count({ where }),
    prisma.monitoringPlan.findMany({
      where,
      ...prismaPagination(pagination),
      orderBy: { createdAt: 'desc' },
      include: {
        project: { select: { id: true, projectName: true } },
        _count: { select: { monitoringVisits: true } },
      },
    }),
  ]);

  return buildPaginatedResult(items, total, pagination);
}

export async function getPlanById(id: string) {
  const plan = await prisma.monitoringPlan.findUnique({
    where: { id },
    include: {
      project: { select: { id: true, projectName: true } },
      monitoringVisits: {
        orderBy: { plannedDate: 'desc' },
        select: {
          id: true,
          visitType: true,
          plannedDate: true,
          actualDate: true,
          status: true,
          sdvPercentage: true,
          craUserId: true,
        },
      },
    },
  });
  if (!plan) throw new AppError('监察计划不存在', 404, 'PLAN_NOT_FOUND');
  return plan;
}

export async function updatePlan(id: string, data: UpdateMonitoringPlanDto) {
  const plan = await prisma.monitoringPlan.findUnique({ where: { id } });
  if (!plan) throw new AppError('监察计划不存在', 404, 'PLAN_NOT_FOUND');

  return prisma.monitoringPlan.update({
    where: { id },
    data: {
      planName: data.planName,
      frequency: data.frequency,
      description: data.description,
      status: data.status,
    },
    include: {
      project: { select: { id: true, projectName: true } },
    },
  });
}

export async function deletePlan(id: string) {
  const plan = await prisma.monitoringPlan.findUnique({ where: { id } });
  if (!plan) throw new AppError('监察计划不存在', 404, 'PLAN_NOT_FOUND');

  await prisma.monitoringPlan.delete({ where: { id } });
}

// ==================== 监察访视 ====================

export async function createVisit(data: CreateMonitoringVisitDto, _userId: string) {
  const project = await prisma.project.findUnique({ where: { id: data.projectId } });
  if (!project) throw new AppError('项目不存在', 404, 'PROJECT_NOT_FOUND');

  if (data.planId) {
    const plan = await prisma.monitoringPlan.findUnique({ where: { id: data.planId } });
    if (!plan) throw new AppError('监察计划不存在', 404, 'PLAN_NOT_FOUND');
  }

  const visit = await prisma.monitoringVisit.create({
    data: {
      planId: data.planId,
      projectId: data.projectId,
      siteId: data.siteId,
      craUserId: data.craUserId,
      visitType: data.visitType,
      plannedDate: new Date(data.plannedDate),
      actualDate: data.actualDate ? new Date(data.actualDate) : undefined,
      status: data.status ?? 'planned',
      sdvPercentage: data.sdvPercentage,
      reportId: data.reportId,
    },
    include: {
      project: { select: { id: true, projectName: true } },
      site: { select: { id: true, siteName: true } },
      plan: { select: { id: true, planName: true } },
    },
  });
  return visit;
}

export async function listVisits(query: MonitoringQueryDto) {
  const pagination = parsePagination(query as Record<string, any>);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.siteId) where.siteId = query.siteId;
  if (query.craUserId) where.craUserId = query.craUserId;
  if (query.status) where.status = query.status;
  if (query.visitType) where.visitType = query.visitType;

  const [total, items] = await Promise.all([
    prisma.monitoringVisit.count({ where }),
    prisma.monitoringVisit.findMany({
      where,
      ...prismaPagination(pagination),
      orderBy: { plannedDate: 'desc' },
      include: {
        project: { select: { id: true, projectName: true } },
        site: { select: { id: true, siteName: true } },
        plan: { select: { id: true, planName: true } },
      },
    }),
  ]);

  return buildPaginatedResult(items, total, pagination);
}

export async function getVisitById(id: string) {
  const visit = await prisma.monitoringVisit.findUnique({
    where: { id },
    include: {
      project: { select: { id: true, projectName: true } },
      site: { select: { id: true, siteName: true } },
      plan: { select: { id: true, planName: true } },
    },
  });
  if (!visit) throw new AppError('监察访视不存在', 404, 'VISIT_NOT_FOUND');
  return visit;
}

export async function updateVisit(id: string, data: UpdateMonitoringVisitDto) {
  const visit = await prisma.monitoringVisit.findUnique({ where: { id } });
  if (!visit) throw new AppError('监察访视不存在', 404, 'VISIT_NOT_FOUND');

  return prisma.monitoringVisit.update({
    where: { id },
    data: {
      planId: data.planId,
      siteId: data.siteId,
      craUserId: data.craUserId,
      visitType: data.visitType,
      plannedDate: data.plannedDate ? new Date(data.plannedDate) : undefined,
      actualDate: data.actualDate ? new Date(data.actualDate) : undefined,
      status: data.status,
      sdvPercentage: data.sdvPercentage,
      reportId: data.reportId,
    },
    include: {
      project: { select: { id: true, projectName: true } },
      site: { select: { id: true, siteName: true } },
      plan: { select: { id: true, planName: true } },
    },
  });
}

export async function deleteVisit(id: string) {
  const visit = await prisma.monitoringVisit.findUnique({ where: { id } });
  if (!visit) throw new AppError('监察访视不存在', 404, 'VISIT_NOT_FOUND');

  await prisma.monitoringVisit.delete({ where: { id } });
}

export async function getMonitoringStats(projectId: string) {
  const [totalPlans, totalVisits, visitsByStatus] = await Promise.all([
    prisma.monitoringPlan.count({ where: { projectId } }),
    prisma.monitoringVisit.count({ where: { projectId } }),
    prisma.monitoringVisit.groupBy({
      by: ['status'],
      where: { projectId },
      _count: { id: true },
    }),
  ]);

  const statusBreakdown: Record<string, number> = {};
  for (const row of visitsByStatus) {
    statusBreakdown[row.status] = row._count.id;
  }

  return {
    totalPlans,
    totalVisits,
    visitsByStatus: statusBreakdown,
  };
}
