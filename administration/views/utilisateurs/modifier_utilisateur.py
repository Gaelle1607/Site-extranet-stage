"""
=============================================================================
MODIFIER_UTILISATEUR.PY - Vue de modification d'un utilisateur
=============================================================================

Permet de modifier les informations d'un utilisateur existant :
    - Nom d'utilisateur
    - Adresse email
    - Mot de passe (optionnel)

Validations effectuées :
    - Unicité du nom d'utilisateur (si modifié)
    - Unicité de l'email (si modifié)
    - Longueur minimale du mot de passe (4 caractères)
    - Le nouveau mot de passe doit être différent de l'ancien

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.models import User

from clients.models import Utilisateur
from ..utils.decorators import admin_required


@admin_required
def modifier_utilisateur(request, utilisateur_id):
    """
    Permet de modifier les informations d'un utilisateur.

    Cette vue gère à la fois l'affichage du formulaire (GET) et
    le traitement des modifications (POST).

    Champs modifiables :
    - username : Obligatoire, doit être unique
    - email : Obligatoire, doit être unique
    - nouveau_mdp : Optionnel, si fourni doit être différent de l'actuel

    Args:
        request: L'objet HttpRequest Django
            POST:
                - username : Nouveau nom d'utilisateur
                - email : Nouvelle adresse email
                - nouveau_mdp : Nouveau mot de passe (optionnel)
                - confirm_mdp : Confirmation du mot de passe
        utilisateur_id (int): L'identifiant de l'utilisateur

    Returns:
        HttpResponse: Formulaire de modification ou redirection après succès

    Raises:
        Http404: Si l'utilisateur n'existe pas
    """
    # Récupérer l'utilisateur et son compte Django associé
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    user = utilisateur.user

    if request.method == 'POST':
        # Récupérer les nouvelles valeurs du formulaire
        nouveau_username = request.POST.get('username', '').strip()
        nouveau_email = request.POST.get('email', '').strip()
        nouveau_mdp = request.POST.get('nouveau_mdp', '')
        confirm_mdp = request.POST.get('confirm_mdp', '')

        erreurs = []

        # =====================================================================
        # VALIDATION DU NOM D'UTILISATEUR
        # =====================================================================
        if not nouveau_username:
            erreurs.append("Le nom d'utilisateur est obligatoire.")
        elif nouveau_username != user.username and User.objects.filter(username=nouveau_username).exists():
            # Vérifie l'unicité seulement si le username a changé
            erreurs.append("Ce nom d'utilisateur existe déjà.")

        # =====================================================================
        # VALIDATION DE L'EMAIL
        # =====================================================================
        if not nouveau_email:
            erreurs.append("L'adresse email est obligatoire.")
        elif nouveau_email != user.email and User.objects.filter(email=nouveau_email).exists():
            # Vérifie l'unicité seulement si l'email a changé
            erreurs.append("Cette adresse email est déjà utilisée.")

        # =====================================================================
        # VALIDATION DU MOT DE PASSE (optionnel)
        # =====================================================================
        if nouveau_mdp:
            if len(nouveau_mdp) < 4:
                erreurs.append("Le mot de passe doit contenir au moins 4 caractères.")
            elif nouveau_mdp != confirm_mdp:
                erreurs.append("Les mots de passe ne correspondent pas.")
            elif user.check_password(nouveau_mdp):
                erreurs.append("Le nouveau mot de passe doit être différent de l'ancien.")

        # =====================================================================
        # APPLICATION DES MODIFICATIONS
        # =====================================================================
        if erreurs:
            # Afficher toutes les erreurs
            for erreur in erreurs:
                messages.error(request, erreur)
        else:
            # Appliquer les modifications
            user.username = nouveau_username
            user.email = nouveau_email
            if nouveau_mdp:
                user.set_password(nouveau_mdp)
            user.save()

            messages.success(request, f"Les informations de {nouveau_username} ont été mises à jour.")
            return redirect('administration:information_utilisateur', utilisateur_id=utilisateur.id)

    context = {
        'page_title': f'Modifier - {user.username}',
        'utilisateur': utilisateur,
    }
    return render(request, 'administration/utilisateurs/modifier_utilisateur.html', context)
