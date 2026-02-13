"""
=============================================================================
TESTS.PY - Tests de l'application Recommandations
=============================================================================

Tests couverts :
    - Modeles : HistoriqueAchat, PreferenceCategorie
    - Vues : acces aux pages et APIs
    - Methode : enregistrer_achat

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from clients.models import Utilisateur
from .models import HistoriqueAchat, PreferenceCategorie


# =============================================================================
# HELPERS
# =============================================================================

def creer_utilisateur(username='client1', password='testpass1234', code_tiers='CLI001'):
    user = User.objects.create_user(username=username, password=password, email='c@t.com')
    utilisateur = Utilisateur.objects.create(user=user, code_tiers=code_tiers)
    return user, utilisateur


# =============================================================================
# TESTS DES MODELES
# =============================================================================

class HistoriqueAchatModelTest(TestCase):
    """Tests du modele HistoriqueAchat."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()

    def test_enregistrer_achat_creation(self):
        h = HistoriqueAchat.enregistrer_achat(
            self.utilisateur, 'PROD001', 5, categorie='Viande'
        )
        self.assertEqual(h.quantite_totale, 5)
        self.assertEqual(h.nombre_commandes, 1)
        self.assertEqual(h.categorie, 'Viande')

    def test_enregistrer_achat_mise_a_jour(self):
        HistoriqueAchat.enregistrer_achat(self.utilisateur, 'PROD001', 5)
        h = HistoriqueAchat.enregistrer_achat(self.utilisateur, 'PROD001', 3)
        self.assertEqual(h.quantite_totale, 8)
        self.assertEqual(h.nombre_commandes, 2)

    def test_enregistrer_achat_categorie_non_ecrasee(self):
        HistoriqueAchat.enregistrer_achat(
            self.utilisateur, 'PROD001', 5, categorie='Viande'
        )
        h = HistoriqueAchat.enregistrer_achat(
            self.utilisateur, 'PROD001', 3, categorie='Charcuterie'
        )
        # La categorie existante ne doit pas etre ecrasee
        self.assertEqual(h.categorie, 'Viande')

    def test_enregistrer_achat_categorie_remplie_si_vide(self):
        HistoriqueAchat.enregistrer_achat(self.utilisateur, 'PROD001', 5, categorie='')
        h = HistoriqueAchat.enregistrer_achat(
            self.utilisateur, 'PROD001', 3, categorie='Viande'
        )
        self.assertEqual(h.categorie, 'Viande')

    def test_unicite_utilisateur_produit(self):
        HistoriqueAchat.enregistrer_achat(self.utilisateur, 'PROD001', 5)
        HistoriqueAchat.enregistrer_achat(self.utilisateur, 'PROD001', 3)
        self.assertEqual(HistoriqueAchat.objects.count(), 1)

    def test_produits_differents(self):
        HistoriqueAchat.enregistrer_achat(self.utilisateur, 'PROD001', 5)
        HistoriqueAchat.enregistrer_achat(self.utilisateur, 'PROD002', 3)
        self.assertEqual(HistoriqueAchat.objects.count(), 2)

    def test_str(self):
        h = HistoriqueAchat.enregistrer_achat(self.utilisateur, 'PROD001', 5)
        self.assertIn('CLI001', str(h))
        self.assertIn('PROD001', str(h))


class PreferenceCategorieModelTest(TestCase):
    """Tests du modele PreferenceCategorie."""

    def setUp(self):
        self.user, self.utilisateur = creer_utilisateur()

    def test_creation(self):
        pref = PreferenceCategorie.objects.create(
            utilisateur=self.utilisateur,
            categorie='Viande',
            score=15.5,
        )
        self.assertEqual(pref.score, 15.5)

    def test_unicite_utilisateur_categorie(self):
        PreferenceCategorie.objects.create(
            utilisateur=self.utilisateur, categorie='Viande', score=10
        )
        with self.assertRaises(Exception):
            PreferenceCategorie.objects.create(
                utilisateur=self.utilisateur, categorie='Viande', score=20
            )

    def test_ordering_par_score(self):
        PreferenceCategorie.objects.create(
            utilisateur=self.utilisateur, categorie='Fromage', score=5
        )
        PreferenceCategorie.objects.create(
            utilisateur=self.utilisateur, categorie='Viande', score=20
        )
        prefs = list(PreferenceCategorie.objects.all())
        self.assertEqual(prefs[0].categorie, 'Viande')

    def test_str(self):
        pref = PreferenceCategorie.objects.create(
            utilisateur=self.utilisateur, categorie='Viande', score=15.0
        )
        self.assertIn('Viande', str(pref))
        self.assertIn('CLI001', str(pref))


# =============================================================================
# TESTS DES VUES
# =============================================================================

class RecommandationsAccesTest(TestCase):
    """Tests de controle d'acces aux vues des recommandations."""

    def test_liste_non_connecte(self):
        response = self.client.get(reverse('recommandations:liste'))
        self.assertEqual(response.status_code, 302)

    def test_api_non_connecte(self):
        response = self.client.get(reverse('recommandations:api'))
        self.assertEqual(response.status_code, 302)

    def test_api_favoris_non_connecte(self):
        response = self.client.get(reverse('recommandations:api_favoris'))
        self.assertEqual(response.status_code, 302)
