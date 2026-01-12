from django.urls import path
from .views import (
    BankListView, CreditCardListView,
    UserCardListCreateView, UserCardDetailView,
    CardNetworkIdentifyView, CardRewardsView, PeekabooCardNamesView
)

urlpatterns = [
    path('banks/', BankListView.as_view(), name='bank-list'),
    path('cards/', CreditCardListView.as_view(), name='card-list'),
    path('user-cards/', UserCardListCreateView.as_view(), name='user-card-list'),
    path('user-cards/<int:pk>/', UserCardDetailView.as_view(), name='user-card-detail'),
    path('identify-network/', CardNetworkIdentifyView.as_view(), name='identify-network'),
    path('cards/<int:card_id>/rewards/', CardRewardsView.as_view(), name='card-rewards'),
    path('peekaboo-card-names/', PeekabooCardNamesView.as_view(), name='peekaboo-card-names'),
]