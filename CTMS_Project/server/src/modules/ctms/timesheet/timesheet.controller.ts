import { Request, Response, NextFunction } from 'express';
import { timesheetService } from './timesheet.service';
import { createTimesheetSchema, submitTimesheetSchema, approveTimesheetSchema } from './timesheet.dto';

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createTimesheetSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await timesheetService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await timesheetService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await timesheetService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function submit(req: Request, res: Response, next: NextFunction) {
  try {
    const input = submitTimesheetSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await timesheetService.submit(req.params.id, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function approve(req: Request, res: Response, next: NextFunction) {
  try {
    const input = approveTimesheetSchema.parse(req.body);
    const approverId = (req as any).user?.userId;
    const result = await timesheetService.approve(req.params.id, input, approverId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const timesheetController = { create, list, getById, submit, approve };
