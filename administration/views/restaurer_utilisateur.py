"""
=============================================================================
RESTAURER_UTILISATEUR.PY - Vue de restauration d'un utilisateur supprimé
=============================================================================

Permet de restaurer un utilisateur supprimé pendant le délai de grâce
(5 minutes par défaut).

Processus de restauration :
1. Vérification que le délai n'est pas dépassé
2. Vérification qu'aucun nouveau compte n'utilise le même username
3. Recréation du compte Django avec le mot de passe hashé original
4. Recréation de l'utilisateur extranet
5. Recréation de toutes les commandes et leurs lignes
6. Suppression de l'archive

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from decimal import Decimal
from datetime import datetime

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.http import require_POST

from clients.models import Utilisateur, UtilisateurSupprime
from commandes.models import Commande, LigneCommande
from .decorators import admin_required


@admin_required
@require_POST
def restaurer_utilisateur(request, utilisateur_supprime_id):
    """
    Restaure un utilisateur précédemment supprimé.

    Cette vue recrée entièrement un utilisateur à partir de l'archive :
    - Compte Django (User) avec le hash de mot de passe original
    - Profil Utilisateur lié au code tiers
    - Toutes les commandes avec leurs dates originales
    - Toutes les lignes de commande

    Vérifications préalables :
    - Le délai de restauration (5 min) ne doit pas être dépassé
    - Aucun utilisateur ne doit avoir pris le même username

    Args:
        request: L'objet HttpRequest Django
        utilisateur_supprime_id (int): L'ID de l'archive à restaurer

    Returns:
        HttpResponse: Redirection vers le dashboard

    Raises:
        Http404: Si l'archive n'existe pas
    """
    # Récupérer l'archive de l'utilisateur supprimé
    utilisateur_supprime = get_object_or_404(UtilisateurSupprime, id=utilisateur_supprime_id)

    # =========================================================================
    # VÉRIFICATIONS PRÉALABLES
    # =========================================================================
    # Vérifier que le délai de restauration n'est pas dépassé
    if not utilisateur_supprime.est_restaurable():
        messages.error(request, f'L\'utilisateur {utilisateur_supprime.username} ne peut plus être restauré (délai de 5 minutes dépassé).')
        utilisateur_supprime.delete()  # Nettoyer l'archive expirée
        return redirect('administration:dashboard')

    # Vérifier qu'aucun nouvel utilisateur n'a pris le username
    if User.objects.filter(username=utilisateur_supprime.username).exists():
        messages.error(request, f'Un utilisateur avec le nom {utilisateur_supprime.username} existe déjà.')
        return redirect('administration:dashboard')

    # =========================================================================
    # RECRÉATION DU COMPTE DJANGO
    # =========================================================================
    # Créer le User avec le hash de mot de passe original
    user = User(
        username=utilisateur_supprime.username,
        password=utilisateur_supprime.password_hash,  # Hash original, pas besoin de set_password
        email=utilisateur_supprime.email,
        first_name=utilisateur_supprime.first_name,
        last_name=utilisateur_supprime.last_name,
    )
    user.save()

    # Restaurer la date d'inscription originale (contourne auto_now_add)
    User.objects.filter(id=user.id).update(date_joined=utilisateur_supprime.date_joined)

    # =========================================================================
    # RECRÉATION DU PROFIL UTILISATEUR
    # =========================================================================
    utilisateur = Utilisateur.objects.create(
        user=user,
        code_tiers=utilisateur_supprime.code_tiers,
    )

    # =========================================================================
    # RECRÉATION DES COMMANDES
    # =========================================================================
    for commande_data in utilisateur_supprime.commandes_json:
        # Parser les dates depuis le format ISO
        date_commande = datetime.fromisoformat(commande_data['date_commande'])
        date_livraison = None
        if commande_data.get('date_livraison'):
            date_livraison = datetime.fromisoformat(commande_data['date_livraison']).date()
        date_depart = None
        if commande_data.get('date_depart_camions'):
            date_depart = datetime.fromisoformat(commande_data['date_depart_camions']).date()

        # Créer la commande
        commande = Commande.objects.create(
            utilisateur=utilisateur,
            numero=commande_data['numero'],
            date_livraison=date_livraison,
            date_depart_camions=date_depart,
            total_ht=Decimal(commande_data['total_ht']),
            commentaire=commande_data.get('commentaire', ''),
        )

        # Restaurer la date de commande originale (contourne auto_now_add)
        Commande.objects.filter(id=commande.id).update(date_commande=date_commande)

        # Recréer les lignes de commande
        for ligne_data in commande_data.get('lignes', []):
            LigneCommande.objects.create(
                commande=commande,
                reference_produit=ligne_data['reference_produit'],
                nom_produit=ligne_data['nom_produit'],
                quantite=ligne_data['quantite'],
                prix_unitaire=Decimal(ligne_data['prix_unitaire']),
                total_ligne=Decimal(ligne_data['total_ligne']),
            )

    # =========================================================================
    # NETTOYAGE
    # =========================================================================
    # Supprimer l'archive maintenant que la restauration est complète
    utilisateur_supprime.delete()

    messages.success(request, f'L\'utilisateur {user.username} ({utilisateur_supprime.nom_client}) a été restauré avec succès.')
    return redirect('administration:dashboard')
