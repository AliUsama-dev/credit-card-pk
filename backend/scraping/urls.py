# scraping/urls.py
from django.urls import path
from .views import (
    ScrapeBankOffersView, ScrapingStatusView,
    TriggerManualScrapingView, ScrapingLogsView,
    ScrapePeekabooBankView, ScrapeAllPeekabooBanksView,
    ScrapePeekabooCategoriesView,
)

urlpatterns = [
    path('scrape-bank/<int:bank_id>/', ScrapeBankOffersView.as_view(), name='scrape-bank'),
    path('status/', ScrapingStatusView.as_view(), name='scraping-status'),
    path('trigger/', TriggerManualScrapingView.as_view(), name='trigger-scraping'),
    path('logs/', ScrapingLogsView.as_view(), name='scraping-logs'),
    path('scrape-peekaboo-bank/', ScrapePeekabooBankView.as_view(), name='scrape-peekaboo-bank'),
    path('scrape-all-peekaboo-banks/', ScrapeAllPeekabooBanksView.as_view(), name='scrape-all-peekaboo-banks'),
    path('scrape-peekaboo-categories/', ScrapePeekabooCategoriesView.as_view(), name='scrape-peekaboo-categories'),
]