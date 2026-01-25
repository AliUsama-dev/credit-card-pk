import api from './api';

export interface Transaction {
  id: number;
  date: string;
  merchant: string;
  amount: number;
  category: string;
  description?: string;
  reward_earned: number;
  potential_reward: number;
  missed_savings: number;
  card?: {
    id: number;
    name: string;
    bank: string;
  };
  recommended_card_id?: number;
}

export interface TransactionFilters {
  category?: string;
  start_date?: string;
  end_date?: string;
  card_id?: number;
  search?: string;
  page?: number;
  page_size?: number;
}

export interface TransactionSummary {
  total_spent: number;
  total_reward_earned: number;
  total_potential_reward: number;
  total_missed_savings: number;
}

export interface SavingsAnalysis {
  period_days: number;
  total_spent: number;
  total_reward_earned: number;
  total_potential_reward: number;
  total_missed_savings: number;
  projected_annual_savings: number;
  by_category: Record<string, {
    name: string;
    total_spent: number;
    reward_earned: number;
    potential_reward: number;
    missed_savings: number;
    transaction_count: number;
  }>;
  recommended_actions: Array<{
    merchant: string;
    amount: number;
    category: string;
    recommended_card: string;
    missed_savings: number;
    date: string;
  }>;
}

export interface SpendingCategory {
  code: string;
  name: string;
  amount: number;
  percentage: number;
  transaction_count: number;
}

export const transactionsService = {
  // Upload statement PDF
  uploadStatement: async (file: File, cardId?: number): Promise<{
    status: string;
    message: string;
    transactions: any[];
    analysis: any;
    saved_count: number;
  }> => {
    const formData = new FormData();
    formData.append('statement', file);
    if (cardId) {
      formData.append('card_id', cardId.toString());
    }
    
    const response = await api.post('/transactions/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Get transactions list
  getTransactions: async (filters?: TransactionFilters): Promise<{
    transactions: Transaction[];
    pagination: {
      page: number;
      page_size: number;
      total: number;
      total_pages: number;
    };
    summary: TransactionSummary;
  }> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    
    const response = await api.get(`/transactions/transactions/?${params.toString()}`);
    return response.data;
  },

  // Get savings analysis
  getSavingsAnalysis: async (days: number = 30): Promise<SavingsAnalysis> => {
    const response = await api.get(`/transactions/savings-analysis/?days=${days}`);
    return response.data;
  },

  // Get spending categories
  getSpendingCategories: async (days: number = 30): Promise<SpendingCategory[]> => {
    const response = await api.get(`/transactions/categories/?days=${days}`);
    return response.data;
  },

  // Export transactions
  exportTransactions: async (format: 'csv' | 'json', filters?: TransactionFilters): Promise<Blob> => {
    const params = new URLSearchParams();
    params.append('format', format);
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '' && key !== 'page' && key !== 'page_size') {
          params.append(key, value.toString());
        }
      });
    }
    
    const response = await api.get(`/transactions/export/?${params.toString()}`, {
      responseType: 'blob',
    });
    return response.data;
  },
};

