from django.urls import path
from . import views

app_name = 'recommandations'

urlpatterns = [
    path('', views.mes_recommandations, name='liste'),
    path('api/', views.api_recommandations, name='api'),
    path('api/favoris/', views.api_produits_favoris, name='api_favoris'),
]
