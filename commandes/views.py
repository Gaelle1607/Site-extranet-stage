from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal
from catalogue.services import get_produit_by_reference
from .services import envoyer_commande
from .models import Commande, LigneCommande


def get_panier(request):
    """Récupère le panier depuis la session"""
    if 'panier' not in request.session:
        request.session['panier'] = {}
    return request.session['panier']


def save_panier(request, panier):
    """Sauvegarde le panier en session"""
    request.session['panier'] = panier
    request.session.modified = True


@login_required
def voir_panier(request):
    """Affiche le panier"""
    client = request.user.client
    panier = get_panier(request)

    # Construire les lignes avec les infos produits
    lignes = []
    total = 0
    for reference, quantite in panier.items():
        produit = get_produit_by_reference(client, reference)
        if produit:
            ligne_total = produit['prix'] * quantite
            lignes.append({
                'reference': reference,
                'produit': produit,
                'quantite': quantite,
                'total': ligne_total,
            })
            total += ligne_total

    context = {
        'lignes': lignes,
        'total': total,
        'nombre_articles': sum(panier.values()),
    }
    return render(request, 'commandes/panier.html', context)


@login_required
@require_POST
def ajouter_au_panier(request):
    """Ajoute un produit au panier"""
    reference = request.POST.get('reference')
    quantite = int(request.POST.get('quantite', 1))

    panier = get_panier(request)

    if reference in panier:
        panier[reference] += quantite
    else:
        panier[reference] = quantite

    save_panier(request, panier)

    # Récupérer le nom du produit pour le message
    client = request.user.client
    produit = get_produit_by_reference(client, reference)
    nom = produit['nom'] if produit else reference

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Construire les données du panier pour le récap
        lignes_panier = []
        total_panier = 0
        for ref, qte in panier.items():
            p = get_produit_by_reference(client, ref)
            if p:
                ligne_total = p['prix'] * qte
                lignes_panier.append({
                    'reference': ref,
                    'nom': p['nom'],
                    'quantite': qte,
                    'prix': p['prix'],
                    'total': ligne_total,
                })
                total_panier += ligne_total

        return JsonResponse({
            'success': True,
            'message': f'{nom} ajouté au panier',
            'panier_count': sum(panier.values()),
            'lignes_panier': lignes_panier,
            'total_panier': total_panier,
        })

    messages.success(request, f'{nom} ajouté au panier.')
    return redirect('commandes:panier')


@login_required
@require_POST
def modifier_quantite(request):
    """Modifie la quantité d'un article du panier"""
    reference = request.POST.get('reference')
    quantite = int(request.POST.get('quantite', 0))

    panier = get_panier(request)
    client = request.user.client

    if quantite <= 0:
        if reference in panier:
            del panier[reference]
        message = 'Article supprimé.'
        total_ligne = 0
    else:
        panier[reference] = quantite
        message = 'Quantité mise à jour.'
        # Calculer le total de la ligne
        produit = get_produit_by_reference(client, reference)
        total_ligne = produit['prix'] * quantite if produit else 0

    save_panier(request, panier)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Recalculer le total du panier
        total_panier = 0
        for ref, qte in panier.items():
            produit = get_produit_by_reference(client, ref)
            if produit:
                total_panier += produit['prix'] * qte

        return JsonResponse({
            'success': True,
            'message': message,
            'total_panier': total_panier,
            'total_ligne': total_ligne,
            'panier_count': sum(panier.values())
        })

    messages.success(request, message)
    return redirect('commandes:panier')


