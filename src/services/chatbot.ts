import api from './api';

export interface ChatMessage {
  id: string;
  message: string;
  response?: string;
  timestamp: string;
  intent?: string;
  recommendations?: Array<{
    id: number;
    title: string;
    merchant: string;
    discount: number;
    bank: string;
  }>;
  user_cards?: Array<{
    id: number;
    name: string;
    bank: string;
    is_primary: boolean;
  }>;
}

export interface ChatResponse {
  status: string;
  response: string;
  recommendations?: Array<{
    id: number;
    title: string;
    merchant: string;
    discount: number;
    bank: string;
  }>;
  intent?: string;
  timestamp: string;
  user_cards?: Array<{
    id: number;
    name: string;
    bank: string;
    is_primary: boolean;
  }>;
}

export const chatbotService = {
  sendMessage: async (message: string): Promise<ChatResponse> => {
    try {
      const response = await api.post<ChatResponse>('/chatbot/chat/', { message });
      // Handle both direct response and response.data
      return response.data || (response as any);
    } catch (error) {
      console.error('Chatbot API error:', error);
      throw error;
    }
  },
  
  getHistory: async (): Promise<ChatMessage[]> => {
    try {
      const response = await api.get<{ history?: ChatMessage[] }>('/chatbot/history/');
      // Handle both direct response and response.data
      return response.data?.history || (response.data as any) || [];
    } catch (error) {
      console.error('Chatbot history error:', error);
      return [];
    }
  },
};

