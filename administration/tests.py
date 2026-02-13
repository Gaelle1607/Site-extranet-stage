"""
=============================================================================
TESTS.PY - Tests de l'application Administration
=============================================================================

Tests couverts :
    - Decorateur : admin_required, is_admin
    - Routeur DB : DatabaseRouter
    - Vues : acces dashboard, commandes, utilisateurs, inscription
    - Controle d'acces : clients non-admin rediriges

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from django.urls import reverse

from clients.models import Utilisateur
from commandes.models import Commande
from .views.utils.decorators import is_admin
from extranet.db_router import DatabaseRouter


# =============================================================================
# HELPERS
# =============================================================================

def creer_utilisateur(username='client1', password='testpass1234', code_tiers='CLI001'):
    user = User.objects.create_user(username=username, password=password, email='c@t.com')
    utilisateur = Utilisateur.objects.create(user=user, code_tiers=code_tiers)
    return user, utilisateur


def creer_admin(username='admin1', password='adminpass1234'):
    user = User.objects.create_user(
        username=username, password=password, is_staff=True
    )
    return user


# =============================================================================
# TESTS DU DECORATEUR
# =============================================================================

class IsAdminTest(TestCase):
    """Tests de la fonction is_admin."""

    def test_admin_authentifie(self):
        user = creer_admin()
        self.assertTrue(is_admin(user))

    def test_client_authentifie(self):
        user, _ = creer_utilisateur()
        self.assertFalse(is_admin(user))

    def test_utilisateur_anonyme(self):
        self.assertFalse(is_admin(AnonymousUser()))

    def test_staff_non_authentifie(self):
        user = creer_admin()
        # Simuler non-authentifie en utilisant AnonymousUser
        anon = AnonymousUser()
        self.assertFalse(is_admin(anon))


# =============================================================================
# TESTS DU ROUTEUR DE BASE DE DONNEES
# =============================================================================

class DatabaseRouterTest(TestCase):
    """Tests du routeur de base de donnees."""

    def setUp(self):
        self.router = DatabaseRouter()

    def test_logigvd_models_set(self):
        self.assertIn('comcli', self.router.logigvd_models)
        self.assertIn('comclilig', self.router.logigvd_models)
        self.assertIn('catalogue', self.router.logigvd_models)
        self.assertIn('prod', self.router.logigvd_models)

    def test_db_for_read_default(self):
        result = self.router.db_for_read(Utilisateur)
        self.assertEqual(result, 'default')

    def test_db_for_write_default(self):
        result = self.router.db_for_write(Utilisateur)
        self.assertEqual(result, 'default')

    def test_db_for_read_commande(self):
        result = self.router.db_for_read(Commande)
        self.assertEqual(result, 'default')

    def test_allow_migrate_default(self):
        result = self.router.allow_migrate('default', 'clients')
        self.assertTrue(result)

    def test_allow_migrate_logigvd_bloque(self):
        result = self.router.allow_migrate('default', 'catalogue', model_name='prod')
        self.assertFalse(result)

    def test_allow_migrate_non_default_db(self):
        result = self.router.allow_migrate('logigvd', 'clients')
        self.assertFalse(result)


# =============================================================================
# TESTS D'ACCES AUX VUES ADMIN
# =============================================================================

class AdminAccesNonConnecteTest(TestCase):
    """Tests : un utilisateur non connecte est redirige."""

    def test_dashboard_redirige(self):
        response = self.client.get(reverse('administration:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_liste_commande_redirige(self):
        response = self.client.get(reverse('administration:liste_commande'))
        self.assertEqual(response.status_code, 302)

    def test_catalogue_utilisateur_redirige(self):
        response = self.client.get(reverse('administration:catalogue_utilisateur'))
        self.assertEqual(response.status_code, 302)

    def test_inscription_redirige(self):
        response = self.client.get(reverse('administration:inscription'))
        self.assertEqual(response.status_code, 302)


class AdminAccesClientTest(TestCase):
    """Tests : un client non-admin est redirige."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()
        self.client.login(username='client1', password='testpass1234')

    def test_dashboard_redirige(self):
        response = self.client.get(reverse('administration:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_liste_commande_redirige(self):
        response = self.client.get(reverse('administration:liste_commande'))
        self.assertEqual(response.status_code, 302)

    def test_inscription_redirige(self):
        response = self.client.get(reverse('administration:inscription'))
        self.assertEqual(response.status_code, 302)


def _mock_logigvd_cursor():
    """Cree un mock pour le curseur de la base logigvd."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.__enter__ = lambda s: s
    mock_cursor.__exit__ = MagicMock(return_value=False)
    return mock_cursor


class AdminAccesAdminTest(TestCase):
    """Tests : un admin connecte a acces aux pages."""

    def setUp(self):
        self.admin_user = creer_admin()
        self.client.login(username='admin1', password='adminpass1234')

    def test_liste_commande_accessible(self):
        response = self.client.get(reverse('administration:liste_commande'))
        self.assertEqual(response.status_code, 200)

    def test_catalogue_utilisateur_accessible(self):
        response = self.client.get(reverse('administration:catalogue_utilisateur'))
        self.assertEqual(response.status_code, 200)

    def test_inscription_accessible(self):
        response = self.client.get(reverse('administration:inscription'))
        self.assertEqual(response.status_code, 200)

    def test_reset_password_admin_accessible(self):
        response = self.client.get(reverse('administration:reset_password_admin'))
        self.assertEqual(response.status_code, 200)

    def test_profil_admin_accessible(self):
        response = self.client.get(reverse('administration:profil_admin'))
        self.assertEqual(response.status_code, 200)

    def test_mentions_legales_accessible(self):
        response = self.client.get(reverse('administration:mentions_legales_admin'))
        self.assertEqual(response.status_code, 200)
