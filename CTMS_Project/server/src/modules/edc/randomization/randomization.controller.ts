// randomization.controller.ts - 随机化管理控制器

import { Request, Response, NextFunction } from 'express';
import * as randomizationService from './randomization.service';

export async function createRecord(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).user?.id ?? '';
    const record = await randomizationService.createRecord(req.body, userId);
    res.status(201).json({ success: true, data: record });
  } catch (err) {
    next(err);
  }
}

export async function listRecords(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await randomizationService.listRecords(req.query as any);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function getRecordById(req: Request, res: Response, next: NextFunction) {
  try {
    const record = await randomizationService.getRecordById(req.params.id);
    res.json({ success: true, data: record });
  } catch (err) {
    next(err);
  }
}

export async function getRecordBySubject(req: Request, res: Response, next: NextFunction) {
  try {
    const record = await randomizationService.getRecordBySubject(req.params.subjectId);
    res.json({ success: true, data: record });
  } catch (err) {
    next(err);
  }
}

export async function getRandomizationStats(req: Request, res: Response, next: NextFunction) {
  try {
    const stats = await randomizationService.getRandomizationStats(req.params.projectId);
    res.json({ success: true, data: stats });
  } catch (err) {
    next(err);
  }
}

export async function emergencyUnblind(req: Request, res: Response, next: NextFunction) {
  try {
    const { reason } = req.body;
    const userId = (req as any).user?.userId;
    const result = await randomizationService.emergencyUnblind(req.params.subjectId, reason, userId);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function getNumberPoolStatus(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await randomizationService.getNumberPoolStatus(req.params.projectId);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}

export async function exportRandomizationList(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await randomizationService.exportRandomizationList(req.params.projectId);
    res.json({ success: true, data: result });
  } catch (err) {
    next(err);
  }
}
