// monitoring.controller.ts - 监察管理控制器

import { Request, Response, NextFunction } from 'express';
import * as monitoringService from './monitoring.service';

// ==================== 监察计划 ====================

export async function createPlan(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).user?.id ?? '';
    const plan = await monitoringService.createPlan(req.body, userId);
    res.status(201).json({ success: true, data: plan });
  } catch (err) {
    next(err);
  }
}

export async function listPlans(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await monitoringService.listPlans(req.query as any);
    res.json({ success: true, ...result });
  } catch (err) {
    next(err);
  }
}

export async function getPlanById(req: Request, res: Response, next: NextFunction) {
  try {
    const plan = await monitoringService.getPlanById(req.params.id);
    res.json({ success: true, data: plan });
  } catch (err) {
    next(err);
  }
}

export async function updatePlan(req: Request, res: Response, next: NextFunction) {
  try {
    const plan = await monitoringService.updatePlan(req.params.id, req.body);
    res.json({ success: true, data: plan });
  } catch (err) {
    next(err);
  }
}

export async function deletePlan(req: Request, res: Response, next: NextFunction) {
  try {
    await monitoringService.deletePlan(req.params.id);
    res.json({ success: true, message: '监察计划已删除' });
  } catch (err) {
    next(err);
  }
}

// ==================== 监察访视 ====================

export async function createVisit(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).user?.id ?? '';
    const visit = await monitoringService.createVisit(req.body, userId);
    res.status(201).json({ success: true, data: visit });
  } catch (err) {
    next(err);
  }
}

export async function listVisits(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await monitoringService.listVisits(req.query as any);
    res.json({ success: true, ...result });
  } catch (err) {
    next(err);
  }
}

export async function getVisitById(req: Request, res: Response, next: NextFunction) {
  try {
    const visit = await monitoringService.getVisitById(req.params.id);
    res.json({ success: true, data: visit });
  } catch (err) {
    next(err);
  }
}

export async function updateVisit(req: Request, res: Response, next: NextFunction) {
  try {
    const visit = await monitoringService.updateVisit(req.params.id, req.body);
    res.json({ success: true, data: visit });
  } catch (err) {
    next(err);
  }
}

export async function deleteVisit(req: Request, res: Response, next: NextFunction) {
  try {
    await monitoringService.deleteVisit(req.params.id);
    res.json({ success: true, message: '监察访视已删除' });
  } catch (err) {
    next(err);
  }
}

export async function getMonitoringStats(req: Request, res: Response, next: NextFunction) {
  try {
    const { projectId } = req.params;
    const stats = await monitoringService.getMonitoringStats(projectId);
    res.json({ success: true, data: stats });
  } catch (err) {
    next(err);
  }
}
