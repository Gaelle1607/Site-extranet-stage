"""
=============================================================================
URLS.PY - Routes de l'application Catalogue
=============================================================================

Ce fichier définit les URLs pour la consultation du catalogue produits
côté client (utilisateurs connectés).

Routes disponibles :
    /catalogue/                     -> Liste des produits disponibles
    /catalogue/produit/<reference>/ -> Détail d'un produit
    /catalogue/favoris/             -> Produits les plus commandés
    /catalogue/mentions-legales/    -> Page des mentions légales
    /catalogue/commander/           -> Formulaire de commande

Préfixe : /catalogue/ (défini dans extranet/urls.py)

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.urls import path
from . import views

# Namespace pour les URLs de cette application
# Usage dans les templates : {% url 'catalogue:liste' %}
app_name = 'catalogue'

urlpatterns = [
    # Liste des produits disponibles pour le client connecté
    # Inclut les filtres et la recherche
    path('', views.liste_produits, name='liste'),

    # Détail d'un produit spécifique
    # <str:reference> = code produit (ex: "PORC001")
    path('produit/<str:reference>/', views.detail_produit, name='detail'),

    # Page des produits favoris (les plus commandés par le client)
    path('favoris/', views.favoris, name='favoris'),

    # Page des mentions légales (accessible sans connexion)
    path('mentions-legales/', views.mentions_legales, name='mentions_legales'),

    # Formulaire de commande avec sélection des produits et quantités
    path('commander/', views.commander, name='commander'),
]
