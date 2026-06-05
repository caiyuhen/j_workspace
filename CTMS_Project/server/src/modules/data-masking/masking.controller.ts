import { Request, Response, NextFunction } from 'express';
import { maskingService } from './masking.service';
import { createMaskingRuleSchema, updateMaskingRuleSchema, previewMaskSchema } from './masking.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createMaskingRuleSchema.parse(req.body);
    const result = await maskingService.create(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await maskingService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await maskingService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateMaskingRuleSchema.parse(req.body);
    const result = await maskingService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function remove(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await maskingService.remove(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function preview(req: Request, res: Response, next: NextFunction) {
  try {
    const input = previewMaskSchema.parse(req.body);
    const result = await maskingService.preview(input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function batchMask(req: Request, res: Response, next: NextFunction) {
  try {
    const { records, tableName } = req.body;
    const result = await maskingService.batchMask(records, tableName);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getSuggestions(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await maskingService.getSuggestions(req.query.tableName as string | undefined);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getStats(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await maskingService.getStats();
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const maskingController = {
  create, list, getById, update, remove, preview, batchMask, getSuggestions, getStats,
};
