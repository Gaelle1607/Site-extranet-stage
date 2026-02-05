"""
=============================================================================
URLS.PY - Configuration des URLs racine du projet Extranet
=============================================================================

Ce fichier définit le routage principal de l'application.
Chaque application possède son propre fichier urls.py qui est inclus ici.

Structure des URLs :
    /admin/          -> Interface d'administration Django native
    /                -> Application clients (connexion, profil)
    /catalogue/      -> Consultation et recherche de produits
    /commandes/      -> Gestion du panier et des commandes
    /recommandations/-> Produits recommandés
    /administration/ -> Interface d'administration personnalisée

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.contrib import admin
from django.urls import path, include

# =============================================================================
# CONFIGURATION DES URLS PRINCIPALES
# =============================================================================
urlpatterns = [
    # Interface d'administration Django native (accès restreint aux superusers)
    path('admin/', admin.site.urls),

    # Application clients : authentification, profil utilisateur
    # Montée à la racine pour avoir /connexion, /deconnexion, /profil
    path('', include('clients.urls')),

    # Application catalogue : liste des produits, recherche, détails
    path('catalogue/', include('catalogue.urls')),

    # Application commandes : panier, validation, historique
    path('commandes/', include('commandes.urls')),

    # Application recommandations : produits suggérés
    path('recommandations/', include('recommandations.urls')),

    # Interface d'administration personnalisée : gestion utilisateurs, commandes
    path('administration/', include('administration.urls')),
]
