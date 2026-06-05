import { Request, Response, NextFunction } from 'express';
import { queryService } from './query.service';
import { createQuerySchema, replyQuerySchema } from './query.dto';
import { z } from 'zod';

const reassignSchema = z.object({
  assignedTo: z.string().uuid(),
});

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createQuerySchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await queryService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await queryService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await queryService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function reply(req: Request, res: Response, next: NextFunction) {
  try {
    const input = replyQuerySchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await queryService.reply(req.params.id, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function reassign(req: Request, res: Response, next: NextFunction) {
  try {
    const input = reassignSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await queryService.reassign(req.params.id, input.assignedTo, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const queryController = { create, list, getById, reply, reassign };
