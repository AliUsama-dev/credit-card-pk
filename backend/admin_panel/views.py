# admin_panel/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.db.models import Count
from cards.models import Bank, CreditCard
from offers.models import Offer, Merchant
from users.models import User

class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        # Get statistics
        stats = {
            'total_users': User.objects.count(),
            'total_banks': Bank.objects.count(),
            'total_cards': CreditCard.objects.count(),
            'total_offers': Offer.objects.count(),
            'active_offers': Offer.objects.filter(is_active=True).count(),
            'total_merchants': Merchant.objects.count(),
            'users_by_type': dict(User.objects.values_list('user_type').annotate(count=Count('id'))),
            'offers_by_bank': list(Offer.objects.values('bank__name').annotate(count=Count('id')).order_by('-count')[:5]),
        }
        
        return Response(stats)

class BankManagementView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        banks = Bank.objects.all()
        data = [{
            'id': bank.id,
            'name': bank.name,
            'code': bank.code,
            'cards_count': bank.cards.count(),
            'offers_count': bank.offers.count(),
            'is_active': bank.is_active,
            'created_at': bank.created_at
        } for bank in banks]
        
        return Response(data)

class CardManagementView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        cards = CreditCard.objects.select_related('bank').all()
        data = [{
            'id': card.id,
            'name': card.name,
            'bank': card.bank.name,
            'card_type': card.card_type,
            'annual_fee': card.annual_fee,
            'is_active': card.is_active,
            'last_scraped': card.last_scraped,
            'users_count': card.usercard_set.count()
        } for card in cards]
        
        return Response(data)

class OfferManagementView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        offers = Offer.objects.select_related('bank', 'merchant').all()
        data = [{
            'id': offer.id,
            'title': offer.title,
            'bank': offer.bank.name,
            'merchant': offer.merchant.name if offer.merchant else None,
            'offer_type': offer.offer_type,
            'discount_percentage': offer.discount_percentage,
            'valid_to': offer.valid_to,
            'is_active': offer.is_active,
            'last_updated': offer.last_updated
        } for offer in offers]
        
        return Response(data)