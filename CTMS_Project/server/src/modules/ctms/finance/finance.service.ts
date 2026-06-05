import prisma from '../../../config/database';
import { CreateIncomeInput, UpdateIncomeInput, CreateExpenseInput, UpdateExpenseInput } from './finance.dto';
import { parsePagination, buildPaginatedResult, prismaPagination } from '../../../shared/utils/pagination';
import { parseSort } from '../../../shared/utils/sort';
import { NotFoundError, ConflictError, BadRequestError } from '../../../shared/errors/AppError';
import logger from '../../../shared/utils/logger';

// ========== 收入管理 ==========

const INCOME_SORT_FIELDS = ['incomeCode', 'incomeType', 'amount', 'status', 'expectedDate', 'createdAt'];

async function createIncome(input: CreateIncomeInput) {
  const existing = await prisma.financialIncome.findUnique({
    where: { incomeCode: input.incomeCode },
  });
  if (existing) throw new ConflictError(`收入编码 ${input.incomeCode} 已存在`);

  const income = await prisma.financialIncome.create({
    data: {
      ...input,
      expectedDate: input.expectedDate ? new Date(input.expectedDate) : null,
      status: 'expected',
    },
  });

  logger.info('Income created', {
    audit: true,
    eventType: 'FINANCE_INCOME_CREATE',
    message: `创建收入记录 ${input.incomeCode}, 金额 ${input.amount}`,
  });

  return income;
}

async function getIncomeList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, INCOME_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.incomeType) where.incomeType = query.incomeType;
  if (query.status) where.status = query.status;

  const [incomes, total] = await Promise.all([
    prisma.financialIncome.findMany({
      where, ...prismaPagination(pagination),
      orderBy: sort.orderBy,
    }),
    prisma.financialIncome.count({ where }),
  ]);

  return buildPaginatedResult(incomes, total, pagination);
}

async function getIncomeById(id: string) {
  const income = await prisma.financialIncome.findUnique({ where: { id } });
  if (!income) throw new NotFoundError('FinancialIncome', id);
  return income;
}

async function updateIncome(id: string, input: UpdateIncomeInput) {
  const income = await prisma.financialIncome.findUnique({ where: { id } });
  if (!income) throw new NotFoundError('FinancialIncome', id);

  const data: any = { ...input };
  if (input.expectedDate) data.expectedDate = new Date(input.expectedDate);
  if (input.receivedDate) data.receivedDate = new Date(input.receivedDate);

  const updated = await prisma.financialIncome.update({ where: { id }, data });

  logger.info('Income updated', { audit: true, eventType: 'FINANCE_INCOME_UPDATE', message: `更新收入记录 ${income.incomeCode}` });
  return updated;
}

async function removeIncome(id: string) {
  const income = await prisma.financialIncome.findUnique({ where: { id } });
  if (!income) throw new NotFoundError('FinancialIncome', id);
  if (income.status === 'received') throw new BadRequestError('已收款的记录不能删除');

  await prisma.financialIncome.update({ where: { id }, data: { status: 'cancelled' } });
  logger.info('Income cancelled', { audit: true, eventType: 'FINANCE_INCOME_CANCEL', message: `取消收入记录 ${income.incomeCode}` });
  return { message: '收入记录已取消' };
}

// ========== 支出管理 ==========

const EXPENSE_SORT_FIELDS = ['expenseCode', 'expenseType', 'amount', 'status', 'expenseDate', 'createdAt'];

async function createExpense(input: CreateExpenseInput, userId: string) {
  const existing = await prisma.financialExpense.findUnique({
    where: { expenseCode: input.expenseCode },
  });
  if (existing) throw new ConflictError(`支出编码 ${input.expenseCode} 已存在`);

  const expense = await prisma.financialExpense.create({
    data: {
      ...input,
      expenseDate: new Date(input.expenseDate),
      submittedBy: input.submittedBy || userId,
      reimbursementStatus: 'pending',
      status: 'draft',
    },
  });

  logger.info('Expense created', {
    audit: true,
    eventType: 'FINANCE_EXPENSE_CREATE',
    message: `创建支出记录 ${input.expenseCode}, 金额 ${input.amount}`,
  });

  return expense;
}

async function getExpenseList(query: Record<string, any>) {
  const pagination = parsePagination(query);
  const sort = parseSort(query, EXPENSE_SORT_FIELDS);

  const where: any = {};
  if (query.projectId) where.projectId = query.projectId;
  if (query.expenseType) where.expenseType = query.expenseType;
  if (query.status) where.status = query.status;
  if (query.reimbursementStatus) where.reimbursementStatus = query.reimbursementStatus;

  const [expenses, total] = await Promise.all([
    prisma.financialExpense.findMany({
      where, ...prismaPagination(pagination),
      orderBy: sort.orderBy,
    }),
    prisma.financialExpense.count({ where }),
  ]);

  return buildPaginatedResult(expenses, total, pagination);
}

async function getExpenseById(id: string) {
  const expense = await prisma.financialExpense.findUnique({ where: { id } });
  if (!expense) throw new NotFoundError('FinancialExpense', id);
  return expense;
}

async function updateExpense(id: string, input: UpdateExpenseInput) {
  const expense = await prisma.financialExpense.findUnique({ where: { id } });
  if (!expense) throw new NotFoundError('FinancialExpense', id);

  const data: any = { ...input };
  if (input.expenseDate) data.expenseDate = new Date(input.expenseDate);

  const updated = await prisma.financialExpense.update({ where: { id }, data });

  logger.info('Expense updated', { audit: true, eventType: 'FINANCE_EXPENSE_UPDATE', message: `更新支出记录 ${expense.expenseCode}` });
  return updated;
}

async function removeExpense(id: string) {
  const expense = await prisma.financialExpense.findUnique({ where: { id } });
  if (!expense) throw new NotFoundError('FinancialExpense', id);
  if (expense.reimbursementStatus === 'reimbursed') throw new BadRequestError('已报销的记录不能删除');

  await prisma.financialExpense.update({ where: { id }, data: { status: 'cancelled' } });
  logger.info('Expense cancelled', { audit: true, eventType: 'FINANCE_EXPENSE_CANCEL', message: `取消支出记录 ${expense.expenseCode}` });
  return { message: '支出记录已取消' };
}

// ========== 收支汇总 ==========

async function getFinanceSummary(projectId: string) {
  const [incomeResult, expenseResult] = await Promise.all([
    prisma.financialIncome.aggregate({
      where: { projectId, status: { not: 'cancelled' } },
      _sum: { amount: true },
      _count: true,
    }),
    prisma.financialExpense.aggregate({
      where: { projectId, status: { not: 'cancelled' } },
      _sum: { amount: true },
      _count: true,
    }),
  ]);

  return {
    projectId,
    totalIncome: incomeResult._sum.amount || 0,
    totalExpense: expenseResult._sum.amount || 0,
    netAmount: (incomeResult._sum.amount || 0) - (expenseResult._sum.amount || 0),
    incomeCount: incomeResult._count,
    expenseCount: expenseResult._count,
  };
}

export const financeService = {
  createIncome, getIncomeList, getIncomeById, updateIncome, removeIncome,
  createExpense, getExpenseList, getExpenseById, updateExpense, removeExpense,
  getFinanceSummary,
};
