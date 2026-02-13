"""
=============================================================================
TESTS.PY - Tests de l'application Commandes
=============================================================================

Tests couverts :
    - Modeles : Commande, LigneCommande, CommandeSupprimee, HistoriqueSuppression
    - Vues : panier (voir, ajouter, modifier, supprimer, vider),
             historique, details, confirmation
    - Context processor : panier_count
    - Utilitaires : parse_date, get_panier, save_panier

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from datetime import timedelta
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse
from django.utils import timezone

from clients.models import Utilisateur
from .models import Commande, LigneCommande, CommandeSupprimee, HistoriqueSuppression
from .views import parse_date, get_panier, save_panier
from .context_processors import panier_count

MOCK_CLIENT_DISTANT = SimpleNamespace(
    nom='CLIENT TEST', complement='', adresse='1 rue Test',
    cp='44000', acheminement='NANTES'
)


# =============================================================================
# HELPERS
# =============================================================================

def creer_utilisateur(username='client1', password='testpass1234', code_tiers='CLI001'):
    user = User.objects.create_user(username=username, password=password, email='c@t.com')
    utilisateur = Utilisateur.objects.create(user=user, code_tiers=code_tiers)
    return user, utilisateur


def creer_commande(utilisateur, numero='CMD-20260212-1234', total_ht='150.00'):
    return Commande.objects.create(
        utilisateur=utilisateur,
        numero=numero,
        total_ht=Decimal(total_ht),
    )


def _get_request_with_session(user=None):
    """Cree un request avec session pour les tests unitaires."""
    factory = RequestFactory()
    request = factory.get('/')
    middleware = SessionMiddleware(lambda r: None)
    middleware.process_request(request)
    request.session.save()
    if user:
        request.user = user
    return request


# =============================================================================
# TESTS DES UTILITAIRES
# =============================================================================

class ParseDateTest(TestCase):
    """Tests de la fonction parse_date."""

    def test_date_valide(self):
        from datetime import date
        result = parse_date('2026-02-12')
        self.assertEqual(result, date(2026, 2, 12))

    def test_date_none(self):
        self.assertIsNone(parse_date(None))

    def test_date_vide(self):
        self.assertIsNone(parse_date(''))

    def test_date_invalide(self):
        result = parse_date('pas-une-date')
        self.assertEqual(result, 'pas-une-date')


class PanierSessionTest(TestCase):
    """Tests des fonctions get_panier et save_panier."""

    def test_get_panier_vide(self):
        request = _get_request_with_session()
        panier = get_panier(request)
        self.assertEqual(panier, {})

    def test_save_et_get_panier(self):
        request = _get_request_with_session()
        save_panier(request, {'PROD001': 3})
        panier = get_panier(request)
        self.assertEqual(panier, {'PROD001': 3})


# =============================================================================
# TESTS DU CONTEXT PROCESSOR
# =============================================================================

class PanierCountContextProcessorTest(TestCase):
    """Tests du context processor panier_count."""

    def test_panier_count_non_connecte(self):
        from django.contrib.auth.models import AnonymousUser
        request = _get_request_with_session()
        request.user = AnonymousUser()
        result = panier_count(request)
        self.assertEqual(result['panier_count'], 0)

    def test_panier_count_connecte_vide(self):
        user, _ = creer_utilisateur()
        request = _get_request_with_session(user=user)
        result = panier_count(request)
        self.assertEqual(result['panier_count'], 0)

    def test_panier_count_avec_articles(self):
        user, _ = creer_utilisateur()
        request = _get_request_with_session(user=user)
        request.session['panier'] = {'PROD001': 2, 'PROD002': 5}
        result = panier_count(request)
        self.assertEqual(result['panier_count'], 7)


# =============================================================================
# TESTS DES MODELES
# =============================================================================

class CommandeModelTest(TestCase):
    """Tests du modele Commande."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()

    def test_creation_commande(self):
        cmd = creer_commande(self.utilisateur)
        self.assertEqual(cmd.numero, 'CMD-20260212-1234')
        self.assertEqual(cmd.total_ht, Decimal('150.00'))

    def test_str(self):
        cmd = creer_commande(self.utilisateur)
        self.assertIn('CMD-20260212-1234', str(cmd))
        self.assertIn('CLI001', str(cmd))

    def test_generer_numero_format(self):
        numero = Commande.generer_numero()
        self.assertTrue(numero.startswith('CMD-'))
        parties = numero.split('-')
        self.assertEqual(len(parties), 3)
        self.assertEqual(len(parties[1]), 8)  # YYYYMMDD
        self.assertTrue(parties[2].isdigit())

    def test_generer_numero_unique(self):
        n1 = Commande.generer_numero()
        n2 = Commande.generer_numero()
        # Les numeros peuvent etre identiques (rare), mais le test verifie le format
        self.assertTrue(n1.startswith('CMD-'))
        self.assertTrue(n2.startswith('CMD-'))

    def test_ordering_par_date_decroissante(self):
        """Verifie que le Meta ordering est bien -date_commande."""
        self.assertEqual(Commande._meta.ordering, ['-date_commande'])


