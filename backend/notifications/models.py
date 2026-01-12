# notifications/models.py
from django.db import models
from django.contrib.auth import get_user_model
from cards.models import CreditCard, Bank
from offers.models import Offer

User = get_user_model()


class Notification(models.Model):
    """Model for in-app notifications"""
    NOTIFICATION_TYPES = [
        ('EXPIRING_OFFER', 'Expiring Offer'),
        ('NEW_OFFER', 'New Offer'),
        ('SAVINGS_OPPORTUNITY', 'Savings Opportunity'),
        ('SCHEDULED_REMINDER', 'Scheduled Purchase Reminder'),
        ('CHATBOT_SUGGESTION', 'Chatbot Suggestion'),
        ('CARD_RECOMMENDATION', 'Card Recommendation'),
        ('SYSTEM', 'System Notification'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    
    # Related objects (optional)
    related_offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True, blank=True)
    related_card = models.ForeignKey(CreditCard, on_delete=models.SET_NULL, null=True, blank=True)
    related_bank = models.ForeignKey(Bank, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Action link
    action_url = models.CharField(max_length=500, blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email preferences
    email_expiring_offers = models.BooleanField(default=True)
    email_new_offers = models.BooleanField(default=True)
    email_savings_opportunities = models.BooleanField(default=True)
    email_scheduled_reminders = models.BooleanField(default=True)
    email_chatbot_suggestions = models.BooleanField(default=False)
    
    # In-app preferences
    in_app_expiring_offers = models.BooleanField(default=True)
    in_app_new_offers = models.BooleanField(default=True)
    in_app_savings_opportunities = models.BooleanField(default=True)
    in_app_scheduled_reminders = models.BooleanField(default=True)
    in_app_chatbot_suggestions = models.BooleanField(default=True)
    
    # Frequency
    email_frequency = models.CharField(
        max_length=20,
        choices=[('IMMEDIATE', 'Immediate'), ('DAILY', 'Daily Digest'), ('WEEKLY', 'Weekly Digest')],
        default='DAILY'
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.email}"

