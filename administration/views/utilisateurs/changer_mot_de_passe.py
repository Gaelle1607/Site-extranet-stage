"""
=============================================================================
CHANGER_MOT_DE_PASSE.PY - Vue de changement de mot de passe utilisateur
=============================================================================

Permet à un administrateur de changer le mot de passe d'un utilisateur.

Validations :
    - Le mot de passe ne peut pas être vide
    - Les deux saisies doivent correspondre
    - Longueur minimale de 4 caractères
    - Le nouveau mot de passe doit être différent de l'ancien

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST

from clients.models import Utilisateur
from ..utils.decorators import admin_required


@admin_required
@require_POST
def changer_mot_de_passe(request, utilisateur_id):
    """
    Change le mot de passe d'un utilisateur.

    Cette vue est accessible uniquement en POST et permet à un
    administrateur de définir un nouveau mot de passe pour un
    utilisateur.

    Args:
        request: L'objet HttpRequest Django
            POST:
                - nouveau_mdp : Le nouveau mot de passe
                - confirm_mdp : Confirmation du mot de passe
        utilisateur_id (int): L'identifiant de l'utilisateur

    Returns:
        HttpResponse: Redirection vers la fiche utilisateur

    Raises:
        Http404: Si l'utilisateur n'existe pas
    """
    # Récupérer l'utilisateur
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    nouveau_mdp = request.POST.get('nouveau_mdp', '')
    confirm_mdp = request.POST.get('confirm_mdp', '')

    # =========================================================================
    # VALIDATIONS
    # =========================================================================
    if not nouveau_mdp:
        messages.error(request, 'Le mot de passe ne peut pas être vide.')
    elif nouveau_mdp != confirm_mdp:
        messages.error(request, 'Les mots de passe ne correspondent pas.')
    elif len(nouveau_mdp) < 4:
        messages.error(request, 'Le mot de passe doit contenir au moins 4 caractères.')
    elif utilisateur.user.check_password(nouveau_mdp):
        messages.error(request, 'Le nouveau mot de passe doit être différent de l\'ancien.')
    else:
        # =====================================================================
        # CHANGEMENT DU MOT DE PASSE
        # =====================================================================
        utilisateur.user.set_password(nouveau_mdp)
        utilisateur.user.save()

        messages.success(request, f'Mot de passe de {utilisateur.user.username} modifié avec succès.')

    return redirect('administration:information_utilisateur', utilisateur_id=utilisateur_id)
