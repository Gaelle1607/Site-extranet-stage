"""
=============================================================================
MENTIONS_LEGALES_ADMIN.PY - Vue des mentions légales (administration)
=============================================================================

Affiche la page des mentions légales dans l'interface d'administration.
Cette page contient les informations légales obligatoires concernant
l'éditeur du site, l'hébergeur et les conditions d'utilisation.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render

from ..utils.decorators import admin_required


@admin_required
def mentions_legales_admin(request):
    """
    Affiche la page des mentions légales.

    Cette page contient les informations légales obligatoires :
    - Identification de l'éditeur
    - Informations sur l'hébergeur
    - Propriété intellectuelle
    - Protection des données personnelles

    Args:
        request: L'objet HttpRequest Django

    Returns:
        HttpResponse: La page mentions_legales.html
    """
    context = {
        'page_title': 'Mentions légales',
    }
    return render(request, 'administration/legal/mentions_legales.html', context)
