"""
=============================================================================
SUPPRIMER_UTILISATEUR.PY - Vue de suppression d'un utilisateur
=============================================================================

Permet de supprimer un utilisateur avec possibilité de restauration.
La suppression est un "soft delete" : les données sont archivées pendant
5 minutes, permettant une restauration en cas d'erreur.

Processus de suppression :
1. Sauvegarde de toutes les données dans UtilisateurSupprime
2. Sauvegarde des commandes et lignes en JSON
3. Suppression du compte Django (cascade sur Utilisateur, Commandes)
4. Pendant 5 minutes, restauration possible depuis le dashboard

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from clients.models import Utilisateur, UtilisateurSupprime
from commandes.models import Commande
from ..utils.decorators import admin_required


@admin_required
@require_POST
def supprimer_utilisateur(request, utilisateur_id):
    """
    Archive un utilisateur pour suppression avec possibilité de restauration.

    Cette vue effectue un "soft delete" :
    - Les données utilisateur sont sauvegardées dans UtilisateurSupprime
    - Les commandes sont sérialisées en JSON
    - Le compte Django est supprimé (cascade sur tous les objets liés)
    - L'utilisateur peut être restauré pendant 5 minutes

    La sauvegarde inclut :
    - Informations du compte (username, email, mot de passe hashé, etc.)
    - Code tiers et nom du client
    - Toutes les commandes avec leurs lignes

    Args:
        request: L'objet HttpRequest Django
        utilisateur_id (int): L'identifiant de l'utilisateur à supprimer

    Returns:
        HttpResponse: Redirection vers le catalogue utilisateurs

    Raises:
        Http404: Si l'utilisateur n'existe pas
    """
    # Récupérer l'utilisateur à supprimer
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)

    # Récupérer les informations pour le message de confirmation
    client = utilisateur.get_client_distant()
    nom_client = client.nom if client else utilisateur.code_tiers
    username = utilisateur.user.username

    # =========================================================================
    # SÉRIALISATION DES COMMANDES EN JSON
    # =========================================================================
    # Sauvegarde complète des commandes pour permettre la restauration
    commandes_data = []
    commandes = Commande.objects.filter(utilisateur=utilisateur)
    for commande in commandes:
        # Sérialiser chaque ligne de commande
        lignes_data = []
        for ligne in commande.lignes.all():
            lignes_data.append({
                'reference_produit': ligne.reference_produit,
                'nom_produit': ligne.nom_produit,
                'quantite': ligne.quantite,
                'prix_unitaire': str(ligne.prix_unitaire),  # Decimal -> str pour JSON
                'total_ligne': str(ligne.total_ligne),
            })

        # Sérialiser la commande
        commandes_data.append({
            'numero': commande.numero,
            'date_commande': commande.date_commande.isoformat(),
            'date_livraison': commande.date_livraison.isoformat() if commande.date_livraison else None,
            'date_depart_camions': commande.date_depart_camions.isoformat() if commande.date_depart_camions else None,
            'total_ht': str(commande.total_ht),
            'commentaire': commande.commentaire,
            'lignes': lignes_data,
        })

    # =========================================================================
    # CRÉATION DE L'ARCHIVE
    # =========================================================================
    # Sauvegarde de toutes les données pour restauration potentielle
    UtilisateurSupprime.objects.create(
        username=utilisateur.user.username,
        password_hash=utilisateur.user.password,  # Hash du mot de passe, pas le mdp en clair
        email=utilisateur.user.email or '',
        first_name=utilisateur.user.first_name or '',
        last_name=utilisateur.user.last_name or '',
        date_joined=utilisateur.user.date_joined,
        code_tiers=utilisateur.code_tiers,
        nom_client=nom_client,
        commandes_json=commandes_data,
    )

    # =========================================================================
    # SUPPRESSION DU COMPTE
    # =========================================================================
    # La suppression du User Django déclenche la cascade :
    # - Utilisateur (OneToOne avec User)
    # - Commandes (ForeignKey vers Utilisateur)
    # - LigneCommande (ForeignKey vers Commande)
    # - DemandeMotDePasse (ForeignKey vers Utilisateur)
    utilisateur.user.delete()

    messages.success(request, f'L\'utilisateur {username} ({nom_client}) a été supprimé. Vous pouvez le restaurer pendant 5 minutes depuis le tableau de bord.')
    return redirect('administration:catalogue_utilisateur')
