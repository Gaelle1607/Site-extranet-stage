"""
=============================================================================
INFORMATION_UTILISATEUR.PY - Vue des informations d'un utilisateur
=============================================================================

Affiche la fiche complète d'un utilisateur extranet.
Combine les données du compte Django et les informations du client distant.

Informations affichées :
    - Compte : username, email, date d'inscription
    - Client : nom, complément, adresse, code postal, ville

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from types import SimpleNamespace

from django.shortcuts import render, get_object_or_404
from django.db import connections

from clients.models import Utilisateur
from .decorators import admin_required


@admin_required
def information_utilisateur(request, utilisateur_id):
    """
    Affiche les informations détaillées d'un utilisateur.

    Cette vue combine les données de deux sources :
    1. Le compte utilisateur Django (username, email, date d'inscription)
    2. Les informations du client dans la base distante (nom, adresse)

    La récupération des données client priorise l'entrée avec
    complement vide (entrée principale du client).

    Args:
        request: L'objet HttpRequest Django
        utilisateur_id (int): L'identifiant de l'utilisateur

    Returns:
        HttpResponse: La page information_utilisateur.html avec :
            - utilisateur : L'objet Utilisateur
            - client : Les informations du client distant (ou None)

    Raises:
        Http404: Si l'utilisateur n'existe pas
    """
    # Récupérer l'utilisateur par son ID
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)

    # =========================================================================
    # RÉCUPÉRATION DES INFORMATIONS CLIENT
    # =========================================================================
    with connections['logigvd'].cursor() as cursor:
        # Priorité à l'entrée principale (complement vide)
        cursor.execute("""
            SELECT nom, complement, adresse, cp, acheminement FROM comcli
            WHERE tiers = %s AND (complement IS NULL OR TRIM(complement) = '')
            ORDER BY nom
            LIMIT 1
        """, [utilisateur.code_tiers])
        row = cursor.fetchone()

        # Si pas d'entrée principale, prendre la première disponible
        if not row:
            cursor.execute("""
                SELECT nom, complement, adresse, cp, acheminement FROM comcli
                WHERE tiers = %s ORDER BY complement, nom LIMIT 1
            """, [utilisateur.code_tiers])
            row = cursor.fetchone()

    # Créer un objet avec les attributs du client pour le template
    if row:
        client_distant = SimpleNamespace(
            nom=row[0],
            complement=row[1],
            adresse=row[2],
            cp=row[3],
            acheminement=row[4]  # Ville
        )
    else:
        client_distant = None

    context = {
        'page_title': f'Information - {utilisateur.user.username}',
        'utilisateur': utilisateur,
        'client': client_distant,
    }
    return render(request, 'administration/utilisateurs/information_utilisateur.html', context)
