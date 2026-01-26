from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import ConnexionForm
from catalogue.services import get_client_distant


def connexion(request):
    """Page de connexion"""
    if request.user.is_authenticated:
        # Rediriger les admins vers l'administration
        if request.user.is_staff:
            return redirect('administration:dashboard')
        # Vérifier que l'utilisateur a un profil utilisateur
        if hasattr(request.user, 'utilisateur'):
            return redirect('catalogue:liste')
        # Sinon, le déconnecter pour qu'il puisse se reconnecter avec un compte valide
        from django.contrib.auth import logout
        logout(request)
        messages.warning(request, "Votre compte n'est pas associé à un profil utilisateur. Veuillez vous reconnecter ou contacter l'administrateur.")

    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Rediriger les admins vers l'administration
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Bienvenue, {user.username} !")
                return redirect('administration:dashboard')
            # Vérifier que l'utilisateur est actif
            if hasattr(user, 'utilisateur') and not user.utilisateur.actif:
                messages.error(request, "Votre compte est désactivé. Contactez votre commercial.")
                return render(request, 'cote_client/clients/connexion.html', {'form': form})
            login(request, user)
            # Récupérer le nom du client distant
            if hasattr(user, 'utilisateur'):
                client_distant = get_client_distant(user.utilisateur.code_tiers)
                nom_client = client_distant.nom if client_distant else user.username
            else:
                nom_client = user.username
            messages.success(request, f"Bienvenue, {nom_client} !")
            return redirect('recommandations:liste')
    else:
        form = ConnexionForm()

    return render(request, 'cote_client/clients/connexion.html', {'form': form})


def deconnexion(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('clients:connexion')

def contact(request):
    """Page de contact"""
    return render(request, 'cote_client/contact.html')


@login_required
def profil(request):
    """Page de profil utilisateur"""
    utilisateur = request.user.utilisateur
    # Récupérer les infos client depuis la base distante
    client_distant = get_client_distant(utilisateur.code_tiers)
    return render(request, 'cote_client/clients/profil.html', {
        'utilisateur': utilisateur,
        'client': client_distant
    })


@login_required
def modifier_mot_de_passe(request):
    """Modification du mot de passe"""
    utilisateur = request.user.utilisateur
    client_distant = get_client_distant(utilisateur.code_tiers)

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
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
