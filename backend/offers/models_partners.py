# offers/models_partners.py
# Models for Peekaboo Partners Offers (bank detail pages)

from django.db import models
from django.utils import timezone
from cards.models import Bank, CreditCard

class PartnerBank(models.Model):
    """Model to store bank information from Peekaboo Partners Offers"""
    
    # Bank information from Peekaboo
    peekaboo_entity_id = models.BigIntegerField(unique=True, db_index=True, help_text="Entity ID from Peekaboo URL")
    peekaboo_slug = models.CharField(max_length=255, unique=True, db_index=True, help_text="Slug from Peekaboo URL")
    
    # Link to our Bank model
    bank = models.ForeignKey(Bank, on_delete=models.SET_NULL, null=True, blank=True, related_name='partner_banks')
    
    # Bank details from Peekaboo
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    logo = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'partner_banks'
        ordering = ['name']
        indexes = [
            models.Index(fields=['peekaboo_entity_id']),
            models.Index(fields=['peekaboo_slug']),
        ]
    
    def __str__(self):
        return f"{self.name} (ID: {self.peekaboo_entity_id})"

class PartnerCard(models.Model):
    """Model to store cards scraped from Partners Offers pages"""
    
    # Link to partner bank
    partner_bank = models.ForeignKey(PartnerBank, on_delete=models.CASCADE, related_name='cards')
    
    # Link to our CreditCard model (if matched)
    credit_card = models.ForeignKey(CreditCard, on_delete=models.SET_NULL, null=True, blank=True, related_name='partner_cards')
    
    # Card information from Peekaboo
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    
    # Card type
    card_type = models.CharField(max_length=50, blank=True, null=True)  # CREDIT, DEBIT, etc.
    
    # Peekaboo association IDs (from associations array in API)
    peekaboo_association_id = models.BigIntegerField(null=True, blank=True, help_text="Association ID from Peekaboo API for this card")
    peekaboo_association_type_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Association Type ID from Peekaboo API for this card")
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'partner_cards'
        ordering = ['name']
        indexes = [
            models.Index(fields=['partner_bank']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.partner_bank.name})"

class PartnerOffer(models.Model):
    """Model to store offers/deals from Partners Offers pages"""
    
    # Link to partner bank and card
    partner_bank = models.ForeignKey(PartnerBank, on_delete=models.CASCADE, related_name='offers')
    partner_card = models.ForeignKey(PartnerCard, on_delete=models.CASCADE, null=True, blank=True, related_name='offers')
    
    # Offer information
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    
    # Offer details
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Merchant/Entity information
    merchant_name = models.CharField(max_length=255, blank=True, null=True)
    merchant_logo = models.URLField(blank=True, null=True)
    
    # Offer dates
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    
    # City information
    city = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    # Category
    category = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    # Offer image
    image = models.URLField(blank=True, null=True)
    
    # Terms and conditions
    terms_conditions = models.TextField(blank=True, null=True)
    
    # Source URL
    source_url = models.URLField(blank=True, null=True)
    
    # Available On Cards (ManyToMany relationship)
    # This stores which PartnerCard objects this offer is available on
    # Based on the "associations" array from the Peekaboo API
    available_on_cards = models.ManyToManyField(
        PartnerCard,
        blank=True,
        related_name='available_offers',
        help_text="Cards this offer is available on (from 'associations' array in Peekaboo API)"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    is_expired = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_scraped_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'partner_offers'
        ordering = ['-valid_to', '-created_at']
        indexes = [
            models.Index(fields=['partner_bank']),
            models.Index(fields=['partner_card']),
            models.Index(fields=['city']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active', 'is_expired']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.partner_bank.name})"
