import { z } from 'zod';

// ========== 收支管理 DTO ==========

export const createIncomeSchema = z.object({
  projectId: z.string().uuid().optional(),
  incomeCode: z.string().min(1, '收入编码不能为空').max(50),
  incomeType: z.enum(['milestone', 'periodic', 'reimbursement', 'other']),
  amount: z.number().nonnegative('金额不能为负'),
  currency: z.string().length(3).optional().default('CNY'),
  expectedDate: z.string().datetime({ offset: true }).optional().or(z.string().date().optional()),
  description: z.string().optional(),
});
export type CreateIncomeInput = z.infer<typeof createIncomeSchema>;

export const updateIncomeSchema = createIncomeSchema.partial().extend({
  receivedDate: z.string().datetime({ offset: true }).optional().or(z.string().date().optional()),
  status: z.enum(['expected', 'received', 'overdue', 'cancelled']).optional(),
});
export type UpdateIncomeInput = z.infer<typeof updateIncomeSchema>;

export const createExpenseSchema = z.object({
  projectId: z.string().uuid().optional(),
  expenseCode: z.string().min(1, '支出编码不能为空').max(50),
  expenseType: z.enum(['personnel', 'equipment', 'travel', 'site_fee', 'monitoring', 'regulatory', 'data_management', 'other']),
  amount: z.number().nonnegative('金额不能为负'),
  currency: z.string().length(3).optional().default('CNY'),
  expenseDate: z.string().datetime({ offset: true }).or(z.string().date()),
  description: z.string().optional(),
  submittedBy: z.string().uuid().optional(),
});
export type CreateExpenseInput = z.infer<typeof createExpenseSchema>;

export const updateExpenseSchema = createExpenseSchema.partial().extend({
  reimbursementStatus: z.enum(['pending', 'submitted', 'approved', 'reimbursed', 'rejected']).optional(),
  status: z.enum(['draft', 'confirmed', 'cancelled']).optional(),
});
export type UpdateExpenseInput = z.infer<typeof updateExpenseSchema>;
