# planning/models.py
from django.db import models
from django.contrib.auth import get_user_model
from cards.models import CreditCard, UserCard

User = get_user_model()


class ScheduledPurchase(models.Model):
    """Model for scheduled upcoming purchases"""
    PURCHASE_TYPES = [
        ('GROCERIES', 'Groceries'),
        ('DINING', 'Dining'),
        ('SHOPPING', 'Shopping'),
        ('FUEL', 'Fuel'),
        ('TRAVEL', 'Travel'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('UTILITIES', 'Utilities'),
        ('ONLINE_SHOPPING', 'Online Shopping'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_purchases')
    purchase_type = models.CharField(max_length=50, choices=PURCHASE_TYPES)
    scheduled_date = models.DateTimeField(help_text="When the purchase is planned")
    estimated_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    location = models.CharField(max_length=255, blank=True, null=True, help_text="Location/city for the purchase")
    merchant_preference = models.CharField(max_length=255, blank=True, null=True, help_text="Preferred merchant/store")
    notes = models.TextField(blank=True, null=True)
    
    # Recommendations
    recommended_card = models.ForeignKey(CreditCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='recommended_for_purchases')
    recommended_merchants = models.JSONField(default=list, blank=True, help_text="List of merchants with active offers")
    active_offers = models.JSONField(default=list, blank=True, help_text="List of relevant offers for this purchase")
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    reminder_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'scheduled_purchases'
        ordering = ['scheduled_date']
        indexes = [
            models.Index(fields=['user', 'scheduled_date']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_purchase_type_display()} on {self.scheduled_date.strftime('%Y-%m-%d')}"

