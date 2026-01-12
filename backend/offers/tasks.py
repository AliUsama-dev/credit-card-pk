# offers/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Offer
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_expired_offers():
    """Deactivate expired offers"""
    try:
        today = timezone.now().date()
        expired_offers = Offer.objects.filter(
            valid_to__lt=today,
            is_active=True
        )
        
        count = expired_offers.update(is_active=False)
        
        if count > 0:
            logger.info(f"Deactivated {count} expired offers")
        
        return {'status': 'success', 'expired_deactivated': count}
    except Exception as e:
        logger.error(f"Error updating expired offers: {str(e)}")
        return {'status': 'error', 'error': str(e)}