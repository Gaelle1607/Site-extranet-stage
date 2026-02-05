# -*- coding: utf-8 -*-
"""
==============================================================================
Module: commandes/models.py
Application: Commandes - Extranet Giffaud Groupe
==============================================================================

Description:
    Ce module définit les modèles de données pour la gestion des commandes
    clients de l'application Extranet Giffaud Groupe. L'extranet permet aux
    clients professionnels de passer des commandes en ligne.

Modèles définis:
    - HistoriqueSuppression : Archive des commandes supprimées définitivement
      Conserve une trace des commandes supprimées pour audit et traçabilité.

    - CommandeSupprimee : Commandes en attente de suppression définitive
      Système de "corbeille" avec restauration possible pendant 5 minutes.

    - Commande : Commandes actives passées par les utilisateurs
      Modèle principal stockant les commandes validées par les clients.

    - LigneCommande : Détail des articles d'une commande
      Chaque ligne représente un produit commandé avec quantité et prix.

Workflow de commande:
    1. Le client ajoute des produits au panier (session)
    2. Validation du panier -> création d'une Commande avec ses LigneCommande
    3. Génération d'un fichier EDI (CSV) pour l'ERP
    4. Envoi d'un email de confirmation au client
    5. L'administrateur peut supprimer une commande (mise en corbeille 5 min)
    6. Après 5 minutes, suppression définitive et archivage dans HistoriqueSuppression

Auteur: Giffaud Groupe
Date de création: 2024
Dernière modification: 2024
==============================================================================
"""

# ==============================================================================
# IMPORTS
# ==============================================================================

# Django - ORM et modèles
from django.db import models

# Django - Gestion des fuseaux horaires
from django.utils import timezone

# Python - Manipulation des durées
from datetime import timedelta

# Application clients - Modèle Utilisateur
from clients.models import Utilisateur


# ==============================================================================
# MODÈLE: HISTORIQUE DES SUPPRESSIONS DÉFINITIVES
# ==============================================================================

