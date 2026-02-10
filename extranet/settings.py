"""
=============================================================================
SETTINGS.PY - Configuration principale du projet Django Extranet
=============================================================================

Ce fichier contient tous les paramètres de configuration du projet :
- Connexions aux bases de données (SQLite local + MariaDB distant)
- Applications installées
- Middleware de sécurité et session
- Configuration des templates
- Paramètres d'authentification
- Configuration des emails

Architecture des bases de données :
    - 'default' (SQLite)  : Utilisateurs, commandes, données locales
    - 'logigvd' (MariaDB) : Catalogue produits, clients (base distante)

Projet : Extranet Giffaud Groupe
=============================================================================
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# =============================================================================
# CHEMINS DE BASE
# =============================================================================
# BASE_DIR pointe vers le répertoire racine du projet (contenant manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Charger les variables d'environnement depuis .env
load_dotenv(BASE_DIR / '.env')

# =============================================================================
# SÉCURITÉ
# =============================================================================
# Clé secrète chargée depuis les variables d'environnement
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key')

# Mode debug : affiche les erreurs détaillées (désactiver en production)
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')

# Hôtes autorisés à accéder à l'application
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# =============================================================================
# APPLICATIONS INSTALLÉES
# =============================================================================
INSTALLED_APPS = [
    # Applications Django natives
    'django.contrib.admin',         # Interface d'administration Django
    'django.contrib.auth',          # Système d'authentification
    'django.contrib.contenttypes',  # Framework de types de contenu
    'django.contrib.sessions',      # Gestion des sessions utilisateur
    'django.contrib.messages',      # Framework de messages flash
    'django.contrib.staticfiles',   # Gestion des fichiers statiques

    # Applications métier de l'extranet
    'clients',          # Gestion des utilisateurs et authentification
    'catalogue',        # Catalogue des produits
    'commandes',        # Gestion des commandes et panier
    'recommandations',  # Système de recommandations produits
    'administration',   # Interface d'administration personnalisée
]

# =============================================================================
# MIDDLEWARE
# =============================================================================
# Les middleware sont exécutés dans l'ordre pour chaque requête HTTP
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',      # Sécurité HTTP (HTTPS, headers)
    'django.contrib.sessions.middleware.SessionMiddleware',  # Gestion des sessions
    'django.middleware.common.CommonMiddleware',          # Fonctionnalités communes
    'django.middleware.csrf.CsrfViewMiddleware',          # Protection contre les attaques CSRF
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Authentification utilisateur
    'django.contrib.messages.middleware.MessageMiddleware',     # Messages flash
    'django.middleware.clickjacking.XFrameOptionsMiddleware',   # Protection clickjacking
]

# Fichier de configuration des URLs racine
ROOT_URLCONF = 'extranet.urls'

# =============================================================================
# TEMPLATES
# =============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Répertoire des templates globaux
        'APP_DIRS': True,  # Recherche aussi dans les dossiers templates/ de chaque app
        'OPTIONS': {
            'context_processors': [
                # Processeurs de contexte Django natifs
                'django.template.context_processors.request',   # Ajoute 'request' au contexte
                'django.contrib.auth.context_processors.auth',  # Ajoute 'user' et 'perms'
                'django.contrib.messages.context_processors.messages',  # Ajoute 'messages'

                # Processeurs de contexte personnalisés
                'commandes.context_processors.panier_count',    # Nombre d'articles dans le panier
                'clients.context_processors.demandes_mdp_count',  # Nombre de demandes de mot de passe
            ],
        },
    },
]

# Configuration WSGI pour le déploiement
WSGI_APPLICATION = 'extranet.wsgi.application'

# =============================================================================
# BASES DE DONNÉES
# =============================================================================
# Le projet utilise deux bases de données :
# - 'default' : Base SQLite locale pour les données de l'application
# - 'logigvd' : Base MariaDB distante contenant les données métier existantes
DATABASES = {
    # Base de données locale SQLite
    # Contient : utilisateurs extranet, commandes, historiques, sessions
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },

    # Base de données distante MariaDB (système existant LogiGVD)
    # Contient : catalogue produits, informations clients, tarifs
    # ATTENTION : Base en lecture seule, ne pas modifier les données
    'logigvd': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_LOGIGVD_NAME', 'logigvd'),
        'USER': os.getenv('DB_LOGIGVD_USER', ''),
        'PASSWORD': os.getenv('DB_LOGIGVD_PASSWORD', ''),
        'HOST': os.getenv('DB_LOGIGVD_HOST', ''),
        'PORT': os.getenv('DB_LOGIGVD_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',  # Support des caractères spéciaux et emojis
        },
    }
}

# Routeur de base de données personnalisé
# Dirige automatiquement les requêtes vers la bonne base selon le modèle
DATABASE_ROUTERS = ['extranet.db_router.DatabaseRouter']

# =============================================================================
# VALIDATION DES MOTS DE PASSE
# =============================================================================
# Règles de validation pour les mots de passe utilisateur
AUTH_PASSWORD_VALIDATORS = [
    # Vérifie que le mot de passe n'est pas trop similaire aux infos utilisateur
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # Longueur minimale requise (8 caractères par défaut)
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    # Rejette les mots de passe trop courants (ex: "password123")
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    # Rejette les mots de passe entièrement numériques
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# INTERNATIONALISATION
# =============================================================================
LANGUAGE_CODE = 'fr-fr'      # Langue par défaut : français
TIME_ZONE = 'Europe/Paris'   # Fuseau horaire : Paris
USE_I18N = True              # Activer l'internationalisation
USE_TZ = True                # Utiliser les fuseaux horaires

# =============================================================================
# FICHIERS STATIQUES (CSS, JavaScript, Images)
# =============================================================================
STATIC_URL = 'static/'                      # URL de base pour les fichiers statiques
STATICFILES_DIRS = [BASE_DIR / 'static']    # Répertoire des fichiers statiques

# Type de clé primaire par défaut pour les nouveaux modèles
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# AUTHENTIFICATION ET REDIRECTIONS
# =============================================================================
LOGIN_URL = 'clients:connexion'           # URL de la page de connexion
LOGIN_REDIRECT_URL = 'catalogue:liste'    # Redirection après connexion réussie
LOGOUT_REDIRECT_URL = 'clients:connexion' # Redirection après déconnexion

# =============================================================================
# SESSIONS
# =============================================================================
# La session expire à la fermeture du navigateur (sécurité)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# =============================================================================
# CSRF (Protection contre les attaques Cross-Site Request Forgery)
# =============================================================================
# Domaines autorisés pour les requêtes CSRF (nécessaire pour ngrok)
CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://*.ngrok-free.dev',
    'https://*.ngrok.io',
]

# =============================================================================
# CACHE
# =============================================================================
# Cache en mémoire locale pour les filtres et données fréquentes
# En production, utiliser Redis : 'django.core.cache.backends.redis.RedisCache'
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,  # 5 minutes par défaut
    }
}

# =============================================================================
# CONFIGURATION EMAIL
# =============================================================================
# Utilise SMTP si configuré dans .env, sinon affiche dans le terminal
EMAIL_HOST = os.getenv('EMAIL_HOST', '')
if EMAIL_HOST:
    # Mode SMTP (Mailtrap ou production)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
else:
    # Mode développement : affiche les emails dans le terminal
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = 'noreply@giffaud-groupe.fr'
