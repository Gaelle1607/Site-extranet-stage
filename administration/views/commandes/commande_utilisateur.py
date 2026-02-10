"""
=============================================================================
COMMANDE_UTILISATEUR.PY - Vue des commandes d'un utilisateur
=============================================================================

Affiche l'historique des commandes passées par un utilisateur spécifique.
Permet de consulter les 50 dernières commandes d'un client.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render, get_object_or_404
from django.db import connections

from clients.models import Utilisateur
from commandes.models import Commande
from ..utils.decorators import admin_required


@admin_required
def commande_utilisateur(request, utilisateur_id):
    """
    Affiche l'historique des commandes d'un utilisateur.

    Cette vue récupère toutes les commandes passées par un utilisateur
    donné, triées par date décroissante (plus récentes en premier).

    Le nom du client est récupéré depuis la base distante pour
    l'affichage du titre de la page.

    Args:
        request: L'objet HttpRequest Django
        utilisateur_id (int): L'identifiant de l'utilisateur

    Returns:
        HttpResponse: La page commande_utilisateur.html avec :
            - utilisateur : L'objet Utilisateur
            - nom_client : Le nom du client depuis la base distante
            - commandes : Liste des 50 dernières commandes

    Raises:
        Http404: Si l'utilisateur n'existe pas
    """
    # Récupérer l'utilisateur
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)

    # =========================================================================
    # RÉCUPÉRATION DU NOM DU CLIENT
    # =========================================================================
    with connections['logigvd'].cursor() as cursor:
        # Priorité à l'entrée principale (complement vide)
        cursor.execute("""
            SELECT nom FROM comcli
            WHERE tiers = %s AND (complement IS NULL OR TRIM(complement) = '')
            ORDER BY nom
            LIMIT 1
        """, [utilisateur.code_tiers])
        row = cursor.fetchone()

        # Si pas d'entrée principale, prendre la première disponible
        if not row:
            cursor.execute("SELECT nom FROM comcli WHERE tiers = %s ORDER BY complement, nom LIMIT 1", [utilisateur.code_tiers])
            row = cursor.fetchone()

    nom_client = row[0] if row and row[0] else f"Client {utilisateur.code_tiers}"

    # =========================================================================
    # RÉCUPÉRATION DES COMMANDES
    # =========================================================================
    # Limiter aux 50 dernières pour les performances
    commandes = Commande.objects.filter(utilisateur=utilisateur).order_by('-date_commande')[:50]

    context = {
        'page_title': f'Commandes - {nom_client}',
        'utilisateur': utilisateur,
        'nom_client': nom_client,
        'commandes': commandes,
    }
    return render(request, 'administration/commandes/commande_utilisateur.html', context)
