# offers/views.py
from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.conf import settings
from django.db.models import Q, Count
from .models import Offer, UserOffer, Merchant
from .serializers import OfferSerializer, UserOfferSerializer, MerchantSerializer
from cards.models import UserCard, Bank
from admin_panel.models import ScrapingLog
from django.db import models
import logging

# REMOVE THESE IMPORTS:
# from scraping.tasks import scrape_verified_banks
# import asyncio
# from scraping.scrapers.verified_bank_scraper import VerifiedBankScraper

logger = logging.getLogger(__name__)

class OfferListView(generics.ListAPIView):
    serializer_class = OfferSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['bank', 'offer_type', 'merchant__merchant_type', 'merchant__city']
    search_fields = ['title', 'description', 'bank__name', 'merchant__name']
    ordering_fields = ['valid_to', 'created_at', 'discount_percentage']
    ordering = ['-valid_to']
    
    def get_queryset(self):
        user = self.request.user
        now = timezone.now().date()
        
        # Base queryset
        queryset = Offer.objects.filter(
            is_active=True,
            valid_to__gte=now
        ).select_related('bank', 'merchant', 'card')
        
        # Get filter parameters
        bank_id = self.request.query_params.get('bank')
        merchant_type = self.request.query_params.get('merchant_type')
        city = self.request.query_params.get('city')
        card_type = self.request.query_params.get('card_type')
        offer_type = self.request.query_params.get('offer_type')
        search = self.request.query_params.get('search')
        
        # Apply filters
        if bank_id:
            queryset = queryset.filter(bank_id=bank_id)
        
        if merchant_type:
            queryset = queryset.filter(merchant__merchant_type=merchant_type)
        
        if city:
            queryset = queryset.filter(merchant__city=city)
        
        if card_type:
            queryset = queryset.filter(card__card_type=card_type)
        
        if offer_type:
            queryset = queryset.filter(offer_type=offer_type)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(bank__name__icontains=search) |
                Q(merchant__name__icontains=search)
            )
        
        # For regular users, show only offers from their banks
        if not user.is_staff:
            user_bank_ids = UserCard.objects.filter(
                user=user, 
                is_active=True
            ).values_list('card__bank_id', flat=True).distinct()
            
            if user_bank_ids:
                queryset = queryset.filter(bank_id__in=user_bank_ids)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Create UserOffer entries for the user
        for offer in queryset:
            UserOffer.objects.get_or_create(
                user=request.user,
                offer=offer,
                defaults={'status': 'AVAILABLE'}
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

class PersonalizedOfferView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        user_cards = UserCard.objects.filter(user=user).select_related('card__bank')
        if not user_cards.exists():
            return Response([])
        
        user_bank_ids = [card.card.bank.id for card in user_cards]
        offers = Offer.objects.filter(
            bank_id__in=user_bank_ids,
            is_active=True,
            valid_to__gte=timezone.now().date()
        ).select_related('bank', 'merchant').order_by('-discount_percentage')[:20]
        
        # Create UserOffer entries
        for offer in offers:
            UserOffer.objects.get_or_create(
                user=user,
                offer=offer,
                defaults={'status': 'AVAILABLE'}
            )
        
        serializer = OfferSerializer(offers, many=True, context={'request': request})
        return Response(serializer.data)

class BankOffersView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, bank_id):
        try:
            bank = Bank.objects.get(id=bank_id)
            offers = Offer.objects.filter(
                bank=bank,
                is_active=True,
                valid_to__gte=timezone.now().date()
            ).select_related('merchant').order_by('-valid_to')
            
            # Create UserOffer entries
            for offer in offers:
                UserOffer.objects.get_or_create(
                    user=request.user,
                    offer=offer,
                    defaults={'status': 'AVAILABLE'}
                )
            
            serializer = OfferSerializer(offers, many=True, context={'request': request})
            return Response(serializer.data)
        except Bank.DoesNotExist:
            return Response({'error': 'Bank not found'}, status=status.HTTP_404_NOT_FOUND)

