from rest_framework import generics, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .models import Bank, CreditCard, UserCard
from .serializers import BankSerializer, CreditCardSerializer, UserCardSerializer
from .utils import identify_card_network, validate_card_number, get_card_rewards_summary
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BankListView(generics.ListAPIView):
    serializer_class = BankSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Bank.objects.filter(is_active=True)
        country = self.request.query_params.get('country')
        if country:
            queryset = queryset.filter(country=country)
        return queryset.order_by('name')
    
    def list(self, request, *args, **kwargs):
        """Override to include available banks from scraper for Trinidad & Tobago"""
        response = super().list(request, *args, **kwargs)
        country = request.query_params.get('country')
        
        # For Trinidad & Tobago, include all available banks from scraper
        if country == 'TT':
            try:
                from scraping.scrapers.trinidad_tobago_bank_scraper import TrinidadTobagoBankScraper
                scraper = TrinidadTobagoBankScraper()
                
                # Get existing banks from database
                existing_banks = {bank['code']: bank for bank in response.data if isinstance(bank, dict) and 'code' in bank}
                existing_bank_codes = set(existing_banks.keys())
                
                # Add all available banks from scraper
                all_banks_list = list(response.data) if isinstance(response.data, list) else []
                
                for bank_code, bank_info in scraper.banks.items():
                    if bank_code not in existing_bank_codes:
                        # Create a virtual bank entry for banks not yet in database
                        all_banks_list.append({
                            'id': None,  # Not in database yet
                            'code': bank_code,
                            'name': bank_info['name'],
                            'bank_type': bank_info['type'],
                            'country': 'TT',
                            'website': bank_info['urls'][0] if bank_info['urls'] else '',
                            'is_active': True,
                            'is_available': True,  # Flag to indicate it's available but not scraped yet
                        })
                
                response.data = all_banks_list
            except Exception as e:
                # If scraper import fails, just return existing banks
                logger.error(f"Error including Trinidad & Tobago banks: {str(e)}")
                pass
        
        return response
    

# cards/views.py - Update CreditCardListView
class CreditCardListView(generics.ListAPIView):
    serializer_class = CreditCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['bank', 'card_type']
    search_fields = ['name', 'bank__name']
    ordering_fields = ['name', 'annual_fee']
    ordering = ['bank__name', 'name']
    
    def get_queryset(self):
        # Get query parameters
        show_all = self.request.query_params.get('show_all', 'false').lower() == 'true'
        bank_id = self.request.query_params.get('bank')
        card_type = self.request.query_params.get('card_type')
        search = self.request.query_params.get('search')
        country = self.request.query_params.get('country')
        
        # ALWAYS show ALL cards when show_all=true (for card selection)
        # This ensures users can see all available cards for any bank
        queryset = CreditCard.objects.all().select_related('bank')
        
        # Filter by country if provided
        if country:
            queryset = queryset.filter(bank__country=country)
        
        # Apply filters
        if bank_id and bank_id != 'null':
            try:
                bank_id_int = int(bank_id)
                queryset = queryset.filter(bank_id=bank_id_int)
            except (ValueError, TypeError):
                pass  # Invalid bank_id, ignore filter
        
        if card_type and card_type != 'null':
            queryset = queryset.filter(card_type=card_type)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(bank__name__icontains=search)
            )
        
        # IMPORTANT: When show_all=true, show ALL cards (active and inactive)
        # This is needed for card selection dropdown
        if show_all:
            # Don't filter by is_active - show everything
            pass
        elif not self.request.user.is_staff:
            # For non-staff users without show_all, only show active cards
            queryset = queryset.filter(is_active=True)
        
        return queryset.distinct().order_by('bank__name', 'name')
     
class UserCardListCreateView(generics.ListCreateAPIView):
    serializer_class = UserCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserCard.objects.filter(user=self.request.user).select_related('card', 'card__bank')
    
    def perform_create(self, serializer):
        # Get card data
        card_id = serializer.validated_data.get('card')
        card_number_last4 = serializer.validated_data.get('card_number_last4', '')
        
        # Auto-identify card network from last 4 digits
        # In production, you might have full card number temporarily for network detection
        # For now, we'll use the card template's network or default
        card_network = 'VISA'  # Default, can be enhanced with card template
        
        # If primary card is being set, unset other primary cards
        if serializer.validated_data.get('is_primary', False):
            UserCard.objects.filter(user=self.request.user, is_primary=True).update(is_primary=False)
        
        # Save the user card immediately (user gets instant response)
        # IMPORTANT: Do NOT scrape here - scraping will happen automatically when user visits "My Cards" tab
        # This ensures card addition is instant and scraping happens on-demand
        user_card = serializer.save(user=self.request.user, card_network=card_network)
        
        import logging
        logger = logging.getLogger(__name__)
        if user_card.card and user_card.card.bank:
            logger.info(f"✅ Card added: {user_card.card.bank.code} - {user_card.card.name} (ID: {user_card.card.id}). Scraping will happen when user visits 'My Cards' tab.")


