import { Request, Response, NextFunction } from 'express';
import { vendorService } from './vendor.service';
import { createVendorSchema, updateVendorSchema } from './vendor.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createVendorSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await vendorService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await vendorService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await vendorService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateVendorSchema.parse(req.body);
    const result = await vendorService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await vendorService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function updateRating(req: Request, res: Response, next: NextFunction) {
  try {
    const { score, comment } = req.body;
    const result = await vendorService.updateRating(req.params.id, score, comment);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function toggleBlacklist(req: Request, res: Response, next: NextFunction) {
  try {
    const { reason } = req.body;
    const result = await vendorService.toggleBlacklist(req.params.id, reason);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await vendorService.getStats();
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getContractStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await vendorService.getContractStats(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const vendorController = {
  create, list, getById, update, remove, updateRating, toggleBlacklist, getStats, getContractStats,
};
