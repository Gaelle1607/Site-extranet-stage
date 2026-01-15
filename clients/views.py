from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import ConnexionForm


def connexion(request):
    """Page de connexion"""
    if request.user.is_authenticated:
        return redirect('catalogue:liste')

    if request.method == 'POST':
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Vérifier que le client est actif
            if hasattr(user, 'client') and not user.client.actif:
                messages.error(request, "Votre compte est désactivé. Contactez votre commercial.")
                return render(request, 'clients/connexion.html', {'form': form})
            login(request, user)
            messages.success(request, f"Bienvenue, {user.client.nom if hasattr(user, 'client') else user.username} !")
            return redirect('catalogue:liste')
    else:
        form = ConnexionForm()

    return render(request, 'clients/connexion.html', {'form': form})


def deconnexion(request):
    """Déconnexion"""
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('clients:connexion')
