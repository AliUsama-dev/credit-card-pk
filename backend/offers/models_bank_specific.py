# offers/models_bank_specific.py
# Models for bank-specific deals from secure-sdk.peekaboo.guru

from django.db import models
from django.utils import timezone
from cards.models import Bank, CreditCard

class BankSpecificCity(models.Model):
    """Model to store cities available for a specific bank"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='bank_cities')
    city_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    country = models.CharField(max_length=100, default='Pakistan')
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    image = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bank_specific_cities'
        unique_together = ['bank', 'city_id']
        ordering = ['name']
        indexes = [
            models.Index(fields=['bank', 'city_id']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.bank.name} - {self.name}"

class BankSpecificCategory(models.Model):
    """Model to store categories for a specific bank"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='bank_categories')
    category_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    order = models.IntegerField(default=0)
    category_logo_url = models.URLField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bank_specific_categories'
        unique_together = ['bank', 'category_id']
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['bank', 'category_id']),
        ]
    
    def __str__(self):
        return f"{self.bank.name} - {self.name}"

class BankSpecificEntity(models.Model):
    """Model to store merchants/entities for a specific bank"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='bank_entities')
    entity_id = models.BigIntegerField(db_index=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    package = models.CharField(max_length=50, blank=True, null=True)  # PREMIUM, etc.
    contact_number = models.CharField(max_length=50, blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    entity_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    
    # Images
    cover = models.URLField(blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    gallery = models.JSONField(default=list, blank=True)  # Array of image URLs
    menu = models.JSONField(default=list, blank=True)  # Array of menu image URLs
    
    # Social links
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    whatsapp = models.CharField(max_length=50, blank=True, null=True)
    android = models.URLField(blank=True, null=True)
    ios = models.URLField(blank=True, null=True)
    
    # Statistics
    total_branches = models.IntegerField(default=0)
    total_open_branches = models.IntegerField(default=0)
    total_associated_deals = models.IntegerField(default=0)
    max_discount = models.IntegerField(default=0)
    wishlist_count = models.IntegerField(default=0)
    review_counts = models.IntegerField(default=0)
    
    # Tags/Categories
    tags = models.JSONField(default=list, blank=True)  # Array of tag objects
    
    # Nearest branch info
    nearest_branch_id = models.BigIntegerField(null=True, blank=True)
    nearest_branch_name = models.CharField(max_length=255, blank=True, null=True)
    nearest_branch_lat_long = models.CharField(max_length=100, blank=True, null=True)
    nearest_branch_distance = models.CharField(max_length=50, blank=True, null=True)
    nearest_branch_open_now = models.BooleanField(default=False)
    nearest_branch_contact_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Branches (comma-separated IDs)
    branches = models.TextField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    online_service_available = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bank_specific_entities'
        unique_together = ['bank', 'entity_id']
        ordering = ['name']
        indexes = [
            models.Index(fields=['bank', 'entity_id']),
            models.Index(fields=['name']),
            models.Index(fields=['entity_rating']),
        ]
    
    def __str__(self):
        return f"{self.bank.name} - {self.name}"

class BankSpecificCardAssociation(models.Model):
    """Model to store card associations for a specific bank"""
    bank = models.ForeignKey(Bank, on_delete=models.CASCADE, related_name='bank_card_associations')
    association_id = models.IntegerField(db_index=True)
    type_id = models.IntegerField()
    type_name = models.CharField(max_length=255)  # e.g., "Visa Infinite Debit Card"
    card_type = models.CharField(max_length=50)  # DEBIT, CREDIT
    image = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)
    
    # Amenities (stored as JSON)
    amenities = models.JSONField(default=dict, blank=True)  # {amenity_name: {value, image}}
    amenity_count = models.IntegerField(default=0)
    
    # Deal count
    deal_count = models.IntegerField(default=0)
    
    # Link to CreditCard if matched
    linked_card = models.ForeignKey(
        CreditCard, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='bank_associations'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'bank_specific_card_associations'
        unique_together = ['bank', 'association_id']
        ordering = ['type_name']
        indexes = [
            models.Index(fields=['bank', 'association_id']),
            models.Index(fields=['type_name']),
            models.Index(fields=['card_type']),
        ]
    
    def __str__(self):
        return f"{self.bank.name} - {self.type_name}"

