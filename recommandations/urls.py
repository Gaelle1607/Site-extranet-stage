from django.urls import path
from . import views

app_name = 'recommandations'

urlpatterns = [
    path('', views.mes_recommandations, name='liste'),
    path('api/', views.api_recommandations, name='api'),
    path('api/complementaires/<int:produit_id>/', views.api_produits_complementaires, name='api_complementaires'),
]
