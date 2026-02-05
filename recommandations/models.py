"""
=============================================================================
MODELS.PY - Modèles de l'application Recommandations
=============================================================================

Ce module définit les modèles Django pour le système de recommandations
personnalisées basé sur l'historique d'achat des clients.

Modèles :
    - HistoriqueAchat : Suivi des achats par produit et utilisateur
    - PreferenceCategorie : Scores de préférence par catégorie

Architecture :
    - Les produits proviennent d'une source externe (base LogiGVD)
    - Seules les références produits (string) sont stockées, pas de FK
    - L'historique est mis à jour à chaque commande validée

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.db import models
from clients.models import Utilisateur


class HistoriqueAchat(models.Model):
    """
    Modèle représentant l'historique des achats d'un utilisateur.

    Cette table agrège les informations d'achat par couple
    utilisateur/produit pour permettre le calcul des recommandations
    et l'identification des produits favoris.

    Attributs:
        utilisateur (FK): Référence vers l'utilisateur concerné
        reference_produit (str): Code produit (depuis la base externe)
        categorie (str): Catégorie du produit (pour les stats)
        quantite_totale (int): Cumul des quantités commandées
        nombre_commandes (int): Nombre de fois que ce produit a été commandé
        dernier_achat (datetime): Date/heure de la dernière commande
        premier_achat (datetime): Date/heure de la première commande

    Contraintes:
        - Unicité sur (utilisateur, reference_produit)
        - Tri par défaut sur dernier_achat décroissant

    Note:
        Comme les produits viennent d'une source externe (base LogiGVD),
        on stocke uniquement la référence produit en tant que string
        et non une clé étrangère vers une table locale.
    """
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='historique_achats',
        verbose_name='Utilisateur'
    )
    reference_produit = models.CharField(
        'Référence produit',
        max_length=50,
        help_text="Code produit depuis la base externe"
    )
    categorie = models.CharField(
        'Catégorie',
        max_length=100,
        blank=True,
        default='',
        help_text="Catégorie du produit pour les statistiques"
    )
    quantite_totale = models.PositiveIntegerField(
        'Quantité totale achetée',
        default=0,
        help_text="Cumul des quantités commandées"
    )
    nombre_commandes = models.PositiveIntegerField(
        'Nombre de commandes',
        default=0,
        help_text="Nombre de fois où ce produit a été commandé"
    )
    dernier_achat = models.DateTimeField(
        'Dernier achat',
        auto_now=True,
        help_text="Date de la dernière commande de ce produit"
    )
    premier_achat = models.DateTimeField(
        'Premier achat',
        auto_now_add=True,
        help_text="Date de la première commande de ce produit"
    )

    class Meta:
        verbose_name = 'Historique achat'
        verbose_name_plural = 'Historiques achats'
        # Un seul enregistrement par couple utilisateur/produit
        unique_together = ('utilisateur', 'reference_produit')
        # Tri par date décroissante (achats récents en premier)
        ordering = ['-dernier_achat']

    def __str__(self):
        """Représentation textuelle pour l'admin Django."""
        return f"{self.utilisateur.code_tiers} - {self.reference_produit} ({self.quantite_totale})"

    @classmethod
    def enregistrer_achat(cls, utilisateur, reference_produit, quantite, categorie=''):
        """
        Enregistre ou met à jour l'historique d'achat pour un produit.

        Cette méthode est appelée lors de la validation d'une commande
        pour mettre à jour les statistiques d'achat de l'utilisateur.

        Args:
            utilisateur (Utilisateur): L'utilisateur qui a passé la commande
            reference_produit (str): Code du produit commandé
            quantite (int): Quantité commandée
            categorie (str): Catégorie du produit (optionnel)

        Returns:
            HistoriqueAchat: L'instance créée ou mise à jour

        Comportement:
            - Si l'historique existe : incrémente quantite_totale et
              nombre_commandes, met à jour dernier_achat automatiquement
            - Si l'historique n'existe pas : crée un nouvel enregistrement
            - La catégorie est mise à jour uniquement si elle était vide
        """
        historique, created = cls.objects.get_or_create(
            utilisateur=utilisateur,
            reference_produit=reference_produit,
            defaults={'categorie': categorie}
        )

        # Mise à jour de la catégorie si elle était vide
        if not created and categorie and not historique.categorie:
            historique.categorie = categorie

        # Incrémentation des compteurs
        historique.quantite_totale += quantite
        historique.nombre_commandes += 1
        historique.save()

        return historique


class PreferenceCategorie(models.Model):
    """
    Modèle représentant les préférences de catégories d'un utilisateur.

    Cette table stocke les scores de préférence calculés automatiquement
    pour chaque catégorie de produits. Les scores sont utilisés pour
    affiner les recommandations en proposant des produits des catégories
    préférées de l'utilisateur.

    Attributs:
        utilisateur (FK): Référence vers l'utilisateur concerné
        categorie (str): Nom de la catégorie
        score (float): Score de préférence calculé
        date_calcul (datetime): Date du dernier calcul du score

    Contraintes:
        - Unicité sur (utilisateur, categorie)
        - Tri par défaut sur score décroissant

    Calcul du score:
        Le score est calculé par la fonction calculer_preferences_categories()
        dans services.py. Formule : quantité_totale × nombre_produits_distincts
        Plus le score est élevé, plus la catégorie est importante pour l'utilisateur.
    """
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='preferences_categories',
        verbose_name='Utilisateur'
    )
    categorie = models.CharField(
        'Catégorie',
        max_length=100,
        help_text="Nom de la catégorie de produits"
    )
    score = models.FloatField(
        'Score de préférence',
        default=0,
        help_text="Score calculé basé sur l'historique d'achat"
    )
    date_calcul = models.DateTimeField(
        'Date du calcul',
        auto_now=True,
        help_text="Date de la dernière mise à jour du score"
    )

    class Meta:
        verbose_name = 'Préférence catégorie'
        verbose_name_plural = 'Préférences catégories'
        # Un seul score par couple utilisateur/catégorie
        unique_together = ('utilisateur', 'categorie')
        # Tri par score décroissant (catégories préférées en premier)
        ordering = ['-score']

    def __str__(self):
        """Représentation textuelle pour l'admin Django."""
        return f"{self.utilisateur.code_tiers} - {self.categorie} ({self.score:.2f})"
