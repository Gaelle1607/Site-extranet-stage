"""
=============================================================================
CLIENTS - Vues de gestion des clients (base distante LogiGVD)
=============================================================================
"""
from .catalogue_clients import catalogue_clients
from .cadencier_client import cadencier_client

__all__ = [
    'catalogue_clients',
    'cadencier_client',
]
