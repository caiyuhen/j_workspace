import { Request, Response, NextFunction } from 'express';
import { sdvService } from './sdv.service';
import {
  createSdvRecordSchema, updateSdvRecordSchema,
  createSdvItemSchema, updateSdvItemSchema, completeSdvSchema,
} from './sdv.dto';
import { z } from 'zod';

const batchUpdateSchema = z.object({
  updates: z.array(z.object({
    itemId: z.string().uuid(),
    data: updateSdvItemSchema,
  })),
});

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createSdvRecordSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await sdvService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await sdvService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await sdvService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function updateRecord(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateSdvRecordSchema.parse(req.body);
    const result = await sdvService.updateRecord(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function addItems(req: Request, res: Response, next: NextFunction) {
  try {
    const items = z.array(createSdvItemSchema).parse(req.body.items || req.body);
    const userId = (req as any).user?.userId;
    const result = await sdvService.addItems(req.params.id, items, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function updateItem(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateSdvItemSchema.parse(req.body);
    const result = await sdvService.updateItem(req.params.id, req.params.itemId, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function batchUpdateItems(req: Request, res: Response, next: NextFunction) {
  try {
    const input = batchUpdateSchema.parse(req.body);
    const result = await sdvService.batchUpdateItems(req.params.id, input.updates);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function complete(req: Request, res: Response, next: NextFunction) {
  try {
    const input = completeSdvSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await sdvService.complete(req.params.id, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getStatistics(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await sdvService.getStatistics(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const sdvController = {
  create, list, getById, updateRecord,
  addItems, updateItem, batchUpdateItems,
  complete, getStatistics,
};
