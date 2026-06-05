import { Request, Response, NextFunction } from 'express';
import { syncService } from './sync.service';
import { triggerSyncSchema } from './sync.dto';

async function trigger(req: Request, res: Response, next: NextFunction) {
  try {
    const input = triggerSyncSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await syncService.triggerSync(input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function listLogs(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await syncService.getLogList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function stats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await syncService.getStats(req.query.projectId as string);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const syncController = { trigger, listLogs, stats };
