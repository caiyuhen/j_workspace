import { Request, Response, NextFunction } from 'express';
import { ethicsService } from './ethics.service';
import { createEthicsSchema, updateEthicsSchema } from './ethics.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createEthicsSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await ethicsService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await ethicsService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await ethicsService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateEthicsSchema.parse(req.body);
    const result = await ethicsService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function transitionStatus(req: Request, res: Response, next: NextFunction) {
  try {
    const { status, comment } = req.body;
    const userId = (req as any).user?.userId;
    const result = await ethicsService.transitionStatus(req.params.id, status, userId, comment);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function expiringSoon(req: Request, res: Response, next: NextFunction) {
  try {
    const days = parseInt(req.query.days as string) || 60;
    const result = await ethicsService.getExpiringSoon(days);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await ethicsService.getStats(req.query.projectId as string | undefined);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getTimeline(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await ethicsService.getTimeline(req.params.projectId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const ethicsController = {
  create, list, getById, update, transitionStatus, expiringSoon, getStats, getTimeline,
};
