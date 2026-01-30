from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, CharField
from django.db.models.functions import Cast
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import connections
from django.utils import timezone
from clients.models import Utilisateur, DemandeMotDePasse
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

    # Récupérer les dernières activités
    dernieres_commandes = Commande.objects.select_related('utilisateur', 'utilisateur__user').order_by('-date_commande')[:5]
    derniers_utilisateurs = Utilisateur.objects.filter(
        user__is_staff=False, user__is_superuser=False
    ).select_related('user').order_by('-user__date_joined')[:5]

    # Construire la liste des activités récentes
    activites = []

    for commande in dernieres_commandes:
        # Récupérer le nom du client
        client = commande.utilisateur.get_client_distant()
        nom_client = client.nom if client else commande.utilisateur.code_tiers
        activites.append({
            'type': 'commande',
            'date': commande.date_commande,
            'description': f"Nouvelle commande {commande.numero} passée par {nom_client}",
            'commande': commande,
        })

    for utilisateur in derniers_utilisateurs:
        client = utilisateur.get_client_distant()
        nom_client = client.nom if client else utilisateur.code_tiers
        activites.append({
            'type': 'utilisateur',
            'date': utilisateur.user.date_joined,
            'description': f"Nouvel utilisateur créé : {nom_client} ({utilisateur.user.username})",
            'utilisateur': utilisateur,
        })

    # Trier par date décroissante et prendre les 5 dernières
    activites.sort(key=lambda x: x['date'], reverse=True)
    activites = activites[:5]

    # Récupérer les demandes de mot de passe non traitées
    demandes_mdp = DemandeMotDePasse.objects.filter(traitee=False).select_related(
        'utilisateur', 'utilisateur__user'
    ).order_by('-date_demande')

    # Enrichir avec le nom du client
    demandes_mdp_liste = []
    for demande in demandes_mdp:
        client = demande.utilisateur.get_client_distant()
        demandes_mdp_liste.append({
            'demande': demande,
            'nom_client': client.nom if client else demande.utilisateur.code_tiers,
        })

    context = {
        'page_title': 'Administration',
        'nb_utilisateurs': nb_utilisateurs,
        'nb_commandes': nb_commandes,
        'nb_clients': nb_clients,
        'activites': activites,
        'demandes_mdp': demandes_mdp_liste,
        'nb_demandes_mdp': len(demandes_mdp_liste),
    }
    return render(request, 'administration/dashboard.html', context)

