"""
Vues du catalogue - Extranet Giffaud Groupe
============================================

Ce module contient les vues Django pour la gestion du catalogue de produits
de l'application Extranet Giffaud Groupe. Cette application permet aux clients
professionnels de consulter les produits disponibles, de gérer leurs favoris
et de passer des commandes en ligne.

Fonctionnalités principales:
    - Affichage de la liste des produits disponibles pour chaque client
    - Gestion des produits favoris basée sur l'historique de commandes
    - Consultation du détail de chaque produit
    - Passage de commandes avec génération de fichiers EDI
    - Gestion du panier en session

Architecture:
    Les vues utilisent les services définis dans catalogue/services.py pour
    récupérer les données produits depuis la base de données distante.
    Le système de filtres est partagé avec le module administration.

Auteur: Giffaud Groupe
Date de création: 2024
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.db.models import Sum
from decimal import Decimal
import traceback

# Import des services métier pour l'accès aux données produits
from .services import get_produits_client, get_categories_client, get_produit_by_reference, get_client_distant

# Import des fonctions de filtrage partagées avec le module administration
from administration.views.utils.filtres import preparer_filtres, appliquer_filtres

# Import des modèles de commandes
from commandes.models import Commande, LigneCommande

# Import du service de génération de fichiers EDI
from commandes.services import generer_csv_edi


@login_required
def liste_produits(request):
    """
    Affiche la liste des produits disponibles pour le client connecté.

    Cette vue est le point d'entrée principal du catalogue. Elle affiche
    tous les produits auxquels le client a accès, avec ses produits favoris
    mis en avant. La vue gère également le système de filtrage et la recherche.

    Args:
        request (HttpRequest): L'objet requête Django contenant:
            - GET['filtre']: Liste des filtres actifs (optionnel)
            - GET['q']: Terme de recherche (optionnel)
            - session['panier']: Contenu du panier en cours

    Returns:
        HttpResponse:
            - Redirection vers la page de connexion si l'utilisateur n'a pas
              de profil utilisateur associé
            - Rendu du template 'cote_client/catalogue/liste.html' avec le contexte:
                - produits: Liste des produits (hors favoris)
                - produits_favoris: Les 4 produits les plus commandés
                - filtres_groupes: Groupes de filtres disponibles
                - filtres_actifs: Liste des filtres actuellement appliqués
                - recherche: Terme de recherche actuel
                - lignes_panier: Détail des lignes du panier
                - total_panier: Montant total du panier

    Note:
        Les produits favoris ne sont affichés que si aucun filtre ni recherche
        n'est actif, afin de ne pas les dupliquer dans les résultats filtrés.
    """

    # Vérification que l'utilisateur Django a bien un profil utilisateur associé
    # Cette relation est nécessaire pour accéder au catalogue personnalisé du client
    if not hasattr(request.user, 'utilisateur'):
        messages.error(
            request,
            "Votre compte n'est pas associé à un profil utilisateur. Contactez l'administrateur."
        )
        return redirect('clients:connexion')

    # Récupération de l'objet utilisateur métier (lié au User Django)
    utilisateur = request.user.utilisateur

    # Récupération de tous les produits disponibles pour ce client
    # La liste dépend du code_tiers de l'utilisateur et de son tarif associé
    produits = get_produits_client(utilisateur)

    # =========================================================================
    # PRÉPARATION DES FILTRES
    # =========================================================================
    # Utilisation de la même logique de filtrage que côté administration
    # Le seuil d'occurrences (3) définit le nombre minimum de produits
    # qu'une valeur de filtre doit avoir pour être affichée
    produits, filtres_groupes, _ = preparer_filtres(produits, seuil_occurrences=3)

    # Récupération des paramètres de filtrage depuis l'URL (GET)
    filtres_actifs = request.GET.getlist("filtre")  # Peut contenir plusieurs valeurs
    recherche = request.GET.get('q', '').strip()     # Terme de recherche textuelle

    # Application des filtres et de la recherche sur la liste de produits
    produits_filtres = appliquer_filtres(produits, filtres_actifs, recherche)
    produits = produits_filtres

    # =========================================================================
    # GESTION DES PRODUITS FAVORIS
    # =========================================================================
    # Les favoris sont les produits les plus commandés par cet utilisateur
    # Ils sont affichés en priorité uniquement sans filtre ni recherche active
    produits_favoris = []
    if not filtres_actifs and not recherche:
        # Requête d'agrégation pour obtenir les 4 références les plus commandées
        # On somme les quantités commandées pour chaque référence produit
        top_references = (
            LigneCommande.objects
            .filter(commande__utilisateur=utilisateur)
            .values('reference_produit')
            .annotate(total_commande=Sum('quantite'))
            .order_by('-total_commande')[:4]
        )

        # Récupération des informations complètes de chaque produit favori
        # depuis la base de données distante
        for entry in top_references:
            produit = get_produit_by_reference(
                utilisateur,
                entry['reference_produit']
            )
            if produit:
                produits_favoris.append(produit)

        # Suppression des favoris de la liste principale pour éviter les doublons
        # On crée un ensemble (set) des références favorites pour une recherche O(1)
        refs_favoris = {p['reference'] for p in produits_favoris}
        produits = [
            p for p in produits
            if p['reference'] not in refs_favoris
        ]

    # =========================================================================
    # CALCUL DU RÉCAPITULATIF DU PANIER
    # =========================================================================
    # Le panier est stocké en session sous forme de dictionnaire {reference: quantite}
    panier = request.session.get('panier', {})
    lignes_panier = []
    total_panier = 0

    # Construction du détail du panier avec les informations produits actuelles
    for reference, quantite in panier.items():
        produit = get_produit_by_reference(utilisateur, reference)
        if produit:
            # Calcul du total de la ligne (prix unitaire × quantité)
            ligne_total = produit['prix'] * quantite
            lignes_panier.append({
                'reference': reference,
                'nom': produit['nom'],
                'quantite': quantite,
                'prix': produit['prix'],
                'total': ligne_total,
            })
            total_panier += ligne_total

    # Préparation du contexte pour le template
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
    """
    Affiche la page dédiée aux produits favoris de l'utilisateur.

    Cette vue présente les 12 produits les plus commandés par l'utilisateur,
    avec leur total de quantités commandées. Elle permet de retrouver
    rapidement les produits habituels et de les recommander facilement.

    Args:
        request (HttpRequest): L'objet requête Django contenant:
            - GET['filtre']: Liste des filtres actifs (optionnel)
            - GET['q']: Terme de recherche (optionnel)
            - session['panier']: Contenu du panier en cours

    Returns:
        HttpResponse:
            - Redirection vers la page de connexion si l'utilisateur n'a pas
              de profil utilisateur associé
            - Rendu du template 'cote_client/catalogue/favoris.html' avec:
                - produits_favoris: Les 12 produits les plus commandés
                - filtres_groupes: Groupes de filtres disponibles
                - filtres_actifs: Liste des filtres actuellement appliqués
                - recherche: Terme de recherche actuel
                - lignes_panier: Détail des lignes du panier
                - total_panier: Montant total du panier
                - page_title: Titre de la page ('Favoris')

    Note:
        Les favoris sont calculés dynamiquement à partir de l'historique
        des commandes. Un produit qui n'est plus disponible dans le catalogue
        ne sera pas affiché même s'il a été beaucoup commandé.
    """
    # Vérification du profil utilisateur
    if not hasattr(request.user, 'utilisateur'):
        messages.error(request, "Votre compte n'est pas associé à un profil utilisateur. Contactez l'administrateur.")
        return redirect('clients:connexion')
    utilisateur = request.user.utilisateur

    # =========================================================================
    # RÉCUPÉRATION DES PRODUITS LES PLUS COMMANDÉS
    # =========================================================================
    # Agrégation des lignes de commande pour obtenir les 12 références
    # les plus commandées en termes de quantité totale
    top_references = (
        LigneCommande.objects
        .filter(commande__utilisateur=utilisateur)
        .values('reference_produit')
        .annotate(total_commande=Sum('quantite'))
        .order_by('-total_commande')[:12]
    )

    # Enrichissement des données avec les informations complètes du produit
    # depuis la base de données distante
    produits_favoris = []
    for entry in top_references:
        produit = get_produit_by_reference(utilisateur, entry['reference_produit'])
        if produit:
            # Ajout du total commandé pour affichage dans le template
            produit['total_commande'] = entry['total_commande']
            produits_favoris.append(produit)

    # =========================================================================
    # APPLICATION DES FILTRES
    # =========================================================================
    # Même système de filtrage que pour la liste complète
    # Seuil réduit à 2 car moins de produits à filtrer
    produits_favoris, filtres_groupes, _ = preparer_filtres(produits_favoris, seuil_occurrences=2)

    # Récupération et application des filtres de l'URL
    filtres_actifs = request.GET.getlist("filtre")
    recherche = request.GET.get('q', '').strip()

    # Filtrage de la liste des favoris
    produits_favoris = appliquer_filtres(produits_favoris, filtres_actifs, recherche)

    # =========================================================================
    # RÉCAPITULATIF DU PANIER
    # =========================================================================
    # Construction identique à la vue liste_produits
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

    # Préparation du contexte pour le template
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
    """
    Affiche la page de détail d'un produit spécifique.

    Cette vue permet de consulter toutes les informations détaillées
    d'un produit identifié par sa référence. Elle vérifie que le produit
    est bien accessible par l'utilisateur connecté.

    Args:
        request (HttpRequest): L'objet requête Django
        reference (str): La référence unique du produit à afficher

    Returns:
        HttpResponse:
            - Redirection vers la page de connexion si l'utilisateur n'a pas
              de profil utilisateur associé
            - Erreur 404 si le produit n'existe pas ou n'est pas accessible
            - Rendu du template 'cote_client/catalogue/detail.html' avec:
                - produit: Dictionnaire contenant toutes les informations du produit

    Raises:
        Http404: Si le produit n'est pas trouvé ou n'est pas accessible
            pour cet utilisateur

    Note:
        La fonction get_produit_by_reference vérifie automatiquement que
        le produit fait partie du catalogue accessible à l'utilisateur.
    """
    # Vérification du profil utilisateur
    if not hasattr(request.user, 'utilisateur'):
        messages.error(request, "Votre compte n'est pas associé à un profil utilisateur.")
        return redirect('clients:connexion')

    utilisateur = request.user.utilisateur

    # Récupération du produit par sa référence
    # La fonction retourne None si le produit n'existe pas ou n'est pas accessible
    produit = get_produit_by_reference(utilisateur, reference)

    # Vérification que le produit a bien été trouvé
    if not produit:
        raise Http404("Produit non trouvé")

    context = {
        'produit': produit,
    }
    return render(request, 'cote_client/catalogue/detail.html', context)


def mentions_legales(request):
    """
    Affiche la page des mentions légales du site.

    Cette vue est publique et ne nécessite pas d'authentification.
    Elle affiche les informations légales obligatoires concernant
    l'entreprise Giffaud Groupe et l'utilisation du site.

    Args:
        request (HttpRequest): L'objet requête Django

    Returns:
        HttpResponse: Rendu du template 'cote_client/mention_legale.html'

    Note:
        Cette page est accessible sans connexion conformément aux
        obligations légales d'affichage des mentions légales.
    """
    return render(request, 'cote_client/mention_legale.html')


@login_required
def commander(request):
    """
    Gère le formulaire de commande et la création de nouvelles commandes.

    Cette vue traite à la fois l'affichage du formulaire de commande (GET)
    et la soumission d'une nouvelle commande (POST). Elle gère le panier
    en session, crée les enregistrements en base de données et génère
    le fichier CSV au format EDI pour l'intégration avec le système ERP.

    Args:
        request (HttpRequest): L'objet requête Django contenant:
            - POST['qte_{reference}']: Quantité pour chaque produit
            - POST['commentaires']: Commentaires sur la commande (optionnel)
            - POST['date_livraison']: Date de livraison souhaitée (optionnel)
            - POST['date_depart_camions']: Date de départ des camions (optionnel)
            - session['panier']: Contenu du panier pré-rempli

    Returns:
        HttpResponse:
            - GET: Rendu du template 'cote_client/catalogue/commander.html' avec:
                - client: Informations du client distant (depuis la base ERP)
                - produits: Liste des produits avec quantités du panier
            - POST réussi: Redirection vers 'commandes:confirmation' avec
              message de succès
            - POST sans produits: Redirection vers 'catalogue:commander' avec
              message d'avertissement

    Workflow de création de commande:
        1. Extraction des quantités depuis le formulaire POST
        2. Calcul des totaux par ligne et global
        3. Création de l'objet Commande avec numéro auto-généré
        4. Création des LigneCommande associées
        5. Génération du fichier CSV EDI pour l'ERP
        6. Vidage du panier en session
        7. Redirection avec message de confirmation

    Note:
        - Les erreurs de génération EDI sont capturées et loguées mais
          n'empêchent pas la validation de la commande
        - Le panier est automatiquement vidé après une commande réussie
        - Les prix sont convertis en Decimal pour une précision comptable
    """
    # Récupération des informations utilisateur et client
    utilisateur = request.user.utilisateur

    # Récupération des informations client depuis la base distante (ERP)
    # Ces informations sont nécessaires pour la génération du fichier EDI
    client_distant = get_client_distant(utilisateur.code_tiers)

    # Récupération de la liste complète des produits du client
    produits = get_produits_client(utilisateur)

    # =========================================================================
    # TRAITEMENT DU FORMULAIRE DE COMMANDE (POST)
    # =========================================================================
    if request.method == 'POST':
        # Liste des lignes de commande avec leurs totaux
        lignes = []
        total = 0

        # Parcours de tous les produits pour extraire les quantités commandées
        for produit in produits:
            # Le nom du champ de quantité suit le format "qte_{reference}"
            qte_key = f"qte_{produit['reference']}"
            quantite = int(request.POST.get(qte_key, 0))

            # Ajout à la commande uniquement si quantité positive
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

        # Validation: au moins un produit doit être commandé
        if not lignes:
            messages.warning(request, 'Veuillez sélectionner au moins un produit.')
            return redirect('catalogue:commander')

        # Récupération des informations complémentaires de la commande
        commentaires = request.POST.get('commentaires', '')
        date_livraison = request.POST.get('date_livraison') or None
        date_depart_camions = request.POST.get('date_depart_camions') or None

        # =====================================================================
        # CRÉATION DE LA COMMANDE EN BASE DE DONNÉES
        # =====================================================================
        # Le numéro de commande est généré automatiquement par la méthode de classe
        commande = Commande.objects.create(
            utilisateur=utilisateur,
            numero=Commande.generer_numero(),
            date_livraison=date_livraison,
            date_depart_camions=date_depart_camions,
            total_ht=Decimal(str(total)),  # Conversion en Decimal pour précision
            commentaire=commentaires
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

        # =====================================================================
        # GÉNÉRATION DU FICHIER EDI
        # =====================================================================
        # Le fichier CSV EDI est utilisé pour l'intégration avec le système ERP
        # Les erreurs sont capturées pour ne pas bloquer la validation
        try:
            csv_path = generer_csv_edi(commande, client_distant, lignes)
            print(f"Fichier EDI généré: {csv_path}")
            messages.info(request, f"Fichier EDI généré: {csv_path}")
        except Exception as e:
            # Log détaillé de l'erreur pour le débogage
            error_msg = f"Erreur génération EDI: {e}\n{traceback.format_exc()}"
            print(error_msg)
            messages.warning(request, f"Erreur génération EDI: {e}")

        # =====================================================================
        # FINALISATION DE LA COMMANDE
        # =====================================================================
        # Vidage du panier après validation de la commande
        request.session['panier'] = {}
        request.session.modified = True  # Force la sauvegarde de la session

        # Message de confirmation avec le numéro de commande
        messages.success(request, f'Votre commande n°{commande.numero} a été envoyée avec succès !')
        return redirect('commandes:confirmation')

    # =========================================================================
    # AFFICHAGE DU FORMULAIRE DE COMMANDE (GET)
    # =========================================================================
    # Pré-remplissage des quantités avec le contenu du panier en session
    panier = request.session.get('panier', {})
    for produit in produits:
        # Ajout de la quantité du panier à chaque produit pour pré-remplir le formulaire
        produit['panier_qte'] = panier.get(produit['reference'], 0)

    context = {
        'client': client_distant,
        'produits': produits,
    }

    return render(request, 'cote_client/catalogue/commander.html', context)
