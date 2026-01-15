def panier_count(request):
    """Context processor pour afficher le nombre d'articles dans le panier"""
    count = 0
    if request.user.is_authenticated:
        panier = request.session.get('panier', {})
        count = sum(panier.values())
    return {'panier_count': count}
