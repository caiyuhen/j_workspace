import { Request, Response, NextFunction } from 'express';
import { contractService } from './contract.service';
import { createContractSchema, updateContractSchema } from './contract.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createContractSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await contractService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await contractService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await contractService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateContractSchema.parse(req.body);
    const result = await contractService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await contractService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function transitionStatus(req: Request, res: Response, next: NextFunction) {
  try {
    const { status } = req.body;
    const userId = (req as any).user?.userId;
    const result = await contractService.transitionStatus(req.params.id, status, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function expiringSoon(req: Request, res: Response, next: NextFunction) {
  try {
    const days = parseInt(req.query.days as string) || 30;
    const result = await contractService.getExpiringSoon(days);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await contractService.getStats(req.query.projectId as string | undefined);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const contractController = {
  create, list, getById, update, remove, transitionStatus, expiringSoon, getStats,
};
