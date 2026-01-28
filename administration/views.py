from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import connections
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
    with connections['logigvd'].cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM (SELECT 1 FROM comcli WHERE tiers != 0 GROUP BY tiers, complement) t")
        nb_clients = cursor.fetchone()[0]

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
    commandes = Commande.objects.all().order_by('-date_commande')

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

    commandes = commandes[:50]

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
    client = commande.utilisateur.get_client_distant()
    context = {
        'page_title': f'Détails de la commande {commande.numero}',
        'commande': commande,
        'client': client,
    }
    return render(request, 'administration/details_commande.html', context)

@admin_required
def commande_utilisateur(request, utilisateur_id):
    """Liste des commandes d'un client"""
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    client_distant = ComCli.objects.using('logigvd').filter(tiers=utilisateur.code_tiers).first()
    nom_client = client_distant.nom if client_distant else f"Client {utilisateur.code_tiers}"

    commandes = Commande.objects.filter(utilisateur=utilisateur).order_by('-date_commande')[:50]

    context = {
        'page_title': f'Commandes - {nom_client}',
        'utilisateur': utilisateur,
        'client': client_distant,
        'nom_client': nom_client,
        'commandes': commandes,
    }
    return render(request, 'administration/commande_utilisateur.html', context)


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
    query = request.GET.get('q', '').strip()

    # SQL brut : groupé par (tiers, complement)
    # Même tiers sans complement = 1 carte, même tiers avec complements différents = plusieurs cartes
    if query:
        if query.isdigit():
            # Recherche numérique : tiers exact (index) + FULLTEXT nom/acheminement
            sql = """
                SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement, MAX(acheminement) as acheminement
                FROM comcli
                WHERE tiers = %s
                GROUP BY tiers, complement

                UNION

                SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement, MAX(acheminement) as acheminement
                FROM comcli
                WHERE tiers != 0
                  AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
                GROUP BY tiers, complement

                ORDER BY tiers
                LIMIT 100
            """
            params = [int(query), f'{query}*']
        else:
            # Recherche texte : FULLTEXT sur nom/acheminement
            sql = """
                SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement, MAX(acheminement) as acheminement
                FROM comcli
                WHERE tiers != 0
                  AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
                GROUP BY tiers, complement
                ORDER BY tiers
                LIMIT 100
            """
            params = [f'{query}*']
    else:
        sql = """
            SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement, MAX(acheminement) as acheminement
            FROM comcli
            WHERE tiers != 0
            GROUP BY tiers, complement
            ORDER BY tiers
            LIMIT 100
        """
        params = []

    with connections['logigvd'].cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    clients = [
        {'tiers': row[0], 'nom': row[1], 'complement': row[2] or '', 'acheminement': row[3] or ''}
        for row in rows
    ]

    context = {
        'page_title': 'Catalogue Clients',
        'clients': clients,
        'query': query,
    }
    return render(request, 'administration/catalogue_clients.html', context) 

@admin_required
def cadencier_client(request, code_tiers):
    with connections['logigvd'].cursor() as cursor:
        cursor.execute("SELECT MAX(nom) FROM comcli WHERE tiers = %s", [code_tiers])
        row = cursor.fetchone()
    nom_client = row[0] if row and row[0] else str(code_tiers)

    # Créer un objet avec code_tiers pour le service
    from types import SimpleNamespace
    utilisateur_proxy = SimpleNamespace(code_tiers=code_tiers)
    produits = get_produits_client(utilisateur_proxy)

    # Recherche
    query = request.GET.get('q', '')
    if query:
        query_lower = query.lower()
        produits = [p for p in produits if
                    query_lower in p.get('libelle', '').lower() or
                    query_lower in p.get('prod', '').lower()]

    # Vérifier si un utilisateur est inscrit pour ce client
    utilisateur = Utilisateur.objects.filter(code_tiers=str(code_tiers)).first()

    context = {
        'page_title': f'Cadencier - {nom_client}',
        'client': {'tiers': code_tiers, 'nom': nom_client},
        'utilisateur': utilisateur,
        'produits': produits,
        'query': query,
    }
    return render(request, 'administration/cadencier_client.html', context)

@admin_required
def information_utilisateur(request, utilisateur_id):
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    client_distant = ComCli.objects.using('logigvd').filter(tiers=utilisateur.code_tiers).first()

    context = {
        'page_title': f'Information - {utilisateur.user.username}',
        'utilisateur': utilisateur,
        'client': client_distant,
    }
    return render(request, 'administration/information_utilisateur.html', context)

@admin_required
@require_POST
def changer_mot_de_passe(request, utilisateur_id):
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    nouveau_mdp = request.POST.get('nouveau_mdp', '')
    confirm_mdp = request.POST.get('confirm_mdp', '')

    if not nouveau_mdp:
        messages.error(request, 'Le mot de passe ne peut pas être vide.')
    elif nouveau_mdp != confirm_mdp:
        messages.error(request, 'Les mots de passe ne correspondent pas.')
    elif len(nouveau_mdp) < 4:
        messages.error(request, 'Le mot de passe doit contenir au moins 4 caractères.')
    else:
        utilisateur.user.set_password(nouveau_mdp)
        utilisateur.user.save()
        messages.success(request, f'Mot de passe de {utilisateur.user.username} modifié avec succès.')

    return redirect('administration:information_utilisateur', utilisateur_id=utilisateur_id)

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

    # Pré-remplissage depuis le cadencier (paramètres GET)
    prefill_tiers = request.GET.get('tiers', '')
    prefill_nom = request.GET.get('nom', '')

    context = {
        'page_title': 'Inscription',
        'prefill_tiers': prefill_tiers,
        'prefill_nom': prefill_nom,
    }
    return render(request, 'administration/inscription.html', context)


@admin_required
def recherche_clients_api(request):
    """API pour rechercher les clients (utilisée par le champ de recherche AJAX)"""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'clients': []})

    # Recherche optimisée avec FULLTEXT + index tiers
    if query.isdigit():
        sql = """
            SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement
            FROM comcli
            WHERE tiers = %s
            GROUP BY tiers, complement

            UNION

            SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement
            FROM comcli
            WHERE tiers != 0
              AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
            GROUP BY tiers, complement

            ORDER BY tiers
            LIMIT 20
        """
        params = [int(query), f'{query}*']
    else:
        sql = """
            SELECT tiers, MAX(nom) as nom, IFNULL(complement, '') as complement
            FROM comcli
            WHERE tiers != 0
              AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
            GROUP BY tiers, complement
            ORDER BY tiers
            LIMIT 20
        """
        params = [f'{query}*']

    with connections['logigvd'].cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    result = [{'tiers': row[0], 'nom': row[1], 'complement': row[2] or ''} for row in rows]

    return JsonResponse({'clients': result})
