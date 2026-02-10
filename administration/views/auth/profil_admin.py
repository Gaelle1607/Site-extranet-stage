"""
=============================================================================
PROFIL_ADMIN.PY - Vue du profil administrateur
=============================================================================

Affiche la page de profil de l'administrateur connecté.
Permet de consulter ses informations et d'accéder au changement
de mot de passe.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render

from .decorators import admin_required


@admin_required
def profil_admin(request):
    """
    Affiche la page de profil de l'administrateur connecté.

    Cette page permet à l'administrateur de :
    - Voir ses informations de compte (username, date de connexion)
    - Accéder au formulaire de changement de mot de passe

    L'utilisateur connecté est automatiquement disponible dans le
    template via request.user.

    Args:
        request: L'objet HttpRequest Django

    Returns:
        HttpResponse: La page profil_admin.html
    """
    context = {
        'page_title': 'Mon profil',
    }
    return render(request, 'administration/auth/profil_admin.html', context)
