# scraping/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from celery.result import AsyncResult
from .tasks import scrape_verified_banks
from cards.models import Bank
from admin_panel.models import ScrapingLog
import logging

logger = logging.getLogger(__name__)

class ScrapeBankOffersView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, bank_id):
        try:
            bank = Bank.objects.get(id=bank_id)
            
            # Create scraping log
            log = ScrapingLog.objects.create(
                bank=bank,
                status='RUNNING',
                offers_found=0,
                offers_created=0,
                offers_updated=0,
            )
            
            # Trigger scraping task
            task = scrape_verified_banks.delay()
            
            return Response({
                'status': 'success',
                'message': f'Scraping started for {bank.name}',
                'task_id': task.id,
                'bank': {'id': bank.id, 'name': bank.name, 'code': bank.code}
            })
            
        except Bank.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Bank not found'
            }, status=status.HTTP_404_NOT_FOUND)

class ScrapingStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        task_id = request.query_params.get('task_id')
        if task_id:
            try:
                task_result = AsyncResult(task_id)
                return Response({
                    'task_id': task_id,
                    'status': task_result.status,
                    'result': task_result.result if task_result.ready() else None
                })
            except Exception as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'status': 'no_task_id',
            'message': 'Provide task_id parameter'
        })

class TriggerManualScrapingView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        # Trigger full scraping
        task = scrape_verified_banks.delay()
        
        return Response({
            'status': 'success',
            'message': 'Scraping initiated for all verified banks',
            'task_id': task.id
        })

class ScrapingLogsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    
    def get(self, request):
        logs = (
            ScrapingLog.objects.select_related("bank")
            .order_by("-started_at")[:50]
        )
        data = []
        for log in logs:
            data.append(
                {
                    "id": log.id,
                    "bank": {"id": log.bank_id, "name": log.bank.name, "code": log.bank.code} if log.bank else None,
                    "task_id": log.task_id,
                    "status": log.status,
                    "offers_found": log.offers_found,
                    "offers_created": log.offers_created,
                    "offers_updated": log.offers_updated,
                    "error_message": log.error_message,
                    "started_at": log.started_at,
                    "completed_at": log.completed_at,
                    "duration_seconds": log.duration_seconds,
                }
            )
        return Response({"logs": data})

class ScrapePeekabooBankView(APIView):
    """Admin-only endpoint to manually scrape Peekaboo deals for a selected bank"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        bank_id = request.data.get('bank_id')
        city = request.data.get('city', 'LAHORE')
        card_id = request.data.get('card_id')  # Optional
        
        if not bank_id:
            return Response({
                'status': 'error',
                'error': 'bank_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            bank = Bank.objects.get(id=bank_id)
            
            # Import Peekaboo scraping functions
            from .tasks_peekaboo import scrape_peekaboo_deals_by_bank, scrape_peekaboo_entities_by_card
            from cards.models import CreditCard
            
            # If card_id provided, scrape for that specific card
            if card_id:
                try:
                    card = CreditCard.objects.get(id=card_id, bank=bank)
                    # Scrape entities first
                    entities_result = scrape_peekaboo_entities_by_card(
                        bank_code=bank.code,
                        card_id=card_id,
                        city_name=city.upper(),
                        limit=100,
                        offset=0
                    )
                    # Then scrape deals
                    result = scrape_peekaboo_deals_by_bank(
                        bank.code,
                        city.upper(),
                        card_id=card_id
                    )
                except CreditCard.DoesNotExist:
                    return Response({
                        'status': 'error',
                        'error': f'Card {card_id} not found for bank {bank.name}'
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # Scrape all deals for the bank
                result = scrape_peekaboo_deals_by_bank(
                    bank.code,
                    city.upper()
                )
            
            # Handle result
            if isinstance(result, dict):
                created = result.get('created', 0)
                updated = result.get('updated', 0)
                skipped = result.get('skipped', 0)
            elif isinstance(result, tuple) and len(result) == 3:
                created, updated, skipped = result
            else:
                created, updated, skipped = 0, 0, 0
            
            return Response({
                'status': 'success',
                'message': f'Scraping completed for {bank.name}',
                'bank': {'id': bank.id, 'name': bank.name, 'code': bank.code},
                'created': created,
                'updated': updated,
                'skipped': skipped,
                'city': city.upper()
            })
            
        except Bank.DoesNotExist:
            return Response({
                'status': 'error',
                'error': 'Bank not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error scraping Peekaboo deals: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ScrapeAllPeekabooBanksView(APIView):
    """Admin-only endpoint to scrape Peekaboo deals for ALL banks (async)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        city = request.data.get('city', 'LAHORE')
        
        try:
            # Import async task
            from .tasks_peekaboo import scrape_all_banks_card_deals_async
            
            # Trigger async task (returns immediately)
            task = scrape_all_banks_card_deals_async.delay(city.upper())
            
            logger.info(f"🚀 Started async scraping task {task.id} for all banks in {city}")
            
            return Response({
                'status': 'success',
                'message': f'Scraping started in background for all banks in {city}',
                'task_id': task.id,
                'city': city.upper(),
                'note': 'This will run in the background. Check Celery logs for progress.'
            })
            
        except Exception as e:
            logger.error(f"Error starting async scraping: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScrapePeekabooCategoriesView(APIView):
    """Admin-only endpoint to scrape Peekaboo categories (needed for category-based recommendations)."""
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        try:
            from .tasks_peekaboo import scrape_peekaboo_categories

            # Run async if available (Celery task), else run directly
            try:
                task = scrape_peekaboo_categories.delay()
                return Response({
                    'status': 'success',
                    'message': 'Peekaboo categories scraping started in background',
                    'task_id': task.id,
                })
            except Exception:
                # Fallback to direct run
                count = scrape_peekaboo_categories()
                return Response({
                    'status': 'success',
                    'message': 'Peekaboo categories scraping completed',
                    'categories_processed': count,
                })
        except Exception as e:
            logger.error(f"Error scraping Peekaboo categories: {str(e)}", exc_info=True)
            return Response({'status': 'error', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)