class HistoriqueSuppression(models.Model):
    """
    Modèle d'historique des commandes supprimées définitivement.

    Cette classe conserve une trace permanente des commandes qui ont été
    supprimées de manière définitive après expiration du délai de restauration
    de 5 minutes. Elle permet de garder un historique à des fins d'audit,
    de traçabilité et de conformité réglementaire.

    Les données conservées sont minimales mais suffisantes pour identifier
    la commande supprimée et son contexte.

    Attributes:
        numero (CharField):
            Numéro unique de la commande supprimée.
            Format: CMD-YYYYMMDD-XXXX (ex: CMD-20240115-1234)
            Max 50 caractères.

        nom_client (CharField):
            Nom complet du client ayant passé la commande.
            Récupéré depuis la base distante au moment de la suppression.
            Max 200 caractères.

        code_tiers (CharField):
            Code tiers du client dans l'ERP.
            Identifiant unique du client dans le système de gestion.
            Max 50 caractères.

        total_ht (DecimalField):
            Montant total HT de la commande en euros.
            Précision: 10 chiffres dont 2 décimales (max: 99 999 999,99 €).

        date_suppression_definitive (DateTimeField):
            Horodatage de la suppression définitive.
            Renseigné automatiquement à la création de l'enregistrement.

    Meta:
        verbose_name: 'Historique de suppression'
        verbose_name_plural: 'Historiques de suppression'
        ordering: Plus récentes en premier ([-date_suppression_definitive])

    Note:
        - Les données sont conservées à titre d'archive uniquement.
        - Aucun fichier EDI n'est conservé après suppression définitive.
        - Ce modèle ne permet pas de restaurer une commande supprimée.

    Example:
        >>> historique = HistoriqueSuppression.objects.create(
        ...     numero='CMD-20240115-1234',
        ...     nom_client='Restaurant Le Bon Goût',
        ...     code_tiers='CLI001',
        ...     total_ht=Decimal('450.00')
        ... )
        >>> print(historique)
        Suppression définitive CMD-20240115-1234 - Restaurant Le Bon Goût
    """

    # ==========================================================================
    # CHAMPS DU MODÈLE
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Informations de la commande supprimée
    # --------------------------------------------------------------------------

    # Numéro unique de la commande (copié depuis Commande.numero)
    numero = models.CharField(
        verbose_name='Numéro de commande',
        max_length=50,
        help_text="Numéro unique de la commande au format CMD-YYYYMMDD-XXXX"
    )

    # Nom du client au moment de la suppression
    nom_client = models.CharField(
        verbose_name='Nom du client',
        max_length=200,
        help_text="Nom complet du client récupéré depuis la base distante"
    )

    # Code tiers du client dans l'ERP
    code_tiers = models.CharField(
        verbose_name='Code tiers',
        max_length=50,
        help_text="Identifiant du client dans le système de gestion"
    )

    # Montant total HT de la commande
    total_ht = models.DecimalField(
        verbose_name='Total HT',
        max_digits=10,          # Jusqu'à 99 999 999,99 €
        decimal_places=2,       # 2 décimales pour les centimes
        default=0,
        help_text="Montant total HT de la commande en euros"
    )

    # --------------------------------------------------------------------------
    # Horodatage de la suppression
    # --------------------------------------------------------------------------

    # Date et heure de la suppression définitive (automatique)
    date_suppression_definitive = models.DateTimeField(
        verbose_name='Date de suppression définitive',
        auto_now_add=True,      # Horodatage automatique à la création
        help_text="Date et heure de la suppression définitive"
    )

    # ==========================================================================
    # MÉTA-DONNÉES DU MODÈLE
    # ==========================================================================

    class Meta:
        """Configuration des métadonnées du modèle HistoriqueSuppression."""

        # Nom affiché dans l'interface d'administration
        verbose_name = 'Historique de suppression'
        verbose_name_plural = 'Historiques de suppression'

        # Tri par défaut: plus récentes en premier
        ordering = ['-date_suppression_definitive']

    # ==========================================================================
    # MÉTHODES SPÉCIALES
    # ==========================================================================

    def __str__(self):
        """
        Représentation textuelle de l'historique de suppression.

        Cette méthode est utilisée par Django dans l'interface d'administration
        et lors de l'affichage de l'objet dans les logs ou le débogage.

        Returns:
            str: Chaîne au format "Suppression définitive {numero} - {nom_client}"

        Example:
            >>> historique = HistoriqueSuppression(
            ...     numero='CMD-20240115-1234',
            ...     nom_client='Restaurant Le Bon Goût'
            ... )
            >>> str(historique)
            'Suppression définitive CMD-20240115-1234 - Restaurant Le Bon Goût'
        """
        return f"Suppression définitive {self.numero} - {self.nom_client}"


# ==============================================================================
# MODÈLE: COMMANDE SUPPRIMÉE (CORBEILLE)
# ==============================================================================

