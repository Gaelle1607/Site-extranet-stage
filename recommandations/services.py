"""
=============================================================================
SERVICES.PY - Services de l'application Recommandations
=============================================================================

Ce module contient la logique métier du système de recommandations
personnalisées basé sur les habitudes d'achat des clients.

Fonctions principales :
    - obtenir_produits_favoris : Récupère les produits les plus commandés
    - obtenir_recommandations : Calcule les recommandations personnalisées
    - obtenir_produits_categories_preferees : Filtre par catégories préférées
    - mettre_a_jour_historique_commande : Met à jour l'historique après achat
    - calculer_preferences_categories : Calcule les scores de préférence

Architecture :
    - Les produits proviennent de la base externe via catalogue.services
    - L'historique d'achat est stocké localement dans la base Django
    - Les recommandations sont calculées dynamiquement à chaque requête

Projet : Extranet Giffaud Groupe
=============================================================================
"""

from django.db.models import Count, Sum
from .models import HistoriqueAchat, PreferenceCategorie
from catalogue.services import get_produits_client, get_produit_by_reference


def obtenir_produits_favoris(utilisateur, limite=4):
    """
    Retourne les produits les plus commandés par l'utilisateur.

    Cette fonction identifie les produits régulièrement commandés
    par l'utilisateur en se basant sur le nombre de commandes et
    la quantité totale achetée.

    Args:
        utilisateur (Utilisateur): Instance de l'utilisateur concerné
        limite (int): Nombre maximum de produits à retourner (défaut = 4)

    Returns:
        list: Liste de dictionnaires produit avec les informations complètes
              provenant de la base distante. Liste vide si pas d'historique.

    Tri:
        1. Par nombre de commandes décroissant
        2. Puis par quantité totale décroissante

    Exemple:
        >>> favoris = obtenir_produits_favoris(utilisateur, limite=4)
        >>> for p in favoris:
        ...     print(f"{p['nom']} - {p['prix']}€")
    """
    # Récupération de l'historique trié par fréquence d'achat
    historique = HistoriqueAchat.objects.filter(
        utilisateur=utilisateur
    ).order_by('-nombre_commandes', '-quantite_totale')[:limite]

    # Enrichissement avec les données produit de la base distante
    produits_favoris = []
    for h in historique:
        produit = get_produit_by_reference(utilisateur, h.reference_produit)
        if produit:
            produits_favoris.append(produit)

    return produits_favoris


def obtenir_recommandations(utilisateur, limite=8):
    """
    Obtient les recommandations personnalisées pour un utilisateur.

    Cette fonction implémente l'algorithme de recommandation en trois
    étapes pour proposer les produits les plus pertinents à l'utilisateur.

    Algorithme :
        1. Produits fréquemment achetés (réassort) - ~50% des recommandations
           Suggère de recommander des produits habituellement commandés.

        2. Produits des catégories préférées - ~25% des recommandations
           Découverte de nouveaux produits dans les catégories appréciées.

        3. Produits populaires globalement - Complément si nécessaire
           Produits disponibles non encore essayés par l'utilisateur.

    Args:
        utilisateur (Utilisateur): Instance de l'utilisateur concerné
        limite (int): Nombre maximum de recommandations (défaut = 8)

    Returns:
        list: Liste de dictionnaires produit avec informations complètes.
              La liste est garantie de ne pas contenir de doublons.

    Note:
        L'ensemble refs_exclus évite les doublons entre les différentes
        sources de recommandations.
    """
    recommandations = []
    refs_exclus = set()  # Pour éviter les doublons

    # =========================================================================
    # ÉTAPE 1 : Produits régulièrement achetés (réassort)
    # =========================================================================
    # Ces produits sont ceux que l'utilisateur commande le plus souvent
    produits_reguliers = obtenir_produits_favoris(utilisateur, limite=4)
    for p in produits_reguliers:
        if p['reference'] not in refs_exclus:
            recommandations.append(p)
            refs_exclus.add(p['reference'])

    # =========================================================================
    # ÉTAPE 2 : Produits des catégories préférées
    # =========================================================================
    # Découverte de nouveaux produits dans les catégories appréciées
    if len(recommandations) < limite:
        produits_categories = obtenir_produits_categories_preferees(
            utilisateur,
            refs_exclus,
            limite=4
        )
        for p in produits_categories:
            if p['reference'] not in refs_exclus and len(recommandations) < limite:
                recommandations.append(p)
                refs_exclus.add(p['reference'])

    # =========================================================================
    # ÉTAPE 3 : Compléter avec d'autres produits disponibles
    # =========================================================================
    # Si on n'a pas assez de recommandations, on complète avec le catalogue
    if len(recommandations) < limite:
        tous_produits = get_produits_client(utilisateur)
        for p in tous_produits:
            if p['reference'] not in refs_exclus and len(recommandations) < limite:
                recommandations.append(p)
                refs_exclus.add(p['reference'])

    return recommandations[:limite]


