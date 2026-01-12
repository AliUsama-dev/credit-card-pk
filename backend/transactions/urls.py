# transactions/urls.py
from django.urls import path
from .views import (
    StatementUploadView, TransactionListView,
    SavingsAnalysisView, SpendingCategoriesView, ExportTransactionsView
)

urlpatterns = [
    path('upload/', StatementUploadView.as_view(), name='statement-upload'),
    path('transactions/', TransactionListView.as_view(), name='transaction-list'),
    path('savings-analysis/', SavingsAnalysisView.as_view(), name='savings-analysis'),
    path('categories/', SpendingCategoriesView.as_view(), name='spending-categories'),
    path('export/', ExportTransactionsView.as_view(), name='export-transactions'),
]