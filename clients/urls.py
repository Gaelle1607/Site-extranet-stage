"""
=============================================================================
URLS.PY - Routes de l'application Clients
=============================================================================

Ce fichier définit les URLs pour la gestion de l'authentification et
du profil utilisateur côté client.

Routes disponibles :
    /                       -> Page de connexion (alias)
    /connexion/             -> Formulaire de connexion
    /deconnexion/           -> Déconnexion et redirection
    /contact/               -> Page de contact
    /profil/                -> Consultation du profil utilisateur
    /profil/mot-de-passe/   -> Modification du mot de passe
    /demande-mot-de-passe/  -> Demande de réinitialisation par email
    /reset-password/<token>/ -> Confirmation de réinitialisation avec token

Préfixe : /clients/ (défini dans extranet/urls.py)

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.urls import path
from . import views

# Namespace pour les URLs de cette application
# Usage dans les templates : {% url 'clients:connexion' %}
app_name = 'clients'

urlpatterns = [
    # =========================================================================
    # AUTHENTIFICATION
    # =========================================================================

    # Page d'accueil de l'application clients (redirige vers connexion)
    path('', views.connexion, name='connexion'),

    # Formulaire de connexion avec identifiant et mot de passe
    # Redirige vers le catalogue après connexion réussie
    path('connexion/', views.connexion, name='connexion'),

    # Déconnexion de l'utilisateur et invalidation de la session
    # Redirige vers la page de connexion
    path('deconnexion/', views.deconnexion, name='deconnexion'),

    # =========================================================================
    # INFORMATIONS
    # =========================================================================

    # Page de contact avec les coordonnées de l'entreprise
    path('contact/', views.contact, name='contact'),

    # =========================================================================
    # GESTION DU PROFIL
    # =========================================================================

    # Affichage du profil utilisateur avec informations client distant
    # Nécessite une authentification
    path('profil/', views.profil, name='profil'),

    # Formulaire de modification du mot de passe
    # Nécessite une authentification et l'ancien mot de passe
    path('profil/mot-de-passe/', views.modifier_mot_de_passe, name='modifier_mot_de_passe'),

    # Formulaire de modification de l'adresse email
    # Nécessite une authentification
    path('profil/email/', views.modifier_email, name='modifier_email'),

    # =========================================================================
    # RÉINITIALISATION DE MOT DE PASSE
    # =========================================================================

    # Demande de réinitialisation : envoi d'un email avec lien sécurisé
    # Accessible sans authentification (mot de passe oublié)
    path('demande-mot-de-passe/', views.demande_mot_de_passe, name='demande_mdp'),

    # Confirmation de réinitialisation avec token unique
    # <str:token> = token de sécurité généré lors de la demande
    # Valide pendant 1 heure après génération
    path('reset-password/<str:token>/', views.reset_password_confirm, name='reset_password_confirm'),
]
