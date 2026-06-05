import { Request, Response, NextFunction } from 'express';
import { signatureService } from './signature.service';
import { createSignatureSchema } from './signature.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createSignatureSchema.parse(req.body);
    const result = await signatureService.create(input, req.ip, req.get('User-Agent'));
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function batchCreate(req: Request, res: Response, next: NextFunction) {
  try {
    const { signatures } = req.body;
    const result = await signatureService.batchCreate(signatures, req.ip, req.get('User-Agent'));
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await signatureService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function verify(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await signatureService.verify(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function revoke(req: Request, res: Response, next: NextFunction) {
  try {
    const { reason } = req.body;
    const userId = (req as any).user?.userId;
    const result = await signatureService.revoke(req.params.id, userId, reason);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function auditTrail(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await signatureService.getAuditTrail(req.params.recordId, req.query.tableName as string);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function exportAuditReport(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await signatureService.exportAuditReport(req.params.recordId, req.query.tableName as string);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await signatureService.getStats(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const signatureController = {
  create, batchCreate, list, verify, revoke, auditTrail, exportAuditReport, getStats,
};
