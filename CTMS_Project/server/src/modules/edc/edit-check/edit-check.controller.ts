import { Request, Response, NextFunction } from 'express';
import { editCheckService } from './edit-check.service';
import { testRuleSchema, executeFormChecksSchema } from './edit-check.dto';

async function testRule(req: Request, res: Response, next: NextFunction) {
  try {
    const input = testRuleSchema.parse(req.body);
    const result = await editCheckService.testRule(input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

async function executeFormChecks(req: Request, res: Response, next: NextFunction) {
  try {
    const input = executeFormChecksSchema.parse(req.body);
    const result = await editCheckService.executeFormChecks(input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const editCheckController = { testRule, executeFormChecks };
