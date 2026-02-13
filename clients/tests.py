"""
=============================================================================
TESTS.PY - Tests de l'application Clients
=============================================================================

Tests couverts :
    - Modeles : Utilisateur, TokenResetPassword, UtilisateurSupprime,
                HistoriqueSuppressionUtilisateur
    - Vues : connexion, deconnexion, profil, modifier_mot_de_passe,
             modifier_email, reset_password_confirm
    - Formulaire : ConnexionForm

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from .models import (
    Utilisateur,
    TokenResetPassword,
    UtilisateurSupprime,
    HistoriqueSuppressionUtilisateur,
)
from .forms import ConnexionForm


# Mock du client distant pour eviter les requetes sur logigvd
MOCK_CLIENT_DISTANT = SimpleNamespace(
    nom='CLIENT TEST', complement='', adresse='1 rue Test',
    cp='44000', acheminement='NANTES'
)


# =============================================================================
# HELPERS
# =============================================================================

def creer_utilisateur(username='client1', password='testpass1234', code_tiers='CLI001',
                      email='client1@test.com', is_staff=False):
    """Cree un User Django + profil Utilisateur et retourne le tuple (user, utilisateur)."""
    user = User.objects.create_user(
        username=username, password=password, email=email, is_staff=is_staff
    )
    utilisateur = Utilisateur.objects.create(user=user, code_tiers=code_tiers)
    return user, utilisateur


def creer_admin(username='admin1', password='adminpass1234'):
    """Cree un User Django staff (admin) sans profil Utilisateur."""
    return User.objects.create_user(
        username=username, password=password, is_staff=True
    )


# =============================================================================
# TESTS DES MODELES
# =============================================================================

class UtilisateurModelTest(TestCase):
    """Tests du modele Utilisateur."""

    def test_creation_utilisateur(self):
        user, utilisateur = creer_utilisateur()
        self.assertEqual(utilisateur.code_tiers, 'CLI001')
        self.assertEqual(utilisateur.user, user)

    def test_str(self):
        _, utilisateur = creer_utilisateur()
        self.assertEqual(str(utilisateur), 'client1 - CLI001')

    def test_relation_one_to_one(self):
        user, utilisateur = creer_utilisateur()
        self.assertEqual(user.utilisateur, utilisateur)


class TokenResetPasswordModelTest(TestCase):
    """Tests du modele TokenResetPassword."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='pass1234')

    def test_generer_token(self):
        token_obj = TokenResetPassword.generer_token(self.user)
        self.assertEqual(len(token_obj.token), 64)
        self.assertFalse(token_obj.utilise)
        self.assertEqual(token_obj.user, self.user)

    def test_generer_token_invalide_anciens(self):
        token1 = TokenResetPassword.generer_token(self.user)
        token2 = TokenResetPassword.generer_token(self.user)
        token1.refresh_from_db()
        self.assertTrue(token1.utilise)
        self.assertFalse(token2.utilise)

    def test_est_valide_nouveau(self):
        token_obj = TokenResetPassword.generer_token(self.user)
        self.assertTrue(token_obj.est_valide())

    def test_est_valide_utilise(self):
        token_obj = TokenResetPassword.generer_token(self.user)
        token_obj.utilise = True
        token_obj.save()
        self.assertFalse(token_obj.est_valide())

    def test_est_valide_expire(self):
        token_obj = TokenResetPassword.generer_token(self.user)
        TokenResetPassword.objects.filter(pk=token_obj.pk).update(
            date_creation=timezone.now() - timedelta(hours=2)
        )
        token_obj.refresh_from_db()
        self.assertFalse(token_obj.est_valide())

    def test_nettoyer_anciens(self):
        token_obj = TokenResetPassword.generer_token(self.user)
        TokenResetPassword.objects.filter(pk=token_obj.pk).update(
            date_creation=timezone.now() - timedelta(hours=25)
        )
        TokenResetPassword.nettoyer_anciens()
        self.assertEqual(TokenResetPassword.objects.count(), 0)

    def test_nettoyer_anciens_garde_recents(self):
        TokenResetPassword.generer_token(self.user)
        TokenResetPassword.nettoyer_anciens()
        self.assertEqual(TokenResetPassword.objects.count(), 1)

    def test_str(self):
        token_obj = TokenResetPassword.generer_token(self.user)
        self.assertIn('Token pour testuser', str(token_obj))