class CommandeSupprimee(models.Model):
    """
    Modèle pour les commandes supprimées temporairement (système de corbeille).

    Cette classe gère le système de "corbeille" avec restauration possible
    pendant une période de 5 minutes après suppression. Passé ce délai,
    la commande est définitivement supprimée et archivée dans HistoriqueSuppression.

    Ce système permet aux administrateurs de :
    - Supprimer une commande (mise en attente de 5 minutes)
    - Restaurer une commande supprimée par erreur avant expiration
    - Laisser expirer automatiquement les commandes non restaurées

    Attributes:
        utilisateur (ForeignKey):
            Référence vers l'utilisateur propriétaire de la commande.
            Relation vers clients.Utilisateur.
            Suppression en cascade si l'utilisateur est supprimé.

        numero (CharField):
            Numéro unique de la commande.
            Format: CMD-YYYYMMDD-XXXX.
            Max 50 caractères.

        date_commande (DateTimeField):
            Date et heure de la commande originale.
            Conservée pour permettre une restauration complète.

        date_livraison (DateField):
            Date de livraison souhaitée par le client.
            Optionnel (peut être null).

        date_depart_camions (DateField):
            Date de départ prévu des camions.
            Optionnel (peut être null).

        total_ht (DecimalField):
            Montant total HT de la commande en euros.
            Précision: 10 chiffres dont 2 décimales.

        commentaire (TextField):
            Notes ou commentaires du client.
            Optionnel, vide par défaut.

        lignes_json (JSONField):
            Sauvegarde JSON des lignes de commande.
            Permet une restauration complète sans dépendance aux modèles liés.
            Structure: [{reference, nom, quantite, prix_unitaire, total_ligne}, ...]

        date_suppression (DateTimeField):
            Horodatage de la mise en corbeille.
            Renseigné automatiquement à la création.

    Meta:
        verbose_name: 'Commande supprimée'
        verbose_name_plural: 'Commandes supprimées'
        ordering: Plus récentes en premier ([-date_suppression])

    Methods:
        est_restaurable(): Vérifie si la commande peut encore être restaurée
        temps_restant(): Calcule le temps restant avant suppression définitive
        nettoyer_anciennes(): Méthode de classe pour supprimer les commandes expirées

    Note:
        Les lignes de commande sont stockées en JSON pour permettre
        une restauration complète sans dépendance aux modèles liés.
        Cette approche évite les problèmes de clés étrangères lors de la restauration.
    """

    # ==========================================================================
    # CHAMPS DU MODÈLE
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Relation vers l'utilisateur
    # --------------------------------------------------------------------------

    # Référence vers l'utilisateur propriétaire de la commande
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,   # Suppression en cascade si l'utilisateur est supprimé
        related_name='commandes_supprimees',  # Accès inverse: utilisateur.commandes_supprimees.all()
        verbose_name='Utilisateur',
        help_text="Utilisateur ayant passé la commande"
    )

    # --------------------------------------------------------------------------
    # Données principales de la commande
    # --------------------------------------------------------------------------

    # Numéro unique de la commande
    numero = models.CharField(
        verbose_name='Numéro de commande',
        max_length=50,
        help_text="Numéro unique au format CMD-YYYYMMDD-XXXX"
    )

    # Date et heure de la commande originale
    date_commande = models.DateTimeField(
        verbose_name='Date de commande',
        help_text="Date et heure de création de la commande originale"
    )

    # Date de livraison souhaitée (optionnel)
    date_livraison = models.DateField(
        verbose_name='Date de livraison prévue',
        blank=True,
        null=True,
        help_text="Date de livraison souhaitée par le client"
    )

    # Date de départ des camions (optionnel)
    date_depart_camions = models.DateField(
        verbose_name='Date de départ des camions',
        blank=True,
        null=True,
        help_text="Date de départ prévu des camions"
    )

    # Montant total HT
    total_ht = models.DecimalField(
        verbose_name='Total HT',
        max_digits=10,          # Jusqu'à 99 999 999,99 €
        decimal_places=2,       # 2 décimales
        default=0,
        help_text="Montant total HT de la commande en euros"
    )

    # Commentaires du client
    commentaire = models.TextField(
        verbose_name='Commentaire',
        blank=True,
        default='',
        help_text="Notes ou instructions spéciales du client"
    )

    # --------------------------------------------------------------------------
    # Sauvegarde des lignes de commande
    # --------------------------------------------------------------------------

    # Lignes de commande au format JSON pour restauration
    # Structure attendue: [
    #     {
    #         "reference": "PROD001",
    #         "nom": "Produit A",
    #         "quantite": 10,
    #         "prix_unitaire": 15.50,
    #         "total_ligne": 155.00
    #     },
    #     ...
    # ]
    lignes_json = models.JSONField(
        verbose_name='Lignes de commande',
        default=list,
        help_text="Sauvegarde JSON des lignes pour restauration"
    )

    # --------------------------------------------------------------------------
    # Horodatage de la suppression
    # --------------------------------------------------------------------------

    # Date de mise en corbeille (automatique)
    date_suppression = models.DateTimeField(
        verbose_name='Date de suppression',
        auto_now_add=True,      # Horodatage automatique à la création
        help_text="Date et heure de mise en corbeille"
    )

    # ==========================================================================
    # MÉTA-DONNÉES DU MODÈLE
    # ==========================================================================

    class Meta:
        """Configuration des métadonnées du modèle CommandeSupprimee."""

        # Nom affiché dans l'interface d'administration
        verbose_name = 'Commande supprimée'
        verbose_name_plural = 'Commandes supprimées'

        # Tri par défaut: plus récentes en premier
        ordering = ['-date_suppression']

    # ==========================================================================
    # MÉTHODES SPÉCIALES
    # ==========================================================================

    def __str__(self):
        """
        Représentation textuelle de la commande supprimée.

        Returns:
            str: Chaîne au format "Commande supprimée {numero}"

        Example:
            >>> cmd = CommandeSupprimee(numero='CMD-20240115-1234')
            >>> str(cmd)
            'Commande supprimée CMD-20240115-1234'
        """
        return f"Commande supprimée {self.numero}"

    # ==========================================================================
    # MÉTHODES D'INSTANCE
    # ==========================================================================

    def est_restaurable(self):
        """
        Vérifie si la commande peut encore être restaurée.

        La restauration est possible pendant 5 minutes après la suppression.
        Passé ce délai, la commande sera définitivement supprimée par
        la tâche de nettoyage automatique (méthode nettoyer_anciennes).

        Returns:
            bool: True si moins de 5 minutes se sont écoulées depuis la suppression,
                  False si le délai est dépassé.

        Example:
            >>> cmd = CommandeSupprimee.objects.get(numero='CMD-20240115-1234')
            >>> if cmd.est_restaurable():
            ...     # Proposer la restauration à l'utilisateur
            ...     pass
        """
        # Calcul de la limite de restauration (5 minutes après suppression)
        limite = self.date_suppression + timedelta(minutes=5)

        # Comparaison avec l'heure actuelle
        return timezone.now() < limite

    def temps_restant(self):
        """
        Calcule le temps restant avant suppression définitive.

        Cette méthode est utilisée pour afficher un compte à rebours
        sur l'interface d'administration, permettant aux administrateurs
        de savoir combien de temps il reste pour restaurer une commande.

        Returns:
            int: Nombre de secondes restantes avant suppression définitive.
                 Retourne 0 si le délai est dépassé (jamais de valeur négative).

        Example:
            >>> cmd = CommandeSupprimee.objects.get(numero='CMD-20240115-1234')
            >>> secondes = cmd.temps_restant()
            >>> minutes = secondes // 60
            >>> print(f"Temps restant: {minutes} min {secondes % 60} sec")
        """
        # Calcul de la limite (5 minutes après suppression)
        limite = self.date_suppression + timedelta(minutes=5)

        # Calcul du delta temporel entre la limite et maintenant
        delta = limite - timezone.now()

        # Retourne au minimum 0 (pas de valeur négative)
        return max(0, int(delta.total_seconds()))

    # ==========================================================================
    # MÉTHODES DE CLASSE
    # ==========================================================================

    @classmethod
    def nettoyer_anciennes(cls):
        """
        Supprime définitivement les commandes expirées et leurs fichiers EDI.

        Cette méthode de classe est appelée périodiquement (via une tâche planifiée,
        un signal Django, ou au chargement de certaines pages d'administration)
        pour nettoyer les commandes dont le délai de restauration de 5 minutes
        est dépassé.

        Pour chaque commande expirée, la méthode effectue les opérations suivantes:
        1. Récupération des informations client depuis la base distante
        2. Création d'une entrée dans HistoriqueSuppression (traçabilité)
        3. Suppression du fichier CSV EDI associé sur le disque
        4. Suppression de l'enregistrement en base de données

        Note:
            - Les erreurs de suppression de fichiers sont ignorées silencieusement
              (le fichier peut avoir déjà été supprimé manuellement ou ne pas exister).
            - La méthode utilise select_related pour optimiser les requêtes SQL.
            - La suppression finale est effectuée en masse pour de meilleures performances.

        Example:
            >>> # Appel manuel (généralement automatisé)
            >>> CommandeSupprimee.nettoyer_anciennes()
            >>> # Toutes les commandes expirées sont maintenant archivées
        """
        import os
        from pathlib import Path

        # Chemin du dossier contenant les fichiers EDI exportés
        # Ce chemin doit correspondre à celui défini dans commandes/services.py
        EDI_OUTPUT_DIR = Path(r'C:\Users\Giffaud\Documents\Site_extranet\edi_exports')

        # Calcul de la limite : commandes supprimées il y a plus de 5 minutes
        limite = timezone.now() - timedelta(minutes=5)

        # Récupération des commandes expirées avec les données utilisateur
        # select_related optimise en faisant une seule requête SQL avec JOIN
        anciennes = cls.objects.select_related('utilisateur').filter(
            date_suppression__lt=limite
        )

        # Traitement de chaque commande expirée
        for commande in anciennes:
            # ------------------------------------------------------------------
            # Étape 1: Récupération du nom du client
            # ------------------------------------------------------------------
            # Utilisation de la méthode get_client_distant pour récupérer
            # les informations client depuis la base de données distante
            client = commande.utilisateur.get_client_distant()
            nom_client = client.nom if client else f"Client {commande.utilisateur.code_tiers}"

            # ------------------------------------------------------------------
            # Étape 2: Création de l'entrée d'historique pour traçabilité
            # ------------------------------------------------------------------
            HistoriqueSuppression.objects.create(
                numero=commande.numero,
                nom_client=nom_client,
                code_tiers=commande.utilisateur.code_tiers,
                total_ht=commande.total_ht,
            )

            # ------------------------------------------------------------------
            # Étape 3: Suppression du fichier CSV EDI associé
            # ------------------------------------------------------------------
            fichier_edi = EDI_OUTPUT_DIR / f"{commande.numero}.csv"
            if fichier_edi.exists():
                try:
                    os.remove(fichier_edi)
                except OSError:
                    # Erreur ignorée silencieusement
                    # Le fichier peut être verrouillé ou déjà supprimé
                    pass

        # ----------------------------------------------------------------------
        # Étape 4: Suppression en masse des enregistrements expirés
        # ----------------------------------------------------------------------
        # La suppression en masse est plus efficace qu'une boucle de delete()
        anciennes.delete()


