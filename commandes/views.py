"""
=============================================================================
VIEWS.PY - Vues de l'application Commandes
=============================================================================

Ce module contient les vues Django pour la gestion du panier d'achat
et des commandes côté client.

Fonctionnalités principales :
    - Gestion du panier (ajout, modification, suppression, vidage)
    - Validation et confirmation de commande
    - Génération de fichiers EDI pour l'intégration ERP
    - Envoi d'emails de confirmation
    - Historique des commandes

Architecture :
    - Panier stocké en session Django (dictionnaire {reference: quantite})
    - Support AJAX pour mise à jour dynamique sans rechargement
    - Intégration avec le système ERP via fichiers CSV EDI
    - Envoi d'emails via le backend configuré dans settings.py

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from datetime import datetime
import traceback


def parse_date(date_str):
    """
    Convertit une chaîne de date au format ISO en objet date.

    Cette fonction utilitaire permet de formater correctement les dates
    dans les templates Django.

    Args:
        date_str (str): Chaîne de date au format 'YYYY-MM-DD' ou None

    Returns:
        date: Objet date Python si la conversion réussit
        str: La chaîne originale si la conversion échoue
        None: Si date_str est None ou vide
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return date_str


from catalogue.services import get_produit_by_reference, get_client_distant
from .services import envoyer_commande, generer_csv_edi
from .models import Commande, LigneCommande


# =============================================================================
# FONCTIONS UTILITAIRES POUR LE PANIER
# =============================================================================

def get_panier(request):
    """
    Récupère le panier depuis la session utilisateur.

    Le panier est stocké en session sous forme de dictionnaire où les clés
    sont les références produits et les valeurs sont les quantités.

    Args:
        request (HttpRequest): L'objet requête Django

    Returns:
        dict: Dictionnaire {reference: quantite}, vide si pas de panier

    Exemple:
        >>> panier = get_panier(request)
        >>> panier
        {'PROD001': 2, 'PROD002': 5}
    """
    if 'panier' not in request.session:
        request.session['panier'] = {}
    return request.session['panier']


def save_panier(request, panier):
    """
    Sauvegarde le panier dans la session utilisateur.

    Args:
        request (HttpRequest): L'objet requête Django
        panier (dict): Dictionnaire {reference: quantite} à sauvegarder

    Note:
        Le flag session.modified = True force Django à sauvegarder
        la session même si seul le contenu du dictionnaire a changé.
    """
    request.session['panier'] = panier
    request.session.modified = True


# =============================================================================
# VUES DU PANIER
# =============================================================================

@login_required
def voir_panier(request):
    """
    Affiche le contenu du panier de l'utilisateur.

    Cette vue construit la liste détaillée des articles du panier avec
    les informations produits actuelles (nom, prix) et calcule les totaux.

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django

    Returns:
        HttpResponse: Rendu du template 'cote_client/commandes/panier.html'
            avec le contexte :
            - lignes : Liste des articles avec détails produits et totaux
            - total : Montant total du panier
            - nombre_articles : Somme des quantités de tous les articles

    Note:
        Les produits qui n'existent plus dans le catalogue sont ignorés
        mais restent en session. Un nettoyage pourrait être ajouté.
    """
    utilisateur = request.user.utilisateur
    panier = get_panier(request)

    # Construction des lignes avec informations produits actuelles
    lignes = []
    total = 0
    for reference, quantite in panier.items():
        produit = get_produit_by_reference(utilisateur, reference)
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
    return render(request, 'cote_client/commandes/panier.html', context)


