# offers/models_peekaboo.py
# New model for Peekaboo API deals

from django.db import models
from django.utils import timezone
from cards.models import Bank, CreditCard

class PeekabooEntity(models.Model):
    """Model to store source entities/merchants from Peekaboo v6/sourceEntities API"""
    
    # Entity ID from Peekaboo API
    source_entity_id = models.BigIntegerField(unique=True, db_index=True)
    entity_id = models.BigIntegerField(null=True, blank=True)  # Alternative ID field
    
    # Basic entity information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    
    # Entity metadata
    keywords = models.TextField(blank=True, null=True)  # Comma-separated keywords
    is_applied_allowed = models.BooleanField(default=False)
    is_membership_allowed = models.BooleanField(default=False)
    
    # Categories (stored as JSON)
    categories = models.JSONField(default=list, blank=True)  # [{categoryId, categoryName, categoryLogo}]
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    
    # Status flags
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'peekaboo_entities'
        ordering = ['name']
        indexes = [
            models.Index(fields=['source_entity_id']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} (Entity ID: {self.source_entity_id})"

class PeekabooDeal(models.Model):
    """Model to store deals from Peekaboo Guru API"""
    
    # Deal ID from Peekaboo API
    deal_id = models.BigIntegerField(unique=True, db_index=True)
    
    # Basic deal information
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    
    # Deal details
    percentage_value = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Entity/Merchant information - Link to PeekabooEntity
    target_entity = models.ForeignKey('PeekabooEntity', on_delete=models.SET_NULL, null=True, blank=True, related_name='deals', db_index=True)
    # Store raw entity ID from API (separate from ForeignKey's auto-generated _id)
    raw_entity_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Raw entity ID from Peekaboo API")
    target_entity_name = models.CharField(max_length=255, blank=True, null=True)
    target_entity_logo = models.URLField(blank=True, null=True)
    
    # Deal dates
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    # Deal status
    is_redeemable = models.BooleanField(default=False)
    redeemable_count = models.IntegerField(default=0)
    redeemed_count = models.IntegerField(default=0)
    
    # Deal image
    image = models.URLField(blank=True, null=True)
    
    # Deal metadata
    keywords = models.JSONField(default=list, blank=True)
    target_branches = models.JSONField(default=dict, blank=True)  # {branch_id: branch_name}
    order_type = models.CharField(max_length=50, blank=True, null=True)
    powered_by = models.CharField(max_length=100, blank=True, null=True)
    
    # Expiry tracking
    expires_in = models.IntegerField(null=True, blank=True)  # seconds until expiry
    
    # Category (from v7/category API)
    category = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    # City information
    city = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    # Bank association (if applicable) - Try to match from entity name or deal description
    bank = models.ForeignKey(Bank, on_delete=models.SET_NULL, null=True, blank=True, related_name='peekaboo_deals')
    
    # Card associations - Many deals can be linked to many cards
    # Store associations from API (JSON format)
    associations = models.JSONField(default=list, blank=True, help_text="Card associations from Peekaboo API")
    source_entity_id = models.BigIntegerField(null=True, blank=True, help_text="Source entity ID (bank) from API")
    source_entity_name = models.CharField(max_length=255, blank=True, null=True, help_text="Source entity name (bank) from API")
    source_entity_logo = models.URLField(blank=True, null=True, help_text="Source entity logo (bank) from API")
    
    # Linked cards (many-to-many relationship)
    linked_cards = models.ManyToManyField(CreditCard, blank=True, related_name='peekaboo_deals', help_text="Credit cards this deal applies to")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    
    # Status flags
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'peekaboo_deals'
        ordering = ['-end_date', '-created_at']
        indexes = [
            models.Index(fields=['deal_id']),
            models.Index(fields=['city', 'is_expired']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['target_entity_id']),
            models.Index(fields=['end_date']),
        ]
    
    def __str__(self):
        return f"{self.title} (Deal ID: {self.deal_id})"
    
    @property
    def is_currently_valid(self):
        """Check if deal is currently valid"""
        now = timezone.now()
        return self.start_date <= now <= self.end_date and not self.is_expired
    
    def mark_expired(self):
        """Mark deal as expired"""
        self.is_expired = True
        self.is_active = False
        self.save(update_fields=['is_expired', 'is_active'])

class PeekabooCategory(models.Model):
    """Model to store categories from Peekaboo v7/category API"""
    
    category_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    icon = models.URLField(blank=True, null=True)
    parent_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'peekaboo_categories'
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Peekaboo Categories'
    
    def __str__(self):
        return self.name
