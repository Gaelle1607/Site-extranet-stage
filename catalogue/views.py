from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.db.models import Sum
from decimal import Decimal
from .services import get_produits_client, get_categories_client, get_produit_by_reference, get_client_distant
from commandes.models import Commande, LigneCommande


@login_required
def liste_produits(request):
    """Liste des produits pour le client connecté"""
    if not hasattr(request.user, 'utilisateur'):
        messages.error(request, "Votre compte n'est pas associé à un profil utilisateur. Contactez l'administrateur.")
        return redirect('clients:connexion')
    utilisateur = request.user.utilisateur
    produits = get_produits_client(utilisateur)
    categories = get_categories_client(utilisateur)

    # Filtrer par catégorie
    categorie = request.GET.get('categorie')
    if categorie:
        produits = [p for p in produits if categorie in p.get('categories', [])]

    # Recherche
    recherche = request.GET.get('q', '').strip().lower()
    if recherche:
        produits = [p for p in produits if
                    recherche in p.get('nom', '').lower() or
                    recherche in p.get('reference', '').lower()]

    # Top 4 des produits les plus commandés sur le site (commandes locales)
    produits_favoris = []
    if not categorie and not recherche:
        top_references = (
            LigneCommande.objects
            .filter(commande__utilisateur=utilisateur)
            .values('reference_produit')
            .annotate(total_commande=Sum('quantite'))
            .order_by('-total_commande')[:4]
        )
        for entry in top_references:
            produit = get_produit_by_reference(utilisateur, entry['reference_produit'])
            if produit:
                produits_favoris.append(produit)
        # Retirer les favoris de la liste principale
        refs_favoris = {p['reference'] for p in produits_favoris}
        produits = [p for p in produits if p['reference'] not in refs_favoris]

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
        'produits': produits,
        'produits_favoris': produits_favoris,
        'categories': categories,
        'categorie_active': categorie,
        'recherche': request.GET.get('q', ''),
        'lignes_panier': lignes_panier,
        'total_panier': total_panier,
    }
    return render(request, 'cote_client/catalogue/liste.html', context)


@login_required
def favoris(request):
    """Liste des produits favoris (les plus commandés)"""
    if not hasattr(request.user, 'utilisateur'):
        messages.error(request, "Votre compte n'est pas associé à un profil utilisateur. Contactez l'administrateur.")
        return redirect('clients:connexion')
    utilisateur = request.user.utilisateur

    # Top 10 des produits les plus commandés sur le site par cet utilisateur
    top_references = (
        LigneCommande.objects
        .filter(commande__utilisateur=utilisateur)
        .values('reference_produit')
        .annotate(total_commande=Sum('quantite'))
        .order_by('-total_commande')[:10]
    )

    # Récupérer les infos complètes de chaque produit
    produits_favoris = []
    for entry in top_references:
        produit = get_produit_by_reference(utilisateur, entry['reference_produit'])
        if produit:
            produit['total_commande'] = entry['total_commande']
            produits_favoris.append(produit)

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
        'produits_favoris': produits_favoris,
        'recherche': request.GET.get('q', ''),
        'lignes_panier': lignes_panier,
        'total_panier': total_panier,
        'page_title': 'Favoris',
    }
    return render(request, 'cote_client/catalogue/favoris.html', context)


@login_required
def detail_produit(request, reference):
    """Détail d'un produit"""
    if not hasattr(request.user, 'utilisateur'):
        messages.error(request, "Votre compte n'est pas associé à un profil utilisateur.")
        return redirect('clients:connexion')
    utilisateur = request.user.utilisateur
    produit = get_produit_by_reference(utilisateur, reference)

    if not produit:
        raise Http404("Produit non trouvé")

    context = {
        'produit': produit,
    }
    return render(request, 'cote_client/catalogue/detail.html', context)

def mentions_legales(request):
    """Page des mentions légales"""
    return render(request, 'cote_client/mention_legale.html')

@login_required
def commander(request):
    utilisateur = request.user.utilisateur
    client_distant = get_client_distant(utilisateur.code_tiers)
    produits = get_produits_client(utilisateur)

    if request.method == 'POST':
        # Récupérer les quantités
        lignes = []
        total = 0

        for produit in produits:
            qte_key = f"qte_{produit['reference']}"
            quantite = int(request.POST.get(qte_key, 0))

            if quantite > 0:
                ligne_total = produit['prix'] * quantite
                lignes.append({
                    'reference': produit['reference'],
                    'nom': produit['nom'],
                    'prix': produit['prix'],
                    'quantite': quantite,
                    'total': ligne_total,
                })
                total += ligne_total

        if not lignes:
            messages.warning(request, 'Veuillez sélectionner au moins un produit.')
            return redirect('catalogue:commander')

        # Récupérer les commentaires et la date de livraison
        commentaires = request.POST.get('commentaires', '')
        date_livraison = request.POST.get('date_livraison') or None

        # Créer la commande
        commande = Commande.objects.create(
            utilisateur=utilisateur,
            numero=Commande.generer_numero(),
            date_livraison=date_livraison,
            total_ht=Decimal(str(total)),
            commentaire=commentaires,
            statut='en_attente'
        )

        # Créer les lignes de commande
        for ligne in lignes:
            LigneCommande.objects.create(
                commande=commande,
                reference_produit=ligne['reference'],
                nom_produit=ligne['nom'],
                quantite=ligne['quantite'],
                prix_unitaire=Decimal(str(ligne['prix'])),
                total_ligne=Decimal(str(ligne['total']))
            )

        messages.success(request, f'Votre commande n°{commande.numero} a été envoyée avec succès !')
        return redirect('commandes:confirmation')

    # Pré-remplir avec les quantités du panier
    panier = request.session.get('panier', {})
    for produit in produits:
        produit['panier_qte'] = panier.get(produit['reference'], 0)

    context = {
        'client': client_distant,
        'produits': produits,
    }

    return render(request, 'cote_client/catalogue/commander.html', context)
