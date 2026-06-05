import { Request, Response, NextFunction } from 'express';
import { financeService } from './finance.service';
import { createIncomeSchema, updateIncomeSchema, createExpenseSchema, updateExpenseSchema } from './finance.dto';

// POST /income - 创建收入
async function createIncome(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createIncomeSchema.parse(req.body);
    const result = await financeService.createIncome(input);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /income - 收入列表
async function listIncome(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await financeService.getIncomeList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /income/:id - 收入详情
async function getIncome(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await financeService.getIncomeById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// PUT /income/:id - 更新收入
async function updateIncome(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateIncomeSchema.parse(req.body);
    const result = await financeService.updateIncome(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// DELETE /income/:id - 取消收入
async function removeIncome(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await financeService.removeIncome(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// POST /expense - 创建支出
async function createExpense(req: Request, res: Response, next: NextFunction) {
  try {
    const input = createExpenseSchema.parse(req.body);
    const userId = (req as any).user?.userId;
    const result = await financeService.createExpense(input, userId);
    res.status(201).json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /expense - 支出列表
async function listExpense(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await financeService.getExpenseList(req.query as Record<string, any>);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /expense/:id - 支出详情
async function getExpense(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await financeService.getExpenseById(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// PUT /expense/:id - 更新支出
async function updateExpense(req: Request, res: Response, next: NextFunction) {
  try {
    const input = updateExpenseSchema.parse(req.body);
    const result = await financeService.updateExpense(req.params.id, input);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// DELETE /expense/:id - 取消支出
async function removeExpense(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await financeService.removeExpense(req.params.id);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

// GET /summary/:projectId - 项目收支汇总
async function getSummary(req: Request, res: Response, next: NextFunction) {
  try {
    const result = await financeService.getFinanceSummary(req.params.projectId);
    res.json({ success: true, data: result });
  } catch (err) { next(err); }
}

export const financeController = {
  createIncome, listIncome, getIncome, updateIncome, removeIncome,
  createExpense, listExpense, getExpense, updateExpense, removeExpense,
  getSummary,
};