@login_required
@require_POST
def ajouter_au_panier(request):
    """
    Ajoute un produit au panier ou augmente sa quantité.

    Cette vue gère l'ajout de produits au panier avec vérification du
    stock disponible. Elle supporte les requêtes AJAX pour une mise à
    jour dynamique de l'interface.

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié
        @require_POST : N'accepte que les requêtes POST (sécurité CSRF)

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - POST['reference'] : Référence du produit à ajouter
            - POST['quantite'] : Quantité à ajouter (défaut = 1)

    Returns:
        JsonResponse (si AJAX) : Dictionnaire avec :
            - success : Boolean de succès
            - message : Message de confirmation ou d'erreur
            - panier_count : Nombre total d'articles dans le panier
            - lignes_panier : Liste des lignes mises à jour
            - total_panier : Montant total du panier
        HttpResponse (sinon) : Redirection vers 'commandes:panier'

    Comportement :
        - Si le produit est déjà dans le panier, sa quantité est augmentée
        - Si le stock est limité, la quantité est ajustée automatiquement
        - Un message informe l'utilisateur de la limitation de stock
    """
    reference = request.POST.get('reference')
    quantite = int(request.POST.get('quantite', 1))

    utilisateur = request.user.utilisateur
    produit = get_produit_by_reference(utilisateur, reference)

    panier = get_panier(request)

    # Calcul de la quantité totale (existante + nouvelle)
    quantite_actuelle = panier.get(reference, 0)
    quantite_totale = quantite_actuelle + quantite

    # Vérification du stock disponible (si défini et > 0)
    stock_disponible = produit.get('stock') if produit else None
    if stock_disponible is not None and stock_disponible > 0 and quantite_totale > stock_disponible:
        # Limitation de la quantité au stock disponible
        quantite_ajoutee = stock_disponible - quantite_actuelle

        if quantite_ajoutee <= 0:
            # Déjà au maximum du stock
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Stock insuffisant. Vous avez déjà {quantite_actuelle} en panier '
                               f'({stock_disponible} {produit.get("unite", "")} en stock).',
                })
            messages.warning(
                request,
                f'Stock insuffisant. Vous avez déjà {quantite_actuelle} en panier.'
            )
            return redirect('commandes:panier')

        panier[reference] = stock_disponible
        message_stock = f' (limité au stock disponible: {stock_disponible})'
    else:
        panier[reference] = quantite_totale
        message_stock = ''

    save_panier(request, panier)
    nom = produit['nom'] if produit else reference

    # Réponse AJAX avec données du panier mises à jour
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        lignes_panier = []
        total_panier = 0
        for ref, qte in panier.items():
            p = get_produit_by_reference(utilisateur, ref)
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
            'message': f'{nom} ajouté au panier{message_stock}',
            'panier_count': sum(panier.values()),
            'lignes_panier': lignes_panier,
            'total_panier': total_panier,
        })

    messages.success(request, f'{nom} ajouté au panier{message_stock}.')
    return redirect('commandes:panier')


@login_required
@require_POST
def modifier_quantite(request):
    """
    Modifie la quantité d'un article dans le panier.

    Cette vue permet d'ajuster la quantité d'un produit déjà présent
    dans le panier. Si la nouvelle quantité est 0 ou négative, l'article
    est supprimé du panier.

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié
        @require_POST : N'accepte que les requêtes POST

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - POST['reference'] : Référence du produit à modifier
            - POST['quantite'] : Nouvelle quantité (0 = suppression)

    Returns:
        JsonResponse (si AJAX) : Dictionnaire avec :
            - success : Boolean de succès
            - message : Message de confirmation
            - total_panier : Nouveau total du panier
            - total_ligne : Total de la ligne modifiée
            - panier_count : Nombre total d'articles
        HttpResponse (sinon) : Redirection vers 'commandes:panier'

    Note:
        Le stock disponible est vérifié et la quantité peut être
        automatiquement ajustée si elle dépasse le stock.
    """
    reference = request.POST.get('reference')
    quantite = int(request.POST.get('quantite', 0))

    panier = get_panier(request)
    utilisateur = request.user.utilisateur
    produit = get_produit_by_reference(utilisateur, reference)

    if quantite <= 0:
        # Suppression de l'article si quantité <= 0
        if reference in panier:
            del panier[reference]
        message = 'Article supprimé.'
        total_ligne = 0
    else:
        # Vérification du stock disponible
        stock_disponible = produit.get('stock') if produit else None
        if stock_disponible is not None and stock_disponible > 0 and quantite > stock_disponible:
            quantite = stock_disponible
            message = f'Quantité limitée au stock disponible ({stock_disponible}).'
        else:
            message = 'Quantité mise à jour.'

        panier[reference] = quantite
        # Calcul du total de la ligne
        total_ligne = produit['prix'] * quantite if produit else 0

    save_panier(request, panier)

    # Réponse AJAX avec totaux recalculés
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Recalcul du total général du panier
        total_panier = 0
        for ref, qte in panier.items():
            produit = get_produit_by_reference(utilisateur, ref)
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
    """
    Supprime un article du panier.

    Cette vue retire complètement un produit du panier, quelle que
    soit sa quantité actuelle.

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié
        @require_POST : N'accepte que les requêtes POST

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - POST['reference'] : Référence du produit à supprimer

    Returns:
        JsonResponse (si AJAX) : Dictionnaire avec :
            - success : Boolean de succès
            - message : Message de confirmation
            - panier_count : Nombre d'articles restants
            - total_panier : Nouveau total du panier
            - lignes_panier : Liste des lignes restantes
        HttpResponse (sinon) : Redirection vers 'commandes:panier'
    """
    reference = request.POST.get('reference')

    panier = get_panier(request)
    if reference in panier:
        del panier[reference]
    save_panier(request, panier)

    # Réponse AJAX avec panier mis à jour
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            utilisateur = request.user.utilisateur
            total_panier = 0
            lignes_panier = []

            for ref, qte in panier.items():
                produit = get_produit_by_reference(utilisateur, ref)
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
    """
    Vide complètement le panier.

    Cette vue supprime tous les articles du panier en une seule action.

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié
        @require_POST : N'accepte que les requêtes POST

    Args:
        request (HttpRequest): L'objet requête Django

    Returns:
        JsonResponse (si AJAX) : Dictionnaire avec :
            - success : True
            - message : 'Panier vidé'
            - panier_count : 0
        HttpResponse (sinon) : Redirection vers 'commandes:panier'
    """
    request.session['panier'] = {}
    request.session.modified = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': 'Panier vidé',
            'panier_count': 0,
        })

    messages.success(request, 'Votre panier a été vidé.')
    return redirect('commandes:panier')


