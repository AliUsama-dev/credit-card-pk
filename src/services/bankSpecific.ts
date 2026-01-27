// services/bankSpecific.ts
// API service for bank-specific deals

import api from './api';

export interface BankSpecificCity {
  id: number;
  bank: {
    id: number;
    name: string;
  };
  city_id: number;
  name: string;
  slug: string;
  country: string;
  latitude: number | null;
  longitude: number | null;
  image: string | null;
  is_active: boolean;
}

export interface BankSpecificCategory {
  id: number;
  bank: {
    id: number;
    name: string;
  };
  category_id: number;
  name: string;
  order: number;
  category_logo_url: string | null;
  image: string | null;
  is_active: boolean;
}

export interface BankSpecificEntity {
  id: number;
  bank: {
    id: number;
    name: string;
  };
  entity_id: number;
  name: string;
  slug: string;
  description: string | null;
  package: string | null;
  contact_number: string | null;
  keywords: string | null;
  entity_rating: number | null;
  cover: string | null;
  logo: string | null;
  gallery: string[];
  menu: string[];
  facebook: string | null;
  instagram: string | null;
  website: string | null;
  email: string | null;
  whatsapp: string | null;
  android: string | null;
  ios: string | null;
  total_branches: number;
  total_open_branches: number;
  total_associated_deals: number;
  max_discount: number;
  wishlist_count: number;
  review_counts: number;
  tags: Array<{
    tagId: number;
    tag: string;
    image: string | null;
    cover: string | null;
  }>;
  nearest_branch_id: number | null;
  nearest_branch_name: string | null;
  nearest_branch_lat_long: string | null;
  nearest_branch_distance: string | null;
  nearest_branch_open_now: boolean;
  nearest_branch_contact_number: string | null;
  branches: string | null;
  is_active: boolean;
  online_service_available: boolean;
}

export interface BankSpecificCardAssociation {
  id: number;
  bank: {
    id: number;
    name: string;
  };
  association_id: number;
  type_id: number;
  type_name: string;
  card_type: string;
  image: string | null;
  description: string | null;
  additional_info: string | null;
  amenities: Record<string, { value: string; image: string }>;
  amenity_count: number;
  deal_count: number;
  linked_card: {
    id: number;
    name: string;
    bank: string;
    card_type: string;
  } | null;
  is_active: boolean;
}

export interface BankSpecificFilters {
  bank?: number;
  city_id?: number;
  category_id?: number;
  search?: string;
  card_type?: string;
}

export const bankSpecificService = {
  // Get cities for a bank
  getCities: async (bankId?: number): Promise<BankSpecificCity[]> => {
    const params = new URLSearchParams();
    if (bankId) {
      params.append('bank', bankId.toString());
    }
    const url = `/offers/bank-specific/cities/${params.toString() ? '?' + params.toString() : ''}`;
    const response = await api.get<BankSpecificCity[]>(url);
    return response.data;
  },

  // Get categories for a bank
  getCategories: async (bankId?: number): Promise<BankSpecificCategory[]> => {
    const params = new URLSearchParams();
    if (bankId) {
      params.append('bank', bankId.toString());
    }
    const url = `/offers/bank-specific/categories/${params.toString() ? '?' + params.toString() : ''}`;
    const response = await api.get<BankSpecificCategory[]>(url);
    return response.data;
  },

  // Get entities/merchants for a bank
  getEntities: async (filters?: BankSpecificFilters): Promise<BankSpecificEntity[]> => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    const url = `/offers/bank-specific/entities/${params.toString() ? '?' + params.toString() : ''}`;
    const response = await api.get<BankSpecificEntity[]>(url);
    return response.data;
  },

  // Get card associations for a bank
  getCardAssociations: async (bankId?: number, cardType?: string): Promise<BankSpecificCardAssociation[]> => {
    const params = new URLSearchParams();
    if (bankId) {
      params.append('bank', bankId.toString());
    }
    if (cardType) {
      params.append('card_type', cardType);
    }
    const url = `/offers/bank-specific/card-associations/${params.toString() ? '?' + params.toString() : ''}`;
    const response = await api.get<BankSpecificCardAssociation[]>(url);
    return response.data;
  },

  // Trigger scraping
  triggerScraping: async (bankCode: string, cityId?: number, citySlug?: string): Promise<{ status: string; message: string; task_id?: string }> => {
    const response = await api.post('/offers/bank-specific/scrape/', {
      bank_code: bankCode,
      city_id: cityId,
      city_slug: citySlug,
    });
    return response.data;
  },
};

