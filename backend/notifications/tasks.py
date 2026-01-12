# notifications/tasks.py
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Notification, NotificationPreference
from offers.models import Offer, PeekabooDeal
from planning.models import ScheduledPurchase
from cards.models import UserCard
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task
def send_expiring_offer_notifications():
    """Send notifications for offers expiring in next 3 days"""
    try:
        expiring_date = timezone.now().date() + timedelta(days=3)
        expiring_offers = Offer.objects.filter(
            is_active=True,
            valid_to__lte=expiring_date,
            valid_to__gte=timezone.now().date()
        )
        
        count = 0
        for offer in expiring_offers:
            # Get users with cards from this bank
            user_cards = UserCard.objects.filter(
                card__bank=offer.bank,
                is_active=True
            ).select_related('user', 'card')
            
            for user_card in user_cards:
                user = user_card.user
                # Check user preferences
                pref, _ = NotificationPreference.objects.get_or_create(user=user)
                
                if pref.in_app_expiring_offers:
                    Notification.objects.create(
                        user=user,
                        notification_type='EXPIRING_OFFER',
                        title=f'Offer Expiring Soon: {offer.title}',
                        message=f"The offer '{offer.title}' from {offer.bank.name} expires on {offer.valid_to.strftime('%B %d, %Y')}. Don't miss out!",
                        priority='HIGH',
                        related_offer=offer,
                        related_bank=offer.bank,
                        action_url=f'/offers/{offer.id}'
                    )
                    count += 1
        
        logger.info(f"Created {count} expiring offer notifications")
        return {'status': 'success', 'notifications_created': count}
    except Exception as e:
        logger.error(f"Error sending expiring offer notifications: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def send_scheduled_purchase_reminders():
    """Send reminders for scheduled purchases in next 24 hours"""
    try:
        tomorrow = timezone.now() + timedelta(days=1)
        upcoming_purchases = ScheduledPurchase.objects.filter(
            status='SCHEDULED',
            scheduled_date__lte=tomorrow,
            scheduled_date__gte=timezone.now(),
            reminder_sent=False
        )
        
        count = 0
        for purchase in upcoming_purchases:
            user = purchase.user
            pref, _ = NotificationPreference.objects.get_or_create(user=user)
            
            if pref.in_app_scheduled_reminders:
                card_info = ""
                if purchase.recommended_card:
                    card_info = f" Recommended card: {purchase.recommended_card.name}."
                
                Notification.objects.create(
                    user=user,
                    notification_type='SCHEDULED_REMINDER',
                    title=f'Upcoming Purchase: {purchase.get_purchase_type_display()}',
                    message=f"You have a scheduled {purchase.get_purchase_type_display().lower()} purchase on {purchase.scheduled_date.strftime('%B %d at %I:%M %p')}.{card_info}",
                    priority='MEDIUM',
                    related_card=purchase.recommended_card,
                    action_url=f'/planning/purchases/{purchase.id}'
                )
                purchase.reminder_sent = True
                purchase.save()
                count += 1
        
        logger.info(f"Created {count} scheduled purchase reminders")
        return {'status': 'success', 'reminders_created': count}
    except Exception as e:
        logger.error(f"Error sending scheduled purchase reminders: {str(e)}")
        return {'status': 'error', 'error': str(e)}


@shared_task
def send_new_offer_notifications():
    """Send notifications for new offers matching user's cards"""
    try:
        # Get offers created in last 24 hours
        yesterday = timezone.now() - timedelta(days=1)
        new_offers = Offer.objects.filter(
            is_active=True,
            created_at__gte=yesterday,
            valid_to__gte=timezone.now().date()
        )
        
        count = 0
        for offer in new_offers:
            # Get users with cards from this bank
            user_cards = UserCard.objects.filter(
                card__bank=offer.bank,
                is_active=True
            ).select_related('user', 'card')
            
            for user_card in user_cards:
                user = user_card.user
                pref, _ = NotificationPreference.objects.get_or_create(user=user)
                
                if pref.in_app_new_offers:
                    # Check if notification already exists
                    existing = Notification.objects.filter(
                        user=user,
                        notification_type='NEW_OFFER',
                        related_offer=offer
                    ).exists()
                    
                    if not existing:
                        Notification.objects.create(
                            user=user,
                            notification_type='NEW_OFFER',
                            title=f'New Offer Available: {offer.title}',
                            message=f"A new offer '{offer.title}' from {offer.bank.name} is now available! {offer.description[:100]}...",
                            priority='MEDIUM',
                            related_offer=offer,
                            related_bank=offer.bank,
                            action_url=f'/offers/{offer.id}'
                        )
                        count += 1
        
        logger.info(f"Created {count} new offer notifications")
        return {'status': 'success', 'notifications_created': count}
    except Exception as e:
        logger.error(f"Error sending new offer notifications: {str(e)}")
        return {'status': 'error', 'error': str(e)}

