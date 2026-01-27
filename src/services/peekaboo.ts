// services/peekaboo.ts
// API service for Peekaboo deals

import api from './api';

export interface PeekabooDeal {
  id: number;
  deal_id: number;
  title: string;
  description: string;
  percentage_value: number | null;
  discount_amount: number | null;
  target_entity_id: number | null;
  target_entity_name: string | null;
  target_entity_logo: string | null;
  start_date: string;
  end_date: string;
  is_redeemable: boolean;
  redeemable_count: number;
  redeemed_count: number;
  image: string | null;
  keywords: string[];
  target_branches: Record<string, string>; // {branch_id: branch_name}
  order_type: string | null;
  powered_by: string | null;
  expires_in: number | null;
  category: string | null;
  city: string | null;
  bank: {
    id: number;
    name: string;
    logo: string | null;
  } | null;
  linked_cards?: Array<{
    id: number;
    name: string;
    bank?: string;
    card_type?: string;
  }>;
  associations?: Array<{
    typeId: number;
    name: string;
    image: string;
    order: number;
    sourceEntityAssociationId: number;
  }>;
  source_entity?: {
    id: number | null;
    name: string | null;
    logo: string | null;
  };
  is_active: boolean;
  is_expired: boolean;
  is_currently_valid: boolean;
  days_remaining: number | null;
  hours_remaining: number | null;
  created_at: string;
  updated_at: string;
  last_scraped_at: string | null;
}

export interface PeekabooCategory {
  id: number;
  category_id: string;
  name: string;
  slug: string | null;
  description: string | null;
  icon: string | null;
  is_active: boolean;
  display_order: number;
}

export interface PeekabooDealFilters {
  city?: string;
  category?: string;
  bank?: number;
  search?: string;
  show_expired?: boolean;
}

export const peekabooService = {
  // Get all deals
  getDeals: async (filters?: PeekabooDealFilters): Promise<PeekabooDeal[]> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    const url = `/offers/peekaboo/deals/${params.toString() ? '?' + params.toString() : ''}`;
    const response = await api.get<PeekabooDeal[]>(url);
    return response.data;
  },

  // Get deals filtered by bank and/or card
  getDealsByBankCard: async (filters?: { bank_id?: number; card_id?: number; city?: string; search?: string; show_expired?: boolean }): Promise<PeekabooDeal[]> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    const url = `/offers/peekaboo/deals/by-bank-card/${params.toString() ? '?' + params.toString() : ''}`;
    const response = await api.get<PeekabooDeal[]>(url);
    return response.data;
  },

  // Get deals for user's cards (with pagination support)
  getDealsForMyCards: async (filters?: PeekabooDealFilters & { page?: number; card_id?: number; bank_id?: number; city?: string }): Promise<{ count: number; next: string | null; previous: string | null; results: PeekabooDeal[] } | PeekabooDeal[]> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '' && key !== 'page') {
          params.append(key, value.toString());
        }
      });
      // Add page parameter
      if (filters.page) {
        params.append('page', filters.page.toString());
      }
    }
    const url = `/offers/peekaboo/deals/my-cards/${params.toString() ? '?' + params.toString() : ''}`;
    const response = await api.get<{ count: number; next: string | null; previous: string | null; results: PeekabooDeal[] } | PeekabooDeal[]>(url);
    // Return the response as-is (backend always returns paginated format now)
    return response.data;
  },

  // Get categories
  getCategories: async (): Promise<PeekabooCategory[]> => {
    const response = await api.get<PeekabooCategory[]>('/offers/peekaboo/categories/');
    return response.data;
  },

  // Get entities filtered by card (with deals)
  getEntitiesByCard: async (filters: { bank_id: number; card_id: number; city?: string; limit?: number; offset?: number; sort_by?: string }): Promise<{
    entities: Array<{
      id: number;
      entity_id: number;
      name: string;
      slug: string;
      description: string;
      logo: string;
      rating: number;
      stats: { 
        branches: number; 
        partnerOffers: number; 
        brandOffers: number;
        maxDiscount: number;
        discountFlag: string | null;
      };
      nearestBranch: { 
        id: number; 
        name: string; 
        lat: number; 
        long: number; 
        distance: number;
        openNow?: boolean;
      };
      online: boolean;
      openNow?: boolean;
      deals: Array<{
        id: number;
        deal_id: number;
        title: string;
        description: string;
        percentage_value: number | null;
        start_date: string;
        end_date: string;
        target_entity_name: string;
        target_entity_logo: string;
        target_branches?: Record<string, string>;
        associations?: Array<{
          typeId: number;
          name: string;
          image: string;
          order: number;
        }>;
        is_currently_valid?: boolean;
        days_remaining?: number;
      }>;
      deal_count: number;
    }>;
    total: number;
    nextPage: boolean;
    limit: number;
    offset: number;
  }> => {
    const params = new URLSearchParams();
    params.append('bank_id', filters.bank_id.toString());
    params.append('card_id', filters.card_id.toString());
    if (filters.city) params.append('city', filters.city);
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    const response = await api.get(`/offers/peekaboo/entities/by-card/?${params.toString()}`);
    return response.data;
  },

  // Get entities for ALL user cards (for "My Cards" tab - automatic)
  getEntitiesForUserCards: async (filters: { city?: string; limit?: number; offset?: number; sort_by?: string }): Promise<{
    entities: Array<{
      id: number;
      entity_id: number;
      name: string;
      slug: string;
      description: string;
      logo: string;
      rating: number;
      stats: { 
        branches: number; 
        partnerOffers: number; 
        brandOffers: number;
        maxDiscount: number;
        discountFlag: string | null;
      };
      nearestBranch: { 
        id: number; 
        name: string; 
        lat: number; 
        long: number; 
        distance: number;
        openNow?: boolean;
      };
      online: boolean;
      openNow?: boolean;
      deals: Array<{
        id: number;
        deal_id: number;
        title: string;
        description: string;
        percentage_value: number | null;
        start_date: string;
        end_date: string;
        target_entity_name: string;
        target_entity_logo: string;
        target_branches?: Record<string, string>;
        associations?: Array<{
          typeId: number;
          name: string;
          image: string;
          order: number;
        }>;
        is_currently_valid?: boolean;
        days_remaining?: number;
      }>;
      deal_count: number;
      cards?: Array<{ id: number; name: string; bank: string }>;
    }>;
    total: number;
    nextPage: boolean;
    limit: number;
    offset: number;
  }> => {
    const params = new URLSearchParams();
    if (filters.city) params.append('city', filters.city);
    if (filters.limit) params.append('limit', filters.limit.toString());
    if (filters.offset) params.append('offset', filters.offset.toString());
    if (filters.sort_by) params.append('sort_by', filters.sort_by);
    const response = await api.get(`/offers/peekaboo/entities/for-user-cards/?${params.toString()}`);
    return response.data;
  },

  // Trigger scraping
  triggerScraping: async (options?: { bank_code?: string; scrape_all_banks?: boolean; scrape_card_associations?: boolean; city?: string }): Promise<{ status: string; message: string; task_id?: string; task_ids?: any; results?: any }> => {
    const payload: { bank_code?: string; scrape_all_banks?: boolean; scrape_card_associations?: boolean; city?: string } = {};
    if (options?.bank_code) {
      payload.bank_code = options.bank_code;
      if (options.city) {
        payload.city = options.city;
      }
      if (options.scrape_card_associations) {
        payload.scrape_card_associations = true;
      }
    } else if (options?.scrape_all_banks) {
      payload.scrape_all_banks = true;
    }
    const response = await api.post('/offers/peekaboo/scrape/', payload);
    return response.data;
  },
};

