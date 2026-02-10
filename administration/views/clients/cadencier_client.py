"""
=============================================================================
CADENCIER_CLIENT.PY - Vue du cadencier d'un client
=============================================================================

Affiche le cadencier (historique des produits commandés) d'un client.
Permet de voir les habitudes d'achat et de commander pour le client.

Le cadencier présente :
    - Liste des produits habituellement commandés par le client
    - Filtres dynamiques basés sur les catégories de produits
    - Recherche par nom ou code produit
    - Lien vers l'inscription si le client n'a pas de compte

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from types import SimpleNamespace

from django.shortcuts import render
from django.db import connections

from clients.models import Utilisateur
from catalogue.services import get_produits_client
from .decorators import admin_required
from .filtres import preparer_filtres, appliquer_filtres


@admin_required
def cadencier_client(request, code_tiers):
    """
    Affiche le cadencier d'un client avec filtres et recherche.

    Le cadencier est l'historique des produits commandés par un client.
    Il permet aux administrateurs de voir les habitudes d'achat et
    potentiellement de créer un compte pour le client.

    Étapes de traitement :
    1. Récupère le nom du client depuis la base distante
    2. Charge les produits du cadencier via le service catalogue
    3. Prépare les filtres dynamiques basés sur les produits
    4. Applique les filtres et la recherche de l'utilisateur

    Args:
        request: L'objet HttpRequest Django
            - GET['q'] : Terme de recherche (optionnel)
            - GET['filtre'] : Liste des filtres actifs (optionnel)
        code_tiers (int): Le code tiers du client dans la base distante

    Returns:
        HttpResponse: La page cadencier_client.html avec :
            - client : Informations du client (tiers, nom)
            - utilisateur : L'utilisateur extranet si inscrit, None sinon
            - produits : Liste des produits filtrés
            - filtres_groupes : Filtres disponibles groupés par catégorie
            - filtres_actifs : Liste des filtres actuellement sélectionnés
            - query : Le terme de recherche saisi
    """
    # =========================================================================
    # RÉCUPÉRATION DU NOM DU CLIENT
    # =========================================================================
    with connections['logigvd'].cursor() as cursor:
        # Priorité à l'entrée principale (complement vide)
        cursor.execute("""
            SELECT nom FROM comcli
            WHERE tiers = %s AND (complement IS NULL OR TRIM(complement) = '')
            ORDER BY nom
            LIMIT 1
        """, [code_tiers])
        row = cursor.fetchone()

        # Si pas d'entrée principale, prendre la première disponible
        if not row:
            cursor.execute("SELECT nom FROM comcli WHERE tiers = %s ORDER BY complement, nom LIMIT 1", [code_tiers])
            row = cursor.fetchone()

    nom_client = row[0] if row and row[0] else str(code_tiers)

    # =========================================================================
    # RÉCUPÉRATION DES PRODUITS DU CADENCIER
    # =========================================================================
    # Créer un objet proxy pour utiliser le service catalogue
    # (le service attend un objet avec un attribut code_tiers)
    utilisateur_proxy = SimpleNamespace(code_tiers=code_tiers)
    produits = get_produits_client(utilisateur_proxy)

    # =========================================================================
    # PRÉPARATION ET APPLICATION DES FILTRES
    # =========================================================================
    # Générer les filtres disponibles basés sur les produits
    produits, filtres_groupes, _ = preparer_filtres(produits)

    # Récupérer les paramètres de filtrage depuis l'URL
    filtres_actifs = request.GET.getlist("filtre")  # Liste des codes de filtres sélectionnés
    query = request.GET.get('q', '').strip()         # Terme de recherche

    # Appliquer les filtres et la recherche
    produits = appliquer_filtres(produits, filtres_actifs, query)

    # =========================================================================
    # VÉRIFICATION DU COMPTE UTILISATEUR
    # =========================================================================
    # Vérifier si un utilisateur extranet est déjà inscrit pour ce client
    utilisateur = Utilisateur.objects.filter(code_tiers=str(code_tiers)).first()

    context = {
        'page_title': f'Cadencier - {nom_client}',
        'client': {'tiers': code_tiers, 'nom': nom_client},
        'utilisateur': utilisateur,  # None si pas de compte
        'produits': produits,
        'query': query,
        'filtres_groupes': filtres_groupes,
        'filtres_actifs': filtres_actifs,
    }
    return render(request, 'administration/clients/cadencier_client.html', context)
