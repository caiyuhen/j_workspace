import { Router } from 'express';
import { financeController } from './finance.controller';
import { requirePermission } from '../../../shared/middleware/rbac';

const router = Router();

// 收入管理
router.get('/income', financeController.listIncome as any);
router.post('/income', requirePermission('finance:income:create') as any, financeController.createIncome as any);
router.get('/income/:id', financeController.getIncome as any);
router.put('/income/:id', requirePermission('finance:income:update') as any, financeController.updateIncome as any);
router.delete('/income/:id', requirePermission('finance:income:delete') as any, financeController.removeIncome as any);

// 支出管理
router.get('/expense', financeController.listExpense as any);
router.post('/expense', requirePermission('finance:expense:create') as any, financeController.createExpense as any);
router.get('/expense/:id', financeController.getExpense as any);
router.put('/expense/:id', requirePermission('finance:expense:update') as any, financeController.updateExpense as any);
router.delete('/expense/:id', requirePermission('finance:expense:delete') as any, financeController.removeExpense as any);

// 收支汇总
router.get('/summary/:projectId', requirePermission('finance:view') as any, financeController.getSummary as any);

export default router;
