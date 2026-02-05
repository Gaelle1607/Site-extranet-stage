"""
=============================================================================
RECHERCHE_CLIENTS_API.PY - API de recherche de clients
=============================================================================

Endpoint API pour la recherche de clients en temps réel.
Utilisé par les champs de recherche AJAX dans les formulaires
(notamment pour l'inscription d'un nouvel utilisateur).

Fonctionnalités :
    - Recherche par code tiers (partiel)
    - Recherche par nom ou ville (FULLTEXT)
    - Retourne les 20 premiers résultats
    - Format JSON pour utilisation AJAX

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.http import JsonResponse
from django.db import connections

from .decorators import admin_required


@admin_required
def recherche_clients_api(request):
    """
    API pour rechercher des clients dans la base distante.

    Cette vue est appelée en AJAX depuis les formulaires qui nécessitent
    de sélectionner un client (inscription, etc.). Elle utilise une
    recherche FULLTEXT pour des performances optimales.

    La recherche s'effectue différemment selon le type de requête :
    - Numérique : recherche partielle sur le code tiers + FULLTEXT
    - Texte : recherche FULLTEXT sur nom et acheminement (ville)

    La recherche nécessite au moins 2 caractères pour éviter des
    résultats trop nombreux.

    Args:
        request: L'objet HttpRequest Django
            - GET['q'] : Terme de recherche (min 2 caractères)

    Returns:
        JsonResponse: {
            'clients': [
                {'tiers': int, 'nom': str, 'complement': str},
                ...
            ]
        }
    """
    query = request.GET.get('q', '').strip()

    # Nécessite au moins 2 caractères pour lancer la recherche
    if len(query) < 2:
        return JsonResponse({'clients': []})

    # =========================================================================
    # CONSTRUCTION DE LA REQUÊTE SQL
    # =========================================================================
    if query.isdigit():
        # Recherche numérique : par code tiers partiel + FULLTEXT sur nom
        sql = """
            SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement
            FROM comcli
            WHERE tiers != 0
              AND CAST(tiers AS CHAR) LIKE %s
            GROUP BY tiers, complement

            UNION

            SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement
            FROM comcli
            WHERE tiers != 0
              AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
            GROUP BY tiers, complement

            ORDER BY tiers
            LIMIT 20
        """
        params = [f'%{query}%', f'{query}*']
    else:
        # Recherche texte : FULLTEXT sur nom et acheminement (ville)
        sql = """
            SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement
            FROM comcli
            WHERE tiers != 0
              AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
            GROUP BY tiers, complement
            ORDER BY tiers
            LIMIT 20
        """
        params = [f'{query}*']  # Préfixe pour recherche partielle

    # =========================================================================
    # EXÉCUTION DE LA REQUÊTE
    # =========================================================================
    with connections['logigvd'].cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # Formater les résultats pour JSON
    result = [{'tiers': row[0], 'nom': row[1], 'complement': row[2] or ''} for row in rows]

    return JsonResponse({'clients': result})
