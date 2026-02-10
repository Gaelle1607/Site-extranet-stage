"""
=============================================================================
AUTH - Vues du profil administrateur
=============================================================================
"""
from .profil_admin import profil_admin
from .changer_mot_de_passe_admin import changer_mot_de_passe_admin
from .reset_password_admin import reset_password_admin

__all__ = [
    'profil_admin',
    'changer_mot_de_passe_admin',
    'reset_password_admin',
]
