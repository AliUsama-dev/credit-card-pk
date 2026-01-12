from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    USER_TYPES = [
        ('INDIVIDUAL', 'Individual'),
        ('FAMILY_ADMIN', 'Family Admin'),
        ('FAMILY_MEMBER', 'Family Member'),
        ('BUSINESS', 'Business'),
        ('ADMIN', 'Admin'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='INDIVIDUAL')
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    email_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'

class Family(models.Model):
    name = models.CharField(max_length=255)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='family_admin')
    members = models.ManyToManyField(User, related_name='families')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'families'

class Business(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='businesses')
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=100, blank=True, null=True)
    employees = models.ManyToManyField(User, related_name='business_employments')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'businesses'