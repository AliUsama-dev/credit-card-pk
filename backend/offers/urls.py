# offers/urls.py
from django.urls import path
from .views import (
    OfferListView, PersonalizedOfferView, BankOffersView,
    ScrapeBankOffersView, ScrapeAllBanksWithFiltersView, CityOffersView, MerchantTypeOffersView,
    OfferStatsView, ActivateOfferView, MerchantListView
)

# Peekaboo views
try:
    from .views_peekaboo import (
        PeekabooDealListView, PeekabooDealForUserCardsView, PeekabooDealByBankCardView,
        PeekabooCategoryListView, PeekabooEntityListView, trigger_peekaboo_scraping,
        get_entities_by_card, get_entities_for_user_cards
    )
    peekaboo_urls = [
        path('peekaboo/deals/', PeekabooDealListView.as_view(), name='peekaboo-deals'),
        path('peekaboo/deals/my-cards/', PeekabooDealForUserCardsView.as_view(), name='peekaboo-deals-my-cards'),
        path('peekaboo/deals/by-bank-card/', PeekabooDealByBankCardView.as_view(), name='peekaboo-deals-by-bank-card'),
        path('peekaboo/entities/by-card/', get_entities_by_card, name='peekaboo-entities-by-card'),
        path('peekaboo/entities/for-user-cards/', get_entities_for_user_cards, name='peekaboo-entities-for-user-cards'),
        path('peekaboo/categories/', PeekabooCategoryListView.as_view(), name='peekaboo-categories'),
        path('peekaboo/entities/', PeekabooEntityListView.as_view(), name='peekaboo-entities'),
        path('peekaboo/scrape/', trigger_peekaboo_scraping, name='peekaboo-scrape'),
    ]
except ImportError:
    peekaboo_urls = []

# Bank-specific views
try:
    from .views_bank_specific import (
        BankSpecificCityListView, BankSpecificCategoryListView,
        BankSpecificEntityListView, BankSpecificCardAssociationListView,
        trigger_bank_specific_scraping
    )
    bank_specific_urls = [
        path('bank-specific/cities/', BankSpecificCityListView.as_view(), name='bank-specific-cities'),
        path('bank-specific/categories/', BankSpecificCategoryListView.as_view(), name='bank-specific-categories'),
        path('bank-specific/entities/', BankSpecificEntityListView.as_view(), name='bank-specific-entities'),
        path('bank-specific/card-associations/', BankSpecificCardAssociationListView.as_view(), name='bank-specific-card-associations'),
        path('bank-specific/scrape/', trigger_bank_specific_scraping, name='bank-specific-scrape'),
    ]
except ImportError:
    bank_specific_urls = []

# Partners Offers views
try:
    from .views_partners import (
        PartnerBankListView, PartnerCardListView, PartnerOfferListView,
        ScrapePartnersBanksView, ScrapePartnerBankDetailView, ScrapeAllPartnersBanksView
    )
    partners_urls = [
        path('partners/banks/', PartnerBankListView.as_view(), name='partner-banks'),
        path('partners/cards/', PartnerCardListView.as_view(), name='partner-cards'),
        path('partners/offers/', PartnerOfferListView.as_view(), name='partner-offers'),
        path('partners/scrape-banks/', ScrapePartnersBanksView.as_view(), name='scrape-partners-banks'),
        path('partners/scrape-bank-detail/', ScrapePartnerBankDetailView.as_view(), name='scrape-partner-bank-detail'),
        path('partners/scrape-all/', ScrapeAllPartnersBanksView.as_view(), name='scrape-all-partners'),
    ]
except ImportError:
    partners_urls = []

# Smart Recommendations (AI-powered analysis)
try:
    from .views_recommendations import SmartRecommendationsView
    recommendations_urls = [
        path('smart-recommendations/', SmartRecommendationsView.as_view(), name='smart-recommendations'),
    ]
except Exception:
    recommendations_urls = []

urlpatterns = [
    path('', OfferListView.as_view(), name='offer-list'),
    path('personalized/', PersonalizedOfferView.as_view(), name='personalized-offers'),
    path('bank/<int:bank_id>/', BankOffersView.as_view(), name='bank-offers'),
    path('bank/<int:bank_id>/scrape/', ScrapeBankOffersView.as_view(), name='scrape-bank-offers'),
    path('scrape-all/', ScrapeAllBanksWithFiltersView.as_view(), name='scrape-all-banks'),
    path('city/<str:city>/', CityOffersView.as_view(), name='city-offers'),
    path('merchant-type/<str:merchant_type>/', MerchantTypeOffersView.as_view(), name='merchant-type-offers'),
    path('stats/', OfferStatsView.as_view(), name='offer-stats'),
    path('<int:offer_id>/activate/', ActivateOfferView.as_view(), name='activate-offer'),
    path('merchants/', MerchantListView.as_view(), name='merchant-list'),
] + peekaboo_urls + bank_specific_urls + partners_urls + recommendations_urls