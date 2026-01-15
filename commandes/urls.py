from django.urls import path
from . import views

app_name = 'commandes'

urlpatterns = [
    path('panier/', views.voir_panier, name='panier'),
    path('panier/ajouter/', views.ajouter_au_panier, name='ajouter'),
    path('panier/modifier/', views.modifier_quantite, name='modifier'),
    path('panier/supprimer/', views.supprimer_du_panier, name='supprimer'),
    path('panier/vider/', views.vider_panier, name='vider'),
    path('valider/', views.valider_commande, name='valider'),
    path('confirmation/', views.confirmation_commande, name='confirmation'),
]
