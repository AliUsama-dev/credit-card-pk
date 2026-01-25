import api from './api';

export interface Bank {
  id: number | null;
  name: string;
  code: string;
  logo?: string;
  website: string;
  support_email?: string;
  support_phone?: string;
  is_active: boolean;
  created_at?: string;
  is_available?: boolean; // For virtual banks not yet in database
  bank_type?: string;
  country?: string;
}

export interface CreditCard {
  id: number;
  name: string;
  bank: Bank;
  card_type: string;
  annual_fee: number;
  interest_rate: number | null;
  credit_limit_min: number | null;
  credit_limit_max: number | null;
  reward_points_rate: number;
  cashback_rate: number;
  welcome_bonus: string | null;
  requirements: string | null;
  features: string | null;
  image: string | null;
  image_url: string | null;
  scraping_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface UserCard {
  id: number;
  user: number;
  card: CreditCard;
  card_number_last4: string;
  expiry_date: string;
  is_primary: boolean;
  is_active: boolean;
  linked_at: string;
}

export interface CardFilters {
  bank?: number;
  card_type?: string;
  search?: string;
  show_all?: boolean | string;
}

export const bankService = {
  getBanks: async () => {
    try {
      const response = await api.get<Bank[] | { results?: Bank[]; data?: Bank[] }>('/cards/banks/');
      console.log('🏦 Bank Service Response:', response);
      console.log('🏦 Bank Service Data:', response.data);
      console.log('🏦 Bank Service Data Type:', typeof response.data);
      console.log('🏦 Bank Service Data Is Array:', Array.isArray(response.data));
      
      // Handle different response structures
      const data = response.data;
      if (Array.isArray(data)) {
        console.log('🏦 Returning', data.length, 'banks');
        return data;
      } else if (data && typeof data === 'object' && 'results' in data && Array.isArray(data.results)) {
        console.log('🏦 Returning', data.results.length, 'banks from results');
        return data.results;
      } else if (data && typeof data === 'object' && 'data' in data && Array.isArray(data.data)) {
        console.log('🏦 Returning', data.data.length, 'banks from data');
        return data.data;
      }
      console.warn('🏦 Unexpected bank response structure:', data);
      return [];
    } catch (error) {
      console.error('🏦 Error fetching banks:', error);
      return [];
    }
  },
  
  getBankLogoUrl: (bank: Bank) => {
    if (bank.logo) {
      // Handle both relative and absolute URLs
      if (bank.logo.startsWith('http')) {
        return bank.logo;
      } else if (bank.logo.startsWith('/media/')) {
        return `http://localhost:8000${bank.logo}`;
      } else {
        return `http://localhost:8000/media/${bank.logo}`;
      }
    }
    return null;
  }
};

export const cardService = {
  getCards: async (filters?: CardFilters) => {
    const params = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          // Convert boolean to string for URL params
          const paramValue = typeof value === 'boolean' ? value.toString() : value.toString();
          params.append(key, paramValue);
        }
      });
    }
    const url = `/cards/cards/${params.toString() ? '?' + params.toString() : ''}`;
    console.log('Fetching cards from:', url);
    console.log('Filters:', filters);
    const response = await api.get<CreditCard[]>(url);
    console.log('API Response:', response);
    console.log('Response Data:', response.data);
    console.log('Response Data Type:', typeof response.data);
    console.log('Response Data Is Array:', Array.isArray(response.data));
    
    // Return the data directly - response.data should be the array
    const data = response.data;
    if (!Array.isArray(data)) {
      console.warn('API did not return an array!', data);
      return [];
    }
    console.log('Returning cards array with length:', data.length);
    return data;
  },
  
  getUserCards: async () => {
    const response = await api.get<UserCard[]>('/cards/user-cards/');
    return response.data;
  },
  
  addUserCard: async (data: { 
    card: number; 
    card_number_last4: string; 
    expiry_date: string;
    is_primary?: boolean;
  }) => {
    const response = await api.post<UserCard>('/cards/user-cards/', data);
    return response.data;
  },
  
  deleteUserCard: (id: number) => {
    return api.delete(`/cards/user-cards/${id}/`);
  },
  
  setPrimaryCard: (id: number) => {
    return api.patch<UserCard>(`/cards/user-cards/${id}/`, { is_primary: true });
  },
  
  identifyCardNetwork: async (cardNumber: string) => {
    const response = await api.post<{ network: string; network_display: string; is_valid: boolean }>(
      '/cards/identify-network/',
      { card_number: cardNumber }
    );
    return response.data;
  },
  
  getCardRewards: async (cardId: number) => {
    const response = await api.get<{
      card_id: number;
      card_name: string;
      bank_name: string;
      rewards: {
        base_cashback: number;
        base_rewards: number;
        categories: Array<{
          category: string;
          rate: number;
          min_spend: number;
          max_reward: number | null;
        }>;
        annual_fee: number;
        welcome_bonus: string | null;
        features: string | null;
      };
    }>(`/cards/cards/${cardId}/rewards/`);
    return response.data;
  },
  
  getPeekabooCardNames: async (bankId: number) => {
    const response = await api.get<{
      bank_id: number;
      bank_name: string;
      cards: Array<{
        name: string;
        type_id: number;
        card_type: string;
        image: string;
      }>;
      count: number;
    }>(`/cards/peekaboo-card-names/?bank_id=${bankId}`);
    return response.data;
  },
};