"""
=============================================================================
__INIT__.PY - Point d'entrée du package views de l'administration
=============================================================================

Ce fichier centralise tous les exports des vues de l'application administration.
Chaque vue est définie dans son propre fichier (principe : 1 fichier = 1 fonction).

Organisation des vues :
    - Utilitaires       : decorators.py (contrôle d'accès), filtres.py (filtrage)
    - Dashboard         : dashboard.py (page d'accueil admin)
    - Commandes         : liste, détails, suppression, restauration
    - Utilisateurs      : catalogue, information, modification, suppression
    - Clients           : catalogue_clients, cadencier
    - APIs              : recherche_clients_api, verifier_mot_de_passe_api
    - Profil admin      : profil, changement mot de passe, reset

Projet : Extranet Giffaud Groupe
=============================================================================
"""

# =============================================================================
# UTILITAIRES ET DÉCORATEURS
# =============================================================================
from .decorators import admin_required, is_admin, EDI_OUTPUT_DIR
from .filtres import preparer_filtres, appliquer_filtres

# =============================================================================
# DASHBOARD
# =============================================================================
from .dashboard import dashboard

# =============================================================================
# GESTION DES COMMANDES
# =============================================================================
from .liste_commande import liste_commande
from .details_commande import details_commande
from .commande_utilisateur import commande_utilisateur
from .supprimer_commande import supprimer_commande
from .restaurer_commande import restaurer_commande
from .supprimer_definitivement_commande import supprimer_definitivement_commande

# =============================================================================
# GESTION DES UTILISATEURS
# =============================================================================
from .catalogue_utilisateurs import catalogue_utilisateurs
from .information_utilisateur import information_utilisateur
from .modifier_utilisateur import modifier_utilisateur
from .changer_mot_de_passe import changer_mot_de_passe
from .supprimer_utilisateur import supprimer_utilisateur
from .restaurer_utilisateur import restaurer_utilisateur
from .supprimer_definitivement_utilisateur import supprimer_definitivement_utilisateur
from .verifier_mot_de_passe_api import verifier_mot_de_passe_api
from .inscription import inscription

# =============================================================================
# GESTION DES CLIENTS (BASE DISTANTE)
# =============================================================================
from .catalogue_clients import catalogue_clients
from .cadencier_client import cadencier_client
from .recherche_clients_api import recherche_clients_api

# =============================================================================
# PROFIL ADMINISTRATEUR
# =============================================================================
from .profil_admin import profil_admin
from .changer_mot_de_passe_admin import changer_mot_de_passe_admin
from .reset_password_admin import reset_password_admin

# Liste explicite des exports publics du module
__all__ = [
    # Utilitaires
    'admin_required',
    'is_admin',
    'EDI_OUTPUT_DIR',
    # Dashboard
    'dashboard',
    # Commandes
    'liste_commande',
    'details_commande',
    'commande_utilisateur',
    'supprimer_commande',
    'restaurer_commande',
    'supprimer_definitivement_commande',
    # Utilisateurs
    'catalogue_utilisateurs',
    'information_utilisateur',
    'modifier_utilisateur',
    'changer_mot_de_passe',
    'supprimer_utilisateur',
    'restaurer_utilisateur',
    'supprimer_definitivement_utilisateur',
    'verifier_mot_de_passe_api',
    # Clients
    'catalogue_clients',
    'cadencier_client',
    'recherche_clients_api',
    # Inscription
    'inscription',
    # Profil admin
    'profil_admin',
    'changer_mot_de_passe_admin',
    'reset_password_admin',
]
