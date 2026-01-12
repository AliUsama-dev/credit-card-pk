# backend/seed_data.py
import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from cards.models import Bank, CreditCard, CardRewardCategory
from offers.models import Merchant, Offer
from users.models import User
from django.contrib.auth.hashers import make_password

def create_superuser():
    """Create superuser if not exists"""
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@cardoptimizer.com',
            password='admin123',
            first_name='System',
            last_name='Admin',
            user_type='ADMIN',
            phone='03001234567',
            email_verified=True,
            is_premium=True
        )
        print("✅ Superuser created: admin / admin123")

def create_demo_users():
    """Create demo users"""
    demo_users = [
        {
            'username': 'demo',
            'email': 'demo@cardoptimizer.com',
            'password': 'demo123',
            'first_name': 'Demo',
            'last_name': 'User',
            'user_type': 'INDIVIDUAL',
            'phone': '03001234568',
            'email_verified': True,
        },
        {
            'username': 'ali',
            'email': 'ali@example.com',
            'password': 'ali123',
            'first_name': 'Ali',
            'last_name': 'Khan',
            'user_type': 'FAMILY_ADMIN',
            'phone': '03001234569',
            'email_verified': True,
            'is_premium': True,
        },
        {
            'username': 'sara',
            'email': 'sara@example.com',
            'password': 'sara123',
            'first_name': 'Sara',
            'last_name': 'Ahmed',
            'user_type': 'BUSINESS',
            'phone': '03001234570',
            'email_verified': True,
        },
    ]
    
    for user_data in demo_users:
        if not User.objects.filter(username=user_data['username']).exists():
            User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                user_type=user_data['user_type'],
                phone=user_data['phone'],
                email_verified=user_data['email_verified'],
                is_premium=user_data.get('is_premium', False)
            )
            print(f"✅ Demo user created: {user_data['username']} / {user_data['password']}")

