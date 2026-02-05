"""
=============================================================================
MODELS.PY - Modèles de l'application Catalogue
=============================================================================

Ce fichier définit les modèles Django pour accéder aux tables de la
base de données distante LogiGVD (MariaDB).

IMPORTANT : Ces modèles ont managed=False car les tables existent
déjà dans la base distante et ne doivent pas être modifiées par Django.

Tables mappées :
    - prod      : Catalogue des produits (référence, libellé)
    - comcli    : Clients et leurs adresses de livraison
    - comclilig : Lignes de commande historiques (prix, quantités)
    - catalogue : Association produits/clients (disponibilité)

Projet : Extranet Giffaud Groupe
=============================================================================
"""
from django.db import models


class Prod(models.Model):
    """
    Modèle représentant un produit dans le catalogue.

    Cette table contient le référentiel des produits avec leurs
    informations de base (code, libellé).

    Attributs:
        prod (str): Code unique du produit (clé primaire)
        libelle (str): Description/nom du produit

    Note:
        Table en lecture seule depuis la base distante 'logigvd'.
        Utiliser .using('logigvd') pour les requêtes.
    """
    prod = models.CharField('Code produit', max_length=50, primary_key=True)
    libelle = models.CharField('Libellé', max_length=200)

    class Meta:
        managed = False  # Django ne gère pas cette table (pas de migrations)
        db_table = 'prod'  # Nom de la table dans la base distante

    def __str__(self):
        return f"{self.prod} - {self.libelle}"


class ComCli(models.Model):
    """
    Modèle représentant un client et son adresse de livraison.

    Un même client (tiers) peut avoir plusieurs adresses de livraison
    différentes, identifiées par le champ 'complement'.

    Attributs:
        tiers (int): Code client (clé primaire)
        nom (str): Nom du client/société
        complement (str): Complément d'adresse ou nom de l'établissement
        adresse (str): Adresse de livraison
        cp (str): Code postal
        acheminement (str): Ville
        date_dep (date): Date de départ prévue des commandes
        date_liv (date): Date de livraison prévue

    Note:
        Table en lecture seule depuis la base distante 'logigvd'.
    """
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
    """
    Modèle représentant une ligne de commande historique.

    Cette table contient l'historique des commandes passées par les clients,
    avec les prix et quantités. Elle sert de base pour le cadencier
    (historique des achats) et pour calculer les prix personnalisés.

    Attributs:
        prod (str): Code produit (clé primaire composite)
        qte (Decimal): Quantité commandée
        poids (Decimal): Poids total de la ligne
        colis (int): Nombre de colis
        pu_base (Decimal): Prix unitaire de base (tarif standard)
        pu_net (Decimal): Prix unitaire net (après remises)
        commentaire_prep (str): Instructions pour la préparation

    Propriétés:
        produit: Récupère l'objet Prod associé
        libelle: Raccourci pour le libellé du produit

    Note:
        Table en lecture seule depuis la base distante 'logigvd'.
    """
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
        """
        Récupère l'objet Prod associé à cette ligne.

        Returns:
            Prod: L'objet produit ou None si non trouvé
        """
        try:
            return Prod.objects.using('logigvd').get(prod=self.prod)
        except Prod.DoesNotExist:
            return None

    @property
    def libelle(self):
        """
        Raccourci pour obtenir le libellé du produit.

        Returns:
            str: Le libellé du produit ou le code produit si non trouvé
        """
        produit = self.produit
        return produit.libelle if produit else self.prod


class Catalogue(models.Model):
    """
    Modèle représentant l'association produit/client (disponibilité).

    Cette table définit quels produits sont disponibles pour chaque client.
    Un produit doit être présent dans le catalogue d'un client pour
    qu'il puisse le commander.

    Attributs:
        tiers (int): Code client (clé primaire composite)
        prod (str): Code produit (clé primaire composite)

    Propriétés:
        produit: Récupère l'objet Prod associé
        nom_produit: Raccourci pour le libellé du produit

    Note:
        Table en lecture seule depuis la base distante 'logigvd'.
        La clé primaire est composite (tiers + prod).
    """
    tiers = models.IntegerField('Code tiers', primary_key=True)
    prod = models.CharField('Code produit', max_length=50)

    class Meta:
        managed = False
        db_table = 'catalogue'
        unique_together = ('tiers', 'prod')  # Clé primaire composite

    def __str__(self):
        return f"{self.tiers} - {self.prod}"

    @property
    def produit(self):
        """
        Récupère l'objet Prod associé à cette entrée catalogue.

        Returns:
            Prod: L'objet produit ou None si non trouvé
        """
        try:
            return Prod.objects.using('logigvd').get(prod=self.prod)
        except Prod.DoesNotExist:
            return None

    @property
    def nom_produit(self):
        """
        Raccourci pour obtenir le libellé du produit.

        Returns:
            str: Le libellé du produit ou le code produit si non trouvé
        """
        produit = self.produit
        return produit.libelle if produit else self.prod
