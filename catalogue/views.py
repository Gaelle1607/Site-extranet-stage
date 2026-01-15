from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import Http404
from .services import get_produits_client, get_categories_client, get_produit_by_reference


@login_required
def liste_produits(request):
    """Liste des produits pour le client connecté"""
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

    context = {
        'produits': produits,
        'categories': categories,
        'categorie_active': categorie,
        'recherche': request.GET.get('q', ''),
    }
    return render(request, 'catalogue/liste.html', context)


@login_required
def detail_produit(request, reference):
    """Détail d'un produit"""
    client = request.user.client
    produit = get_produit_by_reference(client, reference)

    if not produit:
        raise Http404("Produit non trouvé")

    context = {
        'produit': produit,
    }
    return render(request, 'catalogue/detail.html', context)
