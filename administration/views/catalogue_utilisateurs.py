"""
=============================================================================
CATALOGUE_UTILISATEURS.PY - Vue de la liste des utilisateurs extranet
=============================================================================

Affiche la liste de tous les utilisateurs inscrits sur l'extranet.
Exclut les administrateurs (staff) et superusers.

Enrichit les données avec les noms des clients depuis la base distante.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render
from django.db import connections

from clients.models import Utilisateur
from .decorators import admin_required


@admin_required
def catalogue_utilisateurs(request):
    """
    Affiche le catalogue des utilisateurs extranet avec recherche.

    Cette vue récupère tous les utilisateurs non-administrateurs et
    enrichit leurs informations avec les données de la base distante
    (nom du client).

    La récupération des noms clients est optimisée en une seule requête
    SQL pour éviter le problème N+1.

    Logique de récupération des noms :
    1. Cherche d'abord les clients avec complement vide (entrée principale)
    2. Pour les tiers non trouvés, prend la première entrée disponible

    Args:
        request: L'objet HttpRequest Django
            - GET['q'] : Terme de recherche (optionnel)

    Returns:
        HttpResponse: La page catalogue_utilisateur.html avec :
            - clients : Liste des utilisateurs enrichis
            - query : Le terme de recherche saisi
    """
    # Récupérer tous les utilisateurs (exclure staff et superusers)
    utilisateurs = Utilisateur.objects.filter(user__is_staff=False, user__is_superuser=False)

    # =========================================================================
    # RÉCUPÉRATION DES NOMS CLIENTS (OPTIMISATION)
    # =========================================================================
    # Collecter tous les codes tiers (convertis en entiers pour la requête SQL)
    codes_tiers = []
    for u in utilisateurs:
        try:
            codes_tiers.append(int(u.code_tiers))
        except (ValueError, TypeError):
            pass

    # Récupérer les noms des clients en une seule requête SQL
    clients_distants = {}
    if codes_tiers:
        placeholders = ','.join(['%s'] * len(codes_tiers))
        with connections['logigvd'].cursor() as cursor:
            # Priorité aux entrées avec complement vide (entrée principale du client)
            cursor.execute(f"""
                SELECT tiers, nom FROM comcli
                WHERE tiers IN ({placeholders})
                AND (complement IS NULL OR TRIM(complement) = '')
                ORDER BY tiers, nom
            """, codes_tiers)
            for row in cursor.fetchall():
                if row[0] not in clients_distants:
                    clients_distants[row[0]] = row[1]

            # Récupérer les noms pour les tiers non encore trouvés
            tiers_manquants = [t for t in codes_tiers if t not in clients_distants]
            if tiers_manquants:
                placeholders2 = ','.join(['%s'] * len(tiers_manquants))
                cursor.execute(f"""
                    SELECT tiers, nom FROM comcli
                    WHERE tiers IN ({placeholders2})
                    ORDER BY tiers, complement
                """, tiers_manquants)
                for row in cursor.fetchall():
                    if row[0] not in clients_distants:
                        clients_distants[row[0]] = row[1]

    # =========================================================================
    # CONSTRUCTION DE LA LISTE ENRICHIE
    # =========================================================================
    clients_avec_infos = []
    for utilisateur in utilisateurs:
        try:
            code_tiers_int = int(utilisateur.code_tiers)
            nom_client = clients_distants.get(code_tiers_int)
        except (ValueError, TypeError):
            nom_client = None

        # Ajouter l'utilisateur avec ses informations enrichies
        if nom_client:
            clients_avec_infos.append({
                'id': utilisateur.id,
                'utilisateur': utilisateur,
                'nom': nom_client,
                'code_tiers': utilisateur.code_tiers,
            })
        else:
            # Client non trouvé dans la base distante
            clients_avec_infos.append({
                'id': utilisateur.id,
                'utilisateur': utilisateur,
                'nom': f"Client inconnu ({utilisateur.code_tiers})",
                'code_tiers': utilisateur.code_tiers,
            })

    # =========================================================================
    # FILTRAGE PAR RECHERCHE
    # =========================================================================
    query = request.GET.get('q', '')
    if query:
        # Recherche insensible à la casse dans le nom et le code tiers
        clients_avec_infos = [c for c in clients_avec_infos if
                              query.lower() in c['nom'].lower() or
                              query.lower() in c['code_tiers'].lower()]

    context = {
        'page_title': 'Catalogue Utilisateurs',
        'clients': clients_avec_infos,
        'query': query,
    }
    return render(request, 'administration/catalogue_utilisateur.html', context)
