"""
=============================================================================
SUPPRIMER_DEFINITIVEMENT_UTILISATEUR.PY - Suppression définitive
=============================================================================

Supprime définitivement un utilisateur archivé.
Cette action est irréversible et supprime également les fichiers EDI
associés aux commandes de l'utilisateur.

Actions effectuées :
1. Création d'une entrée dans l'historique des suppressions
2. Suppression des fichiers CSV EDI des commandes
3. Suppression de l'archive utilisateur

Projet : Extranet Giffaud Groupe
=============================================================================
"""
import os

from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from clients.models import UtilisateurSupprime, HistoriqueSuppressionUtilisateur
from .decorators import admin_required, EDI_OUTPUT_DIR


@admin_required
@require_POST
def supprimer_definitivement_utilisateur(request, utilisateur_supprime_id):
    """
    Supprime définitivement un utilisateur archivé et ses fichiers associés.

    Cette action est irréversible. Elle :
    - Crée une trace dans l'historique des suppressions (pour audit)
    - Supprime les fichiers CSV EDI des commandes de l'utilisateur
    - Supprime l'archive UtilisateurSupprime

    L'historique conserve :
    - Username et nom du client
    - Code tiers
    - Nombre de commandes supprimées
    - Date de la suppression définitive

    Args:
        request: L'objet HttpRequest Django
        utilisateur_supprime_id (int): L'ID de l'archive à supprimer

    Returns:
        HttpResponse: Redirection vers le dashboard

    Raises:
        Http404: Si l'archive n'existe pas
    """
    # Récupérer l'archive de l'utilisateur
    utilisateur_supprime = get_object_or_404(UtilisateurSupprime, id=utilisateur_supprime_id)

    # Sauvegarder les informations pour le message et l'historique
    username = utilisateur_supprime.username
    nom_client = utilisateur_supprime.nom_client
    nb_commandes = len(utilisateur_supprime.commandes_json)

    # =========================================================================
    # CRÉATION DE L'ENTRÉE D'HISTORIQUE
    # =========================================================================
    # Conserve une trace de la suppression pour l'audit
    HistoriqueSuppressionUtilisateur.objects.create(
        username=username,
        nom_client=nom_client,
        code_tiers=utilisateur_supprime.code_tiers,
        nb_commandes=nb_commandes,
    )

    # =========================================================================
    # SUPPRESSION DES FICHIERS EDI
    # =========================================================================
    # Supprimer les fichiers CSV générés lors de l'export des commandes
    for commande_data in utilisateur_supprime.commandes_json:
        numero = commande_data.get('numero', '')
        if numero:
            fichier_edi = EDI_OUTPUT_DIR / f"{numero}.csv"
            if fichier_edi.exists():
                try:
                    os.remove(fichier_edi)
                except OSError:
                    # Ignorer les erreurs de suppression de fichiers
                    # (fichier verrouillé, permissions, etc.)
                    pass

    # =========================================================================
    # SUPPRESSION DE L'ARCHIVE
    # =========================================================================
    utilisateur_supprime.delete()

    messages.success(request, f'L\'utilisateur {username} ({nom_client}) a été définitivement supprimé.')
    return redirect('administration:dashboard')
