"""
=============================================================================
APPS.PY - Configuration de l'application Catalogue
=============================================================================

Configuration Django pour l'application de gestion du catalogue produits.

Fonctionnalités principales :
    - Affichage de la liste des produits disponibles
    - Filtrage et recherche de produits
    - Gestion des favoris (produits les plus commandés)
    - Formulaire de commande

L'application accède à la base de données distante LogiGVD pour
récupérer les informations des produits et leurs prix.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.apps import AppConfig


class CatalogueConfig(AppConfig):
    """
    Classe de configuration pour l'application catalogue.

    Attributs:
        name (str): Nom de l'application Django ('catalogue')
    """
    name = 'catalogue'
