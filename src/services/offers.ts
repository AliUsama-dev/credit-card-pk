// src/services/offers.ts - Update
import api from './api';

export interface Offer {
  id: number;
  title: string;
  description: string;
  offer_type: string;
  bank: {
    id: number;
    name: string;
    code: string;
    logo?: string;
  };
  card?: {
    id: number;
    name: string;
    card_type: string;
  };
  merchant?: {
    id: number;
    name: string;
    merchant_type: string;
    city: string;
    address?: string;
    logo?: string;
  };
  discount_percentage?: number;
  cashback_amount?: number;
  min_spend?: number;
  max_discount?: number;
  valid_from: string;
  valid_to: string;
  terms_conditions?: string;
  is_active: boolean;
  status?: string;
  days_remaining?: number;
  last_updated: string;
  created_at: string;
}

export interface OfferFilters {
  bank?: number;
  offer_type?: string;
  merchant_type?: string;
  city?: string;
  card_type?: string;
  search?: string;
}

export interface OfferStats {
  total_offers: number;
  active_offers: number;
  offers_by_bank: Array<{ bank__name: string; count: number }>;
  offers_by_city: Array<{ merchant__city: string; count: number }>;
  offers_by_type: Array<{ offer_type: string; count: number }>;
  recent_scrapes: Array<any>;
}

export interface ScrapingResult {
  status: string;
  message?: string;
  task_id?: string;
  bank?: {
    id: number;
    name: string;
    code: string;
  };
  error?: string;
}

export const offerService = {
  // Get all offers with filters
  getOffers: async (filters?: OfferFilters) => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          params.append(key, value.toString());
        }
      });
    }
    const response = await api.get<Offer[]>(`/offers/?${params.toString()}`);
    return response.data;
  },

  // Get personalized offers
  getPersonalizedOffers: () => {
    return api.get<Offer[]>('/offers/personalized/');
  },

  // Get offers by bank
  getBankOffers: (bankId: number) => {
    return api.get<Offer[]>(`/offers/bank/${bankId}/`);
  },

  // Get offers by city
  getCityOffers: (city: string) => {
    return api.get<Offer[]>(`/offers/city/${city}/`);
  },

  // Get offers by merchant type
  getMerchantTypeOffers: (merchantType: string) => {
    return api.get<Offer[]>(`/offers/merchant-type/${merchantType}/`);
  },

  // Get offer statistics
  getOfferStats: async () => {
    const response = await api.get<OfferStats>('/offers/stats/');
    return response.data;
  },

  // Scrape offers for a bank
  scrapeBankOffers: (bankId: number, payload?: { city?: string; merchant_type?: string; card_type?: string; offer_type?: string; search?: string }) => {
    return api.post<ScrapingResult>(`/offers/bank/${bankId}/scrape/`, payload || {});
  },

  // Get scraping status
  getScrapingStatus: (taskId: string) => {
    return api.get(`/scraping/status/?task_id=${taskId}`);
  },

  // Activate an offer
  activateOffer: (offerId: number) => {
    return api.post(`/offers/${offerId}/activate/`);
  },
};