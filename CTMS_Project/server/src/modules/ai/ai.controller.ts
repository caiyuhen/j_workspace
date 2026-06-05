import { Request, Response, NextFunction } from 'express';
import { aiService } from './ai.service';
import { chatSchema, batchProcessSchema, analyzeSchema } from './ai.dto';

async function chat(req: Request, res: Response, next: NextFunction) {
  try {
    const input = chatSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await aiService.chat(input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function batchProcess(req: Request, res: Response, next: NextFunction) {
  try {
    const input = batchProcessSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await aiService.batchProcess(input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function analyze(req: Request, res: Response, next: NextFunction) {
  try {
    const input = analyzeSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await aiService.analyze(input, userId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getAgentList(req: Request, res: Response, next: NextFunction) {
  try {
    const result = aiService.getAgentList();
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function getLogs(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await aiService.getLogs(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const aiController = { chat, batchProcess, analyze, getAgentList, getLogs };
