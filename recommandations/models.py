from django.db import models
from clients.models import Client


class HistoriqueAchat(models.Model):
    """Historique des achats pour le système de recommandations.

    Note: Les produits viennent d'une source externe, donc on stocke
    uniquement la référence produit (string) et non une clé étrangère.
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='historique_achats',
        verbose_name='Client'
    )
    reference_produit = models.CharField('Référence produit', max_length=50)
    categorie = models.CharField('Catégorie', max_length=100, blank=True, default='')
    quantite_totale = models.PositiveIntegerField('Quantité totale achetée', default=0)
    nombre_commandes = models.PositiveIntegerField('Nombre de commandes', default=0)
    dernier_achat = models.DateTimeField('Dernier achat', auto_now=True)
    premier_achat = models.DateTimeField('Premier achat', auto_now_add=True)

    class Meta:
        verbose_name = 'Historique achat'
        verbose_name_plural = 'Historiques achats'
        unique_together = ('client', 'reference_produit')
        ordering = ['-dernier_achat']

    def __str__(self):
        return f"{self.client.societe} - {self.reference_produit} ({self.quantite_totale})"

    @classmethod
    def enregistrer_achat(cls, client, reference_produit, quantite, categorie=''):
        """Enregistre ou met à jour l'historique d'achat"""
        historique, created = cls.objects.get_or_create(
            client=client,
            reference_produit=reference_produit,
            defaults={'categorie': categorie}
        )
        if not created and categorie and not historique.categorie:
            historique.categorie = categorie
        historique.quantite_totale += quantite
        historique.nombre_commandes += 1
        historique.save()
        return historique


class PreferenceCategorie(models.Model):
    """Préférences de catégories par client (calculé automatiquement)"""
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='preferences_categories',
        verbose_name='Client'
    )
    categorie = models.CharField('Catégorie', max_length=100)
    score = models.FloatField('Score de préférence', default=0)
    date_calcul = models.DateTimeField('Date du calcul', auto_now=True)

    class Meta:
        verbose_name = 'Préférence catégorie'
        verbose_name_plural = 'Préférences catégories'
        unique_together = ('client', 'categorie')
        ordering = ['-score']

    def __str__(self):
        return f"{self.client.societe} - {self.categorie} ({self.score:.2f})"
