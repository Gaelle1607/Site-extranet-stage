"""
=============================================================================
WSGI.PY - Configuration WSGI pour le déploiement en production
=============================================================================

WSGI (Web Server Gateway Interface) est l'interface standard entre les
serveurs web et les applications Python. Ce fichier est utilisé lors du
déploiement avec des serveurs comme :
    - Apache avec mod_wsgi
    - Nginx avec Gunicorn ou uWSGI

La variable 'application' est le point d'entrée appelé par le serveur web
pour chaque requête HTTP entrante.

Pour le développement, utilisez plutôt : python manage.py runserver

Documentation Django :
    https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/

Projet : Extranet Giffaud Groupe
=============================================================================
"""

import os

from django.core.wsgi import get_wsgi_application

# Configure le module de settings Django à utiliser
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'extranet.settings')

# Crée l'application WSGI - point d'entrée pour les serveurs de production
application = get_wsgi_application()
