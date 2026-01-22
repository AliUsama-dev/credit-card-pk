from django.contrib import admin

# Register your models here.

try:
    from offers.models_partners import PartnerBank, PartnerCard, PartnerOffer
    
    @admin.register(PartnerBank)
    class PartnerBankAdmin(admin.ModelAdmin):
        list_display = ['name', 'peekaboo_entity_id', 'peekaboo_slug', 'bank', 'is_active', 'last_scraped_at']
        list_filter = ['is_active', 'created_at']
        search_fields = ['name', 'peekaboo_slug']
        readonly_fields = ['created_at', 'updated_at', 'last_scraped_at']
    
    @admin.register(PartnerCard)
    class PartnerCardAdmin(admin.ModelAdmin):
        list_display = ['name', 'partner_bank', 'credit_card', 'card_type', 'is_active']
        list_filter = ['card_type', 'is_active', 'partner_bank']
        search_fields = ['name', 'partner_bank__name']
        readonly_fields = ['created_at', 'updated_at', 'last_scraped_at']
    
    @admin.register(PartnerOffer)
    class PartnerOfferAdmin(admin.ModelAdmin):
        list_display = ['title', 'partner_bank', 'partner_card', 'discount_percentage', 'city', 'is_active', 'is_expired', 'valid_to']
        list_filter = ['is_active', 'is_expired', 'city', 'category', 'partner_bank']
        search_fields = ['title', 'description', 'merchant_name']
        readonly_fields = ['created_at', 'updated_at', 'last_scraped_at']
        date_hierarchy = 'valid_to'
except ImportError:
    pass
