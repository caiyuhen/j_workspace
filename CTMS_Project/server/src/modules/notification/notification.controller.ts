import { Request, Response, NextFunction } from 'express';
import { notificationService } from './notification.service';
import { createNotificationSchema, batchCreateSchema } from './notification.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createNotificationSchema.parse(req.body);
    const result = await notificationService.create(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function batchCreate(req: Request, res: Response, next: NextFunction) {
  try {
    const input = batchCreateSchema.parse(req.body);
    const result = await notificationService.batchCreate(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function send(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await notificationService.send(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function sendPending(req: Request, res: Response, next: NextFunction) {
  try {
    const { channel } = req.query;
    const result = await notificationService.sendPending(channel as string | undefined);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await notificationService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await notificationService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function markAsRead(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await notificationService.markAsRead(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function markAllAsRead(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).user?.userId;
    const result = await notificationService.markAllAsRead(userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getUnreadCount(req: Request, res: Response, next: NextFunction) {
  try {
    const userId = (req as any).user?.userId;
    const result = await notificationService.getUnreadCount(userId);
    res.json({ success: true, data: { count: result } });
  } catch (err) { next(err); }
}

async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await notificationService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await notificationService.getStatsByBusinessType(req.query.projectId as string | undefined);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function cleanExpired(req: Request, res: Response, next: NextFunction) {
  try {
    const days = parseInt(req.query.days as string) || 90;
    const result = await notificationService.cleanExpired(days);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const notificationController = {
  create, batchCreate, send, sendPending, list, getById,
  markAsRead, markAllAsRead, getUnreadCount, remove, getStats, cleanExpired,
};
