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
        user_card = serializer.save(user=self.request.user, card_network=card_network)
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Trigger background scraping for this new card (async, non-blocking)
        if user_card.card and user_card.card.bank:
            logger.info(f"✅ Card added: {user_card.card.bank.code} - {user_card.card.name} (ID: {user_card.card.id}). Triggering background scraping...")
            
            # Import scraping tasks
            try:
                from scraping.tasks_peekaboo import scrape_peekaboo_deals_by_bank, scrape_peekaboo_card_associations
                from scraping.tasks_partners import scrape_partner_bank_detail
                from offers.models_partners import PartnerBank, PartnerCard
                from django.db.models import Q
                import threading
                
                def scrape_in_background():
                    """Scrape deals in background thread (non-blocking)"""
                    try:
                        bank = user_card.card.bank
                        card = user_card.card
                        city = 'LAHORE'  # Default city, user can change later
                        
                        logger.info(f"🔄 Background: Scraping Peekaboo deals for {bank.code} - {card.name}...")
                        
                        # Step 1: Scrape card associations (to get peekaboo_association_type_id if missing)
                        try:
                            scrape_peekaboo_card_associations(bank.code, city)
                        except Exception as e:
                            logger.warning(f"⚠️  Failed to scrape card associations: {str(e)}")
                        
                        # Step 2: Scrape Peekaboo deals for this specific card
                        try:
                            result = scrape_peekaboo_deals_by_bank(
                                bank_code=bank.code,
                                city_name=city,
                                card_id=card.id  # Scrape deals specifically for this card
                            )
                            logger.info(f"✅ Background: Peekaboo deals scraped - {result.get('created', 0)} created, {result.get('updated', 0)} updated")
                        except Exception as e:
                            logger.error(f"❌ Failed to scrape Peekaboo deals: {str(e)}", exc_info=True)
                        
                        # Step 3: Scrape Partners Offers for this bank (if it's a partner bank)
                        # AND link PartnerCards to this CreditCard if names match
                        try:
                            partner_bank = PartnerBank.objects.filter(bank=bank).first()
                            if partner_bank:
                                logger.info(f"🔄 Background: Scraping Partners Offers for {bank.name}...")
                                scrape_partner_bank_detail(partner_bank.id, city.lower())
                                logger.info(f"✅ Background: Partners Offers scraped for {bank.name}")
                                
                                # Step 4: Link PartnerCards to this CreditCard if names match
                                # This ensures Partners Offers show up for user's card
                                card_name_normalized = card.name.lower().replace(' card', '').replace('card', '').strip()
                                matching_partner_cards = PartnerCard.objects.filter(
                                    partner_bank=partner_bank,
                                    is_active=True
                                ).filter(
                                    Q(name__iexact=card.name) |
                                    Q(name__icontains=card_name_normalized) |
                                    Q(name__icontains=card.name.split()[0] if card.name.split() else '')
                                )
                                
                                linked_count = 0
                                for partner_card in matching_partner_cards:
                                    if not partner_card.credit_card or partner_card.credit_card.id != card.id:
                                        partner_card.credit_card = card
                                        partner_card.save(update_fields=['credit_card'])
                                        linked_count += 1
                                        logger.info(f"✅ Linked PartnerCard '{partner_card.name}' to CreditCard '{card.name}' (ID: {card.id})")
                                
                                if linked_count > 0:
                                    logger.info(f"✅ Background: Linked {linked_count} PartnerCard(s) to user's CreditCard")
                            else:
                                logger.debug(f"Partners Offers not available for {bank.name}")
                        except Exception as e:
                            logger.error(f"❌ Failed to scrape/link Partners Offers: {str(e)}", exc_info=True)
                            
                    except Exception as e:
                        logger.error(f"❌ Background scraping error: {str(e)}", exc_info=True)
                
                # Start background thread (non-blocking)
                thread = threading.Thread(target=scrape_in_background, daemon=True)
                thread.start()
                logger.info(f"🚀 Background scraping thread started for {user_card.card.name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to start background scraping: {str(e)}", exc_info=True)


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