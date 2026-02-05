#!/usr/bin/env python
"""
=============================================================================
MANAGE.PY - Point d'entrée principal du projet Django Extranet
=============================================================================

Ce fichier est le script de gestion Django qui permet d'exécuter des commandes
administratives depuis la ligne de commande.

Commandes courantes :
    - python manage.py runserver     : Démarre le serveur de développement
    - python manage.py migrate       : Applique les migrations de base de données
    - python manage.py makemigrations: Crée de nouvelles migrations
    - python manage.py createsuperuser: Crée un administrateur Django
    - python manage.py shell         : Ouvre un shell Python interactif

Projet : Extranet Giffaud Groupe
=============================================================================
"""
import os
import sys


def main():
    """
    Fonction principale qui configure l'environnement Django et exécute
    la commande passée en argument.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'extranet.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
