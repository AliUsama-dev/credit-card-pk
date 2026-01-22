from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core.validators import EmailValidator, RegexValidator
from django.core.exceptions import ValidationError
import re
from .models import User, Family, Business

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                  'user_type', 'phone', 'profile_image', 'is_premium', 'is_staff', 'is_superuser')
        read_only_fields = ('id',)
    
    def validate_email(self, value):
        """Professional email validation"""
        if not value:
            raise serializers.ValidationError("Email is required.")
        
        # Use Django's built-in email validator
        email_validator = EmailValidator(message="Please enter a valid email address.")
        try:
            email_validator(value)
        except ValidationError:
            raise serializers.ValidationError("Please enter a valid email address.")
        
        # Check for common email patterns
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Please enter a valid email address.")
        
        # Check if email already exists (for updates)
        if self.instance:
            if User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
                raise serializers.ValidationError("This email is already registered.")
        else:
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already registered.")
        
        return value.lower().strip()
    
    def validate_phone(self, value):
        """Professional phone validation (supports international formats)"""
        if not value:
            return value  # Phone is optional
        
        # Remove common separators
        phone_clean = re.sub(r'[\s\-\(\)\+]', '', value)
        
        # Check if it's all digits
        if not phone_clean.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits and common separators (+, -, spaces, parentheses).")
        
        # Check length (minimum 10 digits, maximum 15 for international)
        if len(phone_clean) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits.")
        if len(phone_clean) > 15:
            raise serializers.ValidationError("Phone number cannot exceed 15 digits.")
        
        return value.strip()
    
    def validate_first_name(self, value):
        """Validate first name"""
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("First name must be at least 2 characters.")
            if len(value) > 50:
                raise serializers.ValidationError("First name cannot exceed 50 characters.")
            if not re.match(r'^[a-zA-Z\s\-\']+$', value):
                raise serializers.ValidationError("First name can only contain letters, spaces, hyphens, and apostrophes.")
        return value
    
    def validate_last_name(self, value):
        """Validate last name"""
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError("Last name must be at least 2 characters.")
            if len(value) > 50:
                raise serializers.ValidationError("Last name cannot exceed 50 characters.")
            if not re.match(r'^[a-zA-Z\s\-\']+$', value):
                raise serializers.ValidationError("Last name can only contain letters, spaces, hyphens, and apostrophes.")
        return value

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        style={'input_type': 'password'},
        help_text="Password must be at least 8 characters long and contain both letters and numbers."
    )
    confirm_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Please confirm your password."
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 'first_name', 
                  'last_name', 'user_type', 'phone')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_username(self, value):
        """Validate username"""
        if not value:
            raise serializers.ValidationError("Username is required.")
        
        value = value.strip().lower()
        
        if len(value) < 3:
            raise serializers.ValidationError("Username must be at least 3 characters long.")
        if len(value) > 30:
            raise serializers.ValidationError("Username cannot exceed 30 characters.")
        if not re.match(r'^[a-z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain lowercase letters, numbers, and underscores.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        
        return value
    
    def validate_email(self, value):
        """Professional email validation"""
        if not value:
            raise serializers.ValidationError("Email is required.")
        
        email_validator = EmailValidator(message="Please enter a valid email address.")
        try:
            email_validator(value)
        except ValidationError:
            raise serializers.ValidationError("Please enter a valid email address.")
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise serializers.ValidationError("Please enter a valid email address.")
        
        if User.objects.filter(email=value.lower().strip()).exists():
            raise serializers.ValidationError("This email is already registered.")
        
        return value.lower().strip()
    
    def validate_password(self, value):
        """Professional password validation"""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if len(value) > 128:
            raise serializers.ValidationError("Password cannot exceed 128 characters.")
        if not re.search(r'[a-zA-Z]', value):
            raise serializers.ValidationError("Password must contain at least one letter.")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        return value
    
    def validate_phone(self, value):
        """Professional phone validation"""
        if not value:
            return value  # Phone is optional
        
        phone_clean = re.sub(r'[\s\-\(\)\+]', '', value)
        
        if not phone_clean.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits and common separators.")
        
        if len(phone_clean) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits.")
        if len(phone_clean) > 15:
            raise serializers.ValidationError("Phone number cannot exceed 15 digits.")
        
        return value.strip()
    
    def validate_first_name(self, value):
        """Validate first name"""
        if not value:
            raise serializers.ValidationError("First name is required.")
        
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters.")
        if len(value) > 50:
            raise serializers.ValidationError("First name cannot exceed 50 characters.")
        if not re.match(r'^[a-zA-Z\s\-\']+$', value):
            raise serializers.ValidationError("First name can only contain letters, spaces, hyphens, and apostrophes.")
        
        return value
    
    def validate_last_name(self, value):
        """Validate last name"""
        if not value:
            raise serializers.ValidationError("Last name is required.")
        
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters.")
        if len(value) > 50:
            raise serializers.ValidationError("Last name cannot exceed 50 characters.")
        if not re.match(r'^[a-zA-Z\s\-\']+$', value):
            raise serializers.ValidationError("Last name can only contain letters, spaces, hyphens, and apostrophes.")
        
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'confirm_password': "Passwords do not match."
            })
        return data
    
    def create(self, validated_data):
        """Create user with validated data"""
        validated_data.pop('confirm_password', None)  # Remove confirm_password before creating user
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_type=validated_data.get('user_type', 'INDIVIDUAL'),
            phone=validated_data.get('phone', '')
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        required=True,
        help_text="Enter your username or email address."
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        help_text="Enter your password."
    )
    
    def validate_username(self, value):
        """Validate username field"""
        if not value or not value.strip():
            raise serializers.ValidationError("Username or email is required.")
        return value.strip()
    
    def validate_password(self, value):
        """Validate password field"""
        if not value:
            raise serializers.ValidationError("Password is required.")
        return value
    
    def validate(self, data):
        """Authenticate user"""
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            raise serializers.ValidationError("Both username and password are required.")
        
        # Try to authenticate with username
        user = authenticate(username=username, password=password)
        
        # If authentication fails, try with email
        if not user:
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if not user:
            raise serializers.ValidationError("Invalid username/email or password.")
        
        if not user.is_active:
            raise serializers.ValidationError("Your account has been deactivated. Please contact support.")
        
        return user