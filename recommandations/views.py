"""
=============================================================================
VIEWS.PY - Vues de l'application Recommandations
=============================================================================

Ce module contient les vues Django pour le système de recommandations
personnalisées basé sur l'historique d'achat des clients.

Fonctionnalités principales :
    - Affichage des recommandations personnalisées
    - API REST pour accès aux recommandations en JSON
    - API REST pour accès aux produits favoris en JSON

Architecture :
    - Utilise le service services.py pour le calcul des recommandations
    - Partage le système de filtres avec l'application catalogue
    - Les données produits viennent de la base distante LogiGVD

Algorithme de recommandation :
    1. Produits régulièrement achetés (réassort)
    2. Produits des catégories préférées de l'utilisateur
    3. Complétion avec d'autres produits disponibles

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .services import obtenir_recommandations, obtenir_produits_favoris
from catalogue.services import get_categories_client, get_produit_by_reference
from administration.views.filtres import preparer_filtres, appliquer_filtres


@login_required
def mes_recommandations(request):
    """
    Affiche la page des recommandations personnalisées.

    Cette vue est la page d'accueil après connexion. Elle présente
    les produits recommandés pour l'utilisateur basés sur son
    historique d'achat et ses préférences de catégories.

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - GET['filtre'] : Liste des filtres actifs (optionnel)
            - GET['q'] : Terme de recherche (optionnel)
            - session['panier'] : Contenu du panier en cours

    Returns:
        HttpResponse:
            - Si pas de profil utilisateur : Redirection vers 'clients:connexion'
            - Sinon : Rendu du template 'cote_client/recommandations/liste.html'
              avec le contexte :
              - recommandations : Liste des produits recommandés
              - categories : Catégories disponibles pour l'utilisateur
              - filtres_groupes : Groupes de filtres disponibles
              - filtres_actifs : Filtres actuellement appliqués
              - recherche : Terme de recherche actuel
              - lignes_panier : Détail des lignes du panier
              - total_panier : Montant total du panier

    Note:
        Les recommandations sont calculées dynamiquement à chaque affichage.
        Le seuil de 2 occurrences pour les filtres automatiques est plus
        bas que pour le catalogue car il y a moins de produits affichés.
    """
    # Vérification du profil utilisateur
    if not hasattr(request.user, 'utilisateur'):
        messages.error(
            request,
            "Votre compte n'est pas associé à un profil utilisateur."
        )
        return redirect('clients:connexion')

    utilisateur = request.user.utilisateur

    # =========================================================================
    # CALCUL DES RECOMMANDATIONS
    # =========================================================================
    # Obtention des 12 produits recommandés via l'algorithme du service
    recommandations = obtenir_recommandations(utilisateur, limite=12)
    categories = get_categories_client(utilisateur)

    # =========================================================================
    # PRÉPARATION DES FILTRES
    # =========================================================================
    # Application du même système de filtrage que le catalogue
    # Seuil réduit à 2 car moins de produits à filtrer
    recommandations, filtres_groupes, _ = preparer_filtres(
        recommandations,
        seuil_occurrences=2
    )

    # Récupération des paramètres de filtrage depuis l'URL
    filtres_actifs = request.GET.getlist("filtre")
    recherche = request.GET.get('q', '').strip()

    # Application des filtres et de la recherche
    recommandations = appliquer_filtres(recommandations, filtres_actifs, recherche)

    # =========================================================================
    # RÉCUPÉRATION DU PANIER POUR LE RÉCAPITULATIF
    # =========================================================================
    # Le récapitulatif du panier est affiché dans le bandeau latéral
    panier = request.session.get('panier', {})
    lignes_panier = []
    total_panier = 0

    for reference, quantite in panier.items():
        produit = get_produit_by_reference(utilisateur, reference)
        if produit:
            ligne_total = produit['prix'] * quantite
            lignes_panier.append({
                'reference': reference,
                'nom': produit['nom'],
                'quantite': quantite,
                'prix': produit['prix'],
                'total': ligne_total,
            })
            total_panier += ligne_total

    # Préparation du contexte pour le template
    context = {
        'recommandations': recommandations,
        'categories': categories,
        'filtres_groupes': filtres_groupes,
        'filtres_actifs': filtres_actifs,
        'recherche': request.GET.get('q', ''),
        'lignes_panier': lignes_panier,
        'total_panier': total_panier,
    }
    return render(request, 'cote_client/recommandations/liste.html', context)


@login_required
def api_recommandations(request):
    """
    API REST pour obtenir les recommandations en format JSON.

    Cette vue fournit les recommandations personnalisées au format JSON,
    utilisable par des applications front-end JavaScript ou des
    applications tierces.

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - GET['limite'] : Nombre de recommandations (défaut = 10)

    Returns:
        JsonResponse:
            - Si pas de profil : {'error': 'Utilisateur non trouvé'}, status=404
            - Sinon : {'recommandations': [
                {
                    'reference': str,
                    'nom': str,
                    'prix': float,
                    'stock': int
                },
                ...
              ]}

    Exemple d'utilisation JavaScript :
        fetch('/recommandations/api/?limite=5')
            .then(response => response.json())
            .then(data => console.log(data.recommandations));
    """
    # Vérification du profil utilisateur
    if not hasattr(request.user, 'utilisateur'):
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)

    utilisateur = request.user.utilisateur

    # Récupération du paramètre de limite
    limite = int(request.GET.get('limite', 10))

    # Obtention des recommandations
    recommandations = obtenir_recommandations(utilisateur, limite=limite)

    # Formatage des données pour la réponse JSON
    data = []
    for produit in recommandations:
        data.append({
            'reference': produit['reference'],
            'nom': produit['nom'],
            'prix': float(produit['prix']),
            'stock': produit.get('stock', 0),
        })

    return JsonResponse({'recommandations': data})


@login_required
def api_produits_favoris(request):
    """
    API REST pour obtenir les produits favoris en format JSON.

    Cette vue retourne les produits les plus commandés par l'utilisateur,
    utile pour afficher une section "Mes favoris" ou "Recommander".

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - GET['limite'] : Nombre de favoris (défaut = 4)

    Returns:
        JsonResponse:
            - Si pas de profil : {'error': 'Utilisateur non trouvé'}, status=404
            - Sinon : {'favoris': [
                {
                    'reference': str,
                    'nom': str,
                    'prix': float
                },
                ...
              ]}

    Note:
        Les favoris sont triés par nombre de commandes décroissant,
        puis par quantité totale commandée décroissante.
    """
    # Vérification du profil utilisateur
    if not hasattr(request.user, 'utilisateur'):
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)

    utilisateur = request.user.utilisateur

    # Récupération du paramètre de limite
    limite = int(request.GET.get('limite', 4))

    # Obtention des produits favoris
    favoris = obtenir_produits_favoris(utilisateur, limite=limite)

    # Formatage des données pour la réponse JSON
    data = []
    for produit in favoris:
        data.append({
            'reference': produit['reference'],
            'nom': produit['nom'],
            'prix': float(produit['prix']),
        })

    return JsonResponse({'favoris': data})
