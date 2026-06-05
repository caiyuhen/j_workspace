// ==================== 财务收支 ====================

export interface Income {
  id: string;
  projectId: string;
  incomeType: 'contract' | 'milestone' | 'amendment' | 'other';
  amount: number;
  currency: string;
  expectedDate: string;
  receivedDate?: string;
  invoiceNumber?: string;
  description: string;
  status: 'expected' | 'invoiced' | 'received' | 'overdue';
  createdAt: string;
  updatedAt: string;
}

export interface CreateIncomeParams {
  projectId: string;
  incomeType: 'contract' | 'milestone' | 'amendment' | 'other';
  amount: number;
  currency?: string;
  expectedDate: string;
  invoiceNumber?: string;
  description: string;
}

export interface Expense {
  id: string;
  projectId: string;
  category: 'personnel' | 'travel' | 'equipment' | 'supply' | 'subcontract' | 'miscellaneous';
  amount: number;
  currency: string;
  expenseDate: string;
  invoiceNumber?: string;
  vendor?: string;
  description: string;
  status: 'pending' | 'approved' | 'rejected' | 'paid';
  approvedById?: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateExpenseParams {
  projectId: string;
  category: 'personnel' | 'travel' | 'equipment' | 'supply' | 'subcontract' | 'miscellaneous';
  amount: number;
  currency?: string;
  expenseDate: string;
  invoiceNumber?: string;
  vendor?: string;
  description: string;
}

export interface FinanceSummary {
  projectId: string;
  totalIncome: number;
  totalExpense: number;
  balance: number;
  incomeByType: { type: string; amount: number }[];
  expenseByCategory: { category: string; amount: number }[];
  monthlyTrend: { month: string; income: number; expense: number }[];
}
