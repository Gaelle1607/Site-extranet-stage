from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from .services import get_produits_client, get_categories_client, get_produit_by_reference


@login_required
def liste_produits(request):
    """Liste des produits pour le client connecté"""
    if not hasattr(request.user, 'client'):
        messages.error(request, "Votre compte n'est pas associé à un profil client. Contactez l'administrateur.")
        return redirect('clients:connexion')
    client = request.user.client
    produits = get_produits_client(client)
    categories = get_categories_client(client)

    # Filtrer par catégorie
    categorie = request.GET.get('categorie')
    if categorie:
        produits = [p for p in produits if p.get('categorie') == categorie]

    # Recherche
    recherche = request.GET.get('q', '').strip().lower()
    if recherche:
        produits = [p for p in produits if
                    recherche in p.get('nom', '').lower() or
                    recherche in p.get('reference', '').lower()]

    # Séparer les produits favoris (nb_commandes >= 5)
    # Uniquement si pas de filtre actif
    produits_favoris = []
    if not categorie and not recherche:
        produits_favoris = [p for p in produits if p.get('nb_commandes', 0) >= 5]
        # Trier par nombre de commandes décroissant
        produits_favoris = sorted(produits_favoris, key=lambda x: x.get('nb_commandes', 0), reverse=True)
        # Limiter à 4 favoris max
        produits_favoris = produits_favoris[:4]
        # Retirer les favoris de la liste principale
        refs_favoris = {p['reference'] for p in produits_favoris}
        produits = [p for p in produits if p['reference'] not in refs_favoris]

    # Récupérer le panier pour le récap
    panier = request.session.get('panier', {})
    lignes_panier = []
    total_panier = 0
    for reference, quantite in panier.items():
        produit = get_produit_by_reference(client, reference)
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

    context = {
        'produits': produits,
        'produits_favoris': produits_favoris,
        'categories': categories,
        'categorie_active': categorie,
        'recherche': request.GET.get('q', ''),
        'lignes_panier': lignes_panier,
        'total_panier': total_panier,
    }
    return render(request, 'catalogue/liste.html', context)


@login_required
def favoris(request):
    """Liste des produits favoris (les plus commandés)"""
    if not hasattr(request.user, 'client'):
        messages.error(request, "Votre compte n'est pas associé à un profil client. Contactez l'administrateur.")
        return redirect('clients:connexion')
    client = request.user.client
    produits = get_produits_client(client)
    categories = get_categories_client(client)
    
    # Filtrer les produits favoris (nb_commandes >= 5)
    produits_favoris = [p for p in produits if p.get('nb_commandes', 0) >= 5]
    # Trier par nombre de commandes décroissant
    produits_favoris = sorted(produits_favoris, key=lambda x: x.get('nb_commandes', 0), reverse=True)
    
    # Filtrer par catégorie
    categorie = request.GET.get('categorie')
    if categorie:
        produits_favoris = [p for p in produits_favoris if p.get('categorie') == categorie]

    # Recherche
    recherche = request.GET.get('q', '').strip().lower()
    if recherche:
        produits_favoris = [p for p in produits_favoris if
                    recherche in p.get('nom', '').lower() or
                    recherche in p.get('reference', '').lower()]
    
    # Récupérer le panier pour le récap
    panier = request.session.get('panier', {})
    lignes_panier = []
    total_panier = 0
    for reference, quantite in panier.items():
        produit = get_produit_by_reference(client, reference)
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

    context = {
        'produits_favoris': produits_favoris,
        'categories': categories,
        'categorie_active': categorie,
        'recherche': request.GET.get('q', ''),
        'lignes_panier': lignes_panier,
        'total_panier': total_panier,
        'page_title': 'Favoris',
    }
    return render(request, 'catalogue/favoris.html', context)


@login_required
def detail_produit(request, reference):
    """Détail d'un produit"""
    if not hasattr(request.user, 'client'):
        messages.error(request, "Votre compte n'est pas associé à un profil client.")
        return redirect('clients:connexion')
    client = request.user.client
    produit = get_produit_by_reference(client, reference)

    if not produit:
        raise Http404("Produit non trouvé")

    context = {
        'produit': produit,
    }
    return render(request, 'catalogue/detail.html', context)
