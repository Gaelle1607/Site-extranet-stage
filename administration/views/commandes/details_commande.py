"""
=============================================================================
DETAILS_COMMANDE.PY - Vue des détails d'une commande
=============================================================================

Affiche le détail complet d'une commande spécifique.
Inclut les informations du client et la liste des produits commandés.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render

from commandes.models import Commande
from .decorators import admin_required


@admin_required
def details_commande(request, commande_id):
    """
    Affiche les détails complets d'une commande.

    Récupère la commande par son ID et enrichit l'affichage avec
    les informations du client depuis la base distante.

    Args:
        request: L'objet HttpRequest Django
        commande_id (int): L'identifiant unique de la commande

    Returns:
        HttpResponse: La page details_commande.html avec :
            - commande : L'objet Commande complet
            - client : Les informations du client distant

    Raises:
        Commande.DoesNotExist: Si l'ID de commande n'existe pas
    """
    # Récupérer la commande par son ID
    commande = Commande.objects.get(id=commande_id)

    # Récupérer les informations du client depuis la base distante
    client = commande.utilisateur.get_client_distant()

    context = {
        'page_title': f'Détails de la commande {commande.numero}',
        'commande': commande,
        'client': client,
    }
    return render(request, 'administration/commandes/details_commande.html', context)
