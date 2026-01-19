from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('commandes/', views.liste_commande, name='liste_commande'),
    path('commandes/<int:commande_id>/', views.details_commande, name='details_commande'),
    path('catalogue/', views.catalogue_client, name='catalogue_client'),
    path('cadencier/<int:client_id>/', views.cadencier_client, name='cadencier_client'),
]
