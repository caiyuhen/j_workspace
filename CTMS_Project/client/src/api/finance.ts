<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  Income,
  CreateIncomeParams,
  Expense,
  CreateExpenseParams,
  FinanceSummary,
} from '@/types';

export const financeApi = {
  // 收入管理
  listIncome: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<Income>>>('/finance/income', { params }).then((r) => r.data.data),

  createIncome: (data: CreateIncomeParams) =>
    api.post<ApiResponse<Income>>('/finance/income', data).then((r) => r.data.data),

  getIncome: (id: string) =>
    api.get<ApiResponse<Income>>(`/finance/income/${id}`).then((r) => r.data.data),

  updateIncome: (id: string, data: Partial<CreateIncomeParams>) =>
    api.put<ApiResponse<Income>>(`/finance/income/${id}`, data).then((r) => r.data.data),

  removeIncome: (id: string) =>
    api.delete(`/finance/income/${id}`).then((r) => r.data),

  // 支出管理
  listExpense: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<Expense>>>('/finance/expense', { params }).then((r) => r.data.data),

  createExpense: (data: CreateExpenseParams) =>
    api.post<ApiResponse<Expense>>('/finance/expense', data).then((r) => r.data.data),

  getExpense: (id: string) =>
    api.get<ApiResponse<Expense>>(`/finance/expense/${id}`).then((r) => r.data.data),

  updateExpense: (id: string, data: Partial<CreateExpenseParams>) =>
    api.put<ApiResponse<Expense>>(`/finance/expense/${id}`, data).then((r) => r.data.data),

  removeExpense: (id: string) =>
    api.delete(`/finance/expense/${id}`).then((r) => r.data),

  // 收支汇总
  getSummary: (projectId: string) =>
    api.get<ApiResponse<FinanceSummary>>(`/finance/summary/${projectId}`).then((r) => r.data.data),
};
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
import api from './index';
import type { ApiResponse, PaginatedResponse } from '@/types';
import type {
  Income,
  CreateIncomeParams,
  Expense,
  CreateExpenseParams,
  FinanceSummary,
} from '@/types';

export const financeApi = {
  // 收入管理
  listIncome: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<Income>>>('/finance/income', { params }).then((r) => r.data.data),

  createIncome: (data: CreateIncomeParams) =>
    api.post<ApiResponse<Income>>('/finance/income', data).then((r) => r.data.data),

  getIncome: (id: string) =>
    api.get<ApiResponse<Income>>(`/finance/income/${id}`).then((r) => r.data.data),

  updateIncome: (id: string, data: Partial<CreateIncomeParams>) =>
    api.put<ApiResponse<Income>>(`/finance/income/${id}`, data).then((r) => r.data.data),

  removeIncome: (id: string) =>
    api.delete(`/finance/income/${id}`).then((r) => r.data),

  // 支出管理
  listExpense: (params?: Record<string, any>) =>
    api.get<ApiResponse<PaginatedResponse<Expense>>>('/finance/expense', { params }).then((r) => r.data.data),

  createExpense: (data: CreateExpenseParams) =>
    api.post<ApiResponse<Expense>>('/finance/expense', data).then((r) => r.data.data),

  getExpense: (id: string) =>
    api.get<ApiResponse<Expense>>(`/finance/expense/${id}`).then((r) => r.data.data),

  updateExpense: (id: string, data: Partial<CreateExpenseParams>) =>
    api.put<ApiResponse<Expense>>(`/finance/expense/${id}`, data).then((r) => r.data.data),

  removeExpense: (id: string) =>
    api.delete(`/finance/expense/${id}`).then((r) => r.data),

  // 收支汇总
  getSummary: (projectId: string) =>
    api.get<ApiResponse<FinanceSummary>>(`/finance/summary/${projectId}`).then((r) => r.data.data),
};
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
