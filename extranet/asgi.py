"""
=============================================================================
ASGI.PY - Configuration ASGI pour les fonctionnalités asynchrones
=============================================================================

ASGI (Asynchronous Server Gateway Interface) est l'évolution de WSGI
qui supporte les opérations asynchrones. Utile pour :
    - WebSockets (communication temps réel)
    - Requêtes HTTP asynchrones
    - Long-polling

Ce fichier est utilisé avec des serveurs compatibles ASGI comme :
    - Daphne
    - Uvicorn
    - Hypercorn

Note : Pour une application Django classique sans WebSockets,
WSGI (wsgi.py) est suffisant.

Documentation Django :
    https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/

Projet : Extranet Giffaud Groupe
=============================================================================
"""

import os

from django.core.asgi import get_asgi_application

# Configure le module de settings Django à utiliser
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'extranet.settings')

# Crée l'application ASGI - point d'entrée pour les serveurs asynchrones
application = get_asgi_application()