# =============================================================================
# VALIDATION DE COMMANDE
# =============================================================================

@login_required
def valider_commande(request):
    """
    Gère la validation et la confirmation de commande.

    Cette vue complexe gère plusieurs étapes du processus de commande :
    1. Affichage du récapitulatif (GET avec données en session)
    2. Préparation du récapitulatif (POST sans 'confirmer')
    3. Validation finale et envoi (POST avec 'confirmer')

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - POST['date_livraison'] : Date de livraison souhaitée (optionnel)
            - POST['date_depart_camions'] : Date de départ des camions (optionnel)
            - POST['commentaires'] : Notes sur la commande (optionnel)
            - POST['confirmer'] : Présent uniquement lors de la validation finale

    Returns:
        HttpResponse:
            - Panier vide : Redirection vers 'catalogue:liste' avec avertissement
            - GET sans données : Redirection vers 'commandes:panier'
            - GET avec données : Rendu du template de validation
            - POST récap : Rendu du template de validation avec totaux
            - POST confirmer : Redirection vers 'commandes:confirmation'

    Workflow complet :
        1. Vérification que le panier n'est pas vide
        2. Construction des lignes avec calcul des totaux
        3. Stockage des métadonnées en session (dates, commentaires)
        4. Affichage du récapitulatif pour validation
        5. Création de la commande en base de données
        6. Génération du fichier CSV EDI pour l'ERP
        7. Envoi de l'email de confirmation au client
        8. Vidage du panier et redirection

    Note:
        Les messages de debug (print) sont présents pour le développement.
        En production, utiliser un système de logging approprié.
    """
    utilisateur = request.user.utilisateur
    client_distant = get_client_distant(utilisateur.code_tiers)
    panier = get_panier(request)

    # Vérification que le panier contient des articles
    if not panier:
        messages.warning(request, 'Votre panier est vide.')
        return redirect('catalogue:liste')

    # =========================================================================
    # TRAITEMENT GET : Affichage du récapitulatif
    # =========================================================================
    if request.method == 'GET':
        recap = request.session.get('commande_recap')
        if recap:
            # Reconstruction des lignes pour l'affichage
            lignes = []
            total = 0
            for reference, quantite in panier.items():
                produit = get_produit_by_reference(utilisateur, reference)
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

            context = {
                'lignes': lignes,
                'total': total,
                'nombre_articles': sum(panier.values()),
                'client': client_distant,
                'date_livraison': parse_date(recap.get('date_livraison')),
                'date_depart_camions': parse_date(recap.get('date_depart_camions')),
                'commentaires': recap.get('commentaires', ''),
            }
            return render(request, 'cote_client/commandes/validation.html', context)
        return redirect('commandes:panier')

    # =========================================================================
    # TRAITEMENT POST : Préparation ou confirmation
    # =========================================================================
    # Construction des lignes de commande
    lignes = []
    total = 0
    for reference, quantite in panier.items():
        produit = get_produit_by_reference(utilisateur, reference)
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

    # Distinction entre demande de récap et confirmation finale
    if 'confirmer' in request.POST:
        # =====================================================================
        # CONFIRMATION FINALE : Création de la commande
        # =====================================================================
        recap = request.session.get('commande_recap', {})
        if not recap:
            messages.warning(request, 'Session expirée, veuillez recommencer.')
            return redirect('commandes:panier')

        notes = recap.get('commentaires', '')
        date_livraison = recap.get('date_livraison')
        date_depart_camions = recap.get('date_depart_camions')
    else:
        # =====================================================================
        # DEMANDE DE RÉCAPITULATIF : Stockage en session
        # =====================================================================
        date_livraison = request.POST.get('date_livraison') or None
        date_depart_camions = request.POST.get('date_depart_camions') or None
        notes = request.POST.get('commentaires', '')

        # Stockage des métadonnées de commande en session
        request.session['commande_recap'] = {
            'date_livraison': date_livraison,
            'date_depart_camions': date_depart_camions,
            'commentaires': notes,
        }
        request.session.modified = True

        # Affichage de la page de récapitulatif
        context = {
            'lignes': lignes,
            'total': total,
            'nombre_articles': sum(panier.values()),
            'client': client_distant,
            'date_livraison': parse_date(date_livraison),
            'date_depart_camions': parse_date(date_depart_camions),
            'commentaires': notes,
        }
        return render(request, 'cote_client/commandes/validation.html', context)

    # =========================================================================
    # ENVOI DE LA COMMANDE
    # =========================================================================
    nom_client = client_distant.nom if client_distant else utilisateur.code_tiers
    commande_data = {
        'client': nom_client,
        'lignes': lignes,
        'total': total,
        'notes': notes,
        'date_livraison': date_livraison,
    }

    # Debug : Affichage de la commande dans le terminal
    print("\n" + "="*60)
    print("NOUVELLE COMMANDE REÇUE")
    print("="*60)
    print(f"Client: {nom_client}")
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

    # Envoi au système externe (logiciel métier)
    try:
        resultat = envoyer_commande(commande_data)

        # Création de la commande en base de données
        commande = Commande.objects.create(
            utilisateur=utilisateur,
            numero=Commande.generer_numero(),
            date_livraison=date_livraison,
            date_depart_camions=date_depart_camions,
            total_ht=Decimal(str(total)),
            commentaire=notes
        )

        # Création des lignes de commande associées
        for ligne in lignes:
            LigneCommande.objects.create(
                commande=commande,
                reference_produit=ligne['reference'],
                nom_produit=ligne['nom'],
                quantite=ligne['quantite'],
                prix_unitaire=Decimal(str(ligne['prix'])),
                total_ligne=Decimal(str(ligne['total']))
            )

        # Génération du fichier CSV EDI pour l'ERP
        try:
            csv_path = generer_csv_edi(commande, client_distant, lignes)
            print(f"Fichier EDI généré: {csv_path}")
            messages.info(request, f"Fichier EDI généré: {csv_path}")
        except Exception as e:
            error_msg = f"Erreur génération EDI: {e}\n{traceback.format_exc()}"
            print(error_msg)
            messages.warning(request, f"Erreur génération EDI: {e}")

        # =====================================================================
        # ENVOI DE L'EMAIL DE CONFIRMATION
        # =====================================================================
        email_utilisateur = request.user.email
        if email_utilisateur:
            # Construction du récapitulatif des articles pour l'email
            lignes_email = []
            for ligne in lignes:
                lignes_email.append(f"  - {ligne['nom']} ({ligne['reference']})")
                lignes_email.append(f"    Quantité: {ligne['quantite']} x {ligne['prix']:.2f} € = {ligne['total']:.2f} €")
            articles_texte = "\n".join(lignes_email)

            # Construction du message avec informations optionnelles
            date_livraison_texte = f"\nDate de livraison souhaitée: {date_livraison}" if date_livraison else ""
            commentaire_texte = f"\nCommentaire: {notes}" if notes else ""

            message_email = f"""Bonjour,

Votre commande n° {commande.numero} a bien été enregistrée.

Récapitulatif de votre commande :
{articles_texte}

Total HT: {total:.2f} €{date_livraison_texte}{commentaire_texte}

Nous vous remercions de votre confiance.

Cordialement,
L'équipe Giffaud Groupe"""

            try:
                send_mail(
                    subject=f'Confirmation de commande n° {commande.numero} - Giffaud Groupe',
                    message=message_email,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email_utilisateur],
                    fail_silently=False,
                )
                print(f"Email de confirmation envoyé à {email_utilisateur}")
            except Exception as e:
                print(f"Erreur envoi email: {e}")

        # Nettoyage : vidage du panier et des données de session
        request.session['panier'] = {}
        request.session.pop('commande_recap', None)
        request.session.modified = True

        messages.success(request, 'Votre commande a été envoyée avec succès !')
        return redirect('commandes:confirmation')

    except Exception as e:
        messages.error(request, f'Erreur lors de l\'envoi de la commande : {str(e)}')
        return redirect('commandes:panier')


