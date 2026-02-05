"""
=============================================================================
LISTE_COMMANDE.PY - Vue de la liste des commandes
=============================================================================

Affiche la liste de toutes les commandes passées via l'extranet.
Permet la recherche par numéro de commande ou code client.

Fonctionnalités :
    - Liste paginée des 50 dernières commandes
    - Recherche par numéro de commande ou code tiers
    - Affichage du nom du client depuis la base distante

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render
from django.db.models import Q

from commandes.models import Commande
from .decorators import admin_required


@admin_required
def liste_commande(request):
    """
    Affiche la liste des commandes avec fonction de recherche.

    La liste est triée par date décroissante (plus récentes en premier)
    et limitée aux 50 dernières commandes pour des raisons de performance.

    La recherche s'effectue sur :
    - Le numéro de commande (recherche partielle)
    - Le code tiers du client (recherche partielle)

    Args:
        request: L'objet HttpRequest Django
            - GET['q'] : Terme de recherche (optionnel)

    Returns:
        HttpResponse: La page liste_commandes.html avec :
            - commandes : Liste des commandes enrichies du nom client
            - query : Le terme de recherche saisi
    """
    # Récupérer toutes les commandes, triées par date décroissante
    commandes = Commande.objects.all().order_by('-date_commande')

    # Appliquer la recherche si un terme est fourni
    query = request.GET.get('q', '')
    if query:
        commandes = commandes.filter(
            Q(numero__icontains=query) |                    # Recherche dans le numéro
            Q(utilisateur__code_tiers__icontains=query)     # Recherche dans le code tiers
        )

    # Limiter aux 50 premières pour optimiser les performances
    commandes = commandes[:50]

    # Enrichir chaque commande avec le nom du client depuis la base distante
    commandes_avec_client = []
    for commande in commandes:
        client = commande.utilisateur.get_client_distant()
        commandes_avec_client.append({
            'commande': commande,
            'nom_client': client.nom if client else f"Client {commande.utilisateur.code_tiers}",
        })

    context = {
        'page_title': 'Liste des commandes',
        'commandes': commandes_avec_client,
        'query': query,
    }
    return render(request, 'administration/liste_commandes.html', context)
