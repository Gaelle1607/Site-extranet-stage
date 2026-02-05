"""
=============================================================================
RESET_PASSWORD_ADMIN.PY - Réinitialisation de mot de passe admin
=============================================================================

Permet de réinitialiser le mot de passe d'un administrateur sans
être connecté, en utilisant une clé secrète stockée sur le serveur.

Cette fonctionnalité est utile quand un administrateur a perdu son
mot de passe et ne peut plus se connecter.

Sécurité :
    - La clé secrète est stockée dans reset_key.py sur le serveur
    - Seules les personnes ayant accès au serveur peuvent la connaître
    - Ne fonctionne que pour les comptes staff (is_staff=True)

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages


def reset_password_admin(request):
    """
    Page de réinitialisation du mot de passe admin avec clé secrète.

    Cette vue est accessible SANS authentification car elle sert
    justement quand un admin ne peut plus se connecter. La sécurité
    repose sur la clé secrète stockée sur le serveur.

    Pour utiliser cette fonctionnalité :
    1. Accéder au serveur pour récupérer la clé dans reset_key.py
    2. Aller sur /administration/reset-password/
    3. Entrer le nom d'utilisateur, la clé secrète et le nouveau mot de passe

    Validations :
    - La clé secrète doit correspondre à celle du serveur
    - Le nom d'utilisateur doit exister et être un staff
    - Le mot de passe doit respecter les règles de validation

    Args:
        request: L'objet HttpRequest Django
            POST:
                - username : Le nom d'utilisateur admin
                - secret_key : La clé secrète du serveur
                - nouveau_mdp : Le nouveau mot de passe
                - confirm_mdp : Confirmation du mot de passe

    Returns:
        HttpResponse: Le formulaire ou redirection vers la connexion
    """
    # Import local pour éviter les imports circulaires
    from ..reset_key import RESET_SECRET_KEY

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        secret_key = request.POST.get('secret_key', '').strip()
        nouveau_mdp = request.POST.get('nouveau_mdp', '')
        confirm_mdp = request.POST.get('confirm_mdp', '')

        # =====================================================================
        # VALIDATIONS
        # =====================================================================
        if secret_key != RESET_SECRET_KEY:
            messages.error(request, 'Clé secrète incorrecte.')
        elif not username:
            messages.error(request, 'Veuillez entrer un nom d\'utilisateur.')
        elif not nouveau_mdp:
            messages.error(request, 'Le nouveau mot de passe ne peut pas être vide.')
        elif nouveau_mdp != confirm_mdp:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        elif len(nouveau_mdp) < 4:
            messages.error(request, 'Le mot de passe doit contenir au moins 4 caractères.')
        else:
            # =================================================================
            # RÉINITIALISATION DU MOT DE PASSE
            # =================================================================
            try:
                # Chercher uniquement parmi les administrateurs (is_staff=True)
                user = User.objects.get(username=username, is_staff=True)
                user.set_password(nouveau_mdp)
                user.save()
                messages.success(request, f'Mot de passe de {username} réinitialisé avec succès. Vous pouvez maintenant vous connecter.')
                return redirect('clients:connexion')
            except User.DoesNotExist:
                messages.error(request, 'Aucun administrateur trouvé avec ce nom d\'utilisateur.')

    return render(request, 'administration/reset_password.html')