def create_banks():
    """Create all Pakistani banks"""
    banks_data = [
        {
            'name': 'Habib Bank Limited',
            'code': 'HBL',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/hbl.png',
            'website': 'https://www.hbl.com',
            'support_email': 'customerservice@hbl.com',
            'support_phone': '111-111-111',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 1947,
            'total_branches': 1700,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'HBL ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'United Bank Limited',
            'code': 'UBL',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/ubl.png',
            'website': 'https://www.ubl.com.pk',
            'support_email': 'contactcentre@ubl.com.pk',
            'support_phone': '111-825-888',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 1959,
            'total_branches': 1380,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'UBL ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'MCB Bank',
            'code': 'MCB',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/mcb.png',
            'website': 'https://www.mcb.com.pk',
            'support_email': 'customersupport@mcb.com.pk',
            'support_phone': '111-000-622',
            'headquarters': 'Lahore, Pakistan',
            'established_year': 1947,
            'total_branches': 1450,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'MCB ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Bank Alfalah',
            'code': 'BAFL',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/alfalah.png',
            'website': 'https://www.bankalfalah.com',
            'support_email': 'customercare@bankalfalah.com',
            'support_phone': '111-225-243',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 1997,
            'total_branches': 700,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'Alfalah ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Meezan Bank',
            'code': 'MEZAN',
            'bank_type': 'ISLAMIC',
            'logo': '/media/bank_logos/meezan.png',
            'website': 'https://www.meezanbank.com',
            'support_email': 'info@meezanbank.com',
            'support_phone': '111-331-331',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 1997,
            'total_branches': 880,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'Meezan ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Standard Chartered Pakistan',
            'code': 'SCB',
            'bank_type': 'INTERNATIONAL',
            'logo': '/media/bank_logos/scb.png',
            'website': 'https://www.sc.com/pk',
            'support_email': 'customercare.pk@sc.com',
            'support_phone': '111-002-002',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 2006,
            'total_branches': 67,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'SCB ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Allied Bank',
            'code': 'ABL',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/abl.png',
            'website': 'https://www.abl.com',
            'support_email': 'info@abl.com',
            'support_phone': '111-225-225',
            'headquarters': 'Lahore, Pakistan',
            'established_year': 1942,
            'total_branches': 1400,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'ABL ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Askari Bank',
            'code': 'ASKARI',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/askari.png',
            'website': 'https://www.askaribank.com.pk',
            'support_email': 'info@askaribank.com.pk',
            'support_phone': '111-000-787',
            'headquarters': 'Rawalpindi, Pakistan',
            'established_year': 1991,
            'total_branches': 500,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'Askari ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Bank Islami',
            'code': 'BANKISLAMI',
            'bank_type': 'ISLAMIC',
            'logo': '/media/bank_logos/bankislami.png',
            'website': 'https://www.bankislami.com.pk',
            'support_email': 'customercare@bankislami.com.pk',
            'support_phone': '111-134-786',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 2005,
            'total_branches': 400,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'BankIslami ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Faysal Bank',
            'code': 'FBL',
            'bank_type': 'ISLAMIC',
            'logo': '/media/bank_logos/faysal.png',
            'website': 'https://www.faysalbank.com',
            'support_email': 'customercare@faysalbank.com',
            'support_phone': '111-000-111',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 1994,
            'total_branches': 400,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'Faysal ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'HabibMetro Bank',
            'code': 'HMB',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/habibmetro.png',
            'website': 'https://www.habibmetro.com',
            'support_email': 'customercare@habibmetro.com',
            'support_phone': '111-111-728',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 1992,
            'total_branches': 300,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'HabibMetro ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'JS Bank',
            'code': 'JSBL',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/jsbl.png',
            'website': 'https://www.jsbl.com',
            'support_email': 'info@jsbl.com',
            'support_phone': '111-111-572',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 2006,
            'total_branches': 323,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'JS Bank ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Silk Bank',
            'code': 'SBL',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/silkbank.png',
            'website': 'https://www.silkbank.com.pk',
            'support_email': 'customercare@silkbank.com.pk',
            'support_phone': '111-100-100',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 1994,
            'total_branches': 160,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'Silkbank ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Soneri Bank',
            'code': 'SBP',
            'bank_type': 'COMMERCIAL',
            'logo': '/media/bank_logos/soneri.png',
            'website': 'https://www.soneribank.com',
            'support_email': 'customercare@soneribank.com',
            'support_phone': '111-111-736',
            'headquarters': 'Lahore, Pakistan',
            'established_year': 1991,
            'total_branches': 360,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'Soneri ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Bank of Punjab',
            'code': 'BOP',
            'bank_type': 'GOVERNMENT',
            'logo': '/media/bank_logos/bop.png',
            'website': 'https://www.bop.com.pk',
            'support_email': 'customercare@bop.com.pk',
            'support_phone': '111-267-111',
            'headquarters': 'Lahore, Pakistan',
            'established_year': 1989,
            'total_branches': 780,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'BOP ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'Sindh Bank',
            'code': 'SINDH',
            'bank_type': 'GOVERNMENT',
            'logo': '/media/bank_logos/sindh.png',
            'website': 'https://www.sindhbank.com.pk',
            'support_email': 'info@sindhbank.com.pk',
            'support_phone': '111-111-773',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 2010,
            'total_branches': 300,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'Sindh Bank ATMs & 1-Link',
            'is_active': True,
        },
        {
            'name': 'National Bank of Pakistan',
            'code': 'NBP',
            'bank_type': 'GOVERNMENT',
            'logo': '/media/bank_logos/nbp.png',
            'website': 'https://www.nbp.com.pk',
            'support_email': 'customercare@nbp.com.pk',
            'support_phone': '111-627-627',
            'headquarters': 'Karachi, Pakistan',
            'established_year': 1949,
            'total_branches': 1500,
            'digital_banking': True,
            'mobile_app': True,
            'atm_network': 'NBP ATMs & 1-Link',
            'is_active': True,
        },
    ]
    
    banks = {}
    for bank_data in banks_data:
        bank, created = Bank.objects.get_or_create(
            code=bank_data['code'],
            defaults=bank_data
        )
        banks[bank.code] = bank
        print(f"✅ Bank created: {bank.name} ({bank.code})")
    
    return banks