class UtilisateurSupprimeModelTest(TestCase):
    """Tests du modele UtilisateurSupprime."""

    def _creer_utilisateur_supprime(self, **kwargs):
        defaults = {
            'username': 'supprime1',
            'password_hash': 'hash123',
            'email': 'supp@test.com',
            'code_tiers': 'CLI999',
            'nom_client': 'Client Test',
            'date_joined': timezone.now(),
            'commandes_json': [],
        }
        defaults.update(kwargs)
        return UtilisateurSupprime.objects.create(**defaults)

    def test_est_restaurable_immediat(self):
        us = self._creer_utilisateur_supprime()
        self.assertTrue(us.est_restaurable())

    def test_est_restaurable_expire(self):
        us = self._creer_utilisateur_supprime()
        UtilisateurSupprime.objects.filter(pk=us.pk).update(
            date_suppression=timezone.now() - timedelta(minutes=6)
        )
        us.refresh_from_db()
        self.assertFalse(us.est_restaurable())

    def test_temps_restant_positif(self):
        us = self._creer_utilisateur_supprime()
        self.assertGreater(us.temps_restant(), 0)
        self.assertLessEqual(us.temps_restant(), 300)

    def test_temps_restant_zero_apres_expiration(self):
        us = self._creer_utilisateur_supprime()
        UtilisateurSupprime.objects.filter(pk=us.pk).update(
            date_suppression=timezone.now() - timedelta(minutes=10)
        )
        us.refresh_from_db()
        self.assertEqual(us.temps_restant(), 0)

    def test_str(self):
        us = self._creer_utilisateur_supprime()
        self.assertIn('supprime1', str(us))

    def test_nettoyer_anciens(self):
        us = self._creer_utilisateur_supprime()
        UtilisateurSupprime.objects.filter(pk=us.pk).update(
            date_suppression=timezone.now() - timedelta(minutes=6)
        )
        UtilisateurSupprime.nettoyer_anciens()
        self.assertEqual(UtilisateurSupprime.objects.count(), 0)
        self.assertEqual(HistoriqueSuppressionUtilisateur.objects.count(), 1)

    def test_nettoyer_anciens_garde_recents(self):
        self._creer_utilisateur_supprime()
        UtilisateurSupprime.nettoyer_anciens()
        self.assertEqual(UtilisateurSupprime.objects.count(), 1)


class HistoriqueSuppressionUtilisateurModelTest(TestCase):
    """Tests du modele HistoriqueSuppressionUtilisateur."""

    def test_creation(self):
        h = HistoriqueSuppressionUtilisateur.objects.create(
            username='ancien', nom_client='Client Ancien',
            code_tiers='CLI888', nb_commandes=5
        )
        self.assertEqual(h.nb_commandes, 5)

    def test_str(self):
        h = HistoriqueSuppressionUtilisateur.objects.create(
            username='ancien', nom_client='Client Ancien',
            code_tiers='CLI888'
        )
        self.assertIn('ancien', str(h))
        self.assertIn('Client Ancien', str(h))


# =============================================================================
# TESTS DU FORMULAIRE
# =============================================================================

class ConnexionFormTest(TestCase):
    """Tests du formulaire ConnexionForm."""

    def test_champs_presents(self):
        form = ConnexionForm()
        self.assertIn('username', form.fields)
        self.assertIn('password', form.fields)

    def test_widget_classes(self):
        form = ConnexionForm()
        self.assertIn('form-control', form.fields['username'].widget.attrs['class'])
        self.assertIn('form-control', form.fields['password'].widget.attrs['class'])

    def test_labels(self):
        form = ConnexionForm()
        self.assertEqual(form.fields['username'].label, 'Identifiant')
        self.assertEqual(form.fields['password'].label, 'Mot de passe')


# =============================================================================
# TESTS DES VUES
# =============================================================================

