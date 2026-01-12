# planning/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import ScheduledPurchase
from .serializers import ScheduledPurchaseSerializer, ScheduledPurchaseCreateSerializer
from cards.models import UserCard, CreditCard, CardRewardCategory
from offers.models import Offer, PeekabooDeal
import logging

logger = logging.getLogger(__name__)


class ScheduledPurchaseListCreateView(generics.ListCreateAPIView):
    """List and create scheduled purchases"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ScheduledPurchaseSerializer
    
    def get_queryset(self):
        user = self.request.user
        status_filter = self.request.query_params.get('status', 'SCHEDULED')
        return ScheduledPurchase.objects.filter(
            user=user,
            status=status_filter
        ).order_by('scheduled_date')
    
    def perform_create(self, serializer):
        purchase = serializer.save(user=self.request.user)
        # Generate recommendations
        self._generate_recommendations(purchase)
        return purchase
    
    def _generate_recommendations(self, purchase):
        """Generate card and merchant recommendations for scheduled purchase"""
        user = purchase.user
        user_cards = UserCard.objects.filter(user=user, is_active=True).select_related('card', 'card__bank')
        
        # Find best card for this purchase type
        best_card = None
        best_rate = 0
        
        for user_card in user_cards:
            card = user_card.card
            # Check reward category for this purchase type
            reward = CardRewardCategory.objects.filter(
                card=card,
                category=purchase.purchase_type,
                valid_from__lte=timezone.now().date(),
                valid_to__gte=timezone.now().date()
            ).first()
            
            if reward:
                rate = float(reward.reward_rate)
                if rate > best_rate:
                    best_rate = rate
                    best_card = card
            elif card.cashback_rate and float(card.cashback_rate) > best_rate:
                best_rate = float(card.cashback_rate)
                best_card = card
        
        # Get relevant offers
        user_banks = user_cards.values_list('card__bank_id', flat=True).distinct()
        user_card_ids = user_cards.values_list('card_id', flat=True)
        
        # Regular offers
        offers = Offer.objects.filter(
            is_active=True,
            valid_to__gte=purchase.scheduled_date.date(),
            bank_id__in=user_banks
        ).select_related('bank', 'merchant')
        
        # Filter by purchase type
        if purchase.purchase_type == 'GROCERIES':
            offers = offers.filter(merchant__merchant_type='SUPERMARKET')
        elif purchase.purchase_type == 'DINING':
            offers = offers.filter(merchant__merchant_type='RESTAURANT')
        elif purchase.purchase_type == 'SHOPPING':
            offers = offers.filter(merchant__merchant_type__in=['RETAIL', 'E_COMMERCE', 'FASHION'])
        
        # Peekaboo deals
        peekaboo_deals = PeekabooDeal.objects.filter(
            linked_cards__id__in=user_card_ids,
            is_active=True,
            is_expired=False,
            end_date__gte=purchase.scheduled_date.date()
        ).distinct()[:10]
        
        # Update purchase with recommendations
        purchase.recommended_card = best_card
        purchase.recommended_merchants = [
            {
                'merchant': offer.merchant.name if offer.merchant else 'Various',
                'discount': float(offer.discount_percentage) if offer.discount_percentage else 0,
                'valid_to': offer.valid_to.isoformat(),
            }
            for offer in offers[:5]
        ]
        purchase.active_offers = [
            {
                'title': offer.title,
                'merchant': offer.merchant.name if offer.merchant else 'Various',
                'discount': float(offer.discount_percentage) if offer.discount_percentage else 0,
            }
            for offer in list(offers[:5]) + list(peekaboo_deals[:5])
        ]
        purchase.save()


class ScheduledPurchaseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a scheduled purchase"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ScheduledPurchaseSerializer
    
    def get_queryset(self):
        return ScheduledPurchase.objects.filter(user=self.request.user)


class UpcomingPurchasesView(APIView):
    """Get upcoming scheduled purchases with recommendations"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now() + timedelta(days=days)
        
        purchases = ScheduledPurchase.objects.filter(
            user=user,
            status='SCHEDULED',
            scheduled_date__lte=end_date,
            scheduled_date__gte=timezone.now()
        ).order_by('scheduled_date')
        
        serializer = ScheduledPurchaseSerializer(purchases, many=True)
        return Response(serializer.data)


class CompleteScheduledPurchaseView(APIView):
    """Mark a scheduled purchase as completed"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, purchase_id):
        try:
            purchase = ScheduledPurchase.objects.get(
                id=purchase_id,
                user=request.user,
                status='SCHEDULED'
            )
            purchase.status = 'COMPLETED'
            purchase.completed_at = timezone.now()
            purchase.save()
            
            serializer = ScheduledPurchaseSerializer(purchase)
            return Response(serializer.data)
        except ScheduledPurchase.DoesNotExist:
            return Response(
                {'error': 'Purchase not found'},
                status=status.HTTP_404_NOT_FOUND
            )

