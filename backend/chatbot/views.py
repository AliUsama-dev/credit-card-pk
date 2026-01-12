# chatbot/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from openai import OpenAI
import os
from django.utils import timezone
from django.db.models import Q
from cards.models import UserCard
from offers.models import Offer, UserOffer
from datetime import datetime, timedelta

# Initialize OpenAI client
# Get API key from Django settings or environment variable
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

api_key = os.getenv('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', '')
if api_key:
    client = OpenAI(api_key=api_key)
    logger.info("OpenAI client initialized successfully")
else:
    client = None
    logger.warning("OpenAI API key not found. Chatbot functionality will not work.")

class ChatbotView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user_message = request.data.get('message', '').strip()
        user = request.user
        
        if not user_message:
            return Response({
                'status': 'error',
                'message': 'Message is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Get comprehensive user context
            context = self._build_user_context(user)
            
            # Analyze user query intent
            intent = self._analyze_intent(user_message)
            
            # Get relevant offers based on intent
            relevant_offers_data = self._get_relevant_offers(user, intent)
            relevant_offers = relevant_offers_data.get('regular_offers', [])
            peekaboo_deals = relevant_offers_data.get('peekaboo_deals', [])
            
            # Enhanced context with offers
            enhanced_context = f"""
{context}

Current Active Offers for User:
{self._format_offers(relevant_offers[:10])}

Peekaboo Deals (Card-Linked Offers):
{self._format_peekaboo_deals(peekaboo_deals)}

User Query Intent: {intent}

Instructions: 
You are an intelligent credit card optimization assistant. Your goal is to help users maximize their rewards and savings.

DETECT USER LOCATION: Check the user's cards and location context. If they have Trinidad & Tobago banks (TT country code), use TTD currency and Trinidad & Tobago context. If they have Pakistani banks (PK country code), use PKR currency and Pakistani context. If they have both, adapt based on the query context.

KEY CAPABILITIES:
1. Card Recommendations: When user asks "best card for X" or "which card should I use", analyze their ALL user cards and recommend the optimal one based on:
   - Reward rates for the specific category
   - User's spending patterns
   - Active offers available
   - Annual fees and benefits

2. Contextual Recommendations:
   - When user says "I'm hungry" or "I need food": Suggest nearby restaurants with active card offers, mention which of their cards has the best dining rewards
   - When user says "I need to shop" or "shopping": Recommend shopping offers and which card to use based on their spending history
   - When user mentions a specific merchant: Check if they have offers for that merchant and recommend the best card
   - When user asks about travel: Suggest travel offers and cards with best travel rewards

3. Spending Analysis:
   - Reference their spending patterns when making recommendations
   - Point out missed savings opportunities if relevant
   - Suggest how to optimize future spending

4. Offer Awareness:
   - Always check active offers for user's cards
   - Mention specific merchant names, discount percentages, and validity dates
   - Recommend activating offers before they expire

5. Personalization:
   - Use their name when appropriate
   - Reference their actual cards by name
   - Consider their spending history and preferences
   - Be conversational, helpful, and specific

6. Professional Tone:
   - Be friendly but professional
   - Provide actionable advice
   - Adapt context based on user location:
     * For Trinidad & Tobago: Use TTD currency, mention cities like Port of Spain, San Fernando, Arima; local merchants and T&T banks (Citibank T&T, Republic Bank, First Citizens, etc.)
     * For Pakistan: Use PKR currency, mention cities like Karachi, Lahore, Islamabad; local merchants and Pakistani banks (HBL, UBL, MCB, etc.)
   - Format numbers in the appropriate currency (TTD or PKR)
   - Be concise but comprehensive

IMPORTANT: Always reference the user's actual cards from their profile. If they have multiple cards, compare them and recommend the best one for the specific situation. Adapt your language and currency based on the user's card locations.
"""
            
            # Check if OpenAI client is available
            if not client:
                return Response({
                    'status': 'error',
                    'message': 'OpenAI API key not configured. Please contact administrator.'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Call OpenAI API with enhanced context
            # Try newer models first, fallback to older ones
            models_to_try = [
                "gpt-4o-mini",  # Latest, cost-effective model
                "gpt-4o",       # Latest full model
                "gpt-4-turbo",  # Previous generation
                "gpt-4",        # Standard GPT-4
                "gpt-3.5-turbo" # Fallback
            ]
            
            response = None
            last_error = None
            
            for model_name in models_to_try:
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": enhanced_context},
                            {"role": "user", "content": user_message}
                        ],
                        max_tokens=800,
                        temperature=0.7,
                    )
                    logger.info(f"Successfully used model: {model_name}")
                    break  # Success, exit loop
                except Exception as e:
                    last_error = e
                    logger.warning(f"Model {model_name} failed: {str(e)}, trying next model...")
                    continue
            
            if not response:
                # All models failed
                error_msg = f"All models failed. Last error: {str(last_error)}"
                logger.error(error_msg)
                return Response({
                    'status': 'error',
                    'message': 'OpenAI API error. Please try again later.',
                    'details': str(last_error) if last_error else 'Unknown error'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            bot_response = response.choices[0].message.content
            
            # Extract recommendations (offers mentioned in response)
            all_offers = list(relevant_offers) + list(peekaboo_deals)
            recommendations = self._extract_recommendations(bot_response, all_offers)
            
            # Include user cards summary in response for frontend display
            user_cards_summary = []
            user_cards = UserCard.objects.filter(user=user, is_active=True).select_related('card', 'card__bank')
            for uc in user_cards[:5]:  # Limit to 5 for response
                user_cards_summary.append({
                    'id': uc.id,
                    'name': uc.card.name,
                    'bank': uc.card.bank.name,
                    'is_primary': uc.is_primary,
                })
            
            return Response({
                'status': 'success',
                'response': bot_response,
                'recommendations': recommendations,
                'intent': intent,
                'timestamp': timezone.now().isoformat(),
                'user_cards': user_cards_summary,  # Include user cards for frontend
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _build_user_context(self, user):
        """Build comprehensive user context with all user cards, spending patterns, and financial profile"""
        from transactions.models import Transaction
        from cards.models import CardRewardCategory
        from django.db.models import Sum, Count, Avg
        
        # Get all user cards with detailed information
        user_cards = UserCard.objects.filter(user=user, is_active=True).select_related('card', 'card__bank')
        
        # Detect user's primary country based on cards
        user_countries = set()
        cards_info = []
        for uc in user_cards:
            card = uc.card
            bank = card.bank
            user_countries.add(bank.country)
            
            # Get reward categories for this card
            reward_categories = CardRewardCategory.objects.filter(
                card=card,
                valid_from__lte=timezone.now().date(),
                valid_to__gte=timezone.now().date()
            ).values_list('category', 'reward_rate')
            
            reward_details = []
            for cat, rate in reward_categories:
                reward_details.append(f"{cat}: {rate}%")
            
            # Determine currency based on bank country
            currency = 'TTD' if bank.country == 'TT' else 'PKR'
            
            card_info = f"- {card.name} ({bank.name}): {card.card_type}"
            if card.cashback_rate:
                card_info += f", {card.cashback_rate}% base cashback"
            if reward_details:
                card_info += f"\n  Reward Categories: {', '.join(reward_details)}"
            if card.annual_fee:
                card_info += f"\n  Annual Fee: {currency} {card.annual_fee}"
            if uc.is_primary:
                card_info += " [PRIMARY CARD]"
            
            cards_info.append(card_info)
        
        # Determine primary country and currency
        primary_country = 'TT' if 'TT' in user_countries else ('PK' if 'PK' in user_countries else 'US')
        currency = 'TTD' if primary_country == 'TT' else ('PKR' if primary_country == 'PK' else 'USD')
        location_context = 'Trinidad & Tobago' if primary_country == 'TT' else ('Pakistan' if primary_country == 'PK' else 'United States')
        
        # Get user's spending patterns from transactions (last 90 days)
        recent_date = timezone.now().date() - timedelta(days=90)
        transactions = Transaction.objects.filter(
            user=user,
            date__gte=recent_date
        )
        
        # Spending by category
        spending_by_category = transactions.values('category').annotate(
            total=Sum('amount'),
            count=Count('id'),
            avg_amount=Avg('amount')
        ).order_by('-total')[:10]
        
        category_info = []
        if spending_by_category:
            category_info.append("\nSpending Patterns (Last 90 Days):")
            for item in spending_by_category:
                category_info.append(
                    f"- {item['category']}: {currency} {item['total']:.2f} "
                    f"({item['count']} transactions, avg: {currency} {item['avg_amount']:.2f})"
                )
        
        # Total spending and rewards
        total_spent = transactions.aggregate(total=Sum('amount'))['total'] or 0
        total_reward_earned = transactions.aggregate(total=Sum('reward_earned'))['total'] or 0
        total_missed_savings = transactions.aggregate(total=Sum('missed_savings'))['total'] or 0
        
        # Top merchants
        top_merchants = transactions.values('merchant').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')[:5]
        
        merchant_info = []
        if top_merchants:
            merchant_info.append("\nFrequently Visited Merchants:")
            for item in top_merchants:
                merchant_info.append(f"- {item['merchant']}: {currency} {item['total']:.2f} ({item['count']} visits)")
        
        # Recent transactions summary
        recent_transactions = transactions.order_by('-date')[:5]
        recent_info = []
        if recent_transactions:
            recent_info.append("\nRecent Transactions:")
            for txn in recent_transactions:
                recent_info.append(
                    f"- {txn.date}: {txn.merchant} - {currency} {txn.amount:.2f} "
                    f"({txn.category}, Reward: {currency} {txn.reward_earned:.2f})"
                )
        
        context = f"""
User Profile:
- Name: {user.first_name} {user.last_name}
- Email: {user.email}
- User Type: {getattr(user, 'user_type', 'Standard')}
- Premium Status: {'Yes' if getattr(user, 'is_premium', False) else 'No'}

All User Cards ({user_cards.count()} active cards):
{chr(10).join(cards_info) if cards_info else "No cards added yet"}

Financial Summary (Last 90 Days):
- Total Spent: {currency} {total_spent:.2f}
- Total Rewards Earned: {currency} {total_reward_earned:.2f}
- Missed Savings Opportunity: {currency} {total_missed_savings:.2f}
{chr(10).join(category_info) if category_info else ""}
{chr(10).join(merchant_info) if merchant_info else ""}
{chr(10).join(recent_info) if recent_info else ""}

Current Date: {timezone.now().strftime('%Y-%m-%d %H:%M')}
Location: {location_context} ({', '.join(user_countries) if user_countries else 'Unknown'} banks and merchants)
"""
        return context
    
    def _analyze_intent(self, message):
        """Analyze user intent from message"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['hungry', 'food', 'eat', 'restaurant', 'dining', 'lunch', 'dinner']):
            return 'DINING'
        elif any(word in message_lower for word in ['shop', 'shopping', 'buy', 'purchase', 'store', 'mall']):
            return 'SHOPPING'
        elif any(word in message_lower for word in ['travel', 'hotel', 'flight', 'trip', 'vacation']):
            return 'TRAVEL'
        elif any(word in message_lower for word in ['grocery', 'supermarket', 'food', 'groceries']):
            return 'GROCERIES'
        elif any(word in message_lower for word in ['fuel', 'gas', 'petrol', 'diesel']):
            return 'FUEL'
        elif any(word in message_lower for word in ['best card', 'which card', 'recommend card', 'card for']):
            return 'CARD_RECOMMENDATION'
        elif any(word in message_lower for word in ['offer', 'discount', 'deal', 'promotion']):
            return 'OFFERS'
        else:
            return 'GENERAL'
    
    def _get_relevant_offers(self, user, intent):
        """Get relevant offers based on user and intent - includes both regular offers and Peekaboo deals"""
        from offers.models import PeekabooDeal
        
        # Get user's banks and cards
        user_cards = UserCard.objects.filter(user=user, is_active=True).select_related('card', 'card__bank')
        user_banks = user_cards.values_list('card__bank_id', flat=True).distinct()
        user_card_ids = user_cards.values_list('card_id', flat=True)
        
        # Get regular offers
        offers = Offer.objects.filter(
            is_active=True,
            valid_to__gte=timezone.now().date(),
            bank_id__in=user_banks
        ).select_related('bank', 'merchant')
        
        # Filter by intent
        if intent == 'DINING':
            offers = offers.filter(merchant__merchant_type='RESTAURANT')
        elif intent == 'SHOPPING':
            offers = offers.filter(merchant__merchant_type__in=['RETAIL', 'E_COMMERCE', 'FASHION'])
        elif intent == 'TRAVEL':
            offers = offers.filter(merchant__merchant_type='TRAVEL')
        elif intent == 'GROCERIES':
            offers = offers.filter(merchant__merchant_type='SUPERMARKET')
        elif intent == 'FUEL':
            offers = offers.filter(merchant__merchant_type='FUEL_STATION')
        
        # Get Peekaboo deals for user's cards
        peekaboo_deals = PeekabooDeal.objects.filter(
            linked_cards__id__in=user_card_ids,
            is_active=True,
            is_expired=False,
            end_date__gte=timezone.now().date()
        ).distinct().select_related('bank')[:10]
        
        # Combine and return (we'll format them separately)
        return {
            'regular_offers': offers.order_by('-discount_percentage')[:20],
            'peekaboo_deals': peekaboo_deals
        }
    
    def _format_offers(self, offers):
        """Format offers for context"""
        if not offers:
            return "No active regular offers available."
        
        formatted = []
        for offer in offers:
            merchant_name = offer.merchant.name if offer.merchant else "Various Merchants"
            discount = f"{offer.discount_percentage}% OFF" if offer.discount_percentage else "Special Offer"
            formatted.append(f"- {offer.title} at {merchant_name}: {discount} (Valid until {offer.valid_to})")
        
        return "\n".join(formatted)
    
    def _format_peekaboo_deals(self, deals):
        """Format Peekaboo deals for context"""
        if not deals:
            return "No active Peekaboo deals available."
        
        formatted = []
        for deal in deals:
            discount = f"{deal.percentage_value}% OFF" if deal.percentage_value else "Special Offer"
            merchant = deal.target_entity_name or "Various Merchants"
            city = f" in {deal.city}" if deal.city else ""
            formatted.append(
                f"- {deal.title} at {merchant}{city}: {discount} "
                f"(Valid until {deal.end_date.strftime('%Y-%m-%d')})"
            )
        
        return "\n".join(formatted)
    
    def _extract_recommendations(self, response, offers):
        """Extract offer recommendations from AI response"""
        recommendations = []
        response_lower = response.lower()
        
        for offer in offers[:10]:  # Top 10 offers/deals
            # Handle regular offers
            if hasattr(offer, 'merchant') and offer.merchant:
                merchant_name = offer.merchant.name.lower()
                if merchant_name in response_lower or offer.title.lower() in response_lower:
                    recommendations.append({
                        'id': offer.id,
                        'title': offer.title,
                        'merchant': offer.merchant.name,
                        'discount': offer.discount_percentage,
                        'bank': offer.bank.name if offer.bank else 'Various',
                    })
            # Handle Peekaboo deals
            elif hasattr(offer, 'target_entity_name'):
                merchant_name = (offer.target_entity_name or '').lower()
                if merchant_name in response_lower or offer.title.lower() in response_lower:
                    recommendations.append({
                        'id': offer.id,
                        'title': offer.title,
                        'merchant': offer.target_entity_name or 'Various Merchants',
                        'discount': offer.percentage_value or 0,
                        'bank': offer.bank.name if offer.bank else 'Various',
                    })
        
        return recommendations[:5]  # Return top 5

class ChatHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        # Return user's chat history (to be implemented with a model)
        # For now, return empty array - can be extended with ChatHistory model
        return Response({
            'history': []
        })