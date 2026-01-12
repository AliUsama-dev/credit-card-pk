# backend/context_processors.py
def media_urls(request):
    from django.conf import settings
    return {
        'MEDIA_URL': settings.MEDIA_URL,
        'STATIC_URL': settings.STATIC_URL,
    }