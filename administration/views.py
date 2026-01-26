from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from clients.models import Utilisateur
from commandes.models import Commande
from catalogue.services import get_produits_client
from catalogue.models import ComCli


def is_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.is_staff


def admin_required(view_func):
    """Décorateur pour restreindre l'accès aux administrateurs"""
    decorated_view = user_passes_test(
        is_admin,
        login_url='clients:connexion',
        redirect_field_name='next'
    )(view_func)
    return decorated_view


@admin_required
def dashboard(request):
    """Dashboard administrateur"""
    # Compter les utilisateurs (non staff, non superuser)
    nb_utilisateurs = Utilisateur.objects.filter(user__is_staff=False, user__is_superuser=False).count()
    nb_commandes = Commande.objects.count()
    nb_clients = ComCli.objects.count()

    context = {
        'page_title': 'Administration',
        'nb_utilisateurs': nb_utilisateurs,
        'nb_commandes': nb_commandes,
        'nb_clients': nb_clients,
    }
    return render(request, 'administration/dashboard.html', context)

@admin_required
def liste_commande(request):
    """Liste des commandes"""
    commandes = Commande.objects.all()

    # Recherche
    query = request.GET.get('q', '')
    if query:
        # Convertir les espaces en underscores pour la recherche de statut
        query_statut = query.replace(' ', '_')
        commandes = commandes.filter(
            Q(numero__icontains=query) |
            Q(utilisateur__code_tiers__icontains=query) |
            Q(statut__icontains=query_statut)
        )

    context = {
        'page_title': 'Liste des commandes',
        'commandes': commandes,
        'query': query,
    }
    return render(request, 'administration/liste_commandes.html', context)

@admin_required
def details_commande(request, commande_id):
    """Détails d'une commande"""
    commande = Commande.objects.get(id=commande_id)
    context = {
        'page_title': f'Détails de la commande {commande.numero}',
        'commande': commande,
    }
    return render(request, 'administration/details_commande.html', context)


@admin_required
def catalogue_utilisateurs(request):
    # Exclure les staff et superusers
    utilisateurs = Utilisateur.objects.filter(user__is_staff=False, user__is_superuser=False)

    # Récupérer tous les codes tiers des utilisateurs
    codes_tiers = [u.code_tiers for u in utilisateurs]

    # Récupérer tous les clients distants en UNE seule requête
    clients_distants = {c.tiers: c for c in ComCli.objects.using('logigvd').filter(tiers__in=codes_tiers)}

    # Enrichir avec les infos de la base distante
    clients_avec_infos = []
    for utilisateur in utilisateurs:
        client_distant = clients_distants.get(utilisateur.code_tiers)
        if client_distant:
            clients_avec_infos.append({
                'id': utilisateur.id,
                'utilisateur': utilisateur,
                'nom': client_distant.nom,
                'code_tiers': utilisateur.code_tiers,
            })
        else:
            clients_avec_infos.append({
                'id': utilisateur.id,
                'utilisateur': utilisateur,
                'nom': f"Client inconnu ({utilisateur.code_tiers})",
                'code_tiers': utilisateur.code_tiers,
            })

    # Recherche
    query = request.GET.get('q', '')
    if query:
        clients_avec_infos = [c for c in clients_avec_infos if
                              query.lower() in c['nom'].lower() or
                              query.lower() in c['code_tiers'].lower()]

    context = {
        'page_title': 'Catalogue Utilisateurs',
        'clients': clients_avec_infos,
        'query': query,
    }
    return render(request, 'administration/catalogue_utilisateur.html', context)

@admin_required
def catalogue_clients(request):
    """Liste des clients de la base distante"""
    query = request.GET.get('q', '').strip().lower()

    # Récupérer les tiers distincts avec nom et acheminement
    tiers_distincts = ComCli.objects.using('logigvd').values_list('tiers', 'nom', 'acheminement').distinct()

    # Filtrer par nom, tiers ou acheminement
    if query:
        tiers_distincts = [
            (t, n, a) for t, n, a in tiers_distincts
            if query in str(t).lower() or query in n.lower() or (a and query in a.lower())
        ]

    # Limiter à 100 résultats
    tiers_distincts = tiers_distincts[:100]

    # Récupérer un client par tiers (le premier trouvé)
    clients = []
    for tiers, nom, acheminement in tiers_distincts:
        client = ComCli.objects.using('logigvd').filter(tiers=tiers).first()
        if client:
            clients.append(client)

    context = {
        'page_title': 'Catalogue Clients',
        'clients': clients,
        'query': request.GET.get('q', ''),
    }
    return render(request, 'administration/catalogue_clients.html', context) 