def create_credit_cards(banks):
    """Create credit cards for each bank"""
    cards_data = {
        'HBL': [
            {
                'name': 'HBL Platinum Credit Card',
                'card_type': 'PLATINUM',
                'annual_fee': 5000,
                'interest_rate': 24.5,
                'credit_limit_min': 100000,
                'credit_limit_max': 500000,
                'reward_points_rate': 2.5,
                'cashback_rate': 1.5,
                'welcome_bonus': '10,000 Reward Points on first transaction',
                'requirements': 'Minimum salary Rs. 100,000',
                'features': 'Travel insurance, Lounge access, Discounts',
                'is_active': True,
                'scraping_url': 'https://www.hbl.com/credit-cards/platinum',
            },
            {
                'name': 'HBL Gold Credit Card',
                'card_type': 'GOLD',
                'annual_fee': 3000,
                'interest_rate': 25.5,
                'credit_limit_min': 50000,
                'credit_limit_max': 200000,
                'reward_points_rate': 2.0,
                'cashback_rate': 1.0,
                'welcome_bonus': '5,000 Reward Points',
                'requirements': 'Minimum salary Rs. 50,000',
                'features': 'Discounts on dining and shopping',
                'is_active': True,
            },
            {
                'name': 'HBL Signature Credit Card',
                'card_type': 'PREMIUM',
                'annual_fee': 10000,
                'interest_rate': 23.5,
                'credit_limit_min': 500000,
                'credit_limit_max': 2000000,
                'reward_points_rate': 3.0,
                'cashback_rate': 2.0,
                'welcome_bonus': '25,000 Reward Points',
                'requirements': 'Minimum salary Rs. 250,000',
                'features': 'Premium lounge access, Concierge service',
                'is_active': True,
            },
        ],
        'UBL': [
            {
                'name': 'UBL Wiz Credit Card',
                'card_type': 'CREDIT',
                'annual_fee': 0,
                'interest_rate': 26.0,
                'credit_limit_min': 30000,
                'credit_limit_max': 300000,
                'reward_points_rate': 1.5,
                'cashback_rate': 2.0,
                'welcome_bonus': 'Rs. 1,000 cashback on first transaction',
                'requirements': 'Minimum salary Rs. 30,000',
                'features': 'Zero annual fee, Cashback on all transactions',
                'is_active': True,
            },
            {
                'name': 'UBL Platinum Credit Card',
                'card_type': 'PLATINUM',
                'annual_fee': 4500,
                'interest_rate': 24.0,
                'credit_limit_min': 150000,
                'credit_limit_max': 1000000,
                'reward_points_rate': 2.5,
                'cashback_rate': 1.5,
                'welcome_bonus': '15,000 Reward Points',
                'requirements': 'Minimum salary Rs. 150,000',
                'features': 'Travel benefits, Insurance coverage',
                'is_active': True,
            },
        ],
        'MCB': [
            {
                'name': 'MCB Lite Digital Account',
                'card_type': 'DEBIT',
                'annual_fee': 0,
                'interest_rate': None,
                'credit_limit_min': None,
                'credit_limit_max': None,
                'reward_points_rate': 1.0,
                'cashback_rate': 0.5,
                'welcome_bonus': 'Free debit card',
                'requirements': 'No minimum balance',
                'features': 'Digital banking, Free transfers',
                'is_active': True,
            },
            {
                'name': 'MCB Platinum Credit Card',
                'card_type': 'PLATINUM',
                'annual_fee': 4000,
                'interest_rate': 24.5,
                'credit_limit_min': 100000,
                'credit_limit_max': 500000,
                'reward_points_rate': 2.0,
                'cashback_rate': 1.0,
                'welcome_bonus': '10,000 Reward Points',
                'requirements': 'Minimum salary Rs. 100,000',
                'features': 'Discounts on fuel and groceries',
                'is_active': True,
            },
        ],
        'BAFL': [
            {
                'name': 'Bank Alfalah Visa Signature Credit Card',
                'card_type': 'PREMIUM',
                'annual_fee': 8000,
                'interest_rate': 23.5,
                'credit_limit_min': 300000,
                'credit_limit_max': 1500000,
                'reward_points_rate': 3.0,
                'cashback_rate': 2.5,
                'welcome_bonus': '30,000 Reward Points',
                'requirements': 'Minimum salary Rs. 300,000',
                'features': 'Airport lounge access, Travel insurance',
                'is_active': True,
            },
            {
                'name': 'Bank Alfalah Platinum Credit Card',
                'card_type': 'PLATINUM',
                'annual_fee': 5000,
                'interest_rate': 24.5,
                'credit_limit_min': 100000,
                'credit_limit_max': 500000,
                'reward_points_rate': 2.0,
                'cashback_rate': 1.5,
                'welcome_bonus': '15,000 Reward Points',
                'requirements': 'Minimum salary Rs. 100,000',
                'features': 'Dining discounts, Shopping offers',
                'is_active': True,
            },
        ],
        'MEZAN': [
            {
                'name': 'Meezan Visa Gold Credit Card',
                'card_type': 'GOLD',
                'annual_fee': 3000,
                'interest_rate': None,
                'credit_limit_min': 50000,
                'credit_limit_max': 300000,
                'reward_points_rate': 1.5,
                'cashback_rate': 1.0,
                'welcome_bonus': 'Islamic banking benefits',
                'requirements': 'Shariah-compliant income',
                'features': 'Halal rewards, No interest',
                'is_active': True,
            },
            {
                'name': 'Meezan MasterCard Credit Card',
                'card_type': 'CREDIT',
                'annual_fee': 2000,
                'interest_rate': None,
                'credit_limit_min': 30000,
                'credit_limit_max': 200000,
                'reward_points_rate': 1.0,
                'cashback_rate': 0.5,
                'welcome_bonus': 'Free for first year',
                'requirements': 'Minimum salary Rs. 40,000',
                'features': 'Islamic banking, Halal transactions',
                'is_active': True,
            },
        ],
    }
    
    all_cards = []
    for bank_code, bank_cards in cards_data.items():
        if bank_code in banks:
            bank = banks[bank_code]
            for card_data in bank_cards:
                card, created = CreditCard.objects.get_or_create(
                    name=card_data['name'],
                    bank=bank,
                    defaults=card_data
                )
                all_cards.append(card)
                print(f"✅ Card created: {card.name} ({bank.name})")
    
    return all_cards