def obtenir_produits_categories_preferees(utilisateur, refs_exclus, limite=4):
    """
    Retourne des produits des catégories préférées de l'utilisateur.

    Cette fonction identifie les catégories les plus achetées par
    l'utilisateur et retourne des produits de ces catégories qu'il
    n'a pas encore commandés.

    Args:
        utilisateur (Utilisateur): Instance de l'utilisateur concerné
        refs_exclus (set): Ensemble des références à exclure (déjà recommandées)
        limite (int): Nombre maximum de produits à retourner (défaut = 4)

    Returns:
        list: Liste de dictionnaires produit des catégories préférées.
              Liste vide si pas de catégories identifiées.

    Calcul des catégories préférées :
        On agrège les quantités totales par catégorie depuis l'historique
        d'achat et on prend les 3 catégories avec le plus grand total.
    """
    # Identification des catégories les plus achetées
    categories_preferees = HistoriqueAchat.objects.filter(
        utilisateur=utilisateur
    ).exclude(
        categorie=''  # Exclure les produits sans catégorie
    ).values('categorie').annotate(
        total=Sum('quantite_totale')
    ).order_by('-total')[:3]

    categories_noms = [c['categorie'] for c in categories_preferees]

    if not categories_noms:
        return []

    # Récupération des produits et filtrage par catégorie
    tous_produits = get_produits_client(utilisateur)
    produits = []

    for p in tous_produits:
        # Vérification si le produit appartient à une catégorie préférée
        produit_categories = p.get('categories', [])
        if (any(cat in categories_noms for cat in produit_categories) and
                p['reference'] not in refs_exclus and
                len(produits) < limite):
            produits.append(p)

    return produits


def mettre_a_jour_historique_commande(utilisateur, lignes_panier):
    """
    Met à jour l'historique des achats après une commande validée.

    Cette fonction doit être appelée lors de la validation d'une commande
    pour enregistrer les achats et permettre le calcul des recommandations
    futures.

    Args:
        utilisateur (Utilisateur): Instance de l'utilisateur qui a commandé
        lignes_panier (list): Liste de dictionnaires avec :
            - 'reference' (str): Référence du produit
            - 'quantite' (int): Quantité commandée
            - 'produit' (dict, optionnel): Informations produit avec 'categories'

    Exemple:
        >>> lignes = [
        ...     {'reference': 'PROD001', 'quantite': 5, 'produit': {'categories': ['Viandes']}},
        ...     {'reference': 'PROD002', 'quantite': 3}
        ... ]
        >>> mettre_a_jour_historique_commande(utilisateur, lignes)

    Note:
        Si le produit n'a pas de catégories définies, une chaîne vide
        est utilisée. La catégorie sera mise à jour lors d'un prochain
        achat si elle est fournie.
    """
    for ligne in lignes_panier:
        # Extraction de la première catégorie du produit (ou chaîne vide)
        produit = ligne.get('produit', {})
        categories = produit.get('categories', [])
        categorie = categories[0] if categories else ''

        # Enregistrement ou mise à jour de l'historique
        HistoriqueAchat.enregistrer_achat(
            utilisateur=utilisateur,
            reference_produit=ligne['reference'],
            quantite=ligne['quantite'],
            categorie=categorie
        )


def calculer_preferences_categories(utilisateur):
    """
    Calcule et met à jour les préférences de catégories pour un utilisateur.

    Cette fonction agrège les statistiques d'achat par catégorie et
    calcule un score de préférence pour chaque catégorie. Le score
    peut être utilisé pour affiner les recommandations.

    Args:
        utilisateur (Utilisateur): Instance de l'utilisateur concerné

    Calcul du score :
        score = quantité_totale × nombre_produits_distincts

        Ce calcul favorise les catégories où l'utilisateur :
        - Achète en grande quantité (fidélité)
        - Achète des produits variés (intérêt pour la catégorie)

    Exemple:
        Si l'utilisateur a acheté :
        - Catégorie "Viandes" : 100 unités sur 5 produits → score = 500
        - Catégorie "Charcuterie" : 50 unités sur 2 produits → score = 100
        Les viandes seront la catégorie préférée.

    Note:
        Les préférences sont créées ou mises à jour automatiquement
        via update_or_create(). Les produits sans catégorie sont exclus.
    """
    # Agrégation des statistiques par catégorie
    stats = HistoriqueAchat.objects.filter(
        utilisateur=utilisateur
    ).exclude(
        categorie=''  # Exclure les produits sans catégorie
    ).values('categorie').annotate(
        total_quantite=Sum('quantite_totale'),
        nb_produits=Count('reference_produit', distinct=True)
    )

    # Mise à jour des préférences
    for stat in stats:
        # Calcul du score de préférence
        score = stat['total_quantite'] * stat['nb_produits']

        # Création ou mise à jour de l'enregistrement
        PreferenceCategorie.objects.update_or_create(
            utilisateur=utilisateur,
            categorie=stat['categorie'],
            defaults={'score': score}
        )
