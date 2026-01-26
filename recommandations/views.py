from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .services import obtenir_recommandations, obtenir_produits_favoris
from catalogue.services import get_categories_client, get_produit_by_reference


@login_required
def mes_recommandations(request):
    """Page des recommandations personnalisées"""
    if not hasattr(request.user, 'utilisateur'):
        messages.error(request, "Votre compte n'est pas associé à un profil utilisateur.")
        return redirect('clients:connexion')

    utilisateur = request.user.utilisateur
    recommandations = obtenir_recommandations(utilisateur, limite=12)
    categories = get_categories_client(utilisateur)

    # Récupérer le panier pour le récap
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

    context = {
        'recommandations': recommandations,
        'categories': categories,
        'lignes_panier': lignes_panier,
        'total_panier': total_panier,
    }
    return render(request, 'cote_client/recommandations/liste.html', context)


@login_required
def api_recommandations(request):
    """API pour obtenir les recommandations en JSON"""
    if not hasattr(request.user, 'utilisateur'):
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)

    utilisateur = request.user.utilisateur
    limite = int(request.GET.get('limite', 10))
    recommandations = obtenir_recommandations(utilisateur, limite=limite)

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
    """API pour obtenir les produits favoris en JSON"""
    if not hasattr(request.user, 'utilisateur'):
        return JsonResponse({'error': 'Utilisateur non trouvé'}, status=404)

    utilisateur = request.user.utilisateur
    limite = int(request.GET.get('limite', 4))
    favoris = obtenir_produits_favoris(utilisateur, limite=limite)

    data = []
    for produit in favoris:
        data.append({
            'reference': produit['reference'],
            'nom': produit['nom'],
            'prix': float(produit['prix']),
        })

    return JsonResponse({'favoris': data})