@login_required
@require_POST
def supprimer_du_panier(request):
    """Supprime un article du panier"""
    reference = request.POST.get('reference')

    panier = get_panier(request)
    if reference in panier:
        del panier[reference]
    save_panier(request, panier)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Recalculer le total
        try:
            client = request.user.client
            total_panier = 0
            lignes_panier = []
            for ref, qte in panier.items():
                produit = get_produit_by_reference(client, ref)
                if produit:
                    total_ligne = produit['prix'] * qte
                    total_panier += total_ligne
                    lignes_panier.append({
                        'reference': ref,
                        'nom': produit['nom'],
                        'quantite': qte,
                        'prix': produit['prix'],
                        'total': total_ligne,
                    })

            return JsonResponse({
                'success': True,
                'message': 'Article supprimé',
                'panier_count': sum(panier.values()),
                'total_panier': total_panier,
                'lignes_panier': lignes_panier
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            }, status=500)

    messages.success(request, 'Article supprimé du panier.')
    return redirect('commandes:panier')


@login_required
@require_POST
def vider_panier(request):
    """Vide le panier"""
    request.session['panier'] = {}
    request.session.modified = True

    messages.success(request, 'Votre panier a été vidé.')
    return redirect('commandes:panier')


@login_required
def valider_commande(request):
    """Page de validation et envoi de la commande"""
    client = request.user.client
    panier = get_panier(request)

    if not panier:
        messages.warning(request, 'Votre panier est vide.')
        return redirect('catalogue:liste')

    # Construire les lignes
    lignes = []
    total = 0
    for reference, quantite in panier.items():
        produit = get_produit_by_reference(client, reference)
        if produit:
            ligne_total = produit['prix'] * quantite
            lignes.append({
                'reference': reference,
                'nom': produit['nom'],
                'prix': produit['prix'],
                'unite': produit.get('unite', ''),
                'quantite': quantite,
                'total': ligne_total,
            })
            total += ligne_total

    if request.method == 'POST':
        notes = request.POST.get('notes', '')

        # Préparer les données de commande
        commande_data = {
            'client': client.nom,
            'lignes': lignes,
            'total': total,
            'notes': notes,
        }

        # DEBUG: Afficher la commande dans le terminal
        print("\n" + "="*60)
        print("NOUVELLE COMMANDE REÇUE")
        print("="*60)
        print(f"Client: {client.nom}")
        print(f"Date: {__import__('datetime').datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("-"*60)
        print("Articles:")
        for ligne in lignes:
            print(f"  - {ligne['nom']} ({ligne['reference']})")
            print(f"    Qté: {ligne['quantite']} x {ligne['prix']:.2f} € = {ligne['total']:.2f} €")
        print("-"*60)
        print(f"TOTAL HT: {total:.2f} €")
        if notes:
            print(f"Notes: {notes}")
        print("="*60 + "\n")

        # Envoyer au logiciel externe
        try:
            resultat = envoyer_commande(commande_data)

            # Sauvegarder la commande en base de données
            commande = Commande.objects.create(
                client=client,
                numero=Commande.generer_numero(),
                total_ht=Decimal(str(total)),
                commentaire=notes,
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

            # Vider le panier
            request.session['panier'] = {}
            request.session.modified = True

            messages.success(request, 'Votre commande a été envoyée avec succès !')
            return redirect('commandes:confirmation')

        except Exception as e:
            messages.error(request, f'Erreur lors de l\'envoi de la commande : {str(e)}')

    context = {
        'lignes': lignes,
        'total': total,
        'client': client,
    }
    return render(request, 'commandes/validation.html', context)


@login_required
def confirmation_commande(request):
    """Page de confirmation après envoi"""
    return render(request, 'commandes/confirmation.html')

@login_required
def historique_commandes(request):
    """Affiche l'historique des commandes du client"""
    client = request.user.client
    commandes = Commande.objects.filter(client=client).order_by('-date_commande')
    return render(request, 'commandes/historique.html', {
        'client': client,
        'commandes': commandes
    })


@login_required
def details_commande(request, commande_id):
    """Affiche les détails d'une commande spécifique"""
    client = request.user.client
    commande = get_object_or_404(Commande, id=commande_id, client=client)
    return render(request, 'commandes/details.html', {
        'client': client,
        'commande': commande
    })