@login_required
def confirmation_commande(request):
    """
    Affiche la page de confirmation après envoi de commande.

    Cette vue simple affiche un message de confirmation après le
    traitement réussi d'une commande.

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django

    Returns:
        HttpResponse: Rendu du template 'cote_client/commandes/confirmation.html'
    """
    return render(request, 'cote_client/commandes/confirmation.html')


# =============================================================================
# HISTORIQUE DES COMMANDES
# =============================================================================

@login_required
def historique_commandes(request):
    """
    Affiche l'historique des commandes de l'utilisateur.

    Cette vue liste les 50 dernières commandes passées par l'utilisateur
    connecté, triées par date décroissante (les plus récentes en premier).

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django

    Returns:
        HttpResponse: Rendu du template 'cote_client/commandes/historique.html'
            avec le contexte :
            - client : Informations client depuis la base distante
            - commandes : QuerySet des 50 dernières commandes

    Note:
        La limite de 50 commandes peut être ajustée ou remplacée par
        une pagination pour les clients avec un historique important.
    """
    utilisateur = request.user.utilisateur
    client_distant = get_client_distant(utilisateur.code_tiers)

    # Récupération des 50 dernières commandes
    commandes = Commande.objects.filter(
        utilisateur=utilisateur
    ).order_by('-date_commande')[:50]

    return render(request, 'cote_client/commandes/historique.html', {
        'client': client_distant,
        'commandes': commandes
    })


