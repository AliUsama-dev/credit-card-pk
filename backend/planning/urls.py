# planning/urls.py
from django.urls import path
from .views import (
    ScheduledPurchaseListCreateView,
    ScheduledPurchaseDetailView,
    UpcomingPurchasesView,
    CompleteScheduledPurchaseView,
)

urlpatterns = [
    path('purchases/', ScheduledPurchaseListCreateView.as_view(), name='scheduled-purchases-list'),
    path('purchases/<int:pk>/', ScheduledPurchaseDetailView.as_view(), name='scheduled-purchase-detail'),
    path('purchases/upcoming/', UpcomingPurchasesView.as_view(), name='upcoming-purchases'),
    path('purchases/<int:purchase_id>/complete/', CompleteScheduledPurchaseView.as_view(), name='complete-purchase'),
]

