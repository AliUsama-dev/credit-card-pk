# scraping/urls.py
from django.urls import path
from .views import (
    ScrapeBankOffersView, ScrapingStatusView,
    TriggerManualScrapingView, ScrapingLogsView,
    ScrapeTrinidadTobagoBankView
)

urlpatterns = [
    path('scrape-bank/<int:bank_id>/', ScrapeBankOffersView.as_view(), name='scrape-bank'),
    path('status/', ScrapingStatusView.as_view(), name='scraping-status'),
    path('trigger/', TriggerManualScrapingView.as_view(), name='trigger-scraping'),
    path('logs/', ScrapingLogsView.as_view(), name='scraping-logs'),
    path('scrape-trinidad-tobago-bank/', ScrapeTrinidadTobagoBankView.as_view(), name='scrape-trinidad-tobago-bank'),
]