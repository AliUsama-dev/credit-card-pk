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

class ScrapeTrinidadTobagoBankView(APIView):
    """Scrape credit cards for a Trinidad & Tobago bank"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        bank_code = request.data.get('bank_code')
        if not bank_code:
            return Response({
                'status': 'error',
                'error': 'bank_code is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from .tasks_trinidad_tobago import scrape_trinidad_tobago_bank
            
            # Run synchronously for now (can be made async with Celery if needed)
            result = scrape_trinidad_tobago_bank(bank_code)
            
            if result.get('error'):
                return Response({
                    'status': 'error',
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                'status': 'success',
                'created': result.get('created', 0),
                'updated': result.get('updated', 0),
                'total': result.get('total', 0),
                'bank': result.get('bank', ''),
            })
        except Exception as e:
            logger.error(f"Error scraping Trinidad & Tobago bank {bank_code}: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)