"""
=============================================================================
VIEWS.PY - Vues de l'application Clients
=============================================================================

Ce module contient les vues Django pour la gestion de l'authentification
et du profil utilisateur côté client.

Fonctionnalités principales :
    - Connexion et déconnexion des utilisateurs
    - Affichage et modification du profil
    - Réinitialisation du mot de passe par email (système de tokens)
    - Page de contact

Architecture :
    - Utilise le système d'authentification Django (User)
    - Lié au modèle Utilisateur pour les informations métier (code_tiers)
    - Accès à la base distante LogiGVD pour les informations client

Sécurité :
    - Protection CSRF automatique via Django
    - Hachage sécurisé des mots de passe
    - Tokens de réinitialisation à usage unique avec expiration

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.cache import never_cache
from .forms import ConnexionForm
from .models import Utilisateur, TokenResetPassword
from catalogue.services import get_client_distant


@never_cache
def connexion(request):
    """
    Gère la page de connexion des utilisateurs.

    Cette vue traite l'authentification des utilisateurs (clients et admins).
    Elle redirige automatiquement les utilisateurs déjà connectés vers
    la page appropriée selon leur rôle.

    Décorateurs :
        @never_cache : Empêche la mise en cache de la page de connexion
                       pour des raisons de sécurité (évite l'affichage
                       de données obsolètes après déconnexion)

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - POST['username'] : Identifiant de l'utilisateur
            - POST['password'] : Mot de passe

    Returns:
        HttpResponse:
            - Si déjà connecté (admin) : Redirection vers 'administration:dashboard'
            - Si déjà connecté (client) : Redirection vers 'catalogue:liste'
            - Si connexion réussie (admin) : Redirection vers 'administration:dashboard'
            - Si connexion réussie (client) : Redirection vers 'recommandations:liste'
            - Sinon : Rendu du template de connexion avec le formulaire

    Workflow :
        1. Vérification si l'utilisateur est déjà connecté
        2. Redirection selon le rôle (admin ou client)
        3. Traitement du formulaire POST si soumis
        4. Authentification via le formulaire ConnexionForm
        5. Message de bienvenue personnalisé avec le nom du client

    Note:
        Les utilisateurs sans profil Utilisateur associé sont déconnectés
        automatiquement pour éviter les erreurs d'accès au catalogue.
    """
    # =========================================================================
    # VÉRIFICATION DE L'ÉTAT DE CONNEXION
    # =========================================================================
    if request.user.is_authenticated:
        # Rediriger les administrateurs vers le dashboard
        if request.user.is_staff:
            return redirect('administration:dashboard')

        # Vérifier que l'utilisateur a un profil utilisateur associé
        if hasattr(request.user, 'utilisateur'):
            return redirect('catalogue:liste')

        # Utilisateur connecté mais sans profil : déconnexion forcée
        # Cela peut arriver si le profil a été supprimé après la connexion
        from django.contrib.auth import logout
        logout(request)
        messages.warning(
            request,
            "Votre compte n'est pas associé à un profil utilisateur. "
            "Veuillez vous reconnecter ou contacter l'administrateur."
        )

    # =========================================================================
    # TRAITEMENT DU FORMULAIRE DE CONNEXION
    # =========================================================================
    if request.method == 'POST':
        # Utilisation du formulaire d'authentification personnalisé
        form = ConnexionForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()

            # Traitement spécial pour les administrateurs
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Bienvenue, {user.username} !")
                return redirect('administration:dashboard')

            # Connexion standard pour les clients
            login(request, user)

            # Récupération du nom du client depuis la base distante
            # pour un message de bienvenue personnalisé
            if hasattr(user, 'utilisateur'):
                client_distant = get_client_distant(user.utilisateur.code_tiers)
                nom_client = client_distant.nom if client_distant else user.username
            else:
                nom_client = user.username

            messages.success(request, f"Bienvenue, {nom_client} !")
            return redirect('recommandations:liste')
    else:
        # Affichage du formulaire vide (GET)
        form = ConnexionForm()

    return render(request, 'cote_client/clients/connexion.html', {'form': form})


def deconnexion(request):
    """
    Déconnecte l'utilisateur et invalide sa session.

    Cette vue termine la session de l'utilisateur connecté et le redirige
    vers la page de connexion avec un message de confirmation.

    Args:
        request (HttpRequest): L'objet requête Django

    Returns:
        HttpResponse: Redirection vers 'clients:connexion' avec message info

    Note:
        La fonction logout() de Django invalide automatiquement la session
        et supprime les cookies d'authentification.
    """
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('clients:connexion')


def contact(request):
    """
    Affiche la page de contact de l'entreprise.

    Cette page présente les coordonnées de l'entreprise Giffaud Groupe
    et permet aux visiteurs de trouver les informations de contact.

    Args:
        request (HttpRequest): L'objet requête Django

    Returns:
        HttpResponse: Rendu du template 'cote_client/contact.html'

    Note:
        Cette page est accessible sans authentification.
    """
    return render(request, 'cote_client/contact.html')


@login_required
def profil(request):
    """
    Affiche la page de profil de l'utilisateur connecté.

    Cette vue présente les informations du profil utilisateur ainsi que
    les données du client récupérées depuis la base de données distante
    (nom, adresse de livraison, etc.).

    Décorateurs :
        @login_required : Redirige vers la page de connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django

    Returns:
        HttpResponse: Rendu du template 'cote_client/clients/profil.html' avec :
            - utilisateur : Instance Utilisateur (profil métier)
            - client : Informations client depuis la base distante (ComCli)

    Note:
        Les informations client (adresse, etc.) proviennent de la base LogiGVD
        et sont en lecture seule. Toute modification doit être faite dans l'ERP.
    """
    utilisateur = request.user.utilisateur

    # Récupération des informations client depuis la base distante
    client_distant = get_client_distant(utilisateur.code_tiers)

    return render(request, 'cote_client/clients/profil.html', {
        'utilisateur': utilisateur,
        'client': client_distant
    })


@login_required
def modifier_mot_de_passe(request):
    """
    Gère la modification du mot de passe de l'utilisateur connecté.

    Cette vue permet à l'utilisateur de changer son mot de passe en
    fournissant son ancien mot de passe et en définissant un nouveau.
    La session est automatiquement mise à jour pour éviter la déconnexion.

    Décorateurs :
        @login_required : Redirige vers la page de connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - POST['old_password'] : Ancien mot de passe
            - POST['new_password1'] : Nouveau mot de passe
            - POST['new_password2'] : Confirmation du nouveau mot de passe

    Returns:
        HttpResponse:
            - POST valide : Redirection vers 'clients:profil' avec message succès
            - POST invalide : Rendu du template avec erreurs de validation
            - GET : Rendu du formulaire vide

    Note:
        La fonction update_session_auth_hash() est utilisée pour mettre à jour
        le hash de session après le changement de mot de passe, ce qui évite
        de déconnecter l'utilisateur.
    """
    utilisateur = request.user.utilisateur
    client_distant = get_client_distant(utilisateur.code_tiers)

    if request.method == 'POST':
        # Utilisation du formulaire Django de changement de mot de passe
        form = PasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            # Sauvegarde du nouveau mot de passe
            user = form.save()

            # Mise à jour du hash de session pour maintenir la connexion
            update_session_auth_hash(request, user)

            messages.success(request, 'Votre mot de passe a été modifié avec succès.')
            return redirect('clients:profil')
        else:
            messages.error(request, 'Veuillez corriger les erreurs ci-dessous.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'cote_client/clients/modifier_mot_de_passe.html', {
        'form': form,
        'utilisateur': utilisateur,
        'client': client_distant
    })


@login_required
def modifier_email(request):
    """
    Gère la modification de l'adresse email de l'utilisateur connecté.

    Cette vue permet à l'utilisateur de changer son adresse email.
    L'email est stocké dans le modèle User de Django.

    Décorateurs :
        @login_required : Redirige vers la page de connexion si non authentifié

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - POST['email'] : Nouvelle adresse email

    Returns:
        HttpResponse:
            - POST valide : Redirection vers 'clients:profil' avec message succès
            - POST invalide : Rendu du template avec erreurs
            - GET : Rendu du formulaire avec l'email actuel
    """
    utilisateur = request.user.utilisateur
    client_distant = get_client_distant(utilisateur.code_tiers)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        # Validation de l'email
        if not email:
            messages.error(request, 'Veuillez saisir une adresse email.')
        elif '@' not in email or '.' not in email:
            messages.error(request, 'Veuillez saisir une adresse email valide.')
        elif User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
            messages.error(request, 'Cette adresse email est déjà utilisée.')
        else:
            # Mise à jour de l'email
            request.user.email = email
            request.user.save()
            messages.success(request, 'Votre adresse email a été modifiée avec succès.')
            return redirect('clients:profil')

    return render(request, 'cote_client/clients/modifier_email.html', {
        'utilisateur': utilisateur,
        'client': client_distant
    })


def demande_mot_de_passe(request):
    """
    Traite la demande de réinitialisation de mot de passe.

    Cette vue permet aux utilisateurs ayant oublié leur mot de passe
    de recevoir un email contenant un lien de réinitialisation sécurisé.
    Un token unique est généré et associé à leur compte.

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - POST['email'] : Adresse email de l'utilisateur

    Returns:
        HttpResponse: Redirection vers 'clients:connexion' avec message

    Workflow :
        1. Récupération et normalisation de l'email (minuscules)
        2. Recherche de l'utilisateur par email
        3. Génération d'un token unique via TokenResetPassword
        4. Construction de l'URL de réinitialisation
        5. Envoi de l'email avec le lien sécurisé

    Sécurité :
        - Le même message est affiché que l'email existe ou non dans la base
          (protection contre l'énumération des comptes)
        - Le token est valide pendant 1 heure
        - Chaque token ne peut être utilisé qu'une seule fois

    Note:
        Les messages de debug (print) sont présents pour le développement
        et devraient être remplacés par un système de logging en production.
    """
    if request.method == 'POST':
        # Récupération et normalisation de l'email
        email = request.POST.get('email', '').strip().lower()

        if not email:
            messages.error(request, "Veuillez entrer votre adresse email.")
            return redirect('clients:connexion')

        # Recherche de l'utilisateur par email (insensible à la casse)
        try:
            user = User.objects.get(email__iexact=email)

            # Génération d'un nouveau token de réinitialisation
            token_obj = TokenResetPassword.generer_token(user)

            # Construction de l'URL de réinitialisation
            from django.urls import reverse
            reset_url = request.build_absolute_uri(
                reverse('clients:reset_password_confirm', args=[token_obj.token])
            )

            # Debug : affichage du lien dans la console (développement)
            print(f"\n{'='*60}")
            print(f"[RESET MDP] Lien de réinitialisation pour {user.username}:")
            print(f"{reset_url}")
            print(f"{'='*60}\n")

            # Envoi de l'email de réinitialisation
            send_mail(
                subject='Réinitialisation de votre mot de passe - Giffaud Groupe',
                message=f"""Bonjour,

Vous avez demandé la réinitialisation de votre mot de passe sur l'Espace Pro Giffaud Groupe.

Cliquez sur le lien ci-dessous pour définir un nouveau mot de passe :
{reset_url}

Ce lien est valable pendant 1 heure.

Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.

Cordialement,
L'équipe Giffaud Groupe""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(
                request,
                "Un email avec le lien de réinitialisation a été envoyé à votre adresse."
            )

        except User.DoesNotExist:
            # Sécurité : même message pour ne pas révéler si l'email existe
            print(f"[RESET MDP] Email non trouvé dans la base de données: {email}")
            messages.success(
                request,
                "Si cette adresse email est associée à un compte, "
                "vous recevrez un email de réinitialisation."
            )

    return redirect('clients:connexion')