@admin_required
def liste_commande(request):
    """Liste des commandes"""
    commandes = Commande.objects.all().order_by('-date_commande')

    # Recherche
    query = request.GET.get('q', '')
    if query:
        commandes = commandes.filter(
            Q(numero__icontains=query) |
            Q(utilisateur__code_tiers__icontains=query)
        )

    commandes = commandes[:50]

    # Enrichir avec le nom du client distant
    commandes_avec_client = []
    for commande in commandes:
        client = commande.utilisateur.get_client_distant()
        commandes_avec_client.append({
            'commande': commande,
            'nom_client': client.nom if client else f"Client {commande.utilisateur.code_tiers}",
        })

    context = {
        'page_title': 'Liste des commandes',
        'commandes': commandes_avec_client,
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

    # Prendre le client avec complement vide en priorité (même logique que cadencier_client)
    with connections['logigvd'].cursor() as cursor:
        cursor.execute("""
            SELECT nom FROM comcli
            WHERE tiers = %s AND (complement IS NULL OR TRIM(complement) = '')
            ORDER BY nom
            LIMIT 1
        """, [utilisateur.code_tiers])
        row = cursor.fetchone()
        if not row:
            cursor.execute("SELECT nom FROM comcli WHERE tiers = %s ORDER BY complement, nom LIMIT 1", [utilisateur.code_tiers])
            row = cursor.fetchone()
    nom_client = row[0] if row and row[0] else f"Client {utilisateur.code_tiers}"

    commandes = Commande.objects.filter(utilisateur=utilisateur).order_by('-date_commande')[:50]

    context = {
        'page_title': f'Commandes - {nom_client}',
        'utilisateur': utilisateur,
        'nom_client': nom_client,
        'commandes': commandes,
    }
    return render(request, 'administration/commande_utilisateur.html', context)


@admin_required
def catalogue_utilisateurs(request):
    # Exclure les staff et superusers
    utilisateurs = Utilisateur.objects.filter(user__is_staff=False, user__is_superuser=False)

    # Récupérer tous les codes tiers des utilisateurs (convertis en entiers)
    codes_tiers = []
    for u in utilisateurs:
        try:
            codes_tiers.append(int(u.code_tiers))
        except (ValueError, TypeError):
            pass

    # Récupérer les noms des clients - même logique que cadencier_client
    # Priorité aux entrées avec complement vide/null
    clients_distants = {}
    if codes_tiers:
        placeholders = ','.join(['%s'] * len(codes_tiers))
        with connections['logigvd'].cursor() as cursor:
            # D'abord récupérer les noms des entrées avec complement vide
            cursor.execute(f"""
                SELECT tiers, nom FROM comcli
                WHERE tiers IN ({placeholders})
                AND (complement IS NULL OR TRIM(complement) = '')
                ORDER BY tiers, nom
            """, codes_tiers)
            for row in cursor.fetchall():
                # Ne garder que la première entrée pour chaque tiers
                if row[0] not in clients_distants:
                    clients_distants[row[0]] = row[1]

            # Ensuite récupérer les noms pour les tiers qui n'ont pas été trouvés
            tiers_manquants = [t for t in codes_tiers if t not in clients_distants]
            if tiers_manquants:
                placeholders2 = ','.join(['%s'] * len(tiers_manquants))
                cursor.execute(f"""
                    SELECT tiers, nom FROM comcli
                    WHERE tiers IN ({placeholders2})
                    ORDER BY tiers, complement
                """, tiers_manquants)
                for row in cursor.fetchall():
                    if row[0] not in clients_distants:
                        clients_distants[row[0]] = row[1]

    # Enrichir avec les infos de la base distante
    clients_avec_infos = []
    for utilisateur in utilisateurs:
        try:
            code_tiers_int = int(utilisateur.code_tiers)
            nom_client = clients_distants.get(code_tiers_int)
        except (ValueError, TypeError):
            nom_client = None
        if nom_client:
            clients_avec_infos.append({
                'id': utilisateur.id,
                'utilisateur': utilisateur,
                'nom': nom_client,
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

    with connections['logigvd'].cursor() as cursor:
        # Étape 1: Récupérer les tiers correspondant à la recherche
        if query:
            if query.isdigit():
                # Recherche numérique : tiers exact + FULLTEXT
                cursor.execute("""
                    SELECT DISTINCT tiers FROM comcli WHERE tiers = %s
                    UNION
                    SELECT DISTINCT tiers FROM comcli
                    WHERE tiers != 0 AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
                    LIMIT 100
                """, [int(query), f'{query}*'])
            else:
                # Recherche texte : FULLTEXT sur nom/acheminement
                cursor.execute("""
                    SELECT DISTINCT tiers FROM comcli
                    WHERE tiers != 0 AND MATCH(nom, acheminement) AGAINST (%s IN BOOLEAN MODE)
                    LIMIT 100
                """, [f'{query}*'])
        else:
            cursor.execute("SELECT DISTINCT tiers FROM comcli WHERE tiers != 0 ORDER BY tiers LIMIT 100")

        tiers_list = [row[0] for row in cursor.fetchall()]

        if not tiers_list:
            clients = []
        else:
            # Étape 2: Pour chaque tiers, récupérer le nom avec complement vide en priorité
            # (même logique que cadencier_client)
            placeholders = ','.join(['%s'] * len(tiers_list))

            # D'abord les entrées avec complement vide (ORDER BY tiers, nom pour cohérence)
            cursor.execute(f"""
                SELECT tiers, nom, IFNULL(complement, '') as complement, acheminement
                FROM comcli
                WHERE tiers IN ({placeholders})
                AND (complement IS NULL OR TRIM(complement) = '')
                ORDER BY tiers, nom
            """, tiers_list)

            clients_dict = {}
            for row in cursor.fetchall():
                # Ne garder que la première entrée pour chaque tiers
                if row[0] not in clients_dict:
                    clients_dict[row[0]] = {
                        'tiers': row[0],
                        'nom': row[1],
                        'complement': row[2] or '',
                        'acheminement': row[3] or ''
                    }

            # Ensuite les tiers qui n'ont pas été trouvés (ceux sans complement vide)
            tiers_manquants = [t for t in tiers_list if t not in clients_dict]
            if tiers_manquants:
                placeholders2 = ','.join(['%s'] * len(tiers_manquants))
                cursor.execute(f"""
                    SELECT tiers, nom, IFNULL(complement, '') as complement, acheminement
                    FROM comcli
                    WHERE tiers IN ({placeholders2})
                    ORDER BY tiers, complement
                """, tiers_manquants)
                for row in cursor.fetchall():
                    if row[0] not in clients_dict:
                        clients_dict[row[0]] = {
                            'tiers': row[0],
                            'nom': row[1],
                            'complement': row[2] or '',
                            'acheminement': row[3] or ''
                        }

            # Construire la liste triée par tiers
            clients = [clients_dict[t] for t in sorted(clients_dict.keys())]

    context = {
        'page_title': 'Catalogue Clients',
        'clients': clients,
        'query': query,
    }
    return render(request, 'administration/catalogue_clients.html', context) 

@admin_required
def cadencier_client(request, code_tiers):
    with connections['logigvd'].cursor() as cursor:
        # Prendre le nom de l'entrée principale (complement vide) en priorité
        # ORDER BY nom pour cohérence avec les autres vues
        cursor.execute("""
            SELECT nom FROM comcli
            WHERE tiers = %s AND (complement IS NULL OR TRIM(complement) = '')
            ORDER BY nom
            LIMIT 1
        """, [code_tiers])
        row = cursor.fetchone()
        if not row:
            # Sinon prendre le premier nom trouvé
            cursor.execute("SELECT nom FROM comcli WHERE tiers = %s ORDER BY complement, nom LIMIT 1", [code_tiers])
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

    # Prendre le client avec complement vide en priorité (même logique que cadencier_client)
    with connections['logigvd'].cursor() as cursor:
        cursor.execute("""
            SELECT nom, complement, adresse, cp, acheminement FROM comcli
            WHERE tiers = %s AND (complement IS NULL OR TRIM(complement) = '')
            ORDER BY nom
            LIMIT 1
        """, [utilisateur.code_tiers])
        row = cursor.fetchone()
        if not row:
            # Sinon prendre la première entrée triée par complement
            cursor.execute("""
                SELECT nom, complement, adresse, cp, acheminement FROM comcli
                WHERE tiers = %s ORDER BY complement, nom LIMIT 1
            """, [utilisateur.code_tiers])
            row = cursor.fetchone()

    # Créer un objet similaire à ComCli pour le template
    if row:
        from types import SimpleNamespace
        client_distant = SimpleNamespace(
            nom=row[0],
            complement=row[1],
            adresse=row[2],
            cp=row[3],
            acheminement=row[4]
        )
    else:
        client_distant = None

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
    elif utilisateur.user.check_password(nouveau_mdp):
        messages.error(request, 'Le nouveau mot de passe doit être différent de l\'ancien.')
    else:
        utilisateur.user.set_password(nouveau_mdp)
        utilisateur.user.save()

        # Marquer les demandes de mot de passe comme traitées
        DemandeMotDePasse.objects.filter(
            utilisateur=utilisateur,
            traitee=False
        ).update(traitee=True, date_traitement=timezone.now())

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
@require_POST
def verifier_mot_de_passe_api(request, utilisateur_id):
    """API pour vérifier si le nouveau mot de passe est identique à l'ancien"""
    utilisateur = get_object_or_404(Utilisateur, id=utilisateur_id)
    nouveau_mdp = request.POST.get('nouveau_mdp', '')

    est_identique = utilisateur.user.check_password(nouveau_mdp)
    return JsonResponse({'identique': est_identique})


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


@admin_required
def profil_admin(request):
    """Page de profil de l'administrateur"""
    context = {
        'page_title': 'Mon profil',
    }
    return render(request, 'administration/profil_admin.html', context)


@admin_required
@require_POST
def changer_mot_de_passe_admin(request):
    """Changer le mot de passe de l'administrateur connecté"""
    ancien_mdp = request.POST.get('ancien_mdp', '')
    nouveau_mdp = request.POST.get('nouveau_mdp', '')
    confirm_mdp = request.POST.get('confirm_mdp', '')

    if not request.user.check_password(ancien_mdp):
        messages.error(request, 'Le mot de passe actuel est incorrect.')
    elif not nouveau_mdp:
        messages.error(request, 'Le nouveau mot de passe ne peut pas être vide.')
    elif nouveau_mdp != confirm_mdp:
        messages.error(request, 'Les mots de passe ne correspondent pas.')
    elif len(nouveau_mdp) < 4:
        messages.error(request, 'Le mot de passe doit contenir au moins 4 caractères.')
    elif nouveau_mdp == ancien_mdp:
        messages.error(request, 'Le nouveau mot de passe doit être différent de l\'ancien.')
    else:
        request.user.set_password(nouveau_mdp)
        request.user.save()
        # Reconnecter l'utilisateur pour éviter la déconnexion
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)
        messages.success(request, 'Votre mot de passe a été modifié avec succès.')

    return redirect('administration:profil_admin')


def reset_password_admin(request):
    """
    Page de réinitialisation du mot de passe admin avec clé secrète.
    Accessible sans authentification mais nécessite la clé secrète du serveur.
    """
    from .reset_key import RESET_SECRET_KEY

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        secret_key = request.POST.get('secret_key', '').strip()
        nouveau_mdp = request.POST.get('nouveau_mdp', '')
        confirm_mdp = request.POST.get('confirm_mdp', '')

        # Vérifier la clé secrète
        if secret_key != RESET_SECRET_KEY:
            messages.error(request, 'Clé secrète incorrecte.')
        elif not username:
            messages.error(request, 'Veuillez entrer un nom d\'utilisateur.')
        elif not nouveau_mdp:
            messages.error(request, 'Le nouveau mot de passe ne peut pas être vide.')
        elif nouveau_mdp != confirm_mdp:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
        elif len(nouveau_mdp) < 4:
            messages.error(request, 'Le mot de passe doit contenir au moins 4 caractères.')
        else:
            try:
                user = User.objects.get(username=username, is_staff=True)
                user.set_password(nouveau_mdp)
                user.save()
                messages.success(request, f'Mot de passe de {username} réinitialisé avec succès. Vous pouvez maintenant vous connecter.')
                return redirect('clients:connexion')
            except User.DoesNotExist:
                messages.error(request, 'Aucun administrateur trouvé avec ce nom d\'utilisateur.')

    return render(request, 'administration/reset_password.html')
