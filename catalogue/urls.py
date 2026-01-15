from django.urls import path
from . import views

app_name = 'catalogue'

urlpatterns = [
    path('', views.liste_produits, name='liste'),
    path('produit/<str:reference>/', views.detail_produit, name='detail'),
    path('favoris/', views.favoris, name='favoris'),
]
