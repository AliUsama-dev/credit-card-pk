from django.db import models
from django.contrib.auth import get_user_model
from cards.models import UserCard

User = get_user_model()

class Transaction(models.Model):
    CATEGORIES = [
        ('DINING', 'Dining'),
        ('GROCERIES', 'Groceries'),
        ('FUEL', 'Fuel'),
        ('TRAVEL', 'Travel'),
        ('SHOPPING', 'Shopping'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('UTILITIES', 'Utilities'),
        ('ONLINE_SHOPPING', 'Online Shopping'),
        ('INTERNATIONAL', 'International'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    user_card = models.ForeignKey(UserCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    date = models.DateField()
    merchant = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORIES, default='OTHER')
    description = models.TextField(blank=True, null=True)
    
    # Analysis fields
    reward_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    potential_reward = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    recommended_card_id = models.IntegerField(null=True, blank=True)
    missed_savings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    statement_file = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
        ]
