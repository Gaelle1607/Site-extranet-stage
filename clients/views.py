from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from .forms import ConnexionForm


def connexion(request):
    """Page de connexion"""
    if request.user.is_authenticated:
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
