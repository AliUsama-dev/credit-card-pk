# management/commands/seed_pakistani_banks.py
# Seed all Pakistani banks and their credit/debit cards

from django.core.management.base import BaseCommand
from cards.models import Bank, CreditCard
from django.db import transaction

class Command(BaseCommand):
    help = 'Seed all Pakistani banks and their credit/debit cards'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Pakistani Banks Data
            banks_data = [
                {
                    'name': 'HBL (Habib Bank Limited)',
                    'code': 'HBL',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.hbl.com',
                    'support_email': 'info@hbl.com',
                    'support_phone': '111-111-425',
                    'headquarters': 'Karachi',
                    'established_year': 1941,
                    'cards': [
                        # Debit Cards
                        {'name': 'HBL PayPak Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'HBL Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'HBL USD Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'HBL Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'HBL World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'HBL World Elite Debit Card', 'card_type': 'DEBIT'},  # Match for "HBL World Elite DebitCard"
                        {'name': 'HBL Business Debit Card (Classic)', 'card_type': 'DEBIT'},
                        {'name': 'HBL Business Debit Card (World)', 'card_type': 'DEBIT'},
                        {'name': 'HBL World Business Debit Card', 'card_type': 'DEBIT'},  # Match for "HBL World Business DebitCard"
                        {'name': 'HBL Prestige World Elite Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'HBL Titanium Debit Card', 'card_type': 'DEBIT'},  # Match for "HBL Titanium DebitCard"
                        {'name': 'HBL Islamic Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'HBL ID Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'HBL NISA Debit Card', 'card_type': 'DEBIT'},
                        # Credit Cards
                        {'name': 'HBL Platinum Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'HBL Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'HBL Green Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'HBL Prestige Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Meezan Bank',
                    'code': 'MEEZAN',
                    'bank_type': 'ISLAMIC',
                    'website': 'https://www.meezanbank.com',
                    'support_email': 'info@meezanbank.com',
                    'support_phone': '111-331-331',
                    'headquarters': 'Karachi',
                    'established_year': 1997,
                    'cards': [
                        {'name': 'Meezan Visa Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Meezan Mastercard Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Meezan Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Meezan World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Meezan Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Meezan Business Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Meezan Visa Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Meezan Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Meezan Platinum Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'UBL (United Bank Limited)',
                    'code': 'UBL',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.ubl.com.pk',
                    'support_email': 'info@ubl.com.pk',
                    'support_phone': '111-825-888',
                    'headquarters': 'Karachi',
                    'established_year': 1959,
                    'cards': [
                        {'name': 'UBL Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'UBL Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'UBL World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'UBL Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'UBL Business Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'UBL Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'UBL Platinum Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'UBL Visa Signature Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'MCB Bank (Muslim Commercial Bank)',
                    'code': 'MCB',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.mcb.com.pk',
                    'support_email': 'info@mcb.com.pk',
                    'support_phone': '111-000-622',
                    'headquarters': 'Lahore',
                    'established_year': 1947,
                    'cards': [
                        {'name': 'MCB Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'MCB Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'MCB World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'MCB Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'MCB Business Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'MCB Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'MCB Platinum Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'MCB Visa Signature Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Bank Alfalah',
                    'code': 'ALFALAH',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.bankalfalah.com',
                    'support_email': 'info@bankalfalah.com',
                    'support_phone': '111-225-786',
                    'headquarters': 'Karachi',
                    'established_year': 1992,
                    'cards': [
                        {'name': 'Bank Alfalah Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank Alfalah Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank Alfalah World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank Alfalah Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank Alfalah Business Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank Alfalah Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Bank Alfalah Platinum Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Bank Alfalah Visa Signature Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Standard Chartered Bank',
                    'code': 'SCB',
                    'bank_type': 'INTERNATIONAL',
                    'website': 'https://www.sc.com/pk',
                    'support_email': 'info@sc.com',
                    'support_phone': '111-002-002',
                    'headquarters': 'Karachi',
                    'established_year': 2006,
                    'cards': [
                        {'name': 'Standard Chartered Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Standard Chartered Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Standard Chartered Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Standard Chartered Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Standard Chartered Platinum Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Standard Chartered Visa Infinite Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Allied Bank Limited',
                    'code': 'ABL',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.abl.com',
                    'support_email': 'info@abl.com',
                    'support_phone': '111-225-225',
                    'headquarters': 'Lahore',
                    'established_year': 1942,
                    'cards': [
                        {'name': 'Allied Bank Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Allied Bank Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Allied Bank World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Allied Bank Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Allied Bank Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Allied Bank Platinum Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Faysal Bank',
                    'code': 'FAYSAL',
                    'bank_type': 'ISLAMIC',
                    'website': 'https://www.faysalbank.com',
                    'support_email': 'info@faysalbank.com',
                    'support_phone': '111-111-111',
                    'headquarters': 'Karachi',
                    'established_year': 1994,
                    'cards': [
                        {'name': 'Faysal Bank Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Faysal Bank Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Faysal Bank World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Faysal Bank Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Faysal Bank Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Faysal Bank Platinum Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Askari Bank',
                    'code': 'ASKARI',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.askaribank.com.pk',
                    'support_email': 'info@askaribank.com.pk',
                    'support_phone': '111-225-225',
                    'headquarters': 'Rawalpindi',
                    'established_year': 1991,
                    'cards': [
                        {'name': 'Askari Bank Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Askari Bank Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Askari Bank World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Askari Bank Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Askari Bank Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Askari Bank Platinum Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Bank Islami',
                    'code': 'BANKISLAMI',
                    'bank_type': 'ISLAMIC',
                    'website': 'https://www.bankislami.com.pk',
                    'support_email': 'info@bankislami.com.pk',
                    'support_phone': '111-247-247',
                    'headquarters': 'Karachi',
                    'established_year': 2005,
                    'cards': [
                        {'name': 'Bank Islami Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank Islami Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank Islami World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank Islami Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank Islami Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Bank Islami Platinum Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'JS Bank',
                    'code': 'JSBANK',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.jsbl.com',
                    'support_email': 'info@jsbl.com',
                    'support_phone': '111-575-262',
                    'headquarters': 'Karachi',
                    'established_year': 2006,
                    'cards': [
                        {'name': 'JS Bank Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'JS Bank Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'JS Bank World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'JS Bank Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'JS Bank Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'JS Bank Platinum Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Bank of Punjab',
                    'code': 'BOP',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.bop.com.pk',
                    'support_email': 'info@bop.com.pk',
                    'support_phone': '111-267-267',
                    'headquarters': 'Lahore',
                    'established_year': 1989,
                    'cards': [
                        {'name': 'Bank of Punjab Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank of Punjab Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank of Punjab World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank of Punjab Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Bank of Punjab Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Bank of Punjab Platinum Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Soneri Bank',
                    'code': 'SONERI',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.soneribank.com',
                    'support_email': 'info@soneribank.com',
                    'support_phone': '111-766-374',
                    'headquarters': 'Karachi',
                    'established_year': 1991,
                    'cards': [
                        {'name': 'Soneri Bank Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Soneri Bank Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Soneri Bank World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Soneri Bank Platinum Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Soneri Bank Gold Credit Card', 'card_type': 'CREDIT'},
                        {'name': 'Soneri Bank Platinum Credit Card', 'card_type': 'CREDIT'},
                    ]
                },
                {
                    'name': 'Sindh Bank',
                    'code': 'SINDH',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.sindhbank.com.pk',
                    'support_email': 'info@sindhbank.com.pk',
                    'support_phone': '111-746-342',
                    'headquarters': 'Karachi',
                    'established_year': 2010,
                    'cards': [
                        {'name': 'Sindh Bank Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Sindh Bank Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Sindh Bank World Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'Sindh Bank Platinum Debit Card', 'card_type': 'DEBIT'},
                    ]
                },
                {
                    'name': 'First Women Bank',
                    'code': 'FWB',
                    'bank_type': 'COMMERCIAL',
                    'website': 'https://www.fwbl.com.pk',
                    'support_email': 'info@fwbl.com.pk',
                    'support_phone': '111-392-392',
                    'headquarters': 'Karachi',
                    'established_year': 1989,
                    'cards': [
                        {'name': 'First Women Bank Classic Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'First Women Bank Gold Debit Card', 'card_type': 'DEBIT'},
                        {'name': 'First Women Bank World Debit Card', 'card_type': 'DEBIT'},
                    ]
                },
            ]

            created_banks = 0
            created_cards = 0
            updated_banks = 0
            updated_cards = 0

            for bank_data in banks_data:
                cards = bank_data.pop('cards', [])
                
                # Create or update bank
                bank, bank_created = Bank.objects.update_or_create(
                    code=bank_data['code'],
                    defaults={
                        'name': bank_data['name'],
                        'bank_type': bank_data['bank_type'],
                        'website': bank_data['website'],
                        'support_email': bank_data['support_email'],
                        'support_phone': bank_data['support_phone'],
                        'headquarters': bank_data.get('headquarters', ''),
                        'established_year': bank_data.get('established_year'),
                        'is_active': True,
                    }
                )
                
                if bank_created:
                    created_banks += 1
                    self.stdout.write(self.style.SUCCESS(f'✅ Created bank: {bank.name}'))
                else:
                    updated_banks += 1
                    self.stdout.write(f'🔄 Updated bank: {bank.name}')

                # Create or update cards
                for card_data in cards:
                    card, card_created = CreditCard.objects.update_or_create(
                        bank=bank,
                        name=card_data['name'],
                        defaults={
                            'card_type': card_data['card_type'],
                            'is_active': True,
                        }
                    )
                    
                    if card_created:
                        created_cards += 1
                    else:
                        updated_cards += 1

            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Summary:\n'
                f'   Banks: {created_banks} created, {updated_banks} updated\n'
                f'   Cards: {created_cards} created, {updated_cards} updated\n'
                f'   Total Banks: {Bank.objects.count()}\n'
                f'   Total Cards: {CreditCard.objects.count()}'
            ))

