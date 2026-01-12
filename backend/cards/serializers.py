from rest_framework import serializers
from django.utils import timezone
from datetime import datetime, date
from .models import Bank, CreditCard, CardRewardCategory, UserCard

class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bank
        fields = '__all__'

class CardRewardCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CardRewardCategory
        fields = '__all__'

class CreditCardSerializer(serializers.ModelSerializer):
    bank = BankSerializer(read_only=True)
    reward_categories = CardRewardCategorySerializer(many=True, read_only=True)
    
    class Meta:
        model = CreditCard
        fields = '__all__'

class UserCardSerializer(serializers.ModelSerializer):
    card_details = CreditCardSerializer(source='card', read_only=True)
    card_network_display = serializers.CharField(source='get_card_network_display', read_only=True)
    # Override expiry_date to accept string input (MM/YY format)
    expiry_date = serializers.CharField(required=True, allow_blank=False)
    
    class Meta:
        model = UserCard
        fields = '__all__'
        read_only_fields = ('user', 'linked_at', 'card_network_display')
    
    def validate_card_number_last4(self, value):
        """Validate last 4 digits"""
        if not value or len(value) != 4:
            raise serializers.ValidationError("Last 4 digits must be exactly 4 digits")
        if not value.isdigit():
            raise serializers.ValidationError("Last 4 digits must be numbers only")
        return value
    
    def validate_expiry_date(self, value):
        """Validate and convert expiry date from MM/YY format to YYYY-MM-DD"""
        if not value:
            raise serializers.ValidationError("Expiry date is required")
        
        # Strip whitespace
        value = value.strip()
        
        # If value is already a date object, validate it
        if isinstance(value, date):
            if value < timezone.now().date():
                raise serializers.ValidationError("Expiry date must be in the future")
            return value
        
        # If value is a string, try to parse MM/YY format
        if isinstance(value, str):
            # Try MM/YY format (e.g., "12/25" or "12/89")
            if '/' in value:
                try:
                    parts = value.split('/')
                    if len(parts) != 2:
                        raise serializers.ValidationError("Invalid date format. Use MM/YY format (e.g., 12/25)")
                    
                    month = int(parts[0].strip())
                    year = int(parts[1].strip())
                    
                    # Validate month
                    if month < 1 or month > 12:
                        raise serializers.ValidationError("Month must be between 01 and 12")
                    
                    # Convert 2-digit year to 4-digit (assume 20xx for years 00-99)
                    if year < 100:
                        year = 2000 + year
                    
                    # Validate year is reasonable (not too far in the past)
                    current_year = timezone.now().year
                    if year < current_year - 10:
                        raise serializers.ValidationError(f"Year {year} seems too far in the past. Please check your entry.")
                    # Allow up to 100 years in the future (to handle edge cases like 12/89 = 2089)
                    if year > current_year + 100:
                        raise serializers.ValidationError(f"Year {year} seems too far in the future. Please check your entry.")
                    
                    # Create date object (using last day of month)
                    from calendar import monthrange
                    last_day = monthrange(year, month)[1]
                    expiry_date = date(year, month, last_day)
                    
                    # Validate it's in the future
                    if expiry_date < timezone.now().date():
                        raise serializers.ValidationError("Expiry date must be in the future")
                    
                    return expiry_date
                except ValueError as e:
                    raise serializers.ValidationError(f"Invalid date format. Use MM/YY format (e.g., 12/25). Error: {str(e)}")
            
            # Try YYYY-MM-DD format
            if '-' in value:
                try:
                    expiry_date = datetime.strptime(value, '%Y-%m-%d').date()
                    if expiry_date < timezone.now().date():
                        raise serializers.ValidationError("Expiry date must be in the future")
                    return expiry_date
                except ValueError:
                    raise serializers.ValidationError("Invalid date format. Use MM/YY format (e.g., 12/25) or YYYY-MM-DD format")
            
            # If no slash or dash, it's invalid
            raise serializers.ValidationError("Invalid date format. Use MM/YY format (e.g., 12/25)")
        
        raise serializers.ValidationError("Expiry date must be a string in MM/YY format (e.g., 12/25)")