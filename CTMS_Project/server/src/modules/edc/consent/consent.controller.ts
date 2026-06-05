import { Request, Response, NextFunction } from 'express';
import { consentService } from './consent.service';
import { createConsentSchema, updateConsentSchema } from './consent.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createConsentSchema.parse(req.body);
    const result = await consentService.create(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await consentService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await consentService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateConsentSchema.parse(req.body);
    const result = await consentService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function subjectHistory(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await consentService.getSubjectHistory(
      req.query.projectId as string,
      req.query.siteId as string,
      req.query.subjectId as string,
    );
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function withdraw(req: Request, res: Response, next: NextFunction) {
  try {
    const { reason } = req.body;
    const userId = (req as any).user?.userId;
    const result = await consentService.withdraw(req.params.id, reason, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await consentService.getConsentStats(req.query.projectId as string | undefined);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getVersions(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await consentService.getVersions(req.params.projectId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const consentController = {
  create, list, getById, update, subjectHistory, withdraw, getStats, getVersions,
};
