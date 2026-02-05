"""
=============================================================================
APPS.PY - Configuration de l'application Administration
=============================================================================

Configuration Django pour l'application d'administration personnalisée.
Cette application fournit une interface de gestion pour les administrateurs
du système extranet.

Fonctionnalités principales :
    - Dashboard avec statistiques et activités récentes
    - Gestion des utilisateurs (CRUD, changement de mot de passe)
    - Gestion des commandes (consultation, suppression)
    - Consultation du catalogue clients
    - Gestion des demandes de mot de passe

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.apps import AppConfig


class AdministrationConfig(AppConfig):
    """
    Classe de configuration pour l'application administration.

    Attributs:
        name (str): Nom de l'application Django ('administration')
    """
    name = 'administration'
