"""
Service de recommandations basé sur les habitudes d'achat.

Les produits viennent d'une source externe via catalogue.services,
donc ce service travaille avec des références produit (string).
"""

from django.db.models import Count, Sum
from .models import HistoriqueAchat, PreferenceCategorie
from catalogue.services import get_produits_client, get_produit_by_reference


def obtenir_produits_favoris(client, limite=4):
    """
    Retourne les produits les plus commandés par le client.

    Args:
        client: Instance Client
        limite: Nombre de produits à retourner

    Returns:
        Liste de dictionnaires produit
    """
    # Récupérer l'historique des achats du client
    historique = HistoriqueAchat.objects.filter(
        client=client
    ).order_by('-nombre_commandes', '-quantite_totale')[:limite]

    produits_favoris = []
    for h in historique:
        produit = get_produit_by_reference(client, h.reference_produit)
        if produit:
            produits_favoris.append(produit)

    return produits_favoris


def obtenir_recommandations(client, limite=8):
    """
    Obtient les recommandations personnalisées pour un client.

    Algorithme:
    1. Produits fréquemment achetés par le client
    2. Produits de ses catégories préférées
    3. Produits populaires globalement

    Args:
        client: Instance Client
        limite: Nombre de recommandations à retourner

    Returns:
        Liste de dictionnaires produit
    """
    recommandations = []
    refs_exclus = set()

    # 1. Produits régulièrement achetés (réassort)
    produits_reguliers = obtenir_produits_favoris(client, limite=4)
    for p in produits_reguliers:
        if p['reference'] not in refs_exclus:
            recommandations.append(p)
            refs_exclus.add(p['reference'])

    # 2. Produits des catégories préférées
    if len(recommandations) < limite:
        produits_categories = obtenir_produits_categories_preferees(client, refs_exclus, limite=4)
        for p in produits_categories:
            if p['reference'] not in refs_exclus and len(recommandations) < limite:
                recommandations.append(p)
                refs_exclus.add(p['reference'])

    # 3. Compléter avec d'autres produits disponibles
    if len(recommandations) < limite:
        tous_produits = get_produits_client(client)
        for p in tous_produits:
            if p['reference'] not in refs_exclus and len(recommandations) < limite:
                recommandations.append(p)
                refs_exclus.add(p['reference'])

    return recommandations[:limite]


def obtenir_produits_categories_preferees(client, refs_exclus, limite=4):
    """
    Retourne des produits des catégories préférées du client.
    """
    # Identifier les catégories préférées
    categories_preferees = HistoriqueAchat.objects.filter(
        client=client
    ).exclude(categorie='').values('categorie').annotate(
        total=Sum('quantite_totale')
    ).order_by('-total')[:3]

    categories_noms = [c['categorie'] for c in categories_preferees]

    if not categories_noms:
        return []

    # Récupérer tous les produits et filtrer par catégorie
    tous_produits = get_produits_client(client)
    produits = []
    for p in tous_produits:
        # Vérifier si au moins une catégorie du produit est dans les catégories préférées
        produit_categories = p.get('categories', [])
        if (any(cat in categories_noms for cat in produit_categories) and
                p['reference'] not in refs_exclus and
                len(produits) < limite):
            produits.append(p)

    return produits


def mettre_a_jour_historique_commande(client, lignes_panier):
    """
    Met à jour l'historique des achats après une commande.

    Args:
        client: Instance Client
        lignes_panier: Liste de dict avec 'reference', 'quantite', 'produit'
    """
    for ligne in lignes_panier:
        # Prendre la première catégorie du produit (ou chaîne vide si pas de catégories)
        produit = ligne.get('produit', {})
        categories = produit.get('categories', [])
        categorie = categories[0] if categories else ''
        HistoriqueAchat.enregistrer_achat(
            client=client,
            reference_produit=ligne['reference'],
            quantite=ligne['quantite'],
            categorie=categorie
        )


def calculer_preferences_categories(client):
    """
    Calcule et met à jour les préférences de catégories pour un client.
    """
    # Calculer les scores par catégorie
    stats = HistoriqueAchat.objects.filter(
        client=client
    ).exclude(categorie='').values('categorie').annotate(
        total_quantite=Sum('quantite_totale'),
        nb_produits=Count('reference_produit', distinct=True)
    )

    # Mettre à jour les préférences
    for stat in stats:
        score = stat['total_quantite'] * stat['nb_produits']
        PreferenceCategorie.objects.update_or_create(
            client=client,
            categorie=stat['categorie'],
            defaults={'score': score}
        )
