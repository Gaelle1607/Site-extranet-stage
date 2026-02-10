"""
=============================================================================
URLS.PY - Routes de l'interface d'administration personnalisée
=============================================================================

Ce fichier définit toutes les URLs de l'interface d'administration.
Toutes ces vues sont protégées par le décorateur @admin_required.

Organisation des routes :
    - Dashboard           : Vue d'ensemble et statistiques
    - Gestion commandes   : Liste, détails, suppression, restauration
    - Gestion utilisateurs: Liste, informations, modification, suppression
    - Gestion clients     : Catalogue clients, cadencier
    - APIs internes       : Recherche clients, vérification mot de passe
    - Profil admin        : Gestion du compte administrateur

Préfixe : /administration/

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.urls import path
from . import views

# Namespace pour les URLs de cette application
# Usage dans les templates : {% url 'administration:dashboard' %}
app_name = 'administration'

urlpatterns = [
    # =========================================================================
    # DASHBOARD - Page d'accueil administration
    # =========================================================================
    path('', views.dashboard, name='dashboard'),

    # =========================================================================
    # GESTION DES COMMANDES
    # =========================================================================
    # Liste de toutes les commandes avec filtres
    path('commandes/', views.liste_commande, name='liste_commande'),

    # Détails d'une commande spécifique
    path('commandes/<int:commande_id>/', views.details_commande, name='details_commande'),

    # Suppression d'une commande (soft delete avec possibilité de restauration)
    path('commandes/<int:commande_id>/supprimer/', views.supprimer_commande, name='supprimer_commande'),

    # Restauration d'une commande supprimée (dans le délai imparti)
    path('commandes-supprimees/<int:commande_supprimee_id>/restaurer/', views.restaurer_commande, name='restaurer_commande'),

    # Suppression définitive d'une commande (irréversible)
    path('commandes-supprimees/<int:commande_supprimee_id>/supprimer/', views.supprimer_definitivement_commande, name='supprimer_definitivement_commande'),

    # =========================================================================
    # GESTION DES UTILISATEURS EXTRANET
    # =========================================================================
    # Liste de tous les utilisateurs de l'extranet
    path('utilisateurs/', views.catalogue_utilisateurs, name='catalogue_utilisateur'),

    # Fiche information d'un utilisateur
    path('information/<int:utilisateur_id>/', views.information_utilisateur, name='information_utilisateur'),

    # Modification des informations d'un utilisateur
    path('information/<int:utilisateur_id>/modifier/', views.modifier_utilisateur, name='modifier_utilisateur'),

    # Changement du mot de passe d'un utilisateur
    path('information/<int:utilisateur_id>/mot-de-passe/', views.changer_mot_de_passe, name='changer_mot_de_passe'),

    # Historique des commandes d'un utilisateur
    path('information/<int:utilisateur_id>/commandes/', views.commande_utilisateur, name='commande_utilisateur'),

    # Suppression d'un utilisateur (soft delete)
    path('utilisateurs/<int:utilisateur_id>/supprimer/', views.supprimer_utilisateur, name='supprimer_utilisateur'),

    # Restauration d'un utilisateur supprimé
    path('utilisateurs-supprimes/<int:utilisateur_supprime_id>/restaurer/', views.restaurer_utilisateur, name='restaurer_utilisateur'),

    # Suppression définitive d'un utilisateur (irréversible)
    path('utilisateurs-supprimes/<int:utilisateur_supprime_id>/supprimer/', views.supprimer_definitivement_utilisateur, name='supprimer_definitivement_utilisateur'),

    # Formulaire d'inscription d'un nouvel utilisateur
    path('inscription/', views.inscription, name='inscription'),

    # =========================================================================
    # GESTION DES CLIENTS (base distante LogiGVD)
    # =========================================================================
    # Catalogue des clients de la base distante
    path('clients/', views.catalogue_clients, name='catalogue_clients'),

    # Cadencier d'un client (historique des commandes dans la base distante)
    path('cadencier/<int:code_tiers>/', views.cadencier_client, name='cadencier_client'),

    # =========================================================================
    # APIS INTERNES (appels AJAX)
    # =========================================================================
    # Recherche de clients par nom/code (utilisé dans les formulaires)
    path('api/recherche-clients/', views.recherche_clients_api, name='recherche_clients_api'),

    # Vérification du mot de passe d'un utilisateur (avant modification sensible)
    path('api/verifier-mdp/<int:utilisateur_id>/', views.verifier_mot_de_passe_api, name='verifier_mot_de_passe_api'),

    # =========================================================================
    # PROFIL ADMINISTRATEUR
    # =========================================================================
    # Page de profil de l'administrateur connecté
    path('profil/', views.profil_admin, name='profil_admin'),

    # Changement du mot de passe de l'administrateur
    path('profil/mot-de-passe/', views.changer_mot_de_passe_admin, name='changer_mot_de_passe_admin'),

    # Réinitialisation du mot de passe admin (avec clé secrète)
    path('reset-password/', views.reset_password_admin, name='reset_password_admin'),

    # =========================================================================
    # MENTIONS LÉGALES
    # =========================================================================
    path('mentions-legales/', views.mentions_legales_admin, name='mentions_legales_admin'),
]