# ==============================================================================
# MODÈLE: COMMANDE (MODÈLE PRINCIPAL)
# ==============================================================================

class Commande(models.Model):
    """
    Modèle principal représentant une commande client active.

    Cette classe stocke les commandes passées par les utilisateurs de l'extranet
    Giffaud Groupe. Chaque commande est associée à un utilisateur et contient
    plusieurs lignes de commande (articles commandés) via le modèle LigneCommande.

    Workflow d'une commande:
        1. Le client remplit son panier (stocké en session)
        2. Validation du panier -> création de la Commande et des LigneCommande
        3. Génération d'un fichier EDI (CSV) pour transmission à l'ERP
        4. Envoi d'un email de confirmation au client
        5. Possible suppression (mise en corbeille) par l'administration
        6. Après 5 minutes, suppression définitive et archivage

    Attributes:
        utilisateur (ForeignKey):
            Référence vers l'utilisateur ayant passé la commande.
            Relation vers clients.Utilisateur.
            Suppression en cascade si l'utilisateur est supprimé.

        numero (CharField):
            Numéro unique de la commande.
            Format: CMD-YYYYMMDD-XXXX (ex: CMD-20240115-5678).
            Généré automatiquement par la méthode generer_numero().
            Contrainte d'unicité en base de données.
            Max 50 caractères.

        date_commande (DateTimeField):
            Date et heure de création de la commande.
            Renseigné automatiquement à la création (auto_now_add).

        date_livraison (DateField):
            Date de livraison souhaitée par le client.
            Optionnel (peut être null).

        date_depart_camions (DateField):
            Date de départ prévu des camions.
            Optionnel (peut être null).

        total_ht (DecimalField):
            Montant total HT de la commande en euros.
            Calculé comme la somme des totaux des lignes.
            Précision: 10 chiffres dont 2 décimales (max: 99 999 999,99 €).

        commentaire (TextField):
            Instructions spéciales ou notes du client.
            Optionnel, vide par défaut.

    Meta:
        verbose_name: 'Commande'
        verbose_name_plural: 'Commandes'
        ordering: Plus récentes en premier ([-date_commande])

    Methods:
        generer_numero(): Méthode de classe pour générer un numéro unique

    Relations:
        lignes (reverse ForeignKey): Accès aux LigneCommande via commande.lignes.all()

    Example:
        >>> from decimal import Decimal
        >>> commande = Commande.objects.create(
        ...     utilisateur=utilisateur,
        ...     numero=Commande.generer_numero(),
        ...     date_livraison=date(2024, 1, 20),
        ...     total_ht=Decimal('150.00'),
        ...     commentaire='Livraison le matin SVP'
        ... )
        >>> print(commande)
        Commande CMD-20240115-5678 - CLI001
    """

    # ==========================================================================
    # CHAMPS DU MODÈLE
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Relation vers l'utilisateur propriétaire
    # --------------------------------------------------------------------------

    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,   # Suppression en cascade
        related_name='commandes',   # Accès inverse: utilisateur.commandes.all()
        verbose_name='Utilisateur',
        help_text="Utilisateur ayant passé la commande"
    )

    # --------------------------------------------------------------------------
    # Numéro unique de commande
    # --------------------------------------------------------------------------

    numero = models.CharField(
        verbose_name='Numéro de commande',
        max_length=50,
        unique=True,                # Contrainte d'unicité en base de données
        help_text="Numéro unique au format CMD-YYYYMMDD-XXXX"
    )

    # --------------------------------------------------------------------------
    # Dates de la commande
    # --------------------------------------------------------------------------

    # Date de création (automatique)
    date_commande = models.DateTimeField(
        verbose_name='Date de commande',
        auto_now_add=True,          # Horodatage automatique à la création
        help_text="Date et heure de validation de la commande"
    )

    # Date de livraison souhaitée (optionnel)
    date_livraison = models.DateField(
        verbose_name='Date de livraison prévue',
        blank=True,
        null=True,                  # Optionnel
        help_text="Date de livraison souhaitée par le client"
    )

    # Date de départ des camions (optionnel)
    date_depart_camions = models.DateField(
        verbose_name='Date de départ des camions',
        blank=True,
        null=True,                  # Optionnel
        help_text="Date de départ prévu des camions"
    )

    # --------------------------------------------------------------------------
    # Montant et commentaires
    # --------------------------------------------------------------------------

    # Montant total HT de la commande
    total_ht = models.DecimalField(
        verbose_name='Total HT',
        max_digits=10,              # Jusqu'à 99 999 999,99 €
        decimal_places=2,           # 2 décimales pour les centimes
        default=0,
        help_text="Montant total HT de la commande en euros"
    )

    # Commentaires ou instructions spéciales
    commentaire = models.TextField(
        verbose_name='Commentaire',
        blank=True,
        default='',
        help_text="Instructions spéciales ou notes du client"
    )

    # ==========================================================================
    # MÉTA-DONNÉES DU MODÈLE
    # ==========================================================================

    class Meta:
        """Configuration des métadonnées du modèle Commande."""

        # Nom affiché dans l'interface d'administration
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'

        # Tri par défaut: plus récentes en premier
        ordering = ['-date_commande']

    # ==========================================================================
    # MÉTHODES SPÉCIALES
    # ==========================================================================

    def __str__(self):
        """
        Représentation textuelle de la commande.

        Affiche le numéro de commande et le code tiers du client pour
        une identification rapide dans l'interface d'administration.

        Returns:
            str: Chaîne au format "Commande {numero} - {code_tiers}"

        Example:
            >>> commande = Commande(numero='CMD-20240115-5678')
            >>> commande.utilisateur = Utilisateur(code_tiers='CLI001')
            >>> str(commande)
            'Commande CMD-20240115-5678 - CLI001'
        """
        return f"Commande {self.numero} - {self.utilisateur.code_tiers}"

    # ==========================================================================
    # MÉTHODES DE CLASSE
    # ==========================================================================

    @classmethod
    def generer_numero(cls):
        """
        Génère un numéro de commande unique.

        Le format du numéro est: CMD-YYYYMMDD-XXXX
        - CMD : Préfixe identifiant une commande
        - YYYYMMDD : Date du jour au format ISO (année-mois-jour)
        - XXXX : Nombre aléatoire entre 1000 et 9999

        Cette méthode est appelée lors de la création d'une nouvelle commande
        pour générer automatiquement un numéro unique et identifiable.

        Returns:
            str: Numéro de commande unique (ex: "CMD-20240115-5678")

        Note:
            En cas de collision (très rare, probabilité 1/9000 par jour),
            la contrainte unique en base de données lèvera une IntegrityError.
            L'application devra alors réessayer avec un nouveau numéro.

        Example:
            >>> numero = Commande.generer_numero()
            >>> print(numero)
            'CMD-20240115-5678'
        """
        # Import des modules nécessaires
        from django.utils import timezone
        import random

        # Formatage de la date du jour au format YYYYMMDD
        date = timezone.now().strftime('%Y%m%d')

        # Génération d'un nombre aléatoire à 4 chiffres (1000-9999)
        random_part = random.randint(1000, 9999)

        # Construction et retour du numéro complet
        return f"CMD-{date}-{random_part}"