@patch('clients.views.get_client_distant', return_value=MOCK_CLIENT_DISTANT)
class ConnexionViewTest(TestCase):
    """Tests de la vue de connexion."""

    def setUp(self):
        self.client_http = Client()
        self.user, self.utilisateur = creer_utilisateur()
        self.admin_user = creer_admin()

    def test_page_connexion_get(self, mock_client):
        response = self.client_http.get(reverse('clients:connexion'))
        self.assertEqual(response.status_code, 200)

    def test_connexion_client_valide(self, mock_client):
        response = self.client_http.post(reverse('clients:connexion'), {
            'username': 'client1',
            'password': 'testpass1234',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('recommandations', response.url)

    def test_connexion_admin_valide(self, mock_client):
        response = self.client_http.post(reverse('clients:connexion'), {
            'username': 'admin1',
            'password': 'adminpass1234',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('administration', response.url)

    def test_connexion_invalide(self, mock_client):
        response = self.client_http.post(reverse('clients:connexion'), {
            'username': 'client1',
            'password': 'mauvaismdp',
        })
        self.assertEqual(response.status_code, 200)

    def test_redirection_si_deja_connecte_client(self, mock_client):
        self.client_http.login(username='client1', password='testpass1234')
        response = self.client_http.get(reverse('clients:connexion'))
        self.assertEqual(response.status_code, 302)

    def test_redirection_si_deja_connecte_admin(self, mock_client):
        self.client_http.login(username='admin1', password='adminpass1234')
        response = self.client_http.get(reverse('clients:connexion'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('administration', response.url)


class DeconnexionViewTest(TestCase):
    """Tests de la vue de deconnexion."""

    def test_deconnexion(self):
        creer_utilisateur()
        self.client.login(username='client1', password='testpass1234')
        response = self.client.get(reverse('clients:deconnexion'))
        self.assertEqual(response.status_code, 302)


class ContactViewTest(TestCase):
    """Tests de la vue contact."""

    def test_page_contact(self):
        response = self.client.get(reverse('clients:contact'))
        self.assertEqual(response.status_code, 200)


@patch('clients.views.get_client_distant', return_value=MOCK_CLIENT_DISTANT)
class ModifierMotDePasseViewTest(TestCase):
    """Tests de la vue modifier_mot_de_passe."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()
        self.client.login(username='client1', password='testpass1234')

    def test_page_get(self, mock_client):
        response = self.client.get(reverse('clients:modifier_mot_de_passe'))
        self.assertEqual(response.status_code, 200)

    def test_non_connecte_redirige(self, mock_client):
        self.client.logout()
        response = self.client.get(reverse('clients:modifier_mot_de_passe'))
        self.assertEqual(response.status_code, 302)


@patch('clients.views.get_client_distant', return_value=MOCK_CLIENT_DISTANT)
class ModifierEmailViewTest(TestCase):
    """Tests de la vue modifier_email."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()
        self.client.login(username='client1', password='testpass1234')

    def test_page_get(self, mock_client):
        response = self.client.get(reverse('clients:modifier_email'))
        self.assertEqual(response.status_code, 200)

    def test_modifier_email_valide(self, mock_client):
        response = self.client.post(reverse('clients:modifier_email'), {
            'email': 'nouveau@test.com',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'nouveau@test.com')

    def test_modifier_email_vide(self, mock_client):
        response = self.client.post(reverse('clients:modifier_email'), {
            'email': '',
        })
        self.assertEqual(response.status_code, 200)

    def test_modifier_email_invalide(self, mock_client):
        response = self.client.post(reverse('clients:modifier_email'), {
            'email': 'pasvalide',
        })
        self.assertEqual(response.status_code, 200)

    def test_modifier_email_deja_pris(self, mock_client):
        User.objects.create_user(username='autre', password='pass', email='pris@test.com')
        response = self.client.post(reverse('clients:modifier_email'), {
            'email': 'pris@test.com',
        })
        self.assertEqual(response.status_code, 200)


class ResetPasswordConfirmViewTest(TestCase):
    """Tests de la vue reset_password_confirm."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='resetuser', password='oldpass1234', email='reset@test.com'
        )
        self.token_obj = TokenResetPassword.generer_token(self.user)

    def test_page_get_token_valide(self):
        response = self.client.get(
            reverse('clients:reset_password_confirm', args=[self.token_obj.token])
        )
        self.assertEqual(response.status_code, 200)

    def test_token_invalide(self):
        response = self.client.get(
            reverse('clients:reset_password_confirm', args=['tokeninvalide123'])
        )
        self.assertEqual(response.status_code, 302)

    def test_reset_password_succes(self):
        response = self.client.post(
            reverse('clients:reset_password_confirm', args=[self.token_obj.token]),
            {'password': 'nouveaumdp', 'password_confirm': 'nouveaumdp'}
        )
        self.assertEqual(response.status_code, 302)
        self.token_obj.refresh_from_db()
        self.assertTrue(self.token_obj.utilise)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('nouveaumdp'))

    def test_reset_password_mismatch(self):
        response = self.client.post(
            reverse('clients:reset_password_confirm', args=[self.token_obj.token]),
            {'password': 'nouveaumdp', 'password_confirm': 'different'}
        )
        self.assertEqual(response.status_code, 200)

    def test_reset_password_trop_court(self):
        response = self.client.post(
            reverse('clients:reset_password_confirm', args=[self.token_obj.token]),
            {'password': 'ab', 'password_confirm': 'ab'}
        )
        self.assertEqual(response.status_code, 200)

    def test_reset_password_vide(self):
        response = self.client.post(
            reverse('clients:reset_password_confirm', args=[self.token_obj.token]),
            {'password': '', 'password_confirm': ''}
        )
        self.assertEqual(response.status_code, 200)

    def test_token_expire(self):
        TokenResetPassword.objects.filter(pk=self.token_obj.pk).update(
            date_creation=timezone.now() - timedelta(hours=2)
        )
        response = self.client.get(
            reverse('clients:reset_password_confirm', args=[self.token_obj.token])
        )
        self.assertEqual(response.status_code, 302)
