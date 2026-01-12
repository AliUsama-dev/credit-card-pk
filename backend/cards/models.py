from django.db import models
from users.models import User

# cards/models.py - Update Bank model
from django.db import models

class Bank(models.Model):
    BANK_TYPES = [
        ('COMMERCIAL', 'Commercial Bank'),
        ('ISLAMIC', 'Islamic Bank'),
        ('GOVERNMENT', 'Government Bank'),
        ('INTERNATIONAL', 'International Bank'),
        ('SPECIALIZED', 'Specialized Bank'),
    ]
    
    COUNTRIES = [
        ('PK', 'Pakistan'),
        ('TT', 'Trinidad & Tobago'),
        ('US', 'United States'),
        ('CA', 'Canada'),
        ('UK', 'United Kingdom'),
    ]
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    country = models.CharField(max_length=2, choices=COUNTRIES, default='PK', db_index=True)
    bank_type = models.CharField(max_length=20, choices=BANK_TYPES, default='COMMERCIAL')
    logo = models.ImageField(upload_to='bank_logos/', null=True, blank=True)
    website = models.URLField()
    support_email = models.EmailField()
    support_phone = models.CharField(max_length=20)
    headquarters = models.CharField(max_length=255, blank=True, null=True)
    established_year = models.IntegerField(null=True, blank=True)
    total_branches = models.IntegerField(null=True, blank=True)
    digital_banking = models.BooleanField(default=True)
    mobile_app = models.BooleanField(default=True)
    atm_network = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'banks'
        ordering = ['name']
        
    @property
    def active_cards_count(self):
        return self.cards.filter(is_active=True).count()
    
    @property
    def active_offers_count(self):
        from offers.models import Offer
        from django.utils import timezone
        return self.offers.filter(
            is_active=True,
            valid_to__gte=timezone.now().date()
        ).count()

    
class CreditCard(models.Model):
    CARD_TYPES = [
        ('CREDIT', 'Credit Card'),
        ('DEBIT', 'Debit Card'),
        ('BOTH', 'Both Credit & Debit'),
        ('PREMIUM', 'Premium Cards Only'),
        ('PLATINUM', 'Platinum Cards Only'),
        ('GOLD', 'Gold Cards Only'),
    ]
    
    name = models.CharField(max_length=255)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='cards')
    card_type = models.CharField(max_length=20, choices=CARD_TYPES)
    annual_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    credit_limit_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    credit_limit_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reward_points_rate = models.DecimalField(max_digits=5, decimal_places=2, default=1.0)
    cashback_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    welcome_bonus = models.TextField(blank=True, null=True)
    requirements = models.TextField(blank=True, null=True)
    features = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='card_images/', null=True, blank=True)
    image_url = models.URLField(blank=True, null=True, help_text="URL of card image from bank website")
    is_active = models.BooleanField(default=True)
    scraping_url = models.URLField(blank=True, null=True)
    last_scraped = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Peekaboo API mapping
    peekaboo_association_type_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Peekaboo associationTypeId for this card")
    peekaboo_card_slug = models.CharField(max_length=255, blank=True, null=True, db_index=True, help_text="Peekaboo card slug (e.g., visa-infinite-debit-card)")
    
    class Meta:
        db_table = 'credit_cards'

class CardRewardCategory(models.Model):
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
    
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='reward_categories')
    category = models.CharField(max_length=50, choices=CATEGORIES)
    reward_rate = models.DecimalField(max_digits=5, decimal_places=2)
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_reward = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateField()
    valid_to = models.DateField()
    
    class Meta:
        db_table = 'card_reward_categories'
        unique_together = ('card', 'category')

class UserCard(models.Model):
    CARD_NETWORKS = [
        ('VISA', 'Visa'),
        ('MASTERCARD', 'Mastercard'),
        ('AMEX', 'American Express'),
        ('UNIONPAY', 'UnionPay'),
        ('DISCOVER', 'Discover'),
        ('OTHER', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE)
    card_number_last4 = models.CharField(max_length=4)
    card_network = models.CharField(max_length=20, choices=CARD_NETWORKS, default='VISA')
    expiry_date = models.DateField()
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    linked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_cards'
        ordering = ['-is_primary', '-linked_at']
    
    def __str__(self):
        return f"{self.card.name} - ****{self.card_number_last4} ({self.user.email})"