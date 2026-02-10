"""
=============================================================================
__INIT__.PY - Point d'entrée du package views de l'administration
=============================================================================

Ce fichier centralise tous les exports des vues de l'application administration.
Les vues sont organisées par catégorie dans des sous-dossiers.

Organisation des vues :
    - utils/        : decorators.py (contrôle d'accès), filtres.py (filtrage)
    - commandes/    : liste, détails, suppression, restauration
    - utilisateurs/ : catalogue, information, modification, suppression
    - clients/      : catalogue_clients, cadencier
    - api/          : recherche_clients_api, verifier_mot_de_passe_api
    - auth/         : profil, changement mot de passe, reset
    - legal/        : mentions légales
    - dashboard.py  : page d'accueil admin

Projet : Extranet Giffaud Groupe
=============================================================================
"""

# =============================================================================
# UTILITAIRES ET DÉCORATEURS
# =============================================================================
from .utils import admin_required, is_admin, EDI_OUTPUT_DIR
from .utils import preparer_filtres, appliquer_filtres

# =============================================================================
# DASHBOARD
# =============================================================================
from .dashboard import dashboard

# =============================================================================
# GESTION DES COMMANDES
# =============================================================================
from .commandes import (
    liste_commande,
    details_commande,
    commande_utilisateur,
    supprimer_commande,
    restaurer_commande,
    supprimer_definitivement_commande,
)

# =============================================================================
# GESTION DES UTILISATEURS
# =============================================================================
from .utilisateurs import (
    catalogue_utilisateurs,
    information_utilisateur,
    modifier_utilisateur,
    changer_mot_de_passe,
    supprimer_utilisateur,
    restaurer_utilisateur,
    supprimer_definitivement_utilisateur,
    inscription,
)

# =============================================================================
# GESTION DES CLIENTS (BASE DISTANTE)
# =============================================================================
from .clients import catalogue_clients, cadencier_client

# =============================================================================
# APIS INTERNES
# =============================================================================
from .api import recherche_clients_api, verifier_mot_de_passe_api

# =============================================================================
# PROFIL ADMINISTRATEUR
# =============================================================================
from .auth import profil_admin, changer_mot_de_passe_admin, reset_password_admin

# =============================================================================
# MENTIONS LÉGALES
# =============================================================================
from .legal import mentions_legales_admin

# Liste explicite des exports publics du module
__all__ = [
    # Utilitaires
    'admin_required',
    'is_admin',
    'EDI_OUTPUT_DIR',
    'preparer_filtres',
    'appliquer_filtres',
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
    'inscription',
    # Clients
    'catalogue_clients',
    'cadencier_client',
    # APIs
    'recherche_clients_api',
    'verifier_mot_de_passe_api',
    # Profil admin
    'profil_admin',
    'changer_mot_de_passe_admin',
    'reset_password_admin',
    # Mentions légales
    'mentions_legales_admin',
]
