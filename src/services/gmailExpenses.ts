import api from './api';

// Types
export interface GmailAccount {
  id: number;
  email: string;
  is_active: boolean;
  auto_sync_enabled: boolean;
  sync_frequency_hours: number;
  last_sync_at: string | null;
  created_at: string;
}

export interface EmailTransaction {
  id: number;
  email_id: string;
  email_subject: string;
  email_from: string;
  email_date: string;
  merchant_name: string;
  transaction_date: string;
  amount: string;
  currency: string;
  tax_amount: string | null;
  invoice_id: string | null;
  order_id: string | null;
  category: string;
  category_display: string;
  is_business_expense: boolean;
  is_tax_deductible: boolean;
  reimbursement_status: string;
  status: string;
  user_verified: boolean;
  bank: number | null;
  bank_name: string | null;
  card: number | null;
  extraction_confidence: string;
  created_at: string;
  updated_at: string;
}

export interface BillDocument {
  id: number;
  file_name: string;
  file_path: string;
  file_url: string;
  file_type: string;
  file_size: number;
  merchant_name: string;
  bill_date: string;
  amount: string;
  invoice_number: string | null;
  category: string | null;
  tags: string[];
  primary_tag: string;
  ocr_processed: boolean;
  created_at: string;
}

export interface ExpenseClaim {
  id: number;
  title: string;
  description: string | null;
  total_amount: string;
  currency: string;
  claim_date: string;
  submission_date: string | null;
  status: string;
  transactions_count: number;
  bills_count: number;
  created_at: string;
  updated_at: string;
}

export interface ExpenseDashboard {
  period: string;
  start_date: string | null;
  total_spending: number;
  category_breakdown: Array<{
    category: string;
    total: string;
    count: number;
  }>;
  merchant_breakdown: Array<{
    merchant_name: string;
    total: string;
    count: number;
  }>;
  monthly_trend: Array<{
    month: string;
    total: number;
  }>;
  business_total: number;
  personal_total: number;
  tax_deductible_total: number;
  transaction_count: number;
}

export interface TaxReport {
  year: number;
  direct_taxes: number;
  indirect_taxes: number;
  total_taxes: number;
  tax_deductible_expenses: number;
  business_expenses: number;
  personal_expenses: number;
  missing_invoices_count: number;
  missing_invoices_alert: boolean;
}

// Service
export const gmailExpensesService = {
  // Gmail Account Management
  getAuthorizationUrl: async () => {
    const response = await api.get<{ authorization_url: string; redirect_uri: string }>('/gmail/accounts/authorize/');
    return response.data;
  },

  handleOAuthCallback: async (code: string, state: string) => {
    const response = await api.post<GmailAccount>('/gmail/accounts/callback/', { code, state });
    return response.data;
  },

  getGmailAccounts: async () => {
    const response = await api.get<GmailAccount[]>('/gmail/accounts/');
    return response.data;
  },

  syncGmailAccount: async (accountId: number) => {
    const response = await api.post<{ message: string; task_id: string }>(`/gmail/accounts/${accountId}/sync/`);
    return response.data;
  },

  revokeGmailAccount: async (accountId: number) => {
    const response = await api.post<{ message: string }>(`/gmail/accounts/${accountId}/revoke/`);
    return response.data;
  },

  // Email Transactions
  getTransactions: async (filters?: {
    category?: string;
    merchant?: string;
    start_date?: string;
    end_date?: string;
    is_business?: boolean;
  }) => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    const response = await api.get<EmailTransaction[]>(`/gmail/transactions/${params.toString() ? '?' + params.toString() : ''}`);
    return response.data;
  },

  getTransaction: async (id: number) => {
    const response = await api.get<EmailTransaction>(`/gmail/transactions/${id}/`);
    return response.data;
  },

  verifyTransaction: async (id: number) => {
    const response = await api.patch<EmailTransaction>(`/gmail/transactions/${id}/verify/`);
    return response.data;
  },

  updateTransactionCategory: async (id: number, category: string) => {
    const response = await api.patch<EmailTransaction>(`/gmail/transactions/${id}/update_category/`, { category });
    return response.data;
  },

  // Bills
  getBills: async (filters?: {
    merchant?: string;
    start_date?: string;
    end_date?: string;
  }) => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    const response = await api.get<BillDocument[]>(`/gmail/bills/${params.toString() ? '?' + params.toString() : ''}`);
    return response.data;
  },

  downloadBill: async (id: number) => {
    const response = await api.get(`/gmail/bills/${id}/download/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Dashboard
  getDashboard: async (period: 'month' | 'year' | 'all' = 'month') => {
    const response = await api.get<ExpenseDashboard>(`/gmail/dashboard/?period=${period}`);
    return response.data;
  },

  // Tax Report
  getTaxReport: async (year?: number) => {
    const url = year ? `/gmail/tax-report/?year=${year}` : '/gmail/tax-report/';
    const response = await api.get<TaxReport>(url);
    return response.data;
  },

  // Expense Claims
  getExpenseClaims: async () => {
    const response = await api.get<ExpenseClaim[]>('/gmail/expense-claims/');
    return response.data;
  },

  createExpenseClaim: async (data: {
    title: string;
    description?: string;
    transactions: number[];
    bills: number[];
  }) => {
    const response = await api.post<ExpenseClaim>('/gmail/expense-claims/', data);
    return response.data;
  },

  generateExpenseClaimPDF: async (id: number) => {
    const response = await api.post(`/gmail/expense-claims/${id}/generate_pdf/`);
    return response.data;
  },

  generateExpenseClaimCSV: async (id: number) => {
    const response = await api.post(`/gmail/expense-claims/${id}/generate_csv/`);
    return response.data;
  },
};