class ScrapeBankOffersView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, bank_id):
        try:
            if not request.user.is_staff and not settings.DEBUG:
                return Response({'error': 'Only admins can trigger scraping'}, status=status.HTTP_403_FORBIDDEN)
            
            bank = Bank.objects.get(id=bank_id)
            
            # Get filters from request
            filters = {
                'city': request.data.get('city') or request.query_params.get('city'),
                'merchant_type': request.data.get('merchant_type') or request.query_params.get('merchant_type'),
                'card_type': request.data.get('card_type') or request.query_params.get('card_type'),
                'search': request.data.get('search') or request.query_params.get('search'),
            }
            
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}
            
            # Check for running scrapes
            running_scrapes = ScrapingLog.objects.filter(
                bank=bank,
                status='RUNNING',
                started_at__gte=timezone.now() - timezone.timedelta(minutes=10)
            )
            
            if running_scrapes.exists():
                return Response({'error': 'Scraping is already running for this bank'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create scraping log
            log = ScrapingLog.objects.create(
                bank=bank,
                status='RUNNING',
                offers_found=0,
                offers_created=0,
                offers_updated=0,
            )
            
            # Import locally to avoid circular imports
            from scraping.tasks import scrape_single_bank_with_filters
            task = scrape_single_bank_with_filters.delay(bank_id, filters)
            
            return Response({
                'status': 'success',
                'message': f'Scraping started for {bank.name}',
                'task_id': task.id,
                'filters': filters,
                'bank': {'id': bank.id, 'name': bank.name, 'code': bank.code}
            })
            
        except Bank.DoesNotExist:
            return Response({'error': 'Bank not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ScrapeAllBanksWithFiltersView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        try:
            # Get filters from request
            filters = {
                'city': request.data.get('city'),
                'merchant_type': request.data.get('merchant_type'),
                'search': request.data.get('search'),
            }
            
            # Remove None values
            filters = {k: v for k, v in filters.items() if v is not None}
            
            # Import locally to avoid circular imports
            from scraping.tasks import scrape_verified_banks_with_filters
            task = scrape_verified_banks_with_filters.delay(filters)
            
            return Response({
                'status': 'success',
                'message': 'Scraping started for all banks with filters',
                'task_id': task.id,
                'filters': filters
            })
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CityOffersView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, city):
        valid_cities = [choice[0] for choice in Merchant.PAKISTAN_CITIES]
        if city not in valid_cities:
            return Response({'error': 'Invalid city'}, status=status.HTTP_400_BAD_REQUEST)
        
        offers = Offer.objects.filter(
            merchant__city=city,
            is_active=True,
            valid_to__gte=timezone.now().date()
        ).select_related('bank', 'merchant').order_by('-discount_percentage')
        
        # Create UserOffer entries
        for offer in offers:
            UserOffer.objects.get_or_create(
                user=request.user,
                offer=offer,
                defaults={'status': 'AVAILABLE'}
            )
        
        serializer = OfferSerializer(offers, many=True, context={'request': request})
        return Response(serializer.data)

class MerchantTypeOffersView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, merchant_type):
        valid_types = [choice[0] for choice in Merchant.MERCHANT_TYPES]
        if merchant_type not in valid_types:
            return Response({'error': 'Invalid merchant type'}, status=status.HTTP_400_BAD_REQUEST)
        
        offers = Offer.objects.filter(
            merchant__merchant_type=merchant_type,
            is_active=True,
            valid_to__gte=timezone.now().date()
        ).select_related('bank', 'merchant').order_by('-discount_percentage')
        
        # Create UserOffer entries
        for offer in offers:
            UserOffer.objects.get_or_create(
                user=request.user,
                offer=offer,
                defaults={'status': 'AVAILABLE'}
            )
        
        serializer = OfferSerializer(offers, many=True, context={'request': request})
        return Response(serializer.data)

class OfferStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        now = timezone.now().date()
        
        stats = {
            'total_offers': Offer.objects.filter(is_active=True).count(),
            'active_offers': Offer.objects.filter(is_active=True, valid_to__gte=now).count(),
            'offers_by_bank': list(Offer.objects.filter(is_active=True, valid_to__gte=now)
                                  .values('bank__name')
                                  .annotate(count=Count('id'))
                                  .order_by('-count')),
            'offers_by_city': list(Offer.objects.filter(is_active=True, valid_to__gte=now)
                                  .values('merchant__city')
                                  .annotate(count=Count('id'))
                                  .order_by('-count')),
            'offers_by_type': list(Offer.objects.filter(is_active=True, valid_to__gte=now)
                                  .values('offer_type')
                                  .annotate(count=Count('id'))
                                  .order_by('-count')),
            'recent_scrapes': list(ScrapingLog.objects.filter(status='COMPLETED')
                                  .order_by('-started_at')[:5]
                                  .values('bank__name', 'offers_found', 'offers_created', 'started_at')),
        }
        return Response(stats)

class ActivateOfferView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, offer_id):
        try:
            offer = Offer.objects.get(id=offer_id)
            
            # Check if user has access to this offer
            user_offer, created = UserOffer.objects.get_or_create(
                user=request.user,
                offer=offer,
                defaults={'status': 'ACTIVATED'}
            )
            
            if not created:
                user_offer.status = 'ACTIVATED'
                user_offer.activated_at = timezone.now()
                user_offer.save()
            
            return Response({
                'status': 'success',
                'message': 'Offer activated successfully!',
                'offer_id': offer.id,
                'offer_title': offer.title
            }, status=status.HTTP_200_OK)
            
        except Offer.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Offer not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MerchantListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        merchants = Merchant.objects.filter(is_active=True)
        serializer = MerchantSerializer(merchants, many=True)
        return Response(serializer.data)