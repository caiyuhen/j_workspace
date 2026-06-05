// lock.controller.ts - 数据锁定控制器

import { Request, Response, NextFunction } from 'express';
import * as lockService from './lock.service';

export async function createLock(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).user?.id ?? '';
    const lock = await lockService.createLock(req.body, userId);
    res.status(201).json({ success: true, data: lock });
  } catch (err) {
    next(err);
  }
}

export async function listLocks(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await lockService.listLocks(req.query as any);
    res.json({ success: true, ...result });
  } catch (err) {
    next(err);
  }
}

export async function getLockById(req: Request, res: Response, next: NextFunction) {
  try {
    const lock = await lockService.getLockById(req.params.id);
    res.json({ success: true, data: lock });
  } catch (err) {
    next(err);
  }
}

export async function checkLockStatus(req: Request, res: Response, next: NextFunction) {
  try {
    const { lockType, targetId } = req.params;
    const status = await lockService.checkLockStatus(lockType, targetId);
    res.json({ success: true, data: status });
  } catch (err) {
    next(err);
  }
}

export async function unlockRecord(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).user?.id ?? '';
    const lock = await lockService.unlockRecord(req.params.id, req.body, userId);
    res.json({ success: true, data: lock });
  } catch (err) {
    next(err);
  }
}

export async function getLockStats(req: Request, res: Response, next: NextFunction) {
  try {
    const stats = await lockService.getLockStats(req.params.projectId);
    res.json({ success: true, data: stats });
  } catch (err) {
    next(err);
  }
}
