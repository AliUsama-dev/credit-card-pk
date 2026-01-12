from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/cards/', include('cards.urls')),
    path('api/transactions/', include('transactions.urls')),
    path('api/offers/', include('offers.urls')),
    path('api/chatbot/', include('chatbot.urls')),
    path('api/scraping/', include('scraping.urls')),
    path('api/admin-panel/', include('admin_panel.urls')),
    path('api/planning/', include('planning.urls')),
    path('api/notifications/', include('notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)