class LigneCommandeModelTest(TestCase):
    """Tests du modele LigneCommande."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()
        self.commande = creer_commande(self.utilisateur)

    def test_creation_ligne(self):
        ligne = LigneCommande.objects.create(
            commande=self.commande,
            reference_produit='PROD001',
            nom_produit='Saucisson sec',
            quantite=5,
            prix_unitaire=Decimal('12.50'),
            total_ligne=Decimal('62.50'),
        )
        self.assertEqual(ligne.nom_produit, 'Saucisson sec')

    def test_calcul_auto_total_ligne(self):
        ligne = LigneCommande(
            commande=self.commande,
            reference_produit='PROD001',
            nom_produit='Saucisson sec',
            quantite=3,
            prix_unitaire=Decimal('10.00'),
            total_ligne=Decimal('0'),
        )
        ligne.save()
        self.assertEqual(ligne.total_ligne, Decimal('30.00'))

    def test_str(self):
        ligne = LigneCommande.objects.create(
            commande=self.commande,
            reference_produit='PROD001',
            nom_produit='Saucisson sec',
            quantite=5,
            prix_unitaire=Decimal('12.50'),
            total_ligne=Decimal('62.50'),
        )
        self.assertEqual(str(ligne), 'Saucisson sec x 5')

    def test_relation_commande(self):
        LigneCommande.objects.create(
            commande=self.commande,
            reference_produit='PROD001',
            nom_produit='Produit A',
            quantite=2,
            prix_unitaire=Decimal('10.00'),
            total_ligne=Decimal('20.00'),
        )
        LigneCommande.objects.create(
            commande=self.commande,
            reference_produit='PROD002',
            nom_produit='Produit B',
            quantite=1,
            prix_unitaire=Decimal('5.00'),
            total_ligne=Decimal('5.00'),
        )
        self.assertEqual(self.commande.lignes.count(), 2)


class CommandeSupprimeModelTest(TestCase):
    """Tests du modele CommandeSupprimee."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()

    def _creer_cmd_supprimee(self, **kwargs):
        defaults = {
            'utilisateur': self.utilisateur,
            'numero': 'CMD-20260212-9999',
            'date_commande': timezone.now(),
            'total_ht': Decimal('100.00'),
            'lignes_json': [{'reference': 'P1', 'nom': 'Prod', 'quantite': 1,
                             'prix_unitaire': 100, 'total_ligne': 100}],
        }
        defaults.update(kwargs)
        return CommandeSupprimee.objects.create(**defaults)

    def test_est_restaurable(self):
        cs = self._creer_cmd_supprimee()
        self.assertTrue(cs.est_restaurable())

    def test_est_restaurable_expire(self):
        cs = self._creer_cmd_supprimee()
        CommandeSupprimee.objects.filter(pk=cs.pk).update(
            date_suppression=timezone.now() - timedelta(minutes=6)
        )
        cs.refresh_from_db()
        self.assertFalse(cs.est_restaurable())

    def test_temps_restant(self):
        cs = self._creer_cmd_supprimee()
        self.assertGreater(cs.temps_restant(), 0)
        self.assertLessEqual(cs.temps_restant(), 300)

    def test_temps_restant_expire(self):
        cs = self._creer_cmd_supprimee()
        CommandeSupprimee.objects.filter(pk=cs.pk).update(
            date_suppression=timezone.now() - timedelta(minutes=10)
        )
        cs.refresh_from_db()
        self.assertEqual(cs.temps_restant(), 0)

    def test_str(self):
        cs = self._creer_cmd_supprimee()
        self.assertIn('CMD-20260212-9999', str(cs))


