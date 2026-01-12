# offers/views_bank_specific.py
# API views for bank-specific deals

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Q

try:
    from offers.models_bank_specific import (
        BankSpecificCity, BankSpecificCategory,
        BankSpecificEntity, BankSpecificCardAssociation
    )
    from offers.serializers_bank_specific import (
        BankSpecificCitySerializer, BankSpecificCategorySerializer,
        BankSpecificEntitySerializer, BankSpecificCardAssociationSerializer
    )
    from cards.models import Bank
    from scraping.tasks_bank_specific import scrape_bank_specific_all
except ImportError:
    BankSpecificCity = None
    BankSpecificCategory = None
    BankSpecificEntity = None
    BankSpecificCardAssociation = None

class BankSpecificCityListView(generics.ListAPIView):
    """List cities for a specific bank"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if BankSpecificCitySerializer:
            return BankSpecificCitySerializer
        from rest_framework import serializers
        return serializers.Serializer
    
    def get_queryset(self):
        if not BankSpecificCity:
            return []
        
        queryset = BankSpecificCity.objects.filter(is_active=True).order_by('name')
        
        bank_id = self.request.query_params.get('bank')
        if bank_id:
            queryset = queryset.filter(bank_id=bank_id)
        
        return queryset

class BankSpecificCategoryListView(generics.ListAPIView):
    """List categories for a specific bank"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if BankSpecificCategorySerializer:
            return BankSpecificCategorySerializer
        from rest_framework import serializers
        return serializers.Serializer
    
    def get_queryset(self):
        if not BankSpecificCategory:
            return []
        
        queryset = BankSpecificCategory.objects.filter(is_active=True).order_by('order', 'name')
        
        bank_id = self.request.query_params.get('bank')
        if bank_id:
            queryset = queryset.filter(bank_id=bank_id)
        
        return queryset

class BankSpecificEntityListView(generics.ListAPIView):
    """List entities/merchants for a specific bank"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if BankSpecificEntitySerializer:
            return BankSpecificEntitySerializer
        from rest_framework import serializers
        return serializers.Serializer
    
    def get_queryset(self):
        if not BankSpecificEntity:
            return []
        
        queryset = BankSpecificEntity.objects.filter(is_active=True).order_by('name')
        
        bank_id = self.request.query_params.get('bank')
        if bank_id:
            queryset = queryset.filter(bank_id=bank_id)
        
        city_id = self.request.query_params.get('city_id')
        if city_id:
            # Filter by city if entity has branches in that city
            queryset = queryset.filter(
                Q(nearest_branch_id=city_id) | 
                Q(branches__contains=str(city_id))
            )
        
        category_id = self.request.query_params.get('category_id')
        if category_id:
            # Filter by category (tags contain category)
            queryset = queryset.filter(tags__contains=[{'tagId': int(category_id)}])
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(keywords__icontains=search)
            )
        
        return queryset

class BankSpecificCardAssociationListView(generics.ListAPIView):
    """List card associations for a specific bank"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if BankSpecificCardAssociationSerializer:
            return BankSpecificCardAssociationSerializer
        from rest_framework import serializers
        return serializers.Serializer
    
    def get_queryset(self):
        if not BankSpecificCardAssociation:
            return []
        
        queryset = BankSpecificCardAssociation.objects.filter(is_active=True).order_by('type_name')
        
        bank_id = self.request.query_params.get('bank')
        if bank_id:
            queryset = queryset.filter(bank_id=bank_id)
        
        card_type = self.request.query_params.get('card_type')
        if card_type:
            queryset = queryset.filter(card_type=card_type.upper()            )
        
        return queryset

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
def trigger_bank_specific_scraping(request):
    """Trigger scraping for bank-specific deals"""
    from celery import current_app
    
    bank_code = request.data.get('bank_code', 'MEEZAN')
    city_id = request.data.get('city_id')
    city_slug = request.data.get('city_slug')
    
    try:
        # Trigger async task
        task = scrape_bank_specific_all.delay(bank_code, city_id=city_id, city_slug=city_slug)
        
        return Response({
            'status': 'success',
            'message': f'Scraping started for {bank_code}',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)
    except Exception as e:
        # Fallback to synchronous scraping
        try:
            from scraping.tasks_bank_specific import scrape_bank_specific_all
            scrape_bank_specific_all(bank_code, city_id=city_id, city_slug=city_slug)
            return Response({
                'status': 'success',
                'message': f'Scraping completed for {bank_code} (synchronous)'
            }, status=status.HTTP_200_OK)
        except Exception as sync_error:
            return Response({
                'status': 'error',
                'message': f'Failed to start scraping: {str(sync_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

