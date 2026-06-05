import { Request, Response, NextFunction } from 'express';
import { subjectService } from './subject.service';
import { createSubjectSchema, updateSubjectSchema } from './subject.dto';
import { z } from 'zod';

const createVisitSchema = z.object({
  visitCode: z.string().min(1),
  visitName: z.string().min(1),
  plannedDate: z.string().datetime({ offset: true }).or(z.string().date()),
  siteId: z.string().uuid().optional(),
});

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createSubjectSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await subjectService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await subjectService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await subjectService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateSubjectSchema.parse(req.body);
    const result = await subjectService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function createVisit(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createVisitSchema.parse(req.body);
    const result = await subjectService.createVisit(req.params.id, input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getVisits(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await subjectService.getVisits(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const subjectController = { create, list, getById, update, createVisit, getVisits };
