from django.db import models


class Prod(models.Model):
    """Table des produits (base distante logigvd)"""
    prod = models.CharField('Code produit', max_length=50, primary_key=True)
    libelle = models.CharField('Libellé', max_length=200)

    class Meta:
        managed = False  # Django ne gère pas cette table
        db_table = 'prod'

    def __str__(self):
        return f"{self.prod} - {self.libelle}"


class ComCli(models.Model):
    """Table des clients (base distante logigvd)"""
    tiers = models.IntegerField('Code tiers', primary_key=True)
    nom = models.CharField('Nom', max_length=200)
    complement = models.CharField('Complément', max_length=200, blank=True, null=True)
    adresse = models.CharField('Adresse', max_length=200, blank=True, null=True)
    cp = models.CharField('Code postal', max_length=10, blank=True, null=True)
    acheminement = models.CharField('Ville', max_length=100, blank=True, null=True)
    date_dep = models.DateField('Date départ', blank=True, null=True)
    date_liv = models.DateField('Date livraison', blank=True, null=True)

    class Meta:
        managed = False  # Django ne gère pas cette table
        db_table = 'comcli'

    def __str__(self):
        return f"{self.tiers} - {self.nom}"


class ComCliLig(models.Model):
    """Table des lignes produits par client (base distante logigvd)"""
    prod = models.CharField('Code produit', max_length=50, primary_key=True)
    qte = models.DecimalField('Quantité', max_digits=10, decimal_places=2, blank=True, null=True)
    poids = models.DecimalField('Poids', max_digits=10, decimal_places=2, blank=True, null=True)
    colis = models.IntegerField('Colis', blank=True, null=True)
    pu_base = models.DecimalField('Prix unitaire base', max_digits=10, decimal_places=2, blank=True, null=True)
    pu_net = models.DecimalField('Prix unitaire net', max_digits=10, decimal_places=2, blank=True, null=True)
    commentaire_prep = models.TextField('Commentaire préparation', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'comclilig'

    def __str__(self):
        return f"{self.prod} - Qté: {self.qte}"

    @property
    def produit(self):
        """Récupère le libellé du produit depuis la table prod"""
        try:
            return Prod.objects.using('logigvd').get(prod=self.prod)
        except Prod.DoesNotExist:
            return None

    @property
    def libelle(self):
        """Raccourci pour obtenir le libellé du produit"""
        produit = self.produit
        return produit.libelle if produit else self.prod


class Catalogue(models.Model):
    """Table catalogue - produits disponibles par client (base distante logigvd)"""
    tiers = models.IntegerField('Code tiers', primary_key=True)
    prod = models.CharField('Code produit', max_length=50)

    class Meta:
        managed = False
        db_table = 'catalogue'
        unique_together = ('tiers', 'prod')

    def __str__(self):
        return f"{self.tiers} - {self.prod}"

    @property
    def produit(self):
        """Récupère les infos du produit depuis la table prod"""
        try:
            return Prod.objects.using('logigvd').get(prod=self.prod)
        except Prod.DoesNotExist:
            return None

    @property
    def nom_produit(self):
        """Raccourci pour obtenir le libellé du produit"""
        produit = self.produit
        return produit.libelle if produit else self.prod