def create_reward_categories(cards):
    """Create reward categories for cards"""
    categories = [
        ('DINING', 5.0, 1000, 5000),
        ('GROCERIES', 3.0, 500, 3000),
        ('FUEL', 4.0, 1000, 4000),
        ('TRAVEL', 6.0, 5000, 10000),
        ('SHOPPING', 2.0, 1000, 2000),
        ('ELECTRONICS', 3.5, 5000, 8000),
    ]
    
    for card in cards:
        for category, rate, min_spend, max_reward in categories:
            if random.choice([True, False]):  # Randomly assign categories
                CardRewardCategory.objects.get_or_create(
                    card=card,
                    category=category,
                    defaults={
                        'reward_rate': rate + random.uniform(-1, 1),
                        'min_spend': min_spend,
                        'max_reward': max_reward,
                        'valid_from': timezone.now().date(),
                        'valid_to': timezone.now().date() + timedelta(days=365),
                    }
                )
    
    print("✅ Reward categories created")

def create_merchants():
    """Create merchants for offers"""
    merchants_data = [
        {'name': 'Foodpanda', 'merchant_type': 'RESTAURANT', 'city': 'KARACHI', 'website': 'https://www.foodpanda.pk'},
        {'name': 'Daraz', 'merchant_type': 'E_COMMERCE', 'city': 'KARACHI', 'website': 'https://www.daraz.pk'},
        {'name': 'Careem', 'merchant_type': 'TRAVEL', 'city': 'LAHORE', 'website': 'https://www.careem.com'},
        {'name': 'Shell', 'merchant_type': 'FUEL_STATION', 'city': 'ISLAMABAD', 'website': 'https://www.shell.com.pk'},
        {'name': 'Metro Cash & Carry', 'merchant_type': 'SUPERMARKET', 'city': 'KARACHI', 'website': 'https://www.metro.pk'},
        {'name': 'KFC', 'merchant_type': 'RESTAURANT', 'city': 'LAHORE', 'website': 'https://www.kfc.com.pk'},
        {'name': 'McDonald\'s', 'merchant_type': 'RESTAURANT', 'city': 'ISLAMABAD', 'website': 'https://www.mcdonalds.com.pk'},
        {'name': 'Pizza Hut', 'merchant_type': 'RESTAURANT', 'city': 'KARACHI', 'website': 'https://www.pizzahut.pk'},
        {'name': 'Emirates', 'merchant_type': 'TRAVEL', 'city': 'KARACHI', 'website': 'https://www.emirates.com'},
        {'name': 'Serena Hotels', 'merchant_type': 'HOTEL', 'city': 'ISLAMABAD', 'website': 'https://www.serenahotels.com'},
        {'name': 'Khaadi', 'merchant_type': 'FASHION', 'city': 'LAHORE', 'website': 'https://www.khaadi.com'},
        {'name': 'Gul Ahmed', 'merchant_type': 'FASHION', 'city': 'KARACHI', 'website': 'https://www.gulahmedshop.com'},
        {'name': 'Alkaram Studio', 'merchant_type': 'FASHION', 'city': 'KARACHI', 'website': 'https://www.alkaramstudio.com'},
        {'name': 'Imtiaz Super Market', 'merchant_type': 'SUPERMARKET', 'city': 'KARACHI', 'website': 'https://www.imtiazsupermarket.com'},
        {'name': 'Hyperstar', 'merchant_type': 'SUPERMARKET', 'city': 'LAHORE', 'website': 'https://www.hyperstar.pk'},
        {'name': 'PSO', 'merchant_type': 'FUEL_STATION', 'city': 'KARACHI', 'website': 'https://www.psopk.com'},
        {'name': 'Total Parco', 'merchant_type': 'FUEL_STATION', 'city': 'LAHORE', 'website': 'https://www.totalparco.com.pk'},
        {'name': 'Caltex', 'merchant_type': 'FUEL_STATION', 'city': 'ISLAMABAD', 'website': 'https://www.caltex.com/pk'},
        {'name': 'Nike', 'merchant_type': 'RETAIL', 'city': 'KARACHI', 'website': 'https://www.nike.com'},
        {'name': 'Samsung', 'merchant_type': 'ELECTRONICS', 'city': 'LAHORE', 'website': 'https://www.samsung.com/pk'},
        {'name': 'Apple', 'merchant_type': 'ELECTRONICS', 'city': 'ISLAMABAD', 'website': 'https://www.apple.com'},
        {'name': 'Pearl Continental', 'merchant_type': 'HOTEL', 'city': 'KARACHI', 'website': 'https://www.pchotels.com'},
        {'name': 'Air Blue', 'merchant_type': 'TRAVEL', 'city': 'KARACHI', 'website': 'https://www.airblue.com'},
        {'name': 'PIA', 'merchant_type': 'TRAVEL', 'city': 'KARACHI', 'website': 'https://www.piac.com.pk'},
        {'name': 'Netflix', 'merchant_type': 'ENTERTAINMENT', 'city': 'ALL_PAKISTAN', 'website': 'https://www.netflix.com'},
        {'name': 'Spotify', 'merchant_type': 'ENTERTAINMENT', 'city': 'ALL_PAKISTAN', 'website': 'https://www.spotify.com'},
        {'name': 'Uber', 'merchant_type': 'TRAVEL', 'city': 'KARACHI', 'website': 'https://www.uber.com'},
        {'name': 'Hardee\'s', 'merchant_type': 'RESTAURANT', 'city': 'LAHORE', 'website': 'https://www.hardees.com.pk'},
        {'name': 'Subway', 'merchant_type': 'RESTAURANT', 'city': 'ISLAMABAD', 'website': 'https://www.subway.com'},
        {'name': 'Domino\'s Pizza', 'merchant_type': 'RESTAURANT', 'city': 'KARACHI', 'website': 'https://www.dominos.pk'},
        {'name': 'Gloria Jeans', 'merchant_type': 'RESTAURANT', 'city': 'LAHORE', 'website': 'https://www.gjc.com.pk'},
        {'name': 'Naheed Super Market', 'merchant_type': 'SUPERMARKET', 'city': 'KARACHI', 'website': 'https://www.naheed.pk'},
        {'name': 'Chase Up', 'merchant_type': 'SUPERMARKET', 'city': 'LAHORE', 'website': 'https://www.chaseup.pk'},
        {'name': 'Al-Fatah', 'merchant_type': 'SUPERMARKET', 'city': 'LAHORE', 'website': 'https://www.alfatahmall.com'},
        {'name': 'Dolmen Mall', 'merchant_type': 'RETAIL', 'city': 'KARACHI', 'website': 'https://www.dolmen.com.pk'},
        {'name': 'Park Towers', 'merchant_type': 'RETAIL', 'city': 'KARACHI', 'website': 'https://www.parktowers.com.pk'},
        {'name': 'Centaurus Mall', 'merchant_type': 'RETAIL', 'city': 'ISLAMABAD', 'website': 'https://www.thecentaurusmall.com'},
        {'name': 'Emporium Mall', 'merchant_type': 'RETAIL', 'city': 'LAHORE', 'website': 'https://www.emporiummall.pk'},
        {'name': 'ChenOne', 'merchant_type': 'FASHION', 'city': 'LAHORE', 'website': 'https://www.chenone.com.pk'},
        {'name': 'J.', 'merchant_type': 'FASHION', 'city': 'KARACHI', 'website': 'https://www.junaidjamshed.com'},
        {'name': 'Service', 'merchant_type': 'RETAIL', 'city': 'LAHORE', 'website': 'https://www.service.com.pk'},
        {'name': 'Sapphire', 'merchant_type': 'FASHION', 'city': 'KARACHI', 'website': 'https://www.sapphireonline.pk'},
        {'name': 'Nishat Linen', 'merchant_type': 'FASHION', 'city': 'LAHORE', 'website': 'https://www.nishatlinen.com'},
    ]
    
    merchants = {}
    for merchant_data in merchants_data:
        merchant, created = Merchant.objects.get_or_create(
            name=merchant_data['name'],
            defaults={
                'merchant_type': merchant_data['merchant_type'],
                'city': merchant_data['city'],
                'website': merchant_data.get('website', ''),
                'is_active': True,
                'is_verified': True,
            }
        )
        merchants[merchant.name] = merchant
    
    print(f"✅ {len(merchants)} merchants created")
    return merchants