@admin_required
def cadencier_client(request, client_id):
    utilisateur = Utilisateur.objects.get(id=client_id)
    try:
        client_distant = ComCli.objects.using('logigvd').get(tiers=utilisateur.code_tiers)
        nom_client = client_distant.nom
    except ComCli.DoesNotExist:
        nom_client = utilisateur.code_tiers

    produits = get_produits_client(utilisateur)

    # Recherche
    query = request.GET.get('q', '')
    if query:
        query_lower = query.lower()
        produits = [p for p in produits if
                    query_lower in p.get('libelle', '').lower() or
                    query_lower in p.get('prod', '').lower()]

    context = {
        'page_title': f'Cadencier - {nom_client}',
        'client': {'id': utilisateur.id, 'nom': nom_client},
        'produits': produits,
        'query': query,
    }
    return render(request, 'administration/cadencier_client.html', context)


@admin_required
@require_POST
def supprimer_commande(request, commande_id):
    """Supprimer une commande"""
    commande = get_object_or_404(Commande, id=commande_id)
    numero = commande.numero
    commande.delete()
    messages.success(request, f'La commande {numero} a été supprimée.')
    return redirect('administration:liste_commande')

@admin_required
def inscription(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'admin':
            # Inscription d'un administrateur
            username = request.POST.get('admin_username')
            password = request.POST.get('admin_password')
            password_confirm = request.POST.get('admin_password_confirm')

            if password != password_confirm:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
            else:
                # Créer l'utilisateur staff
                user = User.objects.create_user(username=username, password=password)
                user.is_staff = True
                user.save()
                messages.success(request, f'Administrateur {username} créé avec succès.')
                return redirect('administration:inscription')
        else:
            # Inscription d'un utilisateur client
            code_tiers = request.POST.get('client')
            username = request.POST.get('username')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')

            if password != password_confirm:
                messages.error(request, 'Les mots de passe ne correspondent pas.')
            elif User.objects.filter(username=username).exists():
                messages.error(request, 'Ce nom d\'utilisateur existe déjà.')
            elif Utilisateur.objects.filter(code_tiers=code_tiers).exists():
                messages.error(request, 'Ce client a déjà un compte utilisateur.')
            elif not ComCli.objects.using('logigvd').filter(tiers=code_tiers).exists():
                messages.error(request, 'Ce code client n\'existe pas.')
            else:
                # Créer l'utilisateur Django
                user = User.objects.create_user(username=username, password=password)
                # Créer le profil Utilisateur lié au code_tiers
                Utilisateur.objects.create(user=user, code_tiers=code_tiers)
                messages.success(request, f'Utilisateur {username} créé avec succès.')
                return redirect('administration:catalogue_utilisateur')

    context = {
        'page_title': 'Inscription',
    }
    return render(request, 'administration/inscription.html', context)


@admin_required
def recherche_clients_api(request):
    """API pour rechercher les clients (utilisée par le champ de recherche AJAX)"""
    query = request.GET.get('q', '').strip().lower()
    if len(query) < 2:
        return JsonResponse({'clients': []})

    # Récupérer les tiers distincts avec nom et acheminement
    tiers_distincts = ComCli.objects.using('logigvd').values_list('tiers', 'nom', 'acheminement').distinct()

    # Filtrer par nom, tiers ou acheminement
    result = []
    for tiers, nom, acheminement in tiers_distincts:
        if query in str(tiers).lower() or query in nom.lower() or (acheminement and query in acheminement.lower()):
            result.append({'tiers': tiers, 'nom': nom})
            if len(result) >= 20:
                break

    return JsonResponse({'clients': result})
