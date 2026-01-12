# admin_panel/models.py
from django.db import models

class ScrapingLog(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('RUNNING', 'Running'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    # Bank is optional for "global/all-banks" runs
    bank = models.ForeignKey('cards.Bank', on_delete=models.CASCADE, null=True, blank=True)
    # Celery task id (optional for synchronous runs / eager mode)
    task_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    offers_found = models.IntegerField(default=0)
    offers_created = models.IntegerField(default=0)
    offers_updated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'scraping_logs'
        ordering = ['-started_at']

class SystemConfig(models.Model):
    key = models.CharField(max_length=255, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'system_configs'