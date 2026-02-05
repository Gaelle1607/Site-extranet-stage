"""
=============================================================================
FILTRES.PY - Fonctions de filtrage des produits
=============================================================================

Ce fichier contient les fonctions utilitaires pour préparer et appliquer
des filtres sur les listes de produits dans l'interface d'administration.

Les filtres permettent de :
    - Catégoriser automatiquement les produits selon leur libellé
    - Filtrer les produits par tags/catégories
    - Rechercher par texte dans le libellé ou code produit

Ces fonctions sont utilisées notamment dans la vue du cadencier client.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from catalogue.services import FILTRES_DISPONIBLES, generer_filtres_automatiques, _normaliser


def preparer_filtres(produits, seuil_occurrences=3):
    """
    Prépare les filtres disponibles pour une liste de produits.

    Cette fonction analyse les produits et génère deux types de filtres :
    1. Filtres prédéfinis (définis dans FILTRES_DISPONIBLES)
    2. Filtres automatiques (générés à partir des libellés des produits)

    Les filtres qui ne correspondent à aucun ou à tous les produits
    sont automatiquement exclus (inutiles pour le filtrage).

    Args:
        produits (list): Liste de dictionnaires représentant les produits.
                        Chaque produit doit avoir au minimum 'libelle' et 'tags'.
        seuil_occurrences (int): Nombre minimum de produits devant correspondre
                                 à un filtre automatique pour qu'il soit affiché.
                                 Défaut: 3

    Returns:
        tuple: Un triplet contenant :
            - produits (list): Les produits avec leurs tags mis à jour
            - filtres_groupes (dict): Filtres groupés par catégorie pour l'affichage
            - tags_disponibles (set): Ensemble des codes de tags utilisables
    """
    # Générer les filtres automatiques à partir des libellés des produits
    # Ces filtres sont créés dynamiquement en analysant les mots-clés récurrents
    filtres_auto = generer_filtres_automatiques(produits, seuil_occurrences=seuil_occurrences)

    # Ajouter les tags automatiques aux produits
    # Parcourt chaque produit et lui attribue les tags correspondants
    for produit in produits:
        libelle_normalise = _normaliser(produit.get('libelle', '') or '')
        for code, info in filtres_auto.items():
            # Si un terme du filtre est présent dans le libellé, ajouter le tag
            if any(terme in libelle_normalise for terme in info["termes"]):
                if code not in produit.get('tags', []):
                    produit['tags'].append(code)

    # Compter les occurrences de chaque tag dans la liste des produits
    tags_count = {}
    for p in produits:
        for tag in p.get('tags', []):
            tags_count[tag] = tags_count.get(tag, 0) + 1

    # Ne garder que les tags utiles pour le filtrage :
    # - Plus d'1 produit (sinon trop restrictif)
    # - Moins que le total (sinon filtre inutile car tous les produits correspondent)
    total_produits = len(produits)
    tags_disponibles = {tag for tag, count in tags_count.items() if 1 < count < total_produits}

    # Construire les filtres groupés pour l'affichage dans le template
    filtres_groupes = {}
    for groupe, filtres in FILTRES_DISPONIBLES.items():
        filtres_groupe = {
            code: info["label"]
            for code, info in filtres.items()
            if code in tags_disponibles  # Ne garder que les filtres avec des produits correspondants
        }
        # N'ajouter le groupe que s'il contient au moins un filtre actif
        if filtres_groupe:
            filtres_groupes[groupe] = filtres_groupe

    # Ajouter les filtres automatiques comme groupe séparé "Filtres personnalisés"
    if filtres_auto:
        # Appliquer le même filtre : plus d'1 produit ET moins que le total
        filtres_auto_valides = {
            code: info["label"]
            for code, info in filtres_auto.items()
            if 1 < tags_count.get(code, 0) < total_produits
        }
        if filtres_auto_valides:
            filtres_groupes["Filtres personnalisés"] = filtres_auto_valides

    return produits, filtres_groupes, tags_disponibles


def appliquer_filtres(produits, filtres_actifs, query=''):
    """
    Applique les filtres sélectionnés et la recherche textuelle sur les produits.

    Cette fonction effectue deux types de filtrage :
    1. Recherche textuelle : cherche dans le libellé et le code produit
    2. Filtrage par tags : garde les produits ayant au moins un des tags actifs

    Les deux filtres sont cumulatifs (AND) : un produit doit correspondre
    à la recherche ET avoir un tag actif pour être conservé.

    Args:
        produits (list): Liste des produits à filtrer
        filtres_actifs (list): Liste des codes de filtres/tags actifs.
                              Si vide, aucun filtrage par tag n'est appliqué.
        query (str): Texte de recherche (insensible à la casse).
                    Si vide, aucune recherche textuelle n'est appliquée.

    Returns:
        list: Liste des produits correspondant aux critères de filtrage
    """
    # Étape 1 : Recherche textuelle (si une requête est fournie)
    if query:
        query_lower = query.lower()
        produits = [p for p in produits if
                    query_lower in p.get('libelle', '').lower() or  # Recherche dans le libellé
                    query_lower in p.get('prod', '').lower()]       # Recherche dans le code produit

    # Étape 2 : Filtrage par tags (si des filtres sont actifs)
    if filtres_actifs:
        # Garde le produit si au moins un de ses tags est dans les filtres actifs (OR)
        produits = [
            p for p in produits
            if any(f in p.get('tags', []) for f in filtres_actifs)
        ]

    return produits
