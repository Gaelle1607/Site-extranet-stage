"""
=============================================================================
SUPPRIMER_COMMANDE.PY - Vue de suppression d'une commande
=============================================================================

Permet de supprimer une commande avec possibilité de restauration.
La suppression est un "soft delete" : la commande est archivée pendant
5 minutes, permettant une restauration en cas d'erreur.

Processus :
1. Sérialisation des lignes de commande en JSON
2. Création d'une archive CommandeSupprimee
3. Suppression de la commande originale
4. Possibilité de restauration pendant 5 minutes

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from commandes.models import Commande, CommandeSupprimee
from .decorators import admin_required


@admin_required
@require_POST
def supprimer_commande(request, commande_id):
    """
    Archive une commande pour suppression avec possibilité de restauration.

    Cette vue effectue un "soft delete" :
    - Les lignes de commande sont sérialisées en JSON
    - Une archive CommandeSupprimee est créée avec toutes les données
    - La commande originale est supprimée
    - La restauration est possible pendant 5 minutes

    Args:
        request: L'objet HttpRequest Django
        commande_id (int): L'identifiant de la commande à supprimer

    Returns:
        HttpResponse: Redirection vers la liste des commandes

    Raises:
        Http404: Si la commande n'existe pas
    """
    # Récupérer la commande à supprimer
    commande = get_object_or_404(Commande, id=commande_id)

    # =========================================================================
    # SÉRIALISATION DES LIGNES EN JSON
    # =========================================================================
    # Sauvegarde de chaque ligne pour permettre la restauration
    lignes_data = []
    for ligne in commande.lignes.all():
        lignes_data.append({
            'reference_produit': ligne.reference_produit,
            'nom_produit': ligne.nom_produit,
            'quantite': ligne.quantite,
            'prix_unitaire': str(ligne.prix_unitaire),  # Decimal -> str pour JSON
            'total_ligne': str(ligne.total_ligne),
        })

    # =========================================================================
    # CRÉATION DE L'ARCHIVE
    # =========================================================================
    # Sauvegarde complète de la commande pour restauration potentielle
    CommandeSupprimee.objects.create(
        utilisateur=commande.utilisateur,
        numero=commande.numero,
        date_commande=commande.date_commande,
        date_livraison=commande.date_livraison,
        date_depart_camions=commande.date_depart_camions,
        total_ht=commande.total_ht,
        commentaire=commande.commentaire,
        lignes_json=lignes_data,
    )

    # =========================================================================
    # SUPPRESSION DE LA COMMANDE
    # =========================================================================
    numero = commande.numero
    commande.delete()  # Cascade sur les LigneCommande

    messages.success(request, f'La commande {numero} a été supprimée. Vous pouvez la restaurer pendant 5 minutes depuis le tableau de bord.')
    return redirect('administration:liste_commande')
