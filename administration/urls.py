from django.urls import path
from . import views

app_name = 'administration'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('commandes/', views.liste_commande, name='liste_commande'),
    path('commandes/<int:commande_id>/', views.details_commande, name='details_commande'),
    path('commandes/<int:commande_id>/supprimer/', views.supprimer_commande, name='supprimer_commande'),
    path('utilisateurs/', views.catalogue_utilisateurs, name='catalogue_utilisateur'),
    path('clients/', views.catalogue_clients, name='catalogue_clients'),
    path('cadencier/<int:client_id>/', views.cadencier_client, name='cadencier_client'),
    path('inscription/',views.inscription, name='inscription'),
    path('api/recherche-clients/', views.recherche_clients_api, name='recherche_clients_api'),
]
