import api from './api';

export interface Notification {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  related_offer?: number;
  related_card?: number;
  related_bank?: number;
  action_url?: string;
  is_read: boolean;
  created_at: string;
  read_at?: string;
}

export interface NotificationPreference {
  id: number;
  user: number;
  email_expiring_offers: boolean;
  email_new_offers: boolean;
  email_savings_opportunities: boolean;
  email_scheduled_reminders: boolean;
  email_chatbot_suggestions: boolean;
  in_app_expiring_offers: boolean;
  in_app_new_offers: boolean;
  in_app_savings_opportunities: boolean;
  in_app_scheduled_reminders: boolean;
  in_app_chatbot_suggestions: boolean;
  in_app_savings_summary: boolean;
  in_app_personalized_tips: boolean;
  email_frequency: 'IMMEDIATE' | 'DAILY' | 'WEEKLY';
  updated_at: string;
}

export const notificationService = {
  getNotifications: async (isRead?: boolean, type?: string): Promise<Notification[]> => {
    const params: { is_read?: string; type?: string } = {};
    if (isRead !== undefined) {
      params.is_read = String(isRead).toLowerCase();
    }
    if (type) {
      params.type = type;
    }
    const response = await api.get('/notifications/', { params });
    return response.data;
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await api.get('/notifications/unread-count/');
    return response.data;
  },

  markAsRead: async (id: number): Promise<Notification> => {
    const response = await api.patch(`/notifications/${id}/`, { is_read: true });
    return response.data;
  },

  markAllAsRead: async (): Promise<{ marked_read: number }> => {
    const response = await api.post('/notifications/mark-all-read/');
    return response.data;
  },

  getPreferences: async (): Promise<NotificationPreference> => {
    const response = await api.get('/notifications/preferences/');
    return response.data;
  },

  updatePreferences: async (data: Partial<NotificationPreference>): Promise<NotificationPreference> => {
    const response = await api.patch('/notifications/preferences/', data);
    return response.data;
  },
};
