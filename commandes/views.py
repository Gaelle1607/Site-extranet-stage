from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from catalogue.services import get_produit_by_reference
from .services import envoyer_commande


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
        return JsonResponse({
            'success': True,
            'message': f'{nom} ajouté au panier',
            'panier_count': sum(panier.values())
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

    if quantite <= 0:
        if reference in panier:
            del panier[reference]
        message = 'Article supprimé.'
    else:
        panier[reference] = quantite
        message = 'Quantité mise à jour.'

    save_panier(request, panier)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Recalculer le total
        client = request.user.client
        total = 0
        for ref, qte in panier.items():
            produit = get_produit_by_reference(client, ref)
            if produit:
                total += produit['prix'] * qte

        return JsonResponse({
            'success': True,
            'message': message,
            'total_panier': total,
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
        return JsonResponse({
            'success': True,
            'message': 'Article supprimé',
            'panier_count': sum(panier.values())
        })

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

        # Envoyer au logiciel externe
        try:
            resultat = envoyer_commande(commande_data)
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