def reset_password_confirm(request, token):
    """
    Gère la confirmation de réinitialisation de mot de passe avec token.

    Cette vue permet à l'utilisateur de définir un nouveau mot de passe
    après avoir cliqué sur le lien de réinitialisation reçu par email.
    Elle vérifie la validité du token avant d'autoriser le changement.

    Args:
        request (HttpRequest): L'objet requête Django contenant :
            - POST['password'] : Nouveau mot de passe
            - POST['password_confirm'] : Confirmation du mot de passe
        token (str): Token unique de réinitialisation (64 caractères hex)

    Returns:
        HttpResponse:
            - Token invalide/expiré : Redirection vers 'clients:connexion' avec erreur
            - POST valide : Redirection vers 'clients:connexion' avec succès
            - POST invalide : Rendu du template avec messages d'erreur
            - GET : Rendu du formulaire de nouveau mot de passe

    Validations :
        - Token existe en base de données
        - Token non expiré (< 1 heure depuis création)
        - Token non déjà utilisé
        - Mot de passe non vide
        - Mot de passe >= 4 caractères
        - Confirmation correspond au mot de passe

    Sécurité :
        - Le token est marqué comme utilisé après un changement réussi
        - Les tokens expirés ou invalides sont rejetés
        - Les messages de debug sont présents pour le développement
    """
    # Debug : affichage du token reçu
    print(f"[RESET MDP] Token reçu: {token}")
    print(f"[RESET MDP] Longueur token: {len(token)}")

    # =========================================================================
    # VÉRIFICATION DU TOKEN
    # =========================================================================
    try:
        token_obj = TokenResetPassword.objects.get(token=token)
        print(f"[RESET MDP] Token trouvé pour: {token_obj.user.username}")
    except TokenResetPassword.DoesNotExist:
        # Debug : lister les tokens existants pour diagnostic
        tokens_existants = TokenResetPassword.objects.filter(
            utilise=False
        ).values_list('token', flat=True)[:5]
        print(f"[RESET MDP] Token NON trouvé: {token}")
        print(f"[RESET MDP] Tokens existants (5 premiers): {list(tokens_existants)}")

        messages.error(request, "Le lien de réinitialisation est invalide.")
        return redirect('clients:connexion')

    # Vérification de la validité (expiration et utilisation)
    if not token_obj.est_valide():
        messages.error(
            request,
            "Le lien de réinitialisation a expiré. Veuillez faire une nouvelle demande."
        )
        return redirect('clients:connexion')

    # =========================================================================
    # TRAITEMENT DU FORMULAIRE DE NOUVEAU MOT DE PASSE
    # =========================================================================
    if request.method == 'POST':
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Validation du mot de passe
        if not password:
            messages.error(request, "Veuillez entrer un mot de passe.")
        elif len(password) < 4:
            messages.error(
                request,
                "Le mot de passe doit contenir au moins 4 caractères."
            )
        elif password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            # Changement du mot de passe
            user = token_obj.user
            user.set_password(password)
            user.save()

            # Invalidation du token (usage unique)
            token_obj.utilise = True
            token_obj.save()

            messages.success(
                request,
                "Votre mot de passe a été modifié avec succès. "
                "Vous pouvez maintenant vous connecter."
            )
            return redirect('clients:connexion')

    return render(request, 'cote_client/clients/reset_password.html', {
        'token': token
    })
