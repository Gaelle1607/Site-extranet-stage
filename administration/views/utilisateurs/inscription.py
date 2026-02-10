"""
=============================================================================
INSCRIPTION.PY - Vue d'inscription des utilisateurs et administrateurs
=============================================================================

Gère l'inscription de deux types de comptes :
1. Utilisateurs clients : liés à un code tiers de la base distante
2. Administrateurs : comptes staff sans lien client

Validations effectuées :
    - Correspondance des mots de passe
    - Unicité du nom d'utilisateur
    - Unicité de l'email (pour les utilisateurs)
    - Existence du code tiers dans la base distante
    - Un seul compte utilisateur par code tiers

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages

from clients.models import Utilisateur
from catalogue.models import ComCli
from .decorators import admin_required


@admin_required
def inscription(request):
    """
    Gère l'inscription d'un nouvel utilisateur ou administrateur.

    Cette vue traite deux formulaires différents selon form_type :
    - 'admin' : Création d'un compte administrateur (is_staff=True)
    - autre : Création d'un compte utilisateur lié à un client

    Pour les utilisateurs clients :
    - Le code_tiers doit exister dans la base distante (comcli)
    - Un seul compte est autorisé par code_tiers
    - L'email est obligatoire

    La vue accepte aussi des paramètres GET pour pré-remplir le formulaire
    depuis le cadencier client (tiers et nom).

    Args:
        request: L'objet HttpRequest Django
            POST:
                - form_type : 'admin' ou autre
                - Pour admin : admin_username, admin_password, admin_password_confirm
                - Pour user : client (code_tiers), username, email, password, password_confirm
            GET:
                - tiers : Pré-remplissage du code tiers
                - nom : Pré-remplissage du nom client

    Returns:
        HttpResponse: La page inscription.html ou redirection après succès
    """
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'admin':
            # =========================================================
            # INSCRIPTION D'UN ADMINISTRATEUR
            # =========================================================
            username = request.POST.get('admin_username')
            password = request.POST.get('admin_password')
            password_confirm = request.POST.get('admin_password_confirm')

            # Validation des mots de passe
            if password != password_confirm:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
            # Vérification de l'unicité du nom d'utilisateur
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
            else:
                # Créer le compte Django avec le flag staff
                user = User.objects.create_user(username=username, password=password)
                user.is_staff = True
                user.save()
                messages.success(request, f'Administrateur {username} créé avec succès.')
                return redirect('administration:inscription')
        else:
            # =========================================================
            # INSCRIPTION D'UN UTILISATEUR CLIENT
            # =========================================================
            code_tiers = request.POST.get('client')
            username = request.POST.get('username')
            email = request.POST.get('email', '').strip()
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')

            # Validations successives
            if password != password_confirm:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
            elif not email:
                messages.error(request, 'L\'adresse email est obligatoire.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Cette adresse email est déjà utilisée.')
            elif Utilisateur.objects.filter(code_tiers=code_tiers).exists():
                messages.error(request, 'Ce client a déjà un compte utilisateur.')
            elif not ComCli.objects.using('logigvd').filter(tiers=code_tiers).exists():
                messages.error(request, 'Ce code client n\'existe pas.')
            else:
                # Créer le compte Django avec email
                user = User.objects.create_user(username=username, email=email, password=password)
                # Créer le profil Utilisateur lié au code tiers client
                Utilisateur.objects.create(user=user, code_tiers=code_tiers)
                messages.success(request, f'Utilisateur {username} créé avec succès.')
                return redirect('administration:catalogue_utilisateur')

    # Pré-remplissage depuis le cadencier client (paramètres GET)
    prefill_tiers = request.GET.get('tiers', '')
    prefill_nom = request.GET.get('nom', '')

    context = {
        'page_title': 'Inscription',
        'prefill_tiers': prefill_tiers,
        'prefill_nom': prefill_nom,
    }
    return render(request, 'administration/utilisateurs/inscription.html', context)
