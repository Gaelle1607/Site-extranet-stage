"""
=============================================================================
VERIFIER_MOT_DE_PASSE_API.PY - API de vérification de mot de passe
=============================================================================

Endpoint API pour vérifier si un nouveau mot de passe est identique
à l'ancien. Utilisé en AJAX pour donner un feedback en temps réel
lors du changement de mot de passe.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from clients.models import Utilisateur
from .decorators import admin_required


@admin_required
@require_POST
def verifier_mot_de_passe_api(request, utilisateur_id):
    """
    API pour vérifier si un mot de passe est identique à l'actuel.

    Cette vue est appelée en AJAX lors de la saisie d'un nouveau mot
    de passe pour vérifier en temps réel s'il est différent de l'ancien.
    Cela permet d'informer l'utilisateur avant la soumission du formulaire.

    La vérification utilise check_password() de Django qui compare
    le mot de passe en clair avec le hash stocké.

    Args:
        request: L'objet HttpRequest Django
            - POST['nouveau_mdp'] : Le mot de passe à vérifier
        utilisateur_id (int): L'identifiant de l'utilisateur

    Returns:
        JsonResponse: {
            'identique': bool  # True si le mot de passe est le même
        }

    Raises:
        Http404: Si l'utilisateur n'existe pas
    """
    # Récupérer l'utilisateur
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    nouveau_mdp = request.POST.get('nouveau_mdp', '')

    # Vérifier si le nouveau mot de passe correspond à l'ancien
    est_identique = utilisateur.user.check_password(nouveau_mdp)

    return JsonResponse({'identique': est_identique})