@login_required
def details_commande(request, commande_id):
    """
    Affiche les détails d'une commande spécifique.

    Cette vue présente le détail complet d'une commande avec toutes
    ses lignes. Elle vérifie que la commande appartient bien à
    l'utilisateur connecté pour des raisons de sécurité.

    Décorateurs :
        @login_required : Redirige vers la connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django
        commande_id (int): Identifiant unique de la commande à afficher

    Returns:
        HttpResponse: Rendu du template 'cote_client/commandes/details.html'
            avec le contexte :
            - client : Informations client depuis la base distante
            - commande : Objet Commande avec ses lignes accessibles via
                         commande.lignes.all()

    Raises:
        Http404: Si la commande n'existe pas ou n'appartient pas à
                 l'utilisateur connecté (via get_object_or_404)

    Sécurité:
        Le filtre utilisateur=utilisateur dans get_object_or_404 garantit
        qu'un utilisateur ne peut voir que ses propres commandes.
    """
    utilisateur = request.user.utilisateur
    client_distant = get_client_distant(utilisateur.code_tiers)

    # Récupération sécurisée de la commande (vérifie l'appartenance)
    commande = get_object_or_404(
        Commande,
        id=commande_id,
        utilisateur=utilisateur
    )

    return render(request, 'cote_client/commandes/details.html', {
        'client': client_distant,
        'commande': commande
    })
