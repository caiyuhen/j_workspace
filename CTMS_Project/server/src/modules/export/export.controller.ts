import { Request, Response, NextFunction } from 'express';
import { exportService } from './export.service';
import { exportDataSchema } from './export.dto';

async function exportData(req: Request, res: Response, next: NextFunction) {
  try {
    const input = exportDataSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await exportService.exportData(input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function history(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await exportService.getHistory(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const exportController = { exportData, history };
