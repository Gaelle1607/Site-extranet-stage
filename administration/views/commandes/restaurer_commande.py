"""
=============================================================================
RESTAURER_COMMANDE.PY - Vue de restauration d'une commande supprimée
=============================================================================

Permet de restaurer une commande supprimée pendant le délai de grâce
(5 minutes par défaut).

Processus :
1. Vérification que le délai n'est pas dépassé
2. Recréation de la commande avec ses données originales
3. Recréation de toutes les lignes de commande
4. Suppression de l'archive

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from decimal import Decimal

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from commandes.models import Commande, CommandeSupprimee, LigneCommande
from ..utils.decorators import admin_required


@admin_required
@require_POST
def restaurer_commande(request, commande_supprimee_id):
    """
    Restaure une commande précédemment supprimée.

    Cette vue recrée entièrement une commande à partir de l'archive :
    - Commande avec toutes ses propriétés originales
    - Toutes les lignes de commande avec leurs prix

    La date de commande originale est préservée en contournant
    l'auto_now_add du champ.

    Args:
        request: L'objet HttpRequest Django
        commande_supprimee_id (int): L'ID de l'archive à restaurer

    Returns:
        HttpResponse: Redirection vers le dashboard

    Raises:
        Http404: Si l'archive n'existe pas
    """
    # Récupérer l'archive de la commande
    commande_supprimee = get_object_or_404(CommandeSupprimee, id=commande_supprimee_id)

    # =========================================================================
    # VÉRIFICATION DU DÉLAI
    # =========================================================================
    if not commande_supprimee.est_restaurable():
        messages.error(request, f'La commande {commande_supprimee.numero} ne peut plus être restaurée (délai de 5 minutes dépassé).')
        commande_supprimee.delete()  # Nettoyer l'archive expirée
        return redirect('administration:dashboard')

    # =========================================================================
    # RECRÉATION DE LA COMMANDE
    # =========================================================================
    commande = Commande.objects.create(
        utilisateur=commande_supprimee.utilisateur,
        numero=commande_supprimee.numero,
        date_livraison=commande_supprimee.date_livraison,
        date_depart_camions=commande_supprimee.date_depart_camions,
        total_ht=commande_supprimee.total_ht,
        commentaire=commande_supprimee.commentaire,
    )

    # Restaurer la date de commande originale (contourne auto_now_add)
    Commande.objects.filter(id=commande.id).update(date_commande=commande_supprimee.date_commande)

    # =========================================================================
    # RECRÉATION DES LIGNES DE COMMANDE
    # =========================================================================
    for ligne_data in commande_supprimee.lignes_json:
        LigneCommande.objects.create(
            commande=commande,
            reference_produit=ligne_data['reference_produit'],
            nom_produit=ligne_data['nom_produit'],
            quantite=ligne_data['quantite'],
            prix_unitaire=Decimal(ligne_data['prix_unitaire']),
            total_ligne=Decimal(ligne_data['total_ligne']),
        )

    # =========================================================================
    # NETTOYAGE
    # =========================================================================
    commande_supprimee.delete()

    messages.success(request, f'La commande {commande.numero} a été restaurée avec succès.')
    return redirect('administration:dashboard')
