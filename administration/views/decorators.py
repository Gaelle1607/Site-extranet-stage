"""
=============================================================================
DECORATORS.PY - Décorateurs et utilitaires pour l'administration
=============================================================================

Ce fichier contient les décorateurs utilisés pour protéger les vues
d'administration et les constantes de configuration.

Décorateurs disponibles :
    - @admin_required : Restreint l'accès aux utilisateurs staff uniquement

Constantes :
    - EDI_OUTPUT_DIR : Répertoire de sortie des fichiers EDI (exports)

Utilisation :
    from .decorators import admin_required

    @admin_required
    def ma_vue(request):
        # Cette vue n'est accessible qu'aux administrateurs
        ...

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.contrib.auth.decorators import user_passes_test
from pathlib import Path


# =============================================================================
# CONSTANTES DE CONFIGURATION
# =============================================================================
# Répertoire où sont exportés les fichiers EDI (échange de données)
# Ces fichiers sont générés lors de l'export des commandes
EDI_OUTPUT_DIR = Path(r'C:\Users\Giffaud\Documents\Site_extranet\edi_exports')


# =============================================================================
# FONCTIONS DE VÉRIFICATION
# =============================================================================
def is_admin(user):
    """
    Vérifie si l'utilisateur a les droits d'administration.

    Un administrateur est un utilisateur qui :
    - Est authentifié (connecté)
    - A le flag is_staff=True sur son compte Django

    Args:
        user: L'objet User Django à vérifier

    Returns:
        bool: True si l'utilisateur est administrateur, False sinon
    """
    return user.is_authenticated and user.is_staff


# =============================================================================
# DÉCORATEURS
# =============================================================================
def admin_required(view_func):
    """
    Décorateur qui restreint l'accès d'une vue aux administrateurs.

    Si l'utilisateur n'est pas administrateur, il est redirigé vers
    la page de connexion avec le paramètre 'next' pour revenir après
    authentification.

    Args:
        view_func: La fonction de vue à protéger

    Returns:
        function: La vue décorée avec vérification des droits

    Exemple:
        @admin_required
        def dashboard(request):
            return render(request, 'administration/dashboard.html')
    """
    decorated_view = user_passes_test(
        is_admin,                       # Fonction de vérification
        login_url='clients:connexion',  # URL de redirection si non autorisé
        redirect_field_name='next'      # Paramètre pour la redirection post-login
    )(view_func)
    return decorated_view
