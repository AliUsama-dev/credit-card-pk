# cards/utils.py - Card Network Identification and Utilities
"""
Professional card network identification and utilities
According to SRS: Auto-identify card network (Visa, Mastercard, Amex, etc.)
"""

def identify_card_network(card_number: str) -> str:
    """
    Auto-identify card network from card number (BIN - Bank Identification Number)
    
    Based on ISO/IEC 7812 standard:
    - Visa: Starts with 4
    - Mastercard: Starts with 51-55 or 2221-2720
    - American Express: Starts with 34 or 37
    - UnionPay: Starts with 62
    - Discover: Starts with 6011, 622126-622925, 644-649, 65
    
    Args:
        card_number: Full card number or last 4 digits (for identification from last 4)
                    For full number, uses first 6 digits (BIN)
                    For last 4, uses pattern matching if available
    
    Returns:
        Network name: 'VISA', 'MASTERCARD', 'AMEX', 'UNIONPAY', 'DISCOVER', 'OTHER'
    """
    if not card_number:
        return 'OTHER'
    
    # Remove spaces and non-digits
    card_number = ''.join(filter(str.isdigit, card_number))
    
    if not card_number:
        return 'OTHER'
    
    # If we have full card number (at least 6 digits), use BIN
    if len(card_number) >= 6:
        first_digit = card_number[0]
        first_two = card_number[:2]
        first_four = card_number[:4]
        first_six = int(card_number[:6]) if len(card_number) >= 6 else 0
        
        # Visa: Starts with 4
        if first_digit == '4':
            return 'VISA'
        
        # Mastercard: 51-55 or 2221-2720
        if first_two in ['51', '52', '53', '54', '55']:
            return 'MASTERCARD'
        if 222100 <= first_six <= 272099:
            return 'MASTERCARD'
        
        # American Express: 34 or 37
        if first_two in ['34', '37']:
            return 'AMEX'
        
        # UnionPay: Starts with 62
        if first_two == '62':
            return 'UNIONPAY'
        
        # Discover: 6011, 622126-622925, 644-649, 65
        if first_four == '6011':
            return 'DISCOVER'
        if 622126 <= first_six <= 622925:
            return 'DISCOVER'
        if first_three := card_number[:3]:
            if 644 <= int(first_three) <= 649:
                return 'DISCOVER'
        if first_two == '65':
            return 'DISCOVER'
    
    # If only last 4 digits, try to infer from card template or return default
    # In real implementation, you might have a mapping of last 4 to network
    # For now, default to VISA (most common in Pakistan)
    if len(card_number) == 4:
        # Could check against known patterns, but for now default
        return 'VISA'  # Default for Pakistani cards
    
    return 'OTHER'


def validate_card_number(card_number: str) -> tuple[bool, str]:
    """
    Validate card number using Luhn algorithm
    
    Args:
        card_number: Card number to validate
    
    Returns:
        (is_valid, error_message)
    """
    if not card_number:
        return False, "Card number is required"
    
    # Remove spaces and non-digits
    digits = ''.join(filter(str.isdigit, card_number))
    
    if not digits:
        return False, "Card number must contain digits"
    
    # Luhn algorithm validation
    def luhn_check(card_num: str) -> bool:
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        return checksum % 10 == 0
    
    if not luhn_check(digits):
        return False, "Invalid card number (Luhn check failed)"
    
    # Check length
    network = identify_card_network(digits)
    if network == 'AMEX' and len(digits) != 15:
        return False, "American Express cards must be 15 digits"
    elif network in ['VISA', 'MASTERCARD', 'DISCOVER'] and len(digits) not in [13, 16, 19]:
        return False, f"{network} cards must be 13, 16, or 19 digits"
    
    return True, ""


def get_card_rewards_summary(card):
    """
    Get comprehensive rewards summary for a card
    
    Args:
        card: CreditCard instance
    
    Returns:
        dict with rewards information
    """
    from django.utils import timezone
    from .models import CardRewardCategory
    
    # Get active reward categories
    active_rewards = CardRewardCategory.objects.filter(
        card=card,
        valid_from__lte=timezone.now().date(),
        valid_to__gte=timezone.now().date()
    )
    
    rewards_summary = {
        'base_cashback': float(card.cashback_rate),
        'base_rewards': float(card.reward_points_rate),
        'categories': [],
        'annual_fee': float(card.annual_fee),
        'welcome_bonus': card.welcome_bonus,
        'features': card.features,
    }
    
    for reward in active_rewards:
        rewards_summary['categories'].append({
            'category': reward.category,
            'rate': float(reward.reward_rate),
            'min_spend': float(reward.min_spend),
            'max_reward': float(reward.max_reward) if reward.max_reward else None,
        })
    
    return rewards_summary

