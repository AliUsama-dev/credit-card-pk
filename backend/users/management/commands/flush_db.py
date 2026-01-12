# management/commands/flush_db.py
# Command to flush all database data (except superuser)

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Flush all database data except superuser accounts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-superusers',
            action='store_true',
            help='Keep superuser accounts',
        )

    def handle(self, *args, **options):
        keep_superusers = options.get('keep_superusers', True)
        
        self.stdout.write(self.style.WARNING('⚠️  This will delete ALL data from the database!'))
        
        if keep_superusers:
            self.stdout.write('Superuser accounts will be preserved.')
        
        # Get superuser emails before flush
        superuser_emails = []
        if keep_superusers:
            superuser_emails = list(User.objects.filter(is_superuser=True).values_list('email', flat=True))
            self.stdout.write(f'Found {len(superuser_emails)} superuser(s) to preserve.')
        
        # Flush database
        with transaction.atomic():
            # Delete all data except superusers
            from offers.models import Offer, Merchant, UserOffer
            from offers.models_peekaboo import PeekabooDeal, PeekabooCategory, PeekabooEntity
            from cards.models import UserCard, CardRewardCategory
            from transactions.models import Transaction, Statement
            from chatbot.models import ChatMessage
            
            # Delete in order to avoid foreign key constraints
            self.stdout.write('Deleting chat messages...')
            ChatMessage.objects.all().delete()
            
            self.stdout.write('Deleting transactions...')
            Transaction.objects.all().delete()
            Statement.objects.all().delete()
            
            self.stdout.write('Deleting user cards...')
            UserCard.objects.all().delete()
            CardRewardCategory.objects.all().delete()
            
            self.stdout.write('Deleting offers...')
            UserOffer.objects.all().delete()
            Offer.objects.all().delete()
            Merchant.objects.all().delete()
            
            self.stdout.write('Deleting Peekaboo data...')
            PeekabooDeal.objects.all().delete()
            PeekabooCategory.objects.all().delete()
            PeekabooEntity.objects.all().delete()
            
            # Delete users except superusers
            if keep_superusers:
                self.stdout.write('Deleting non-superuser accounts...')
                User.objects.filter(is_superuser=False).delete()
            else:
                self.stdout.write('Deleting all users...')
                User.objects.all().delete()
            
            # Note: Banks and CreditCards are preserved for card selection
            self.stdout.write('ℹ️  Banks and Credit Cards are preserved.')
            
            # Check if banks exist, if not, suggest seeding
            from cards.models import Bank
            bank_count = Bank.objects.count()
            if bank_count == 0:
                self.stdout.write(self.style.WARNING(
                    '\n⚠️  No banks found in database!'
                ))
                self.stdout.write(self.style.WARNING(
                    '   Run: python manage.py seed_pakistani_banks'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'✅ {bank_count} bank(s) preserved in database.'
                ))
        
        self.stdout.write(self.style.SUCCESS('✅ Database flushed successfully!'))
        
        if keep_superusers and superuser_emails:
            self.stdout.write(f'✅ Preserved {len(superuser_emails)} superuser account(s).')
            for email in superuser_emails:
                self.stdout.write(f'   - {email}')
        
        self.stdout.write(self.style.WARNING(
            '\n💡 Next step: Run "python manage.py seed_pakistani_banks" to populate banks and cards.'
        ))

