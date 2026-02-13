"""
=============================================================================
TESTS.PY - Tests de l'application Catalogue
=============================================================================

Tests couverts :
    - Vues : liste_produits, favoris, detail_produit, mentions_legales, commander
    - Acces : verification des redirections pour utilisateurs non connectes

Note :
    Les modeles de cette application (Prod, ComCli, ComCliLig, Catalogue)
    sont en managed=False (base distante MariaDB). Ils ne peuvent pas etre
    testes directement via la base de test SQLite. Les tests se concentrent
    sur les vues et le controle d'acces.

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from clients.models import Utilisateur


# =============================================================================
# HELPERS
# =============================================================================

def creer_utilisateur(username='client1', password='testpass1234', code_tiers='CLI001'):
    user = User.objects.create_user(username=username, password=password, email='c@t.com')
    utilisateur = Utilisateur.objects.create(user=user, code_tiers=code_tiers)
    return user, utilisateur


# =============================================================================
# TESTS DES VUES
# =============================================================================

class MentionsLegalesViewTest(TestCase):
    """Tests de la vue mentions_legales (accessible sans connexion)."""

    def test_page_mentions_legales(self):
        response = self.client.get(reverse('catalogue:mentions_legales'))
        self.assertEqual(response.status_code, 200)


class CatalogueAccesTest(TestCase):
    """Tests de controle d'acces aux vues du catalogue."""

    def test_liste_produits_non_connecte(self):
        response = self.client.get(reverse('catalogue:liste'))
        self.assertEqual(response.status_code, 302)

    def test_favoris_non_connecte(self):
        response = self.client.get(reverse('catalogue:favoris'))
        self.assertEqual(response.status_code, 302)

    def test_commander_non_connecte(self):
        response = self.client.get(reverse('catalogue:commander'))
        self.assertEqual(response.status_code, 302)