# ==============================================================================
# MODÈLE: LIGNE DE COMMANDE
# ==============================================================================

class LigneCommande(models.Model):
    """
    Modèle représentant une ligne d'une commande (un article commandé).

    Chaque ligne de commande correspond à un produit commandé avec sa quantité
    et son prix unitaire. Le total de la ligne est calculé automatiquement
    lors de la sauvegarde (quantité x prix_unitaire).

    Les informations produit (nom, prix) sont copiées depuis le catalogue
    au moment de la commande pour conserver l'historique exact même si
    le produit change de nom ou de prix ultérieurement dans le catalogue.

    Attributes:
        commande (ForeignKey):
            Référence vers la commande parente.
            Relation vers commandes.Commande.
            Suppression en cascade avec la commande.

        reference_produit (CharField):
            Référence unique du produit dans le catalogue.
            Identifiant stable permettant de retrouver le produit.
            Max 50 caractères.

        nom_produit (CharField):
            Libellé du produit au moment de la commande.
            Copié depuis le catalogue pour conservation historique.
            Max 200 caractères.

        quantite (PositiveIntegerField):
            Quantité commandée.
            Doit être supérieure ou égale à 1.
            Default: 1.

        prix_unitaire (DecimalField):
            Prix unitaire HT au moment de la commande.
            Copié depuis le catalogue pour conservation historique.
            Précision: 10 chiffres dont 2 décimales.

        total_ligne (DecimalField):
            Total HT de la ligne (quantité x prix_unitaire).
            Calculé automatiquement lors de la sauvegarde.
            Précision: 10 chiffres dont 2 décimales.

    Meta:
        verbose_name: 'Ligne de commande'
        verbose_name_plural: 'Lignes de commande'

    Methods:
        save(): Surcharge pour calcul automatique du total_ligne

    Note:
        Le nom et le prix sont stockés en dur (dénormalisés) pour conserver
        l'historique exact au moment de la commande. Cette approche garantit
        que les factures et les historiques restent cohérents même si les
        produits évoluent dans le catalogue.

    Example:
        >>> from decimal import Decimal
        >>> ligne = LigneCommande.objects.create(
        ...     commande=commande,
        ...     reference_produit='PROD001',
        ...     nom_produit='Saucisson sec traditionnel',
        ...     quantite=5,
        ...     prix_unitaire=Decimal('12.50'),
        ...     total_ligne=Decimal('62.50')  # Ou laissé au calcul auto
        ... )
        >>> print(ligne)
        Saucisson sec traditionnel x 5
    """

    # ==========================================================================
    # CHAMPS DU MODÈLE
    # ==========================================================================

    # --------------------------------------------------------------------------
    # Relation vers la commande parente
    # --------------------------------------------------------------------------

    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,   # Suppression en cascade avec la commande
        related_name='lignes',      # Accès inverse: commande.lignes.all()
        verbose_name='Commande',
        help_text="Commande à laquelle appartient cette ligne"
    )

    # --------------------------------------------------------------------------
    # Informations produit (copiées depuis le catalogue)
    # --------------------------------------------------------------------------

    # Référence unique du produit
    reference_produit = models.CharField(
        verbose_name='Référence produit',
        max_length=50,
        help_text="Référence unique du produit dans le catalogue"
    )

    # Nom du produit (snapshot au moment de la commande)
    nom_produit = models.CharField(
        verbose_name='Nom du produit',
        max_length=200,
        help_text="Libellé du produit au moment de la commande"
    )

    # --------------------------------------------------------------------------
    # Quantité et prix
    # --------------------------------------------------------------------------

    # Quantité commandée (minimum 1)
    quantite = models.PositiveIntegerField(
        verbose_name='Quantité',
        default=1,
        help_text="Quantité commandée (minimum 1)"
    )

    # Prix unitaire HT (snapshot au moment de la commande)
    prix_unitaire = models.DecimalField(
        verbose_name='Prix unitaire HT',
        max_digits=10,              # Jusqu'à 99 999 999,99 €
        decimal_places=2,           # 2 décimales
        help_text="Prix unitaire HT au moment de la commande"
    )

    # Total de la ligne (calculé automatiquement)
    total_ligne = models.DecimalField(
        verbose_name='Total ligne HT',
        max_digits=10,              # Jusqu'à 99 999 999,99 €
        decimal_places=2,           # 2 décimales
        help_text="Total HT de la ligne (quantité x prix unitaire)"
    )

    # ==========================================================================
    # MÉTA-DONNÉES DU MODÈLE
    # ==========================================================================

    class Meta:
        """Configuration des métadonnées du modèle LigneCommande."""

        # Nom affiché dans l'interface d'administration
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'

    # ==========================================================================
    # MÉTHODES SPÉCIALES
    # ==========================================================================

    def __str__(self):
        """
        Représentation textuelle de la ligne de commande.

        Affiche le nom du produit et la quantité pour une identification
        rapide dans l'interface d'administration et les logs.

        Returns:
            str: Chaîne au format "{nom_produit} x {quantite}"

        Example:
            >>> ligne = LigneCommande(
            ...     nom_produit='Saucisson sec traditionnel',
            ...     quantite=5
            ... )
            >>> str(ligne)
            'Saucisson sec traditionnel x 5'
        """
        return f"{self.nom_produit} x {self.quantite}"

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour calculer automatiquement le total.

        Le total de la ligne est calculé comme: quantité x prix_unitaire
        Ce calcul est effectué à chaque sauvegarde pour garantir la cohérence
        des données, même si la quantité ou le prix sont modifiés.

        Args:
            *args: Arguments positionnels passés à la méthode parente
            **kwargs: Arguments nommés passés à la méthode parente

        Note:
            Si total_ligne est explicitement fourni et différent du calcul,
            il sera écrasé par le calcul automatique.

        Example:
            >>> ligne = LigneCommande(
            ...     commande=commande,
            ...     reference_produit='PROD001',
            ...     nom_produit='Produit A',
            ...     quantite=3,
            ...     prix_unitaire=Decimal('10.00')
            ... )
            >>> ligne.save()
            >>> ligne.total_ligne
            Decimal('30.00')
        """
        # Calcul automatique du total de la ligne
        self.total_ligne = self.quantite * self.prix_unitaire

        # Appel de la méthode save parente pour persister en base
        super().save(*args, **kwargs)
