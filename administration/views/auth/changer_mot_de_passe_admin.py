"""
=============================================================================
CHANGER_MOT_DE_PASSE_ADMIN.PY - Changement de mot de passe admin
=============================================================================

Permet à un administrateur de changer son propre mot de passe.
Nécessite la saisie de l'ancien mot de passe pour confirmation.

Validations :
    - L'ancien mot de passe doit être correct
    - Le nouveau mot de passe ne peut pas être vide
    - Les deux saisies doivent correspondre
    - Longueur minimale de 4 caractères
    - Le nouveau mot de passe doit être différent de l'ancien

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash

from .decorators import admin_required


@admin_required
@require_POST
def changer_mot_de_passe_admin(request):
    """
    Permet à l'administrateur de changer son propre mot de passe.

    Cette vue traite le changement de mot de passe pour l'utilisateur
    actuellement connecté (request.user). Elle nécessite la saisie
    de l'ancien mot de passe pour sécuriser l'opération.

    Après un changement réussi, la session est mise à jour pour éviter
    que l'utilisateur soit déconnecté (comportement par défaut de Django
    après changement de mot de passe).

    Args:
        request: L'objet HttpRequest Django
            POST:
                - ancien_mdp : Le mot de passe actuel
                - nouveau_mdp : Le nouveau mot de passe
                - confirm_mdp : Confirmation du nouveau mot de passe

    Returns:
        HttpResponse: Redirection vers la page de profil
    """
    ancien_mdp = request.POST.get('ancien_mdp', '')
    nouveau_mdp = request.POST.get('nouveau_mdp', '')
    confirm_mdp = request.POST.get('confirm_mdp', '')

    # =========================================================================
    # VALIDATIONS
    # =========================================================================
    if not request.user.check_password(ancien_mdp):
        messages.error(request, 'Le mot de passe actuel est incorrect.')
    elif not nouveau_mdp:
        messages.error(request, 'Le nouveau mot de passe ne peut pas être vide.')
    elif nouveau_mdp != confirm_mdp:
        messages.error(request, 'Les mots de passe ne correspondent pas.')
    elif len(nouveau_mdp) < 4:
        messages.error(request, 'Le mot de passe doit contenir au moins 4 caractères.')
    elif nouveau_mdp == ancien_mdp:
        messages.error(request, 'Le nouveau mot de passe doit être différent de l\'ancien.')
    else:
        # =====================================================================
        # CHANGEMENT DU MOT DE PASSE
        # =====================================================================
        request.user.set_password(nouveau_mdp)
        request.user.save()

        # Mettre à jour la session pour éviter la déconnexion
        # Django invalide normalement la session après changement de mot de passe
        update_session_auth_hash(request, request.user)

        messages.success(request, 'Votre mot de passe a été modifié avec succès.')

    return redirect('administration:profil_admin')
