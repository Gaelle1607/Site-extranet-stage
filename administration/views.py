from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from clients.models import Client
from commandes.models import Commande
from catalogue.services import get_produits_client


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
    nb_clients = Client.objects.filter(user__is_staff=False, user__is_superuser=False).count()
    nb_commandes = Commande.objects.count()

    context = {
        'page_title': 'Administration',
        'nb_clients': nb_clients,
        'nb_commandes': nb_commandes,
    }
    return render(request, 'administration/dashboard.html', context)

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
            Q(client__nom__icontains=query) |
            Q(statut__icontains=query_statut)
        )

    context = {
        'page_title': 'Liste des commandes',
        'commandes': commandes,
        'query': query,
    }
    return render(request, 'administration/liste_commandes.html', context)

def details_commande(request, commande_id):
    """Détails d'une commande"""
    commande = Commande.objects.get(id=commande_id)
    context = {
        'page_title': f'Détails de la commande {commande.numero}',
        'commande': commande,
    }
    return render(request, 'administration/details_commande.html', context)


def catalogue_client(request):
    # Exclure les staff et superusers
    clients = Client.objects.filter(user__is_staff=False, user__is_superuser=False)

    # Recherche
    query = request.GET.get('q', '')
    if query:
        clients = clients.filter(
            Q(nom__icontains=query)
        )

    context = {
        'page_title': 'Catalogue client',
        'clients': clients,
        'query': query,
    }
    return render(request, 'administration/catalogue_clients.html', context)

def cadencier_client(request, client_id):
    client = Client.objects.get(id=client_id)
    produits = get_produits_client(client)

    # Recherche
    query = request.GET.get('q', '')
    if query:
        query_normalized = query.lower().replace(' ', '_')
        produits = [p for p in produits if
                    query.lower() in p.get('nom', '').lower() or
                    query_normalized in p.get('reference', '').lower()]

    context = {
        'page_title': f'Cadencier - {client.nom}',
        'client': client,
        'produits': produits,
        'query': query,
    }
    return render(request, 'administration/cadencier_client.html', context)