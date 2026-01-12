# notifications/urls.py
from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    UnreadNotificationCountView,
    MarkAllAsReadView,
    NotificationPreferenceView,
)

urlpatterns = [
    path('', NotificationListView.as_view(), name='notifications-list'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),
    path('unread-count/', UnreadNotificationCountView.as_view(), name='unread-count'),
    path('mark-all-read/', MarkAllAsReadView.as_view(), name='mark-all-read'),
    path('preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
]

