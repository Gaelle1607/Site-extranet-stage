from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.db.models import Sum
from decimal import Decimal
import traceback
from .services import get_produits_client, get_categories_client, get_produit_by_reference, get_client_distant, FILTRES_DISPONIBLES, generer_filtres_automatiques, _normaliser
from commandes.models import Commande, LigneCommande
from commandes.services import generer_csv_edi


@login_required
def liste_produits(request):
    """Liste des produits pour le client connecté"""

    if not hasattr(request.user, 'utilisateur'):
        messages.error(
            request,
            "Votre compte n'est pas associé à un profil utilisateur. Contactez l'administrateur."
        )
        return redirect('clients:connexion')

    utilisateur = request.user.utilisateur
    produits = get_produits_client(utilisateur)

    # Générer les filtres automatiques à partir des libellés
    filtres_auto = generer_filtres_automatiques(produits, seuil_occurrences=3)

    # Ajouter les tags automatiques aux produits
    for produit in produits:
        libelle_normalise = _normaliser(produit.get('libelle', '') or '')
        for code, info in filtres_auto.items():
            if any(terme in libelle_normalise for terme in info["termes"]):
                if code not in produit.get('tags', []):
                    produit['tags'].append(code)

    # Collecter tous les tags présents dans le catalogue du client
    tags_disponibles = set()
    for p in produits:
        tags_disponibles.update(p.get('tags', []))

    # Filtres groupés pour le template, filtrés par tags disponibles
    filtres_groupes = {}
    for groupe, filtres in FILTRES_DISPONIBLES.items():
        filtres_groupe = {
            code: info["label"]
            for code, info in filtres.items()
            if code in tags_disponibles
        }
        # N'ajouter le groupe que s'il contient au moins un filtre
        if filtres_groupe:
            filtres_groupes[groupe] = filtres_groupe

    # Ajouter les filtres automatiques comme groupe séparé
    if filtres_auto:
        filtres_groupes["Filtres personnalisés"] = {
            code: info["label"]
            for code, info in filtres_auto.items()
        }

    # Filtres actifs (checkbox)
    filtres_actifs = request.GET.getlist("filtre")

    # Recherche texte
    recherche = request.GET.get('q', '').strip().lower()
    if recherche:
        produits = [
            p for p in produits
            if recherche in p.get('nom', '').lower()
            or recherche in p.get('reference', '').lower()
        ]

    # Application des filtres
    if filtres_actifs:
        produits = [
            p for p in produits
            if any(f in p.get('tags', []) for f in filtres_actifs)
        ]

    # Produits favoris (uniquement sans filtre ni recherche)
    produits_favoris = []
    if not filtres_actifs and not recherche:
        top_references = (
            LigneCommande.objects
            .filter(commande__utilisateur=utilisateur)
            .values('reference_produit')
            .annotate(total_commande=Sum('quantite'))
            .order_by('-total_commande')[:4]
        )

        for entry in top_references:
            produit = get_produit_by_reference(
                utilisateur,
                entry['reference_produit']
            )
            if produit:
                produits_favoris.append(produit)

        refs_favoris = {p['reference'] for p in produits_favoris}
        produits = [
            p for p in produits
            if p['reference'] not in refs_favoris
        ]

    # Panier
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
        'filtres_groupes': filtres_groupes,
        'filtres_actifs': filtres_actifs,
        'recherche': request.GET.get('q', ''),
        'lignes_panier': lignes_panier,
        'total_panier': total_panier,
    }

    return render(
        request,
        'cote_client/catalogue/liste.html',
        context
    )



@login_required
def favoris(request):
    """Liste des produits favoris (les plus commandés)"""
    if not hasattr(request.user, 'utilisateur'):
        messages.error(request, "Votre compte n'est pas associé à un profil utilisateur. Contactez l'administrateur.")
        return redirect('clients:connexion')
    utilisateur = request.user.utilisateur

    # Top 12 des produits les plus commandés sur le site par cet utilisateur
    top_references = (
        LigneCommande.objects
        .filter(commande__utilisateur=utilisateur)
        .values('reference_produit')
        .annotate(total_commande=Sum('quantite'))
        .order_by('-total_commande')[:12]
    )

    # Récupérer les infos complètes de chaque produit
    produits_favoris = []
    for entry in top_references:
        produit = get_produit_by_reference(utilisateur, entry['reference_produit'])
        if produit:
            produit['total_commande'] = entry['total_commande']
            produits_favoris.append(produit)

    # Générer les filtres automatiques à partir des libellés des favoris
    filtres_auto = generer_filtres_automatiques(produits_favoris, seuil_occurrences=2)

    # Ajouter les tags automatiques aux produits favoris
    for produit in produits_favoris:
        libelle_normalise = _normaliser(produit.get('libelle', '') or '')
        for code, info in filtres_auto.items():
            if any(terme in libelle_normalise for terme in info["termes"]):
                if code not in produit.get('tags', []):
                    produit['tags'].append(code)

    # Collecter tous les tags présents dans les favoris
    tags_disponibles = set()
    for p in produits_favoris:
        tags_disponibles.update(p.get('tags', []))

    # Filtres groupés pour le template, filtrés par tags disponibles
    filtres_groupes = {}
    for groupe, filtres in FILTRES_DISPONIBLES.items():
        filtres_groupe = {
            code: info["label"]
            for code, info in filtres.items()
            if code in tags_disponibles
        }
        if filtres_groupe:
            filtres_groupes[groupe] = filtres_groupe

    # Ajouter les filtres automatiques comme groupe séparé
    if filtres_auto:
        filtres_groupes["Filtres personnalisés"] = {
            code: info["label"]
            for code, info in filtres_auto.items()
        }

    # Filtres actifs (checkbox)
    filtres_actifs = request.GET.getlist("filtre")

    # Recherche
    recherche = request.GET.get('q', '').strip().lower()
    if recherche:
        produits_favoris = [p for p in produits_favoris if
                    recherche in p.get('nom', '').lower() or
                    recherche in p.get('reference', '').lower()]

    # Application des filtres
    if filtres_actifs:
        produits_favoris = [
            p for p in produits_favoris
            if any(f in p.get('tags', []) for f in filtres_actifs)
        ]

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
        'filtres_groupes': filtres_groupes,
        'filtres_actifs': filtres_actifs,
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

        # Récupérer les commentaires et les dates
        commentaires = request.POST.get('commentaires', '')
        date_livraison = request.POST.get('date_livraison') or None
        date_depart_camions = request.POST.get('date_depart_camions') or None

        # Créer la commande
        commande = Commande.objects.create(
            utilisateur=utilisateur,
            numero=Commande.generer_numero(),
            date_livraison=date_livraison,
            date_depart_camions=date_depart_camions,
            total_ht=Decimal(str(total)),
            commentaire=commentaires
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

        # Générer le fichier CSV EDI
        try:
            csv_path = generer_csv_edi(commande, client_distant, lignes)
            print(f"Fichier EDI généré: {csv_path}")
            messages.info(request, f"Fichier EDI généré: {csv_path}")
        except Exception as e:
            error_msg = f"Erreur génération EDI: {e}\n{traceback.format_exc()}"
            print(error_msg)
            messages.warning(request, f"Erreur génération EDI: {e}")

        # Vider le panier
        request.session['panier'] = {}
        request.session.modified = True

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
