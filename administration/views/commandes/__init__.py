"""
=============================================================================
COMMANDES - Vues de gestion des commandes
=============================================================================
"""
from .liste_commande import liste_commande
from .details_commande import details_commande
from .commande_utilisateur import commande_utilisateur
from .supprimer_commande import supprimer_commande
from .restaurer_commande import restaurer_commande
from .supprimer_definitivement_commande import supprimer_definitivement_commande

__all__ = [
    'liste_commande',
    'details_commande',
    'commande_utilisateur',
    'supprimer_commande',
    'restaurer_commande',
    'supprimer_definitivement_commande',
]
