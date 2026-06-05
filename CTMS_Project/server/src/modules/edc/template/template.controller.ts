import { Request, Response, NextFunction } from 'express';
import { templateService } from './template.service';
import { createTemplateSchema, updateTemplateSchema, cloneTemplateSchema } from './template.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createTemplateSchema.parse(req.body);
    const result = await templateService.create(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await templateService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await templateService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateTemplateSchema.parse(req.body);
    const result = await templateService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function publish(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await templateService.publish(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function deprecate(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await templateService.deprecate(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function clone(req: Request, res: Response, next: NextFunction) {
  try {
    const input = cloneTemplateSchema.parse(req.body);
    const result = await templateService.clone(req.params.id, input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const templateController = { create, list, getById, update, publish, deprecate, clone };
