"""
=============================================================================
SUPPRIMER_DEFINITIVEMENT_COMMANDE.PY - Suppression définitive
=============================================================================

Supprime définitivement une commande archivée.
Cette action est irréversible et supprime également le fichier EDI
associé à la commande.

Actions effectuées :
1. Création d'une entrée dans l'historique des suppressions
2. Suppression du fichier CSV EDI de la commande
3. Suppression de l'archive

Projet : Extranet Giffaud Groupe
=============================================================================
"""
import os

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from commandes.models import CommandeSupprimee, HistoriqueSuppression
from .decorators import admin_required, EDI_OUTPUT_DIR


@admin_required
@require_POST
def supprimer_definitivement_commande(request, commande_supprimee_id):
    """
    Supprime définitivement une commande archivée et son fichier EDI.

    Cette action est irréversible. Elle :
    - Crée une trace dans l'historique des suppressions (pour audit)
    - Supprime le fichier CSV EDI de la commande
    - Supprime l'archive CommandeSupprimee

    L'historique conserve :
    - Numéro de commande
    - Nom et code tiers du client
    - Total HT
    - Date de la suppression définitive

    Args:
        request: L'objet HttpRequest Django
        commande_supprimee_id (int): L'ID de l'archive à supprimer

    Returns:
        HttpResponse: Redirection vers le dashboard

    Raises:
        Http404: Si l'archive n'existe pas
    """
    # Récupérer l'archive de la commande
    commande_supprimee = get_object_or_404(CommandeSupprimee, id=commande_supprimee_id)
    numero = commande_supprimee.numero

    # Récupérer le nom du client pour l'historique
    client = commande_supprimee.utilisateur.get_client_distant()
    nom_client = client.nom if client else f"Client {commande_supprimee.utilisateur.code_tiers}"

    # =========================================================================
    # CRÉATION DE L'ENTRÉE D'HISTORIQUE
    # =========================================================================
    # Conserve une trace de la suppression pour l'audit
    HistoriqueSuppression.objects.create(
        numero=numero,
        nom_client=nom_client,
        code_tiers=commande_supprimee.utilisateur.code_tiers,
        total_ht=commande_supprimee.total_ht,
    )

    # =========================================================================
    # SUPPRESSION DU FICHIER EDI
    # =========================================================================
    # Supprimer le fichier CSV généré lors de l'export de la commande
    fichier_edi = EDI_OUTPUT_DIR / f"{numero}.csv"
    if fichier_edi.exists():
        try:
            os.remove(fichier_edi)
        except OSError:
            # Ignorer les erreurs (fichier verrouillé, permissions, etc.)
            pass

    # =========================================================================
    # SUPPRESSION DE L'ARCHIVE
    # =========================================================================
    commande_supprimee.delete()

    messages.success(request, f'La commande {numero} a été définitivement supprimée.')
    return redirect('administration:dashboard')
