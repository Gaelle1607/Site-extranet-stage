from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .services import obtenir_recommandations, obtenir_produits_complementaires


@login_required
def mes_recommandations(request):
    """Page des recommandations personnalisées"""
    client = request.user.client
    recommandations = obtenir_recommandations(client, limite=12)

    # Ajouter le prix client
    for produit in recommandations:
        produit.prix_client = produit.get_prix_client(client)

    context = {
        'recommandations': recommandations,
    }
    return render(request, 'recommandations/liste.html', context)


@login_required
def api_recommandations(request):
    """API pour obtenir les recommandations en JSON"""
    client = request.user.client
    limite = int(request.GET.get('limite', 8))
    recommandations = obtenir_recommandations(client, limite=limite)

    data = []
    for produit in recommandations:
        data.append({
            'id': produit.id,
            'reference': produit.reference,
            'nom': produit.nom,
            'prix_client': float(produit.get_prix_client(client)),
            'image': produit.image.url if produit.image else None,
            'en_stock': produit.en_stock,
        })

    return JsonResponse({'recommandations': data})


@login_required
def api_produits_complementaires(request, produit_id):
    """API pour obtenir les produits complémentaires"""
    from catalogue.models import Produit
    from django.shortcuts import get_object_or_404

    client = request.user.client
    produit = get_object_or_404(Produit, pk=produit_id)
    complementaires = obtenir_produits_complementaires(produit, limite=4)

    data = []
    for p in complementaires:
        data.append({
            'id': p.id,
            'reference': p.reference,
            'nom': p.nom,
            'prix_client': float(p.get_prix_client(client)),
            'image': p.image.url if p.image else None,
        })

    return JsonResponse({'produits': data})
