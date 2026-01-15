"""
Service de recommandations basé sur les habitudes d'achat.
"""

from django.db.models import Count, Sum, F
from django.utils import timezone
from datetime import timedelta
from catalogue.models import Produit, Categorie
from .models import HistoriqueAchat, PreferenceCategorie


def obtenir_recommandations(client, limite=8):
    """
    Obtient les recommandations personnalisées pour un client.

    Algorithme:
    1. Produits fréquemment achetés par le client
    2. Produits de ses catégories préférées
    3. Produits populaires auprès de clients similaires
    4. Produits mis en avant

    Args:
        client: Instance Client
        limite: Nombre de recommandations à retourner

    Returns:
        QuerySet de Produit
    """
    recommandations = []
    ids_exclus = set()

    # 1. Produits régulièrement achetés (réassort)
    produits_reguliers = obtenir_produits_reguliers(client, limite=4)
    for p in produits_reguliers:
        if p.id not in ids_exclus:
            recommandations.append(p)
            ids_exclus.add(p.id)

    # 2. Produits des catégories préférées (nouveautés)
    produits_categories = obtenir_produits_categories_preferees(client, ids_exclus, limite=4)
    for p in produits_categories:
        if p.id not in ids_exclus:
            recommandations.append(p)
            ids_exclus.add(p.id)

    # 3. Produits populaires globalement
    if len(recommandations) < limite:
        produits_populaires = obtenir_produits_populaires(ids_exclus, limite=limite - len(recommandations))
        for p in produits_populaires:
            if p.id not in ids_exclus:
                recommandations.append(p)
                ids_exclus.add(p.id)

    # 4. Compléter avec produits mis en avant
    if len(recommandations) < limite:
        produits_avant = Produit.objects.filter(
            actif=True,
            mise_en_avant=True
        ).exclude(id__in=ids_exclus)[:limite - len(recommandations)]
        recommandations.extend(produits_avant)

    return recommandations[:limite]


def obtenir_produits_reguliers(client, limite=4):
    """
    Retourne les produits régulièrement achetés par le client.
    """
    historique = HistoriqueAchat.objects.filter(
        client=client,
        produit__actif=True
    ).select_related('produit').order_by('-nombre_commandes', '-quantite_totale')[:limite]

    return [h.produit for h in historique]


def obtenir_produits_categories_preferees(client, ids_exclus, limite=4):
    """
    Retourne des produits des catégories préférées du client qu'il n'a pas encore achetés.
    """
    # Identifier les catégories préférées
    categories_preferees = HistoriqueAchat.objects.filter(
        client=client
    ).values('produit__categorie').annotate(
        total=Sum('quantite_totale')
    ).order_by('-total')[:3]

    categories_ids = [c['produit__categorie'] for c in categories_preferees if c['produit__categorie']]

    if not categories_ids:
        return []

    # Produits de ces catégories non encore achetés
    produits_achetes = HistoriqueAchat.objects.filter(
        client=client
    ).values_list('produit_id', flat=True)

    produits = Produit.objects.filter(
        actif=True,
        categorie_id__in=categories_ids
    ).exclude(
        id__in=produits_achetes
    ).exclude(
        id__in=ids_exclus
    ).order_by('-mise_en_avant', '?')[:limite]

    return list(produits)


def obtenir_produits_populaires(ids_exclus, limite=4):
    """
    Retourne les produits les plus populaires globalement.
    """
    produits_populaires = HistoriqueAchat.objects.values('produit').annotate(
        total_clients=Count('client', distinct=True),
        total_quantite=Sum('quantite_totale')
    ).order_by('-total_clients', '-total_quantite')[:limite * 2]

    ids_populaires = [p['produit'] for p in produits_populaires]

    return Produit.objects.filter(
        id__in=ids_populaires,
        actif=True
    ).exclude(id__in=ids_exclus)[:limite]


def mettre_a_jour_historique_commande(commande):
    """
    Met à jour l'historique des achats après une commande.

    Args:
        commande: Instance Commande
    """
    for ligne in commande.lignes.all():
        HistoriqueAchat.enregistrer_achat(
            client=commande.client,
            produit=ligne.produit,
            quantite=ligne.quantite
        )


def calculer_preferences_categories(client):
    """
    Calcule et met à jour les préférences de catégories pour un client.
    """
    # Calculer les scores par catégorie
    stats = HistoriqueAchat.objects.filter(
        client=client
    ).values('produit__categorie').annotate(
        score=Sum('quantite_totale') * Count('produit', distinct=True)
    )

    # Mettre à jour les préférences
    for stat in stats:
        if stat['produit__categorie']:
            PreferenceCategorie.objects.update_or_create(
                client=client,
                categorie_id=stat['produit__categorie'],
                defaults={'score': stat['score']}
            )


def obtenir_produits_complementaires(produit, limite=4):
    """
    Retourne des produits souvent achetés avec le produit donné.
    """
    # Clients ayant acheté ce produit
    clients_ayant_achete = HistoriqueAchat.objects.filter(
        produit=produit
    ).values_list('client_id', flat=True)

    # Autres produits achetés par ces clients
    produits_associes = HistoriqueAchat.objects.filter(
        client_id__in=clients_ayant_achete
    ).exclude(
        produit=produit
    ).values('produit').annotate(
        score=Count('client')
    ).order_by('-score')[:limite]

    ids = [p['produit'] for p in produits_associes]
    return Produit.objects.filter(id__in=ids, actif=True)
