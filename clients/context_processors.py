from .models import DemandeMotDePasse


def demandes_mdp_count(request):
    """Ajoute le nombre de demandes de mot de passe non traitées au contexte."""
    if request.user.is_authenticated and request.user.is_staff:
        count = DemandeMotDePasse.objects.filter(traitee=False).count()
        return {'nb_demandes_mdp_global': count}
    return {'nb_demandes_mdp_global': 0}
