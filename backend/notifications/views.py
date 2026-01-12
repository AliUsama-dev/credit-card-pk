# notifications/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer
import logging

logger = logging.getLogger(__name__)


class NotificationListView(generics.ListAPIView):
    """List user notifications"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        user = self.request.user
        is_read = self.request.query_params.get('is_read')
        notification_type = self.request.query_params.get('type')
        
        queryset = Notification.objects.filter(user=user)
        
        if is_read is not None:
            queryset = queryset.filter(is_read=is_read.lower() == 'true')
        
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset.order_by('-created_at')


class NotificationDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or mark notification as read"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        if 'is_read' in request.data and request.data['is_read']:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)


class UnreadNotificationCountView(APIView):
    """Get count of unread notifications"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({'unread_count': count})


class MarkAllAsReadView(APIView):
    """Mark all notifications as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({'marked_read': count})


class NotificationPreferenceView(generics.RetrieveUpdateAPIView):
    """Get or update notification preferences"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationPreferenceSerializer
    
    def get_object(self):
        preference, created = NotificationPreference.objects.get_or_create(
            user=self.request.user
        )
        return preference

