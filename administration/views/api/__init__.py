"""
=============================================================================
API - Endpoints AJAX internes
=============================================================================
"""
from .recherche_clients_api import recherche_clients_api
from .verifier_mot_de_passe_api import verifier_mot_de_passe_api

__all__ = [
    'recherche_clients_api',
    'verifier_mot_de_passe_api',
]
