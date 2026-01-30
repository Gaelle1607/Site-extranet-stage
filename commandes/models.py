from django.db import models
from clients.models import Utilisateur


class Commande(models.Model):
    """Commande passée par un utilisateur"""
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='commandes',
        verbose_name='Utilisateur'
    )
    numero = models.CharField('Numéro de commande', max_length=50, unique=True)
    date_commande = models.DateTimeField('Date de commande', auto_now_add=True)
    date_livraison = models.DateField('Date de livraison prévue', blank=True, null=True)
    date_depart_camions = models.DateField('Date de départ des camions', blank=True, null=True)
    total_ht = models.DecimalField('Total HT', max_digits=10, decimal_places=2, default=0)
    commentaire = models.TextField('Commentaire', blank=True, default='')

    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-date_commande']

    def __str__(self):
        return f"Commande {self.numero} - {self.utilisateur.code_tiers}"

    @classmethod
    def generer_numero(cls):
        """Génère un numéro de commande unique"""
        from django.utils import timezone
        import random
        date = timezone.now().strftime('%Y%m%d')
        random_part = random.randint(1000, 9999)
        return f"CMD-{date}-{random_part}"


class LigneCommande(models.Model):
    """Ligne d'une commande"""
    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name='lignes',
        verbose_name='Commande'
    )
    reference_produit = models.CharField('Référence produit', max_length=50)
    nom_produit = models.CharField('Nom du produit', max_length=200)
    quantite = models.PositiveIntegerField('Quantité', default=1)
    prix_unitaire = models.DecimalField('Prix unitaire HT', max_digits=10, decimal_places=2)
    total_ligne = models.DecimalField('Total ligne HT', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'

    def __str__(self):
        return f"{self.nom_produit} x {self.quantite}"

    def save(self, *args, **kwargs):
        self.total_ligne = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)
