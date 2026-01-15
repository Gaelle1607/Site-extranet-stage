"""
URL configuration for extranet project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('clients.urls')),
    path('catalogue/', include('catalogue.urls')),
    path('commandes/', include('commandes.urls')),
    path('recommandations/', include('recommandations.urls')),
]
