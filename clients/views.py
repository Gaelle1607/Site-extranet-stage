from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from .forms import ConnexionForm


def connexion(request):
    """Page de connexion"""
    if request.user.is_authenticated:
        # Rediriger les admins vers l'administration
        if request.user.is_staff:
            return redirect('administration:dashboard')
        # Vérifier que l'utilisateur a un profil client
        if hasattr(request.user, 'client'):
            return redirect('catalogue:liste')
        # Sinon, le déconnecter pour qu'il puisse se reconnecter avec un compte valide
        from django.contrib.auth import logout
        logout(request)
        messages.warning(request, "Votre compte n'est pas associé à un profil client. Veuillez vous reconnecter ou contacter l'administrateur.")

    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Rediriger les admins vers l'administration
            if user.is_staff:
                login(request, user)
                messages.success(request, f"Bienvenue, {user.username} !")
                return redirect('administration:dashboard')
            # Vérifier que le client est actif
            if hasattr(user, 'client') and not user.client.actif:
                messages.error(request, "Votre compte est désactivé. Contactez votre commercial.")
                return render(request, 'clients/connexion.html', {'form': form})
            login(request, user)
            messages.success(request, f"Bienvenue, {user.client.nom if hasattr(user, 'client') else user.username} !")
            return redirect('recommandations:liste')
    else:
        form = ConnexionForm()

    return render(request, 'clients/connexion.html', {'form': form})


def deconnexion(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('clients:connexion')

def contact(request):
    """Page de contact"""
    return render(request, 'contact.html')


@login_required
def profil(request):
    """Page de profil utilisateur"""
    client = request.user.client
    return render(request, 'clients/profil.html', {'client': client})


@login_required
def modifier_mot_de_passe(request):
    """Modification du mot de passe"""
    client = request.user.client

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

    return render(request, 'clients/modifier_mot_de_passe.html', {
        'form': form,
        'client': client
    })
