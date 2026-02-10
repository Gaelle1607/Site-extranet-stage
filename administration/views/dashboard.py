"""
=============================================================================
DASHBOARD.PY - Vue du tableau de bord administrateur
=============================================================================

Ce fichier contient la vue principale du dashboard d'administration.
Il agrège les données de différentes sources pour présenter une vue
d'ensemble de l'activité du système.

Données affichées :
    - Statistiques : nombre d'utilisateurs, commandes, clients
    - Activités récentes : dernières commandes, nouveaux utilisateurs
    - Demandes en attente : demandes de mot de passe non traitées
    - Éléments supprimés : commandes/utilisateurs en attente de restauration

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from datetime import timedelta

from django.shortcuts import render
from django.db import connections
from django.utils import timezone

from clients.models import Utilisateur, DemandeMotDePasse, UtilisateurSupprime, HistoriqueSuppressionUtilisateur
from commandes.models import Commande, CommandeSupprimee, HistoriqueSuppression
from .utils.decorators import admin_required


@admin_required
def dashboard(request):
    """
    Affiche le tableau de bord principal de l'administration.

    Cette vue agrège plusieurs types de données :
    1. Statistiques globales (compteurs)
    2. Activités récentes (5 dernières)
    3. Demandes de mot de passe en attente
    4. Commandes et utilisateurs supprimés (restaurables)

    Le dashboard effectue aussi un nettoyage automatique des éléments
    supprimés dont le délai de restauration a expiré (5 minutes).

    Args:
        request: L'objet HttpRequest Django

    Returns:
        HttpResponse: La page dashboard.html avec le contexte
    """
    # =========================================================================
    # NETTOYAGE AUTOMATIQUE
    # =========================================================================
    # Supprime définitivement les éléments dont le délai de restauration
    # a expiré (5 minutes par défaut)
    CommandeSupprimee.nettoyer_anciennes()
    UtilisateurSupprime.nettoyer_anciens()

    # =========================================================================
    # STATISTIQUES GLOBALES
    # =========================================================================
    # Compte les utilisateurs extranet (exclut les admins et superusers)
    nb_utilisateurs = Utilisateur.objects.filter(user__is_staff=False, user__is_superuser=False).count()

    # Compte total des commandes passées via l'extranet
    nb_commandes = Commande.objects.count()

    # Compte les clients distincts dans la base distante LogiGVD
    # Requête SQL directe car la table n'est pas gérée par un modèle Django
    with connections['logigvd'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM (SELECT 1 FROM comcli WHERE tiers != 0 GROUP BY tiers, complement) t")
        nb_clients = cursor.fetchone()[0]

    # =========================================================================
    # ACTIVITÉS RÉCENTES
    # =========================================================================
    # Récupère les 5 dernières commandes avec leurs utilisateurs associés
    dernieres_commandes = Commande.objects.select_related('utilisateur', 'utilisateur__user').order_by('-date_commande')[:5]

    # Récupère les 5 derniers utilisateurs créés (hors administrateurs)
    derniers_utilisateurs = Utilisateur.objects.filter(
        user__is_staff=False, user__is_superuser=False
    ).select_related('user').order_by('-user__date_joined')[:5]

    # =========================================================================
    # ÉLÉMENTS SUPPRIMÉS (RESTAURABLES)
    # =========================================================================
    # Commandes en attente de restauration ou de suppression définitive
    commandes_supprimees = CommandeSupprimee.objects.select_related('utilisateur', 'utilisateur__user').order_by('-date_suppression')

    # Utilisateurs en attente de restauration ou de suppression définitive
    utilisateurs_supprimes = UtilisateurSupprime.objects.order_by('-date_suppression')

    # =========================================================================
    # CONSTRUCTION DE LA LISTE DES ACTIVITÉS
    # =========================================================================
    # Liste unifiée de toutes les activités récentes pour affichage chronologique
    activites = []

    # Ajouter les nouvelles commandes
    for commande in dernieres_commandes:
        # Récupérer le nom du client depuis la base distante
        client = commande.utilisateur.get_client_distant()
        nom_client = client.nom if client else commande.utilisateur.code_tiers
        activites.append({
            'type': 'commande',
            'date': commande.date_commande,
            'description': f"Nouvelle commande {commande.numero} passée par {nom_client}",
            'commande': commande,
        })

    # Ajouter les nouveaux utilisateurs
    for utilisateur in derniers_utilisateurs:
        client = utilisateur.get_client_distant()
        nom_client = client.nom if client else utilisateur.code_tiers
        activites.append({
            'type': 'utilisateur',
            'date': utilisateur.user.date_joined,
            'description': f"Nouvel utilisateur créé : {nom_client} ({utilisateur.user.username})",
            'utilisateur': utilisateur,
        })

    # Ajouter les commandes supprimées (restaurables)
    for commande_supp in commandes_supprimees:
        client = commande_supp.utilisateur.get_client_distant()
        nom_client = client.nom if client else commande_supp.utilisateur.code_tiers
        activites.append({
            'type': 'suppression',
            'date': commande_supp.date_suppression,
            'description': f"Commande {commande_supp.numero} supprimée ({nom_client})",
            'commande_supprimee': commande_supp,
            'temps_restant': commande_supp.temps_restant(),
        })

    # =========================================================================
    # HISTORIQUE DES SUPPRESSIONS DÉFINITIVES
    # =========================================================================
    # Récupérer les suppressions définitives des dernières 24h
    limite_historique = timezone.now() - timedelta(hours=24)
    suppressions_definitives = HistoriqueSuppression.objects.filter(
        date_suppression_definitive__gte=limite_historique
    ).order_by('-date_suppression_definitive')[:5]

    for supp in suppressions_definitives:
        activites.append({
            'type': 'suppression_definitive',
            'date': supp.date_suppression_definitive,
            'description': f"Commande {supp.numero} supprimée définitivement ({supp.nom_client})",
            'historique': supp,
        })

    # Ajouter les utilisateurs supprimés aux activités
    for utilisateur_supp in utilisateurs_supprimes:
        activites.append({
            'type': 'suppression_utilisateur',
            'date': utilisateur_supp.date_suppression,
            'description': f"Utilisateur {utilisateur_supp.username} supprimé ({utilisateur_supp.nom_client})",
            'utilisateur_supprime': utilisateur_supp,
            'temps_restant': utilisateur_supp.temps_restant(),
        })

    # Récupérer les suppressions définitives d'utilisateurs récentes
    suppressions_definitives_utilisateurs = HistoriqueSuppressionUtilisateur.objects.filter(
        date_suppression_definitive__gte=limite_historique
    ).order_by('-date_suppression_definitive')[:5]

    for supp in suppressions_definitives_utilisateurs:
        activites.append({
            'type': 'suppression_definitive_utilisateur',
            'date': supp.date_suppression_definitive,
            'description': f"Utilisateur {supp.username} supprimé définitivement ({supp.nom_client})",
            'historique_utilisateur': supp,
        })

    # Trier par date décroissante et prendre les 5 plus récentes
    activites.sort(key=lambda x: x['date'], reverse=True)
    activites = activites[:5]

    # =========================================================================
    # DEMANDES DE MOT DE PASSE EN ATTENTE
    # =========================================================================
    demandes_mdp = DemandeMotDePasse.objects.filter(traitee=False).select_related(
        'utilisateur', 'utilisateur__user'
    ).order_by('-date_demande')

    # Enrichir avec le nom du client pour l'affichage
    demandes_mdp_liste = []
    for demande in demandes_mdp:
        client = demande.utilisateur.get_client_distant()
        demandes_mdp_liste.append({
            'demande': demande,
            'nom_client': client.nom if client else demande.utilisateur.code_tiers,
        })

    # =========================================================================
    # LISTES POUR AFFICHAGE SÉPARÉ
    # =========================================================================
    # Liste des commandes supprimées avec informations enrichies
    commandes_supprimees_liste = []
    for cs in commandes_supprimees:
        client = cs.utilisateur.get_client_distant()
        commandes_supprimees_liste.append({
            'commande': cs,
            'nom_client': client.nom if client else cs.utilisateur.code_tiers,
            'temps_restant': cs.temps_restant(),
        })

    # Liste des utilisateurs supprimés avec informations enrichies
    utilisateurs_supprimes_liste = []
    for us in utilisateurs_supprimes:
        utilisateurs_supprimes_liste.append({
            'utilisateur': us,
            'nom_client': us.nom_client,
            'temps_restant': us.temps_restant(),
            'nb_commandes': len(us.commandes_json),  # Nombre de commandes sauvegardées
        })

    # =========================================================================
    # PRÉPARATION DU CONTEXTE POUR LE TEMPLATE
    # =========================================================================
    context = {
        'page_title': 'Administration',
        # Statistiques
        'nb_utilisateurs': nb_utilisateurs,
        'nb_commandes': nb_commandes,
        'nb_clients': nb_clients,
        # Activités
        'activites': activites,
        # Demandes de mot de passe
        'demandes_mdp': demandes_mdp_liste,
        'nb_demandes_mdp': len(demandes_mdp_liste),
        # Éléments supprimés
        'commandes_supprimees': commandes_supprimees_liste,
        'nb_commandes_supprimees': len(commandes_supprimees_liste),
        'utilisateurs_supprimes': utilisateurs_supprimes_liste,
        'nb_utilisateurs_supprimes': len(utilisateurs_supprimes_liste),
    }
    return render(request, 'administration/dashboard.html', context)
