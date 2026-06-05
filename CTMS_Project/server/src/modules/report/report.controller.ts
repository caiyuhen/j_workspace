import { Request, Response, NextFunction } from 'express';
import { reportService } from './report.service';
import { createReportTemplateSchema, generateReportSchema } from './report.dto';

async function createTemplate(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createReportTemplateSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await reportService.createTemplate(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function listTemplates(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await reportService.getTemplateList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getTemplateById(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await reportService.getTemplateById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function updateTemplate(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createReportTemplateSchema.partial().parse(req.body);
    const result = await reportService.updateTemplate(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function generate(req: Request, res: Response, next: NextFunction) {
  try {
    const input = generateReportSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await reportService.generate(input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function listInstances(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await reportService.getInstanceList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const reportController = { createTemplate, listTemplates, getTemplateById, updateTemplate, generate, listInstances };
