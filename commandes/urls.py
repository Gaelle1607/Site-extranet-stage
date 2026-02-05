"""
=============================================================================
URLS.PY - Routes de l'application Commandes
=============================================================================

Ce fichier définit les URLs pour la gestion du panier d'achat et des
commandes côté client.

Routes disponibles :
    /panier/                    -> Affichage du panier
    /panier/ajouter/            -> Ajout d'un produit au panier (POST)
    /panier/modifier/           -> Modification de quantité (POST)
    /panier/supprimer/          -> Suppression d'un article (POST)
    /panier/vider/              -> Vidage complet du panier (POST)
    /valider/                   -> Récapitulatif et validation de commande
    /confirmation/              -> Page de confirmation après envoi
    /historique/                -> Liste des commandes passées
    /details/<commande_id>/     -> Détail d'une commande

Préfixe : /commandes/ (défini dans extranet/urls.py)

Architecture :
    - Le panier est stocké en session (clé 'panier')
    - Les vues POST supportent les requêtes AJAX (JsonResponse)
    - La validation génère un fichier EDI pour l'ERP

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.urls import path
from . import views

# Namespace pour les URLs de cette application
# Usage dans les templates : {% url 'commandes:panier' %}
app_name = 'commandes'

urlpatterns = [
    # =========================================================================
    # GESTION DU PANIER
    # =========================================================================

    # Affichage du contenu du panier avec totaux
    # Accessible aux utilisateurs connectés uniquement
    path('panier/', views.voir_panier, name='panier'),

    # Ajout d'un produit au panier (POST uniquement)
    # Paramètres POST : reference, quantite (défaut=1)
    # Supporte les requêtes AJAX pour mise à jour dynamique
    path('panier/ajouter/', views.ajouter_au_panier, name='ajouter'),

    # Modification de la quantité d'un article (POST uniquement)
    # Paramètres POST : reference, quantite
    # Si quantite <= 0, l'article est supprimé
    path('panier/modifier/', views.modifier_quantite, name='modifier'),

    # Suppression d'un article du panier (POST uniquement)
    # Paramètre POST : reference
    path('panier/supprimer/', views.supprimer_du_panier, name='supprimer'),

    # Vidage complet du panier (POST uniquement)
    # Remet le panier à vide {}
    path('panier/vider/', views.vider_panier, name='vider'),

    # =========================================================================
    # VALIDATION DE COMMANDE
    # =========================================================================

    # Page de récapitulatif et validation finale
    # GET : Affiche le récapitulatif si données en session
    # POST : Traite la validation et génère le fichier EDI
    path('valider/', views.valider_commande, name='valider'),

    # Page de confirmation après envoi réussi de la commande
    # Affiche un message de succès et le numéro de commande
    path('confirmation/', views.confirmation_commande, name='confirmation'),

    # =========================================================================
    # HISTORIQUE DES COMMANDES
    # =========================================================================

    # Liste des 50 dernières commandes de l'utilisateur
    # Triées par date décroissante (plus récentes en premier)
    path('historique/', views.historique_commandes, name='historique'),

    # Détail d'une commande spécifique
    # <int:commande_id> = identifiant unique de la commande
    # Vérifie que la commande appartient bien à l'utilisateur connecté
    path('details/<int:commande_id>/', views.details_commande, name='details'),
]
