# offers/models.py

from django.db import models
from cards.models import CreditCard, Bank

# Import Peekaboo models
try:
    from .models_peekaboo import PeekabooDeal, PeekabooCategory
except ImportError:
    # Models will be available after migrations
    pass

class Merchant(models.Model):
    # Pakistani cities list
    PAKISTAN_CITIES = [
        ('ALL_PAKISTAN', 'All Pakistan'),
        ('KARACHI', 'Karachi'),
        ('LAHORE', 'Lahore'),
        ('ISLAMABAD', 'Islamabad'),
        ('RAWALPINDI', 'Rawalpindi'),
        ('FAISALABAD', 'Faisalabad'),
        ('MULTAN', 'Multan'),
        ('HYDERABAD', 'Hyderabad'),
        ('PESHAWAR', 'Peshawar'),
        ('QUETTA', 'Quetta'),
        ('GUJRANWALA', 'Gujranwala'),
        ('SIALKOT', 'Sialkot'),
        ('BAHAWALPUR', 'Bahawalpur'),
        ('SARGODHA', 'Sargodha'),
        ('SUKKUR', 'Sukkur'),
        ('LARKANA', 'Larkana'),
        ('SHEIKHUPURA', 'Sheikhupura'),
        ('MIRPUR_KHAS', 'Mirpur Khas'),
        ('RAHIM_YAR_KHAN', 'Rahim Yar Khan'),
        ('KASUR', 'Kasur'),
        ('GUJRAT', 'Gujrat'),
        ('OTHER', 'Other'),
    ]
    
    MERCHANT_TYPES = [
        ('RESTAURANT', 'Restaurant'),
        ('HOTEL', 'Hotel'),
        ('RETAIL', 'Retail Store'),
        ('E_COMMERCE', 'E-commerce'),
        ('FUEL_STATION', 'Fuel Station'),
        ('SUPERMARKET', 'Supermarket'),
        ('TRAVEL', 'Travel Agency'),
        ('ENTERTAINMENT', 'Entertainment'),
        ('HEALTHCARE', 'Healthcare'),
        ('EDUCATION', 'Education'),
        ('AUTOMOTIVE', 'Automotive'),
        ('FASHION', 'Fashion & Apparel'),
        ('ELECTRONICS', 'Electronics'),
        ('HOME', 'Home & Furniture'),
        ('BEAUTY', 'Beauty & Salon'),
        ('OTHER', 'Other'),
    ]
    
    name = models.CharField(max_length=255)
    merchant_type = models.CharField(max_length=50, choices=MERCHANT_TYPES)
    website = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=50, choices=PAKISTAN_CITIES, default='KARACHI')
    area = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, null=True, blank=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, null=True, blank=True)
    logo = models.ImageField(upload_to='merchant_logos/', null=True, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'merchants'
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['merchant_type']),
        ]

        
class Offer(models.Model):
    OFFER_TYPES = [
        ('DISCOUNT', 'Discount'),
        ('CASHBACK', 'Cashback'),
        ('REWARD_MULTIPLIER', 'Reward Multiplier'),
        ('EMI', 'EMI Offer'),
        ('WELCOME_BONUS', 'Welcome Bonus'),
        ('FEE_WAIVER', 'Fee Waiver'),
        ('OTHER', 'Other'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    offer_type = models.CharField(max_length=50, choices=OFFER_TYPES)
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='offers')
    card = models.ForeignKey(CreditCard, on_delete=models.CASCADE, related_name='offers', null=True, blank=True)
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name='offers', null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cashback_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valid_from = models.DateField()
    valid_to = models.DateField()
    terms_conditions = models.TextField(blank=True, null=True)
    redemption_process = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    scraping_source = models.URLField(blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'offers'
        ordering = ['-valid_to']

class UserOffer(models.Model):
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('ACTIVATED', 'Activated'),
        ('USED', 'Used'),
        ('EXPIRED', 'Expired'),
    ]
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='user_offers')
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    activated_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_offers'
        unique_together = ('user', 'offer')