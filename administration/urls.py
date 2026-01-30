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
    path('cadencier/<int:code_tiers>/', views.cadencier_client, name='cadencier_client'),
    path('information/<int:utilisateur_id>/', views.information_utilisateur, name='information_utilisateur'),
    path('information/<int:utilisateur_id>/mot-de-passe/', views.changer_mot_de_passe, name='changer_mot_de_passe'),
    path('information/<int:utilisateur_id>/commandes/', views.commande_utilisateur, name='commande_utilisateur'),
    path('inscription/',views.inscription, name='inscription'),
    path('api/recherche-clients/', views.recherche_clients_api, name='recherche_clients_api'),
    path('profil/', views.profil_admin, name='profil_admin'),
    path('profil/mot-de-passe/', views.changer_mot_de_passe_admin, name='changer_mot_de_passe_admin'),
    path('reset-password/', views.reset_password_admin, name='reset_password_admin'),
]
