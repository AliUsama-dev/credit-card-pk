# transactions/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import generics
from django.http import HttpResponse
from django.db.models import Sum, Count, Q, Max
from django.db import models
import os
from django.conf import settings
from datetime import datetime, timedelta
from .parsers.pdf_parser import StatementParser
from .models import Transaction
from cards.models import UserCard
import json
import csv
import logging

logger = logging.getLogger(__name__)

# Map transaction categories to Peekaboo categories
CATEGORY_MAP = {
    'DINING': ['Food', 'food', 'dining', 'restaurant'],
    'GROCERIES': ['Grocery', 'grocery', 'supermarket'],
    'TRAVEL': ['Hotels', 'hotels', 'travel'],
    'SHOPPING': ['Lifestyle', 'lifestyle', 'shopping', 'Home Décor', 'home-decor', 'Electronics', 'electronics'],
    'ENTERTAINMENT': ['Entertainment', 'entertainment'],
    'ONLINE_SHOPPING': ['E-Stores', 'e-stores', 'online'],
    'UTILITIES': ['Public Services', 'public-services', 'utilities'],
    'OTHER': ['Services', 'services', 'Health', 'health', 'Education', 'education', 'Self-Care', 'self-care'],
}

class StatementUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        if 'statement' not in request.FILES:
            return Response({
                'status': 'error',
                'message': 'No statement file provided'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        statement_file = request.FILES['statement']
        card_id = request.data.get('card_id')
        
        try:
            # Save uploaded file
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'statements')
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, f"{request.user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            
            with open(file_path, 'wb+') as destination:
                for chunk in statement_file.chunks():
                    destination.write(chunk)
            
            # Parse PDF
            parser = StatementParser()
            transactions = parser.parse_pdf_statement(file_path)
            
            # Analyze transactions
            analysis = self.analyze_transactions(request.user, transactions, card_id)
            
            # Save transactions to database
            saved_count = self.save_transactions(request.user, transactions, card_id, file_path)
            
            return Response({
                'status': 'success',
                'message': f'Successfully parsed {len(transactions)} transactions and saved {saved_count}',
                'transactions': transactions[:10],  # Return first 10 for preview
                'analysis': analysis,
                'file_path': file_path,
                'saved_count': saved_count
            })
            
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_peekaboo_category(self, transaction_category: str) -> list:
        """Map transaction category to Peekaboo categories"""
        return CATEGORY_MAP.get(transaction_category, ['OTHER', 'other'])
    
    def _get_best_offer_percentage(self, card_id: int, category: str) -> float:
        """Get best % OFF offer for a card and category from Peekaboo and Partners Offers"""
        try:
            from offers.models_peekaboo import PeekabooDeal
            from offers.models_partners import PartnerOffer
            from cards.models import CreditCard
            
            card = CreditCard.objects.get(id=card_id)
            peekaboo_categories = self._get_peekaboo_category(category)
            
            best_pct = 0.0
            
            # Check Peekaboo Deals
            peekaboo_qs = PeekabooDeal.objects.filter(
                linked_cards__id=card_id,
                is_active=True,
                is_expired=False
            )
            
            # Filter by category (try multiple category names)
            category_filter = Q()
            for cat in peekaboo_categories:
                category_filter |= Q(category__icontains=cat) | Q(title__icontains=cat)
            
            if category_filter:
                peekaboo_qs = peekaboo_qs.filter(category_filter)
            
            # Get best percentage from Peekaboo
            peekaboo_best = peekaboo_qs.aggregate(
                best_pct=Max('percentage_value')
            )['best_pct']
            
            if peekaboo_best:
                best_pct = max(best_pct, float(peekaboo_best))
            
            # Check Partners Offers
            partner_qs = PartnerOffer.objects.filter(
                partner_card__credit_card_id=card_id,
                is_active=True,
                is_expired=False
            )
            
            # Filter by category
            category_filter = Q()
            for cat in peekaboo_categories:
                category_filter |= Q(category__icontains=cat) | Q(title__icontains=cat) | Q(merchant_name__icontains=cat)
            
            if category_filter:
                partner_qs = partner_qs.filter(category_filter)
            
            # Get best percentage from Partners Offers
            partner_best = partner_qs.aggregate(
                best_pct=Max('discount_percentage')
            )['best_pct']
            
            if partner_best:
                best_pct = max(best_pct, float(partner_best))
            
            return best_pct
            
        except Exception as e:
            logger.error(f"Error getting best offer percentage: {str(e)}")
            return 0.0
    
    def analyze_transactions(self, user, transactions, card_id=None):
        """Analyze transactions using % OFF offers from Peekaboo and Partners Offers (Pakistani banks)"""
        # Get user's cards
        user_cards = UserCard.objects.filter(user=user, is_active=True).select_related('card', 'card__bank')
        
        # Get the card used for this statement if provided
        used_card = None
        if card_id:
            try:
                used_card = UserCard.objects.get(user=user, card_id=card_id, is_active=True)
            except UserCard.DoesNotExist:
                logger.warning(f"UserCard not found for card_id={card_id}")
        
        analysis = {
            'total_spent': 0,
            'by_category': {},
            'potential_savings': 0,
            'missed_savings': 0,
            'recommendations': [],
            'card_performance': {}
        }
        
        for transaction in transactions:
            amount = float(transaction['amount'])
            category = transaction['category']
            
            analysis['total_spent'] += amount
            
            # Track by category
            if category not in analysis['by_category']:
                analysis['by_category'][category] = 0
            analysis['by_category'][category] += amount
            
            # Calculate savings (% OFF) earned with used card
            savings_earned = 0.0
            if used_card and used_card.card:
                best_pct = self._get_best_offer_percentage(used_card.card.id, category)
                if best_pct > 0:
                    savings_earned = (amount * best_pct) / 100
            
            # Find best card for this category (highest % OFF)
            best_card = None
            best_user_card = None
            best_pct = 0.0
            
            for user_card in user_cards:
                if user_card.card:
                    card_pct = self._get_best_offer_percentage(user_card.card.id, category)
                    if card_pct > best_pct:
                        best_pct = card_pct
                        best_card = user_card.card
                        best_user_card = user_card
            
            # Calculate potential savings with best card
            potential_savings = (amount * best_pct) / 100 if best_pct > 0 else 0
            missed_savings = potential_savings - savings_earned
            
            if best_card and best_pct > 0:
                analysis['potential_savings'] += potential_savings
                if missed_savings > 0:
                    analysis['missed_savings'] += missed_savings
                    analysis['recommendations'].append({
                        'transaction': transaction['merchant'],
                        'date': transaction.get('date', datetime.now()).strftime('%Y-%m-%d') if isinstance(transaction.get('date'), datetime) else str(transaction.get('date', '')),
                        'amount': amount,
                        'category': category,
                        'used_card': used_card.card.name if used_card and used_card.card else 'Unknown',
                        'savings_earned': round(savings_earned, 2),
                        'recommended_card': best_card.name,
                        'potential_savings': round(potential_savings, 2),
                        'missed_savings': round(missed_savings, 2),
                        'best_offer_pct': round(best_pct, 2)
                    })
        
        # Calculate card performance
        for user_card in user_cards:
            card_transactions = [t for t in transactions if used_card and used_card.id == user_card.id]
            if card_transactions:
                total = sum(float(t['amount']) for t in card_transactions)
                analysis['card_performance'][user_card.card.name if user_card.card else 'Unknown'] = {
                    'total_spent': total,
                    'transaction_count': len(card_transactions)
                }
        
        return analysis
    
    def save_transactions(self, user, transactions, card_id, file_path):
        """Save parsed transactions to database"""
        saved_count = 0
        user_card = None
        
        if card_id:
            try:
                user_card = UserCard.objects.get(user=user, card_id=card_id, is_active=True)
            except UserCard.DoesNotExist:
                pass
        
        for transaction_data in transactions:
            try:
                # Parse date
                transaction_date = transaction_data.get('date')
                if isinstance(transaction_date, str):
                    try:
                        transaction_date = datetime.strptime(transaction_date, '%Y-%m-%d').date()
                    except:
                        transaction_date = datetime.now().date()
                elif isinstance(transaction_date, datetime):
                    transaction_date = transaction_date.date()
                else:
                    transaction_date = datetime.now().date()
                
                # Calculate savings (% OFF) from Pakistani bank offers
                amount = float(transaction_data['amount'])
                category = transaction_data['category']
                
                savings_earned = 0.0
                if user_card and user_card.card:
                    best_pct = self._get_best_offer_percentage(user_card.card.id, category)
                    if best_pct > 0:
                        savings_earned = (amount * best_pct) / 100
                
                # Find best card (highest % OFF offer)
                best_card_id = None
                potential_savings = 0.0
                user_cards = UserCard.objects.filter(user=user, is_active=True).select_related('card', 'card__bank')
                best_pct = 0.0
                
                for uc in user_cards:
                    if uc.card:
                        card_pct = self._get_best_offer_percentage(uc.card.id, category)
                        if card_pct > best_pct:
                            best_pct = card_pct
                            best_card_id = uc.card.id
                
                if best_pct > 0:
                    potential_savings = (amount * best_pct) / 100
                
                missed_savings = potential_savings - savings_earned
                
                # Create or update transaction
                transaction, created = Transaction.objects.update_or_create(
                    user=user,
                    date=transaction_date,
                    merchant=transaction_data['merchant'],
                    amount=amount,
                    defaults={
                        'user_card': user_card,
                        'category': category,
                        'description': transaction_data.get('description', ''),
                        'reward_earned': savings_earned,  # Store as savings (% OFF) not rewards
                        'potential_reward': potential_savings,  # Store as potential savings
                        'recommended_card_id': best_card_id,
                        'missed_savings': missed_savings,
                        'statement_file': file_path
                    }
                )
                
                if created:
                    saved_count += 1
                    
            except Exception as e:
                print(f"Error saving transaction: {e}")
                continue
        
        return saved_count

class TransactionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Transaction.objects.filter(user=user).select_related('user_card__card__bank')
        
        # Filters
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        card_id = self.request.query_params.get('card_id')
        if card_id:
            queryset = queryset.filter(user_card__card_id=card_id)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(merchant__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size
        
        transactions = queryset[start:end]
        
        # Serialize transactions
        transaction_data = []
        for txn in transactions:
            transaction_data.append({
                'id': txn.id,
                'date': txn.date.isoformat(),
                'merchant': txn.merchant,
                'amount': float(txn.amount),
                'category': txn.category,
                'description': txn.description,
                'reward_earned': float(txn.reward_earned),
                'potential_reward': float(txn.potential_reward),
                'missed_savings': float(txn.missed_savings),
                'card': {
                    'id': txn.user_card.card.id if txn.user_card else None,
                    'name': txn.user_card.card.name if txn.user_card else 'Unknown',
                    'bank': txn.user_card.card.bank.name if txn.user_card and txn.user_card.card.bank else None,
                } if txn.user_card else None,
                'recommended_card_id': txn.recommended_card_id,
            })
        
        # Summary statistics
        total_spent = queryset.aggregate(Sum('amount'))['amount__sum'] or 0
        total_reward_earned = queryset.aggregate(Sum('reward_earned'))['reward_earned__sum'] or 0
        total_potential_reward = queryset.aggregate(Sum('potential_reward'))['potential_reward__sum'] or 0
        total_missed_savings = queryset.aggregate(Sum('missed_savings'))['missed_savings__sum'] or 0
        
        return Response({
            'transactions': transaction_data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': queryset.count(),
                'total_pages': (queryset.count() + page_size - 1) // page_size
            },
            'summary': {
                'total_spent': float(total_spent),
                'total_reward_earned': float(total_reward_earned),
                'total_potential_reward': float(total_potential_reward),
                'total_missed_savings': float(total_missed_savings),
            }
        })

class SavingsAnalysisView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get date range
        days = int(request.query_params.get('days', 30))
        start_date = datetime.now().date() - timedelta(days=days)
        
        # Get transactions
        transactions = Transaction.objects.filter(
            user=user,
            date__gte=start_date
        )
        
        # Calculate by category
        by_category = {}
        for category_code, category_name in Transaction.CATEGORIES:
            cat_txns = transactions.filter(category=category_code)
            total_spent = cat_txns.aggregate(Sum('amount'))['amount__sum'] or 0
            total_reward = cat_txns.aggregate(Sum('reward_earned'))['reward_earned__sum'] or 0
            total_potential = cat_txns.aggregate(Sum('potential_reward'))['potential_reward__sum'] or 0
            missed = cat_txns.aggregate(Sum('missed_savings'))['missed_savings__sum'] or 0
            
            if total_spent > 0:
                by_category[category_code] = {
                    'name': category_name,
                    'total_spent': float(total_spent),
                    'reward_earned': float(total_reward),
                    'potential_reward': float(total_potential),
                    'missed_savings': float(missed),
                    'transaction_count': cat_txns.count()
                }
        
        # Total calculations
        total_spent = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        total_reward_earned = transactions.aggregate(Sum('reward_earned'))['reward_earned__sum'] or 0
        total_potential_reward = transactions.aggregate(Sum('potential_reward'))['potential_reward__sum'] or 0
        total_missed_savings = transactions.aggregate(Sum('missed_savings'))['missed_savings__sum'] or 0
        
        # Project annual savings
        annual_savings = (total_missed_savings / days) * 365 if days > 0 else 0
        
        # Get top recommendations
        top_missed = transactions.filter(missed_savings__gt=0).order_by('-missed_savings')[:10]
        recommended_actions = []
        for txn in top_missed:
            if txn.recommended_card_id:
                try:
                    from cards.models import CreditCard
                    recommended_card = CreditCard.objects.get(id=txn.recommended_card_id)
                    recommended_actions.append({
                        'merchant': txn.merchant,
                        'amount': float(txn.amount),
                        'category': txn.category,
                        'recommended_card': recommended_card.name,
                        'missed_savings': float(txn.missed_savings),
                        'date': txn.date.isoformat()
                    })
                except:
                    pass
        
        return Response({
            'period_days': days,
            'total_spent': float(total_spent),
            'total_reward_earned': float(total_reward_earned),
            'total_potential_reward': float(total_potential_reward),
            'total_missed_savings': float(total_missed_savings),
            'projected_annual_savings': float(annual_savings),
            'by_category': by_category,
            'recommended_actions': recommended_actions[:5]  # Top 5
        })

class SpendingCategoriesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get date range
        days = int(request.query_params.get('days', 30))
        start_date = datetime.now().date() - timedelta(days=days)
        
        # Get transactions
        transactions = Transaction.objects.filter(
            user=user,
            date__gte=start_date
        )
        
        total_spent = transactions.aggregate(Sum('amount'))['amount__sum'] or 0
        
        categories = []
        for category_code, category_name in Transaction.CATEGORIES:
            cat_txns = transactions.filter(category=category_code)
            amount = cat_txns.aggregate(Sum('amount'))['amount__sum'] or 0
            
            if amount > 0:
                percentage = (float(amount) / float(total_spent) * 100) if total_spent > 0 else 0
                categories.append({
                    'code': category_code,
                    'name': category_name,
                    'amount': float(amount),
                    'percentage': round(percentage, 2),
                    'transaction_count': cat_txns.count()
                })
        
        # Sort by amount descending
        categories.sort(key=lambda x: x['amount'], reverse=True)
        
        return Response(categories)


class ExportTransactionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        format_type = request.query_params.get('format', 'csv')  # csv or json
        
        # Get filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        category = request.query_params.get('category')
        card_id = request.query_params.get('card_id')
        search = request.query_params.get('search')
        
        queryset = Transaction.objects.filter(user=user).select_related('user_card__card__bank')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if category:
            queryset = queryset.filter(category=category)
        if card_id:
            queryset = queryset.filter(user_card__card_id=card_id)
        if search:
            queryset = queryset.filter(
                Q(merchant__icontains=search) | Q(description__icontains=search)
            )
        
        transactions = queryset.order_by('-date')
        
        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="transactions_{datetime.now().strftime("%Y%m%d")}.csv"'
            
            writer = csv.writer(response)
            # Updated headers to reflect Pakistani banks (% OFF savings, not rewards)
            writer.writerow(['Date', 'Merchant', 'Amount (PKR)', 'Category', 'Card', 'Savings Earned (% OFF)', 'Potential Savings (% OFF)', 'Missed Savings (PKR)'])
            
            for txn in transactions:
                try:
                    # Safely get card name
                    card_name = 'Unknown'
                    if txn.user_card:
                        if hasattr(txn.user_card, 'card') and txn.user_card.card:
                            card_name = txn.user_card.card.name
                        elif hasattr(txn.user_card, 'card_details') and txn.user_card.card_details:
                            card_name = txn.user_card.card_details.get('name', 'Unknown')
                    
                    writer.writerow([
                        txn.date.isoformat(),
                        txn.merchant,
                        float(txn.amount),
                        txn.get_category_display(),
                        card_name,
                        float(txn.reward_earned),  # Stored as savings (% OFF)
                        float(txn.potential_reward),  # Stored as potential savings
                        float(txn.missed_savings)
                    ])
                except Exception as e:
                    logger.error(f"Error exporting transaction {txn.id}: {str(e)}")
                    continue
            
            return response
        
        else:  # JSON
            transaction_data = []
            for txn in transactions:
                try:
                    # Safely get card name
                    card_name = 'Unknown'
                    if txn.user_card:
                        if hasattr(txn.user_card, 'card') and txn.user_card.card:
                            card_name = txn.user_card.card.name
                        elif hasattr(txn.user_card, 'card_details') and txn.user_card.card_details:
                            card_name = txn.user_card.card_details.get('name', 'Unknown')
                    
                    transaction_data.append({
                        'date': txn.date.isoformat(),
                        'merchant': txn.merchant,
                        'amount': float(txn.amount),
                        'category': txn.category,
                        'category_name': txn.get_category_display(),
                        'card': card_name,
                        'savings_earned': float(txn.reward_earned),  # Renamed to reflect savings
                        'potential_savings': float(txn.potential_reward),  # Renamed to reflect savings
                        'missed_savings': float(txn.missed_savings),
                    })
                except Exception as e:
                    logger.error(f"Error exporting transaction {txn.id}: {str(e)}")
                    continue
            
            response = HttpResponse(
                json.dumps(transaction_data, indent=2),
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = f'attachment; filename="transactions_{datetime.now().strftime("%Y%m%d")}.json"'
            return response