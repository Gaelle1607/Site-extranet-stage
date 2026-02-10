"""
=============================================================================
CATALOGUE_CLIENTS.PY - Vue du catalogue des clients distants
=============================================================================

Affiche la liste des clients de la base distante LogiGVD.
Ces clients ne sont pas forcément inscrits sur l'extranet.

Permet de :
    - Consulter tous les clients du système
    - Rechercher par nom, acheminement ou code tiers
    - Accéder au cadencier de chaque client

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render
from django.db import connections

from .decorators import admin_required


@admin_required
def catalogue_clients(request):
    """
    Affiche le catalogue des clients de la base distante avec recherche.

    Cette vue interroge directement la base MariaDB distante pour
    récupérer la liste des clients. La recherche utilise l'index
    FULLTEXT sur les colonnes nom et acheminement pour des performances
    optimales.

    Logique de récupération :
    1. Recherche les tiers correspondant aux critères
    2. Pour chaque tiers, récupère le nom de l'entrée principale (complement vide)
    3. Si pas d'entrée principale, prend la première disponible

    La recherche supporte :
    - Recherche numérique : par code tiers partiel
    - Recherche texte : par nom ou ville (acheminement) via FULLTEXT

    Args:
        request: L'objet HttpRequest Django
            - GET['q'] : Terme de recherche (optionnel)

    Returns:
        HttpResponse: La page catalogue_clients.html avec :
            - clients : Liste des clients avec tiers, nom, complement, acheminement
            - query : Le terme de recherche saisi
    """
    query = request.GET.get('q', '').strip()

    with connections['logigvd'].cursor() as cursor:
        # =====================================================================
        # ÉTAPE 1 : RÉCUPÉRER LES CODES TIERS CORRESPONDANTS
        # =====================================================================
        if query:
            if query.isdigit():
                # Recherche numérique : par code tiers partiel + FULLTEXT sur nom
                cursor.execute("""
                    SELECT DISTINCT tiers FROM comcli
                    WHERE tiers != 0 AND CAST(tiers AS CHAR) LIKE %s
                    UNION
                    SELECT DISTINCT tiers FROM comcli
                    WHERE tiers != 0 AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
                    LIMIT 100
                """, [f'%{query}%', f'{query}*'])
            else:
                # Recherche texte : FULLTEXT sur nom et acheminement (ville)
                cursor.execute("""
                    SELECT DISTINCT tiers FROM comcli
                    WHERE tiers != 0 AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
                    LIMIT 100
                """, [f'{query}*'])
        else:
            # Sans recherche : afficher les 100 premiers clients
            cursor.execute("SELECT DISTINCT tiers FROM comcli WHERE tiers != 0 ORDER BY tiers LIMIT 100")

        tiers_list = [row[0] for row in cursor.fetchall()]

        if not tiers_list:
            clients = []
        else:
            # =================================================================
            # ÉTAPE 2 : RÉCUPÉRER LES INFORMATIONS DÉTAILLÉES
            # =================================================================
            placeholders = ','.join(['%s'] * len(tiers_list))

            # Priorité aux entrées avec complement vide (entrée principale)
            cursor.execute(f"""
                SELECT tiers, nom, IFNULL(complement, '') as complement, acheminement
                FROM comcli
                WHERE tiers IN ({placeholders})
                AND (complement IS NULL OR TRIM(complement) = '')
                ORDER BY tiers, nom
            """, tiers_list)

            # Construire le dictionnaire des clients trouvés
            clients_dict = {}
            for row in cursor.fetchall():
                if row[0] not in clients_dict:
                    clients_dict[row[0]] = {
                        'tiers': row[0],
                        'nom': row[1],
                        'complement': row[2] or '',
                        'acheminement': row[3] or ''
                    }

            # Récupérer les informations pour les tiers non trouvés
            tiers_manquants = [t for t in tiers_list if t not in clients_dict]
            if tiers_manquants:
                placeholders2 = ','.join(['%s'] * len(tiers_manquants))
                cursor.execute(f"""
                    SELECT tiers, nom, IFNULL(complement, '') as complement, acheminement
                    FROM comcli
                    WHERE tiers IN ({placeholders2})
                    ORDER BY tiers, complement
                """, tiers_manquants)
                for row in cursor.fetchall():
                    if row[0] not in clients_dict:
                        clients_dict[row[0]] = {
                            'tiers': row[0],
                            'nom': row[1],
                            'complement': row[2] or '',
                            'acheminement': row[3] or ''
                        }

            # Construire la liste finale triée par code tiers
            clients = [clients_dict[t] for t in sorted(clients_dict.keys())]

    context = {
        'page_title': 'Catalogue Clients',
        'clients': clients,
        'query': query,
    }
    return render(request, 'administration/clients/catalogue_clients.html', context)