def create_offers(banks, merchants):
    """Create sample offers"""
    offers_data = [
        # HBL Offers
        {
            'bank': 'HBL',
            'title': 'HBL - 25% Discount on Foodpanda Orders',
            'description': 'Get 25% discount on all Foodpanda orders using HBL Credit Cards. Maximum discount Rs. 500 per order. Valid till month end.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Foodpanda',
            'discount_percentage': 25.0,
            'min_spend': 1000,
            'max_discount': 500,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=30),
            'city': 'ALL_PAKISTAN',
        },
        {
            'bank': 'HBL',
            'title': 'HBL Credit Card - 15% Cashback at Shell',
            'description': 'Get 15% cashback on fuel purchases at Shell stations. Minimum transaction Rs. 2000. Valid on weekends.',
            'offer_type': 'CASHBACK',
            'merchant': 'Shell',
            'discount_percentage': 15.0,
            'min_spend': 2000,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=45),
            'city': 'ALL_PAKISTAN',
        },
        {
            'bank': 'HBL',
            'title': 'HBL Debit Card - 10% Off at Metro',
            'description': 'Enjoy 10% discount on grocery shopping at all Metro stores. Valid on HBL debit cards only.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Metro Cash & Carry',
            'discount_percentage': 10.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=60),
            'city': 'KARACHI',
        },
        
        # UBL Offers
        {
            'bank': 'UBL',
            'title': 'UBL Wiz Card - 20% Off on Daraz Electronics',
            'description': 'Get 20% discount on electronics and home appliances on Daraz. Maximum discount Rs. 2000.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Daraz',
            'discount_percentage': 20.0,
            'max_discount': 2000,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=15),
            'city': 'ALL_PAKISTAN',
        },
        {
            'bank': 'UBL',
            'title': 'UBL - 30% Discount at Pizza Hut',
            'description': 'Enjoy 30% discount on dine-in and takeaway at Pizza Hut. Valid on all UBL cards.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Pizza Hut',
            'discount_percentage': 30.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=20),
            'city': 'LAHORE',
        },
        
        # MCB Offers
        {
            'bank': 'MCB',
            'title': 'MCB Lite - 15% Cashback on Careem Rides',
            'description': 'Get 15% cashback on all Careem rides in Karachi, Lahore & Islamabad. Maximum cashback Rs. 300 per ride.',
            'offer_type': 'CASHBACK',
            'merchant': 'Careem',
            'discount_percentage': 15.0,
            'max_discount': 300,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=25),
            'city': 'KARACHI',
        },
        {
            'bank': 'MCB',
            'title': 'MCB Platinum - Buy 1 Get 1 Free at KFC',
            'description': 'Buy 1 Get 1 Free on KFC buckets. Valid on MCB Platinum Credit Cards only.',
            'offer_type': 'DISCOUNT',
            'merchant': 'KFC',
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=10),
            'city': 'ISLAMABAD',
        },
        
        # Bank Alfalah Offers
        {
            'bank': 'BAFL',
            'title': 'Bank Alfalah - 40% Off at Nike Stores',
            'description': 'Get 40% discount on Nike products at all Nike stores. Valid on Bank Alfalah Visa Signature cards.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Nike',
            'discount_percentage': 40.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=30),
            'city': 'KARACHI',
        },
        {
            'bank': 'BAFL',
            'title': 'Alfalah Card - 25% Discount at McDonald\'s',
            'description': 'Enjoy 25% discount on all McDonald\'s orders. Minimum order Rs. 500.',
            'offer_type': 'DISCOUNT',
            'merchant': 'McDonald\'s',
            'discount_percentage': 25.0,
            'min_spend': 500,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=20),
            'city': 'LAHORE',
        },
        
        # Meezan Bank Offers
        {
            'bank': 'MEZAN',
            'title': 'Meezan Bank - 20% Off at Khaadi',
            'description': 'Get 20% discount on Khaadi products. Islamic banking offer.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Khaadi',
            'discount_percentage': 20.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=40),
            'city': 'LAHORE',
        },
        {
            'bank': 'MEZAN',
            'title': 'Meezan Card - 15% Cashback on Utility Bills',
            'description': 'Get 15% cashback on utility bill payments through Meezan Mobile App.',
            'offer_type': 'CASHBACK',
            'merchant': 'Various',
            'discount_percentage': 15.0,
            'max_discount': 1000,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=90),
            'city': 'ALL_PAKISTAN',
        },
        
        # Standard Chartered Offers
        {
            'bank': 'SCB',
            'title': 'Standard Chartered - Double Reward Points',
            'description': 'Earn double reward points on all online shopping transactions.',
            'offer_type': 'REWARD_MULTIPLIER',
            'merchant': 'Various',
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=60),
            'city': 'ALL_PAKISTAN',
        },
        {
            'bank': 'SCB',
            'title': 'SCB Platinum - 50% Off at Serena Hotels',
            'description': 'Get 50% discount on room bookings at Serena Hotels.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Serena Hotels',
            'discount_percentage': 50.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=45),
            'city': 'ISLAMABAD',
        },
        
        # Allied Bank Offers
        {
            'bank': 'ABL',
            'title': 'ABL Card - 30% Discount at Hardee\'s',
            'description': 'Enjoy 30% discount on all Hardee\'s burgers and meals.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Hardee\'s',
            'discount_percentage': 30.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=15),
            'city': 'KARACHI',
        },
        
        # Askari Bank Offers
        {
            'bank': 'ASKARI',
            'title': 'Askari Bank - 20% Off on Fuel at PSO',
            'description': 'Get 20% discount on fuel at PSO stations.',
            'offer_type': 'DISCOUNT',
            'merchant': 'PSO',
            'discount_percentage': 20.0,
            'min_spend': 3000,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=30),
            'city': 'LAHORE',
        },
        
        # Bank Islami Offers
        {
            'bank': 'BANKISLAMI',
            'title': 'Bank Islami - 15% Cashback on Groceries',
            'description': 'Get 15% cashback on grocery shopping. Halal banking offer.',
            'offer_type': 'CASHBACK',
            'merchant': 'Imtiaz Super Market',
            'discount_percentage': 15.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=25),
            'city': 'KARACHI',
        },
        
        # Faysal Bank Offers
        {
            'bank': 'FBL',
            'title': 'Faysal Bank - 25% Off at Subway',
            'description': 'Get 25% discount on all Subway sandwiches and meals.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Subway',
            'discount_percentage': 25.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=20),
            'city': 'ISLAMABAD',
        },
        
        # HabibMetro Offers
        {
            'bank': 'HMB',
            'title': 'HabibMetro - Buy 1 Get 1 Free at Domino\'s',
            'description': 'Buy 1 Get 1 Free on all Domino\'s pizzas.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Domino\'s Pizza',
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=10),
            'city': 'KARACHI',
        },
        
        # JS Bank Offers
        {
            'bank': 'JSBL',
            'title': 'JS Bank - 40% Off at Gloria Jeans',
            'description': 'Enjoy 40% discount on coffee and snacks at Gloria Jeans.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Gloria Jeans',
            'discount_percentage': 40.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=15),
            'city': 'LAHORE',
        },
        
        # Silk Bank Offers
        {
            'bank': 'SBL',
            'title': 'Silk Bank - 30% Cashback on Uber Rides',
            'description': 'Get 30% cashback on all Uber rides.',
            'offer_type': 'CASHBACK',
            'merchant': 'Uber',
            'discount_percentage': 30.0,
            'max_discount': 500,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=30),
            'city': 'KARACHI',
        },
        
        # Soneri Bank Offers
        {
            'bank': 'SBP',
            'title': 'Soneri Bank - 20% Off at Naheed Super Market',
            'description': 'Get 20% discount on groceries at Naheed Super Market.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Naheed Super Market',
            'discount_percentage': 20.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=25),
            'city': 'KARACHI',
        },
        
        # Bank of Punjab Offers
        {
            'bank': 'BOP',
            'title': 'BOP Card - 25% Discount at Total Parco',
            'description': 'Get 25% discount on fuel at Total Parco stations.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Total Parco',
            'discount_percentage': 25.0,
            'min_spend': 2500,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=40),
            'city': 'LAHORE',
        },
        
        # Sindh Bank Offers
        {
            'bank': 'SINDH',
            'title': 'Sindh Bank - 15% Off at Al-Fatah',
            'description': 'Enjoy 15% discount on shopping at Al-Fatah stores.',
            'offer_type': 'DISCOUNT',
            'merchant': 'Al-Fatah',
            'discount_percentage': 15.0,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=35),
            'city': 'LAHORE',
        },
        
        # NBP Offers
        {
            'bank': 'NBP',
            'title': 'NBP Debit Card - 10% Cashback on Bill Payments',
            'description': 'Get 10% cashback on utility bill payments through NBP Direct.',
            'offer_type': 'CASHBACK',
            'merchant': 'Various',
            'discount_percentage': 10.0,
            'max_discount': 500,
            'valid_from': timezone.now().date(),
            'valid_to': timezone.now().date() + timedelta(days=90),
            'city': 'ALL_PAKISTAN',
        },
    ]
    
    for offer_data in offers_data:
        if offer_data['bank'] in banks and offer_data['merchant'] in merchants:
            offer = Offer.objects.create(
                title=offer_data['title'],
                description=offer_data['description'],
                offer_type=offer_data['offer_type'],
                bank=banks[offer_data['bank']],
                merchant=merchants[offer_data['merchant']],
                discount_percentage=offer_data.get('discount_percentage'),
                min_spend=offer_data.get('min_spend'),
                max_discount=offer_data.get('max_discount'),
                valid_from=offer_data['valid_from'],
                valid_to=offer_data['valid_to'],
                is_active=True,
                scraping_source='https://www.' + offer_data['bank'].lower() + '.com/offers/',
            )
    
    print(f"✅ {len(offers_data)} offers created")

def main():
    """Main function to seed all data"""
    print("🚀 Starting database seeding...")
    
    # Create superuser
    create_superuser()
    
    # Create demo users
    create_demo_users()
    
    # Create banks
    banks = create_banks()
    
    # Create credit cards
    cards = create_credit_cards(banks)
    
    # Create reward categories
    create_reward_categories(cards)
    
    # Create merchants
    merchants = create_merchants()
    
    # Create offers
    create_offers(banks, merchants)
    
    print("\n🎉 Database seeding completed successfully!")
    print("\n📋 Summary:")
    print(f"   • Users: {User.objects.count()}")
    print(f"   • Banks: {Bank.objects.count()}")
    print(f"   • Credit Cards: {CreditCard.objects.count()}")
    print(f"   • Merchants: {Merchant.objects.count()}")
    print(f"   • Offers: {Offer.objects.count()}")
    print(f"   • Reward Categories: {CardRewardCategory.objects.count()}")
    
    print("\n🔑 Login Credentials:")
    print("   • Admin: admin / admin123")
    print("   • Demo User: demo / demo123")
    print("   • Premium User: ali / ali123")
    print("   • Business User: sara / sara123")
    
    print("\n🚀 Your application is ready to use!")

if __name__ == '__main__':
    main()