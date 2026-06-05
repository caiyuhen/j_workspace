import { Request, Response, NextFunction } from 'express';
import { aeService } from './ae.service';
import {
  createAdverseEventSchema, updateAdverseEventSchema,
  createSaeReportSchema, submitSaeReportSchema, reviewSaeReportSchema,
} from './ae.dto';
import { z } from 'zod';

const closeEventSchema = z.object({ reason: z.string().min(1, '关闭原因不能为空') });

async function create(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createAdverseEventSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await aeService.create(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function list(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await aeService.getList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await aeService.getById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function update(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateAdverseEventSchema.parse(req.body);
    const result = await aeService.update(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function close(req: Request, res: Response, next: NextFunction) {
  try {
    const input = closeEventSchema.parse(req.body);
    const result = await aeService.close(req.params.id, input.reason);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// SAE 报告
async function createSaeReport(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createSaeReportSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await aeService.createSaeReport(req.params.id, input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getSaeReports(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await aeService.getSaeReports(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function updateSaeReport(req: Request, res: Response, next: NextFunction) {
  try {
    const content = req.body;
    const result = await aeService.updateSaeReport(req.params.id, req.params.reportId, content);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function reviewSaeReport(req: Request, res: Response, next: NextFunction) {
  try {
    const input = reviewSaeReportSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await aeService.reviewSaeReport(req.params.id, req.params.reportId, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function submitSaeReport(req: Request, res: Response, next: NextFunction) {
  try {
    const input = submitSaeReportSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await aeService.submitSaeReport(req.params.id, req.params.reportId, input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// 统计
async function getStatistics(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await aeService.getStatistics(req.query.projectId as string);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const aeController = {
  create, list, getById, update, close,
  createSaeReport, getSaeReports, updateSaeReport, reviewSaeReport, submitSaeReport,
  getStatistics,
};