class CardNetworkIdentifyView(APIView):
    """API endpoint to identify card network from card number"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Identify card network from card number
        Body: { "card_number": "4111111111111111" } or { "card_number_last4": "1111" }
        """
        card_number = request.data.get('card_number', '')
        card_number_last4 = request.data.get('card_number_last4', '')
        
        if not card_number and not card_number_last4:
            return Response({
                'error': 'Either card_number or card_number_last4 is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Use full number if available, otherwise last 4
        number_to_check = card_number or card_number_last4
        network = identify_card_network(number_to_check)
        
        # Validate if full number provided
        is_valid = True
        error_message = None
        if card_number:
            is_valid, error_message = validate_card_number(card_number)
        
        return Response({
            'network': network,
            'network_display': dict(UserCard.CARD_NETWORKS).get(network, 'Unknown'),
            'is_valid': is_valid,
            'error_message': error_message,
        })


class CardRewardsView(APIView):
    """Get rewards structure for a card"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, card_id):
        """
        Get comprehensive rewards structure for a card
        """
        try:
            card = CreditCard.objects.get(id=card_id)
            rewards = get_card_rewards_summary(card)
            
            return Response({
                'card_id': card.id,
                'card_name': card.name,
                'bank_name': card.bank.name,
                'rewards': rewards,
            })
        except CreditCard.DoesNotExist:
            return Response({
                'error': 'Card not found'
            }, status=status.HTTP_404_NOT_FOUND)

class UserCardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserCard.objects.filter(user=self.request.user)


class PeekabooCardNamesView(APIView):
    """Get card names from Peekaboo API for a specific bank"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """
        Get card names from Peekaboo API for a bank
        Query params: bank_id (required)
        """
        bank_id = request.query_params.get('bank_id')
        if not bank_id:
            return Response({
                'error': 'bank_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            bank = Bank.objects.get(id=bank_id)
        except Bank.DoesNotExist:
            return Response({
                'error': 'Bank not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Import here to avoid circular imports
        from scraping.tasks_peekaboo import scrape_peekaboo_card_associations, BANK_PEEKABOO_IDS
        import requests
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Get bank's Peekaboo entityId
        bank_info = BANK_PEEKABOO_IDS.get(bank.code.upper())
        if not bank_info or not isinstance(bank_info, dict):
            return Response({
                'error': f'No Peekaboo data found for bank: {bank.code}',
                'cards': []
            })
        
        entity_id = bank_info.get('entityId')
        if not entity_id:
            return Response({
                'error': f'No entityId found for bank: {bank.code}',
                'cards': []
            })
        
        # Fetch card associations from Peekaboo API
        try:
            from scraping.tasks_peekaboo import PEEKABOO_API_BASE, PEEKABOO_HEADERS, CITIES
            
            city_info = next((c for c in CITIES if c['name'] == 'Lahore'), None)
            if not city_info:
                city_info = {'name': 'Lahore', 'code': 'LAHORE', 'lat': 31.554606, 'long': 74.357158}
            
            url = f"{PEEKABOO_API_BASE}/api/sourceEntity/{entity_id}/associationType/_all"
            params = {
                'city': city_info['name'],
                'country': 'Pakistan',
                'entity': bank.name,
                'language': 'en',
                'lat': city_info['lat'],
                'limit': 100,
                'long': city_info['long'],
                'offset': 0,
            }
            
            response = requests.get(url, params=params, headers=PEEKABOO_HEADERS, timeout=30)
            
            if response.status_code == 200:
                associations_data = response.json()
                if not isinstance(associations_data, list):
                    associations_data = []
                
                # Format card names
                cards = []
                for assoc in associations_data:
                    type_name = assoc.get('typeName', '')
                    type_id = assoc.get('typeId')
                    card_type = assoc.get('cardType', '')
                    image = assoc.get('image', '')
                    
                    if type_name:
                        cards.append({
                            'name': type_name,
                            'type_id': type_id,
                            'card_type': card_type,
                            'image': image,
                        })
                
                return Response({
                    'bank_id': bank.id,
                    'bank_name': bank.name,
                    'cards': cards,
                    'count': len(cards)
                })
            else:
                return Response({
                    'error': f'Failed to fetch from Peekaboo API: {response.status_code}',
                    'cards': []
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.error(f"Error fetching Peekaboo card names: {str(e)}")
            return Response({
                'error': f'Error fetching card names: {str(e)}',
                'cards': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)