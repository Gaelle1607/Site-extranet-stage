"""
Service pour récupérer les produits et prix depuis la base MariaDB distante.
"""
from .models import ComCli, ComCliLig, Catalogue, Prod


def get_client_distant(code_tiers):
    """
    Récupère les informations client depuis la base distante.

    Args:
        code_tiers: Code tiers du client

    Returns:
        Instance ComCli ou None
    """
    try:
        return ComCli.objects.using('logigvd').get(tiers=code_tiers)
    except ComCli.DoesNotExist:
        return None


def get_produits_client(utilisateur):
    """
    Récupère la liste des produits avec prix pour un utilisateur.

    Args:
        utilisateur: Instance Utilisateur (avec code_tiers)

    Returns:
        Liste de dictionnaires avec les produits
    """
    code_tiers = utilisateur.code_tiers if hasattr(utilisateur, 'code_tiers') else None

    if not code_tiers:
        return []

    # Récupérer les produits du catalogue pour ce client spécifique
    catalogue_items = Catalogue.objects.using('logigvd').filter(tiers=code_tiers)

    # Récupérer les codes produits du catalogue
    codes_produits = [item.prod for item in catalogue_items]

    # Récupérer les lignes de produits (avec prix et qte) pour ces produits
    lignes = ComCliLig.objects.using('logigvd').filter(prod__in=codes_produits)
    lignes_dict = {ligne.prod: ligne for ligne in lignes}

    # Récupérer les infos produits
    prods = Prod.objects.using('logigvd').filter(prod__in=codes_produits)
    prods_dict = {p.prod: p for p in prods}

    produits = []
    for item in catalogue_items:
        prod_info = prods_dict.get(item.prod)
        ligne_info = lignes_dict.get(item.prod)

        produit = {
            'prod': item.prod,
            'libelle': prod_info.libelle if prod_info else item.prod,
            'pu_base': float(ligne_info.pu_base) if ligne_info and ligne_info.pu_base else 0,
            'reference': item.prod,
            'nb_commandes': int(ligne_info.qte) if ligne_info and ligne_info.qte else 0,
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
