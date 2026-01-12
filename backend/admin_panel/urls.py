# admin_panel/urls.py
from django.urls import path
from .views import (
    AdminDashboardView, BankManagementView,
    CardManagementView, OfferManagementView
)

urlpatterns = [
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('banks/', BankManagementView.as_view(), name='bank-management'),
    path('cards/', CardManagementView.as_view(), name='card-management'),
    path('offers/', OfferManagementView.as_view(), name='offer-management'),
]