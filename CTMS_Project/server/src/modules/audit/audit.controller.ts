import { Request, Response, NextFunction } from 'express';
import { auditService } from './audit.service';

async function queryLogs(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await auditService.queryLogs(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await auditService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getRecordHistory(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await auditService.getRecordHistory(req.params.tableName, req.params.recordId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await auditService.getStats(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const auditController = { queryLogs, getById, getRecordHistory, getStats };
