"""
Service pour récupérer les produits et prix depuis la base MariaDB distante.
"""
from django.db import connections

from .models import ComCli, ComCliLig, Catalogue, Prod


def get_client_distant(code_tiers):
    """
    Récupère les informations client depuis la base distante.

    Args:
        code_tiers: Code tiers du client

    Returns:
        Instance ComCli ou None
    """
    return ComCli.objects.using('logigvd').filter(tiers=code_tiers).first()


def get_produits_client(utilisateur):
    """
    Récupère la liste des produits avec prix pour un utilisateur.
    Utilise une seule requête SQL avec JOINs pour optimiser les performances.

    Args:
        utilisateur: Instance Utilisateur (avec code_tiers)

    Returns:
        Liste de dictionnaires avec les produits
    """
    code_tiers = utilisateur.code_tiers if hasattr(utilisateur, 'code_tiers') else None

    if not code_tiers:
        return []

    with connections['logigvd'].cursor() as cursor:
        # Requête 1 : catalogue + libellé produit (rapide, catalogue filtré par tiers)
        cursor.execute("""
            SELECT c.prod, p.libelle
            FROM catalogue c
            LEFT JOIN prod p ON c.prod = p.prod
            WHERE c.tiers = %s
        """, [code_tiers])
        catalogue_rows = cursor.fetchall()

        if not catalogue_rows:
            return []

        codes_produits = [r[0] for r in catalogue_rows]
        libelles = {r[0]: r[1] for r in catalogue_rows}

        # Requête 2 : prix et quantités depuis comclilig, filtré par client via comcli
        placeholders = ','.join(['%s'] * len(codes_produits))
        cursor.execute(f"""
            SELECT l.prod, MAX(l.pu_base), MAX(l.qte), MAX(l.poids), MAX(l.colis)
            FROM comclilig l
            INNER JOIN comcli c ON l.comcli = c.comcli AND l.lieusais = c.lieusais
            WHERE c.tiers = %s AND l.prod IN ({placeholders})
            GROUP BY l.prod
        """, [code_tiers] + codes_produits)
        lignes = {r[0]: r[1:] for r in cursor.fetchall()}

    produits = []
    for prod_code in codes_produits:
        ligne = lignes.get(prod_code)
        libelle = libelles.get(prod_code) or prod_code
        pu_base = float(ligne[0]) if ligne and ligne[0] else 0
        poids = float(ligne[2]) if ligne and ligne[2] else 0
        colis = int(ligne[3]) if ligne and ligne[3] else 0

        # Déterminer l'unité de vente
        if poids > 0:
            unite = 'kg'
        elif colis > 0:
            unite = 'Colis'
        else:
            unite = ''

        if pu_base <= 0:
            continue

        produit = {
            'prod': prod_code,
            'reference': prod_code,
            'libelle': libelle,
            'nom': libelle,
            'pu_base': pu_base,
            'prix': pu_base,
            'unite': unite,
            'nb_commandes': int(ligne[1]) if ligne and ligne[1] else 0,
            'poids': poids,
            'colis': colis,
        }
        produits.append(produit)

    return produits


def get_categories_client(utilisateur):
    """
    Récupère les catégories disponibles pour un utilisateur.

    Returns:
        Liste de noms de catégories
    """
    produits = get_produits_client(utilisateur)
    categories = set()
    for p in produits:
        for cat in p.get('categories', []):
            categories.add(cat)
    return sorted(categories)


def get_produit_by_reference(utilisateur, reference):
    """
    Récupère un produit par sa référence.

    Returns:
        Dictionnaire du produit ou None
    """
    produits = get_produits_client(utilisateur)
    for p in produits:
        if p['reference'] == reference:
            return p
    return None
