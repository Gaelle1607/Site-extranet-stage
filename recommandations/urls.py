"""
=============================================================================
URLS.PY - Routes de l'application Recommandations
=============================================================================

Ce fichier définit les URLs pour le système de recommandations
personnalisées basé sur l'historique d'achat des clients.

Routes disponibles :
    /                   -> Page des recommandations personnalisées
    /api/               -> API JSON des recommandations
    /api/favoris/       -> API JSON des produits favoris

Préfixe : /recommandations/ (défini dans extranet/urls.py)

Architecture :
    - Les recommandations sont calculées via le service services.py
    - L'algorithme utilise l'historique d'achat stocké en base locale
    - Les informations produits viennent de la base distante LogiGVD

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.urls import path
from . import views

# Namespace pour les URLs de cette application
# Usage dans les templates : {% url 'recommandations:liste' %}
app_name = 'recommandations'

urlpatterns = [
    # =========================================================================
    # PAGE PRINCIPALE
    # =========================================================================

    # Page des recommandations personnalisées (page d'accueil après connexion)
    # Affiche les produits recommandés basés sur l'historique d'achat
    # Inclut les filtres et la recherche comme le catalogue
    path('', views.mes_recommandations, name='liste'),

    # =========================================================================
    # API REST
    # =========================================================================

    # API pour obtenir les recommandations en format JSON
    # Paramètre GET : limite (défaut = 10)
    # Retourne : {recommandations: [{reference, nom, prix, stock}, ...]}
    path('api/', views.api_recommandations, name='api'),

    # API pour obtenir les produits favoris (les plus commandés)
    # Paramètre GET : limite (défaut = 4)
    # Retourne : {favoris: [{reference, nom, prix}, ...]}
    path('api/favoris/', views.api_produits_favoris, name='api_favoris'),
]
