import api from './api';

export interface ScheduledPurchase {
  id?: number;
  purchase_type: string;
  scheduled_date: string;
  estimated_amount?: number;
  location?: string;
  merchant_preference?: string;
  notes?: string;
  recommended_card?: number;
  recommended_card_detail?: {
    id: number;
    name: string;
    bank: { id: number; name: string };
  };
  recommended_merchants?: Array<{
    merchant: string;
    discount: number;
    category: string;
    city: string;
    source_url: string;
    merchant_logo?: string;
    valid_to?: string;
  }>;
  active_offers?: Array<{
    title: string;
    merchant: string;
    discount: number;
    category: string;
    city: string;
    source_url: string;
    image?: string;
    valid_to?: string;
  }>;
  status: 'SCHEDULED' | 'COMPLETED' | 'CANCELLED';
  reminder_sent: boolean;
  created_at?: string;
  updated_at?: string;
  completed_at?: string;
}

export interface PurchaseRecommendations {
  recommended_card: {
    id: number;
    name: string;
    bank: string;
  } | null;
  recommended_merchants: Array<{
    merchant: string;
    discount: number;
    category: string;
    city: string;
    source_url: string;
    merchant_logo?: string;
    valid_to?: string;
  }>;
  active_offers: Array<{
    title: string;
    merchant: string;
    discount: number;
    category: string;
    city: string;
    source_url: string;
    image?: string;
    valid_to?: string;
  }>;
  purchase_type: string;
  location: string;
  scheduled_date: string;
}

export const planningService = {
  // Get all scheduled purchases
  getPurchases: async (status?: string): Promise<ScheduledPurchase[]> => {
    const params = status ? { status } : {};
    const response = await api.get('/planning/purchases/', { params });
    return response.data;
  },

  // Get upcoming purchases
  getUpcomingPurchases: async (days: number = 7): Promise<ScheduledPurchase[]> => {
    const response = await api.get('/planning/purchases/upcoming/', {
      params: { days },
    });
    return response.data;
  },

  // Create a scheduled purchase
  createPurchase: async (purchase: Partial<ScheduledPurchase>): Promise<ScheduledPurchase> => {
    const response = await api.post('/planning/purchases/', purchase);
    return response.data;
  },

  // Get purchase by ID
  getPurchase: async (id: number): Promise<ScheduledPurchase> => {
    const response = await api.get(`/planning/purchases/${id}/`);
    return response.data;
  },

  // Update purchase
  updatePurchase: async (id: number, purchase: Partial<ScheduledPurchase>): Promise<ScheduledPurchase> => {
    const response = await api.patch(`/planning/purchases/${id}/`, purchase);
    return response.data;
  },

  // Delete purchase
  deletePurchase: async (id: number): Promise<void> => {
    await api.delete(`/planning/purchases/${id}/`);
  },

  // Complete purchase
  completePurchase: async (id: number): Promise<ScheduledPurchase> => {
    const response = await api.post(`/planning/purchases/${id}/complete/`);
    return response.data;
  },

  // Get recommendations without creating purchase
  getRecommendations: async (data: {
    purchase_type: string;
    scheduled_date?: string;
    location?: string;
    estimated_amount?: number;
    merchant_preference?: string;
  }): Promise<PurchaseRecommendations> => {
    const response = await api.post('/planning/recommendations/', data);
    return response.data;
  },
};