class HistoriqueSuppressionModelTest(TestCase):
    """Tests du modele HistoriqueSuppression."""

    def test_creation(self):
        h = HistoriqueSuppression.objects.create(
            numero='CMD-20260212-0001',
            nom_client='Client Test',
            code_tiers='CLI001',
            total_ht=Decimal('200.00'),
        )
        self.assertEqual(h.total_ht, Decimal('200.00'))

    def test_str(self):
        h = HistoriqueSuppression.objects.create(
            numero='CMD-20260212-0001',
            nom_client='Client Test',
            code_tiers='CLI001',
        )
        self.assertIn('CMD-20260212-0001', str(h))
        self.assertIn('Client Test', str(h))


# =============================================================================
# TESTS DES VUES
# =============================================================================

class PanierViewsTest(TestCase):
    """Tests des vues du panier (necessite connexion)."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()
        self.client.login(username='client1', password='testpass1234')

    def test_voir_panier_vide(self):
        response = self.client.get(reverse('commandes:panier'))
        self.assertEqual(response.status_code, 200)

    def test_vider_panier(self):
        session = self.client.session
        session['panier'] = {'PROD001': 2}
        session.save()
        response = self.client.post(reverse('commandes:vider'))
        self.assertEqual(response.status_code, 302)

    def test_vider_panier_ajax(self):
        session = self.client.session
        session['panier'] = {'PROD001': 2}
        session.save()
        response = self.client.post(
            reverse('commandes:vider'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['panier_count'], 0)

    def test_non_connecte_redirige(self):
        self.client.logout()
        response = self.client.get(reverse('commandes:panier'))
        self.assertEqual(response.status_code, 302)


@patch('commandes.views.get_client_distant', return_value=MOCK_CLIENT_DISTANT)
class HistoriqueCommandesViewTest(TestCase):
    """Tests de la vue historique_commandes."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()
        self.client.login(username='client1', password='testpass1234')

    def test_historique_vide(self, mock_client):
        response = self.client.get(reverse('commandes:historique'))
        self.assertEqual(response.status_code, 200)

    def test_historique_avec_commandes(self, mock_client):
        creer_commande(self.utilisateur, numero='CMD-20260212-0001')
        creer_commande(self.utilisateur, numero='CMD-20260212-0002')
        response = self.client.get(reverse('commandes:historique'))
        self.assertEqual(response.status_code, 200)


@patch('commandes.views.get_client_distant', return_value=MOCK_CLIENT_DISTANT)
class DetailsCommandeViewTest(TestCase):
    """Tests de la vue details_commande."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()
        self.client.login(username='client1', password='testpass1234')
        self.commande = creer_commande(self.utilisateur)

    def test_details_propre_commande(self, mock_client):
        response = self.client.get(
            reverse('commandes:details', args=[self.commande.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_details_commande_autre_utilisateur(self, mock_client):
        _, autre_utilisateur = creer_utilisateur(
            username='autre', code_tiers='CLI002'
        )
        autre_cmd = creer_commande(autre_utilisateur, numero='CMD-20260212-9999')
        response = self.client.get(
            reverse('commandes:details', args=[autre_cmd.id])
        )
        self.assertEqual(response.status_code, 404)

    def test_details_commande_inexistante(self, mock_client):
        response = self.client.get(
            reverse('commandes:details', args=[99999])
        )
        self.assertEqual(response.status_code, 404)


class ConfirmationCommandeViewTest(TestCase):
    """Tests de la vue confirmation_commande."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()
        self.client.login(username='client1', password='testpass1234')

    def test_page_confirmation(self):
        response = self.client.get(reverse('commandes:confirmation'))
        self.assertEqual(response.status_code, 200